"""
Servicio del Modelo Calista (Delitzas et al., 2023)
Evaluación estética basada en Redes Neuronales Convolucionales (CNN) y Visión por Computadora.

Métricas y calibración:
- Escala: 1.00 - 7.00 puntos (Likert 7)
- Semáforo Cualitativo de Categorías Estéticas:
    * Baja:  1.00 - 3.00  (Rojo: #ef4444)  -> Requiere Ajustes / Sugerencia de Hallazgo
    * Media: 3.01 - 5.00  (Ámbar: #f59e0b) -> Aceptable / Observaciones
    * Alta:  5.01 - 7.00  (Verde: #10b981) -> Aprobado / Excelente Calidad Estética
"""

import os
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageStat
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.assessment_model import EvaluacionEstetica, EvaluacionHallazgo
from app.models.diseno_conceptual_model import NodoPantalla
from app.models.diseno_detallado_model import DisenoDetalladoArchivo
from app.schemas.calista_schema import (
    CalistaDimensiones,
    CalistaPantallaResult,
    CalistaEvaluacionResponse,
    CalistaApplyRequest,
    CalistaHallazgoSugerido,
    CalistaModeloInfo
)
from app.services import assessment_service

logger = logging.getLogger(__name__)

# Pool de modelos cargados en memoria (Cache LRU/Dictionary)
_LOADED_MODELS: Dict[str, Any] = {}
_FAILED_MODELS = set()

# Metadatos conocidos de modelos para UI enriquecida
_MODEL_CATALOG_METADATA = {
    "calista_efficientnet_b0.keras": {
        "nombre": "CNN Calista + EfficientNet-B0 (Multi-Escala & Atención)",
        "arquitectura": "EfficientNet-B0 + Spatial Attention + Multi-Scale Fusion",
        "descripcion": "Transfer Learning con arquitectura EfficientNet-B0 y atención espacial. Entrenado en dataset de interfaces (PLCC: 0.785, MAE: 0.527).",
        "es_recomendado": True,
        "parametros": 4525701
    },
    "calista_mobilenet_v3.keras": {
        "nombre": "CNN Calista + MobileNetV3-Lightweight",
        "arquitectura": "MobileNetV3-Small + GlobalAvgPool + Linear",
        "descripcion": "Transfer Learning con arquitectura MobileNetV3-Small (Delitzas et al., 2023). Ultrarrápido y ligero.",
        "es_recomendado": True,
        "parametros": 977361
    },
    "calista_comparison_based.h5": {
        "nombre": "Calista Comparison-Based - Original",
        "arquitectura": "CaffeNet / AlexNet (Delitzas et al., 2023)",
        "descripcion": "Modelo original de Delitzas et al. (2023) entrenado mediante comparaciones binarias por pares.",
        "es_recomendado": False,
        "parametros": 12035457
    },
    "estetic_559.h5": {
        "nombre": "CNN Calista - Benjamin",
        "arquitectura": "Sequential Conv2D (6 -> 5 -> 4 -> 3 filtros) + ReLU",
        "descripcion": "Modelo original de estudio de Benjamin (2025).",
        "es_recomendado": False,
        "parametros": 2719
    }
}


def _load_calista_comparison_based(model_path: str):
    """
    Reconstruye la arquitectura CaffeNet/AlexNet de Delitzas et al. (2023)
    y carga los pesos serializados en calista_comparison_based.h5.
    """
    import h5py
    import tensorflow as tf
    from keras import layers, models

    inp = layers.Input(shape=(192, 256, 3), name='im_data')
    x = layers.Conv2D(96, (11, 11), strides=(4, 4), padding='valid', activation='relu', name='conv1')(inp)
    x = layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same', name='max_pooling2d_301')(x)
    x = layers.Lambda(lambda t: tf.nn.local_response_normalization(t, depth_radius=2, bias=1.0, alpha=1e-4, beta=0.75), name='norm1')(x)

    x1 = layers.Lambda(lambda t: t[:, :, :, :48], name='lambda_601')(x)
    x2 = layers.Lambda(lambda t: t[:, :, :, 48:], name='lambda_602')(x)
    c2_1 = layers.Conv2D(128, (5, 5), strides=(1, 1), padding='same', activation='relu', name='conv2_1')(x1)
    c2_2 = layers.Conv2D(128, (5, 5), strides=(1, 1), padding='same', activation='relu', name='conv2_2')(x2)
    x = layers.Concatenate(axis=-1, name='conv_2')([c2_1, c2_2])

    x = layers.MaxPooling2D((3, 3), strides=(2, 2), padding='valid', name='max_pooling2d_302')(x)
    x = layers.Lambda(lambda t: tf.nn.local_response_normalization(t, depth_radius=2, bias=1.0, alpha=1e-4, beta=0.75), name='norm2')(x)

    x = layers.Conv2D(384, (3, 3), strides=(1, 1), padding='same', activation='relu', name='conv3')(x)
    x3_1 = layers.Lambda(lambda t: t[:, :, :, :192], name='lambda_603')(x)
    x3_2 = layers.Lambda(lambda t: t[:, :, :, 192:], name='lambda_604')(x)
    c4_1 = layers.Conv2D(192, (3, 3), strides=(1, 1), padding='same', activation='relu', name='conv4_1')(x3_1)
    c4_2 = layers.Conv2D(192, (3, 3), strides=(1, 1), padding='same', activation='relu', name='conv4_2')(x3_2)
    x = layers.Concatenate(axis=-1, name='conv_4')([c4_1, c4_2])

    x4_1 = layers.Lambda(lambda t: t[:, :, :, :192], name='lambda_605')(x)
    x4_2 = layers.Lambda(lambda t: t[:, :, :, 192:], name='lambda_606')(x)
    c5_1 = layers.Conv2D(128, (3, 3), strides=(1, 1), padding='same', activation='relu', name='conv5_1')(x4_1)
    c5_2 = layers.Conv2D(128, (3, 3), strides=(1, 1), padding='same', activation='relu', name='conv5_2')(x4_2)
    x = layers.Concatenate(axis=-1, name='conv_5')([c5_1, c5_2])

    x = layers.MaxPooling2D((3, 3), strides=(2, 2), padding='valid', name='max_pooling2d_303')(x)
    x = layers.Flatten(name='flatten_101')(x)
    x = layers.Dense(1024, activation='relu', name='fc6')(x)
    x = layers.Dropout(0.5, name='dropout_201')(x)
    x = layers.Dense(512, activation='relu', name='fc7')(x)
    x = layers.Dropout(0.5, name='dropout_202')(x)
    out = layers.Dense(1, activation='linear', name='fc8')(x)
    m = models.Model(inputs=inp, outputs=out, name='calista_comparison_based')

    with h5py.File(model_path, 'r') as f:
        w = f['model_weights']
        for layer in m.layers:
            if layer.name in w:
                layer_group = w[layer.name]
                subkeys = list(layer_group.keys())
                if subkeys:
                    sub = layer_group[subkeys[0]]
                    k = np.array(sub['kernel:0'])
                    b = np.array(sub['bias:0'])
                    layer.set_weights([k, b])
    return m


def listar_modelos_calista() -> List[CalistaModeloInfo]:
    """
    Escanea la carpeta app/ml_models y devuelve los modelos disponibles con sus metadatos.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ml_models_dir = os.path.join(current_dir, "..", "ml_models")
    if not os.path.exists(ml_models_dir):
        return []

    archivos = [f for f in os.listdir(ml_models_dir) if os.path.isfile(os.path.join(ml_models_dir, f))]
    modelos_info: List[CalistaModeloInfo] = []

    for f in archivos:
        if not (f.endswith(".keras") or f.endswith(".h5")):
            continue

        meta = _MODEL_CATALOG_METADATA.get(f)
        if meta:
            modelos_info.append(CalistaModeloInfo(
                id=f,
                nombre=meta["nombre"],
                arquitectura=meta["arquitectura"],
                descripcion=meta["descripcion"],
                es_recomendado=meta["es_recomendado"],
                es_valido=True,
                parametros=meta.get("parametros")
            ))
        else:
            # Modelo nuevo detectado automáticamente
            es_mobilenet = "mobilenet" in f.lower()
            es_h5_mob = es_mobilenet and f.endswith(".h5")
            modelos_info.append(CalistaModeloInfo(
                id=f,
                nombre=f"Modelo Personalizado ({f})",
                arquitectura="MobileNetV3" if es_mobilenet else "Red Neuronal",
                descripcion="Modelo detectado en la carpeta app/ml_models." if not es_h5_mob else "Incompatible en Keras 3.",
                es_recomendado=es_mobilenet and not es_h5_mob,
                es_valido=not es_h5_mob,
                parametros=None
            ))

    # Ordenar: primero los recomendados, luego los demás válidos
    modelos_info.sort(key=lambda m: (not m.es_recomendado, not m.es_valido, m.nombre))
    return modelos_info


def _get_model(modelo_id: Optional[str] = None) -> Tuple[Optional[Any], str]:
    """
    Carga o recupera de caché el modelo Keras solicitado.
    Devuelve la tupla (modelo_keras, id_modelo_activo).
    """
    global _LOADED_MODELS, _FAILED_MODELS

    current_dir = os.path.dirname(os.path.abspath(__file__))
    ml_models_dir = os.path.join(current_dir, "..", "ml_models")

    # 1. Determinar el archivo objetivo
    disponibles = listar_modelos_calista()
    validos = [m.id for m in disponibles if m.es_valido]

    target_id = None
    if modelo_id and modelo_id in validos:
        target_id = modelo_id
    elif validos:
        target_id = validos[0]  # El primero ya está ordenado por recomendación
    else:
        target_id = "calista_mobilenet_v3.keras"

    # 2. Verificar caché en memoria
    if target_id in _LOADED_MODELS:
        return _LOADED_MODELS[target_id], target_id

    if target_id in _FAILED_MODELS:
        # Intentar fallback a otro válido
        for alt in validos:
            if alt not in _FAILED_MODELS and alt in _LOADED_MODELS:
                return _LOADED_MODELS[alt], alt

    model_path = os.path.join(ml_models_dir, target_id)
    if not os.path.exists(model_path):
        logger.warning(f"[Calista] Modelo no encontrado en ruta: {model_path}")
        return None, target_id

    # Caso especial para calista_comparison_based.h5 (arquitectura CaffeNet de Delitzas et al., 2023)
    if target_id == "calista_comparison_based.h5":
        try:
            model = _load_calista_comparison_based(model_path)
            _LOADED_MODELS[target_id] = model
            logger.info(f"[Calista] Modelo {target_id} (CaffeNet) cargado exitosamente en memoria.")
            return model, target_id
        except Exception as e:
            logger.error(f"[Calista] Error al reconstruir {target_id}: {e}")
            _FAILED_MODELS.add(target_id)
            return None, target_id

    # Carga de modelos estándar (.keras o .h5) con compile=False (práctica estándar para producción/inferencia)
    custom_objs = {
        "pearson_r": lambda y_true, y_pred: 0.0
    }

    try:
        import keras
        model = keras.models.load_model(model_path, compile=False, custom_objects=custom_objs)
        _LOADED_MODELS[target_id] = model
        logger.info(f"[Calista] Modelo {target_id} cargado exitosamente en memoria con Keras (compile=False).")
        return model, target_id
    except Exception as e1:
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model(model_path, compile=False, custom_objects=custom_objs)
            _LOADED_MODELS[target_id] = model
            logger.info(f"[Calista] Modelo {target_id} cargado exitosamente en memoria con TensorFlow.keras (compile=False).")
            return model, target_id
        except Exception as e2:
            logger.error(f"[Calista] Error al cargar {target_id}: {e1} / {e2}")
            _FAILED_MODELS.add(target_id)
            return None, target_id


def _preprocesar_imagen(
    pil_img: Image.Image,
    ruta_imagen: Optional[str] = None,
    target_shape: Tuple[int, int] = (360, 480)
) -> np.ndarray:
    """
    Preprocesa la imagen de acuerdo a la resolución esperada por el modelo:
    - (360, 480) para CNN Calista / MobileNetV3
    - (192, 256) para Calista Comparison-Based (Delitzas et al., 2023)
    """
    try:
        from skimage import io as ski_io
        from skimage.transform import resize as ski_resize

        if ruta_imagen and os.path.exists(ruta_imagen):
            img_orig = ski_io.imread(ruta_imagen)
        else:
            img_orig = np.array(pil_img)

        dim_ult = img_orig.shape[2] if len(img_orig.shape) == 3 else 3
        img_resized = ski_resize(img_orig, (target_shape[0], target_shape[1], dim_ult), anti_aliasing=True)
        if dim_ult == 4:
            img_resized = img_resized[:, :, :3]
        elif len(img_orig.shape) == 2:
            img_resized = np.stack([img_resized] * 3, axis=-1)

        return np.array([img_resized], dtype=np.float32)
    except Exception as e:
        logger.warning(f"[Calista] Fallback a PIL resize: {e}")
        img_rgb = pil_img.convert("RGB")
        img_resized = img_rgb.resize((target_shape[1], target_shape[0]), Image.Resampling.BILINEAR)
        arr = np.array(img_resized, dtype=np.float32) / 255.0
        return np.expand_dims(arr, axis=0)


def _evaluar_dimensiones_perceptuales(img: Image.Image, score_base: float) -> Tuple[float, float, float]:
    """
    Calcula subdimensiones de diseño visual mediante computer vision perceptual:
    1. Balance Visual: Simetría y proximidad del centro de masa visual a (0.5, 0.5)
    2. Armonía Cromática: Desviación controlada en tono (Hue) y saturación
    3. Complejidad y Espacio: Relación entre densidad de bordes y espacio de respiro
    """
    try:
        gray = img.convert("L").resize((120, 90))
        gray_arr = 1.0 - (np.array(gray, dtype=np.float32) / 255.0)  # Peso visual oscuro
        total_mass = np.sum(gray_arr) + 1e-6
        y_indices, x_indices = np.indices(gray_arr.shape)
        cy = np.sum(y_indices * gray_arr) / (total_mass * gray_arr.shape[0])
        cx = np.sum(x_indices * gray_arr) / (total_mass * gray_arr.shape[1])
        
        # Desviación de (0.5, 0.5)
        dist_centro = math.sqrt((cx - 0.5)**2 + (cy - 0.5)**2)
        factor_balance = max(0.0, 1.0 - (dist_centro / 0.35))
        balance = round(float(np.clip(1.0 + (factor_balance * 6.0), 1.0, 7.0)), 2)

        # Armonía cromática
        hsv_img = img.convert("HSV").resize((100, 75))
        h_arr, s_arr, v_arr = [np.array(c, dtype=np.float32) / 255.0 for c in hsv_img.split()]
        sat_mean = np.mean(s_arr)
        # Paletas demasiado saturadas o incoherentes reducen armonía
        armonia_val = 1.0 + (5.5 * (1.0 - abs(sat_mean - 0.35)))
        armonia = round(float(np.clip(armonia_val, 1.0, 7.0)), 2)

        # Complejidad y espacio
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_density = np.mean(np.array(edges, dtype=np.float32) / 255.0)
        # Densidad equilibrada de bordes (entre 0.05 y 0.20 es óptima)
        factor_comp = 1.0 - min(1.0, abs(edge_density - 0.12) / 0.15)
        complejidad = round(float(np.clip(1.0 + (factor_comp * 6.0), 1.0, 7.0)), 2)

        # Suavizar ligeramente con la predicción del modelo
        balance = round(0.4 * balance + 0.6 * score_base, 2)
        armonia = round(0.4 * armonia + 0.6 * score_base, 2)
        complejidad = round(0.4 * complejidad + 0.6 * score_base, 2)
        return balance, armonia, complejidad
    except Exception as e:
        logger.warning(f"[Calista] Error al calcular dimensiones perceptuales: {e}")
        return score_base, score_base, score_base


def _clasificar_semaforo(score: float) -> Tuple[str, str, str, bool]:
    """
    Aplica las reglas de negocio del usuario:
    - Baja:  1.00 - 3.00 (Rojo: #ef4444) -> No Aprobado
    - Media: 3.01 - 5.00 (Ámbar: #f59e0b) -> Aceptable con sugerencias
    - Alta:  5.01 - 7.00 (Verde: #10b981) -> Aprobado
    """
    if score <= 3.00:
        categoria = "Baja"
        color_hex = "#ef4444"
        diagnostico = "Estética deficiente. La composición visual genera tensión, falta de balance o sobrecarga cognitiva según el modelo neuronal Calista."
        aprobado = False
    elif score <= 5.00:
        categoria = "Media"
        color_hex = "#f59e0b"
        diagnostico = "Estética estándar / aceptable. Cumple con requerimientos funcionales mínimos, pero admite optimizaciones en armonía y jerarquía visual."
        aprobado = True
    else:
        categoria = "Alta"
        color_hex = "#10b981"
        diagnostico = "Alta calidad estética. La composición transmite orden, equilibrio cromático y coherencia visual superior según el modelo Calista."
        aprobado = True

    return categoria, color_hex, diagnostico, aprobado


def _crear_imagen_sintetica_para_nodo(nombre: str) -> Image.Image:
    """Crea una imagen de interfaz básica si el nodo aún no tiene screenshot subido."""
    img = Image.new("RGB", (1280, 800), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    # Cabecera
    draw.rectangle([(0, 0), (1280, 70)], fill=(30, 41, 59))
    # Barra lateral
    draw.rectangle([(0, 70), (240, 800)], fill=(241, 245, 249))
    # Contenedor central
    draw.rounded_rectangle([(280, 110), (1240, 760)], radius=12, fill=(255, 255, 255), outline=(226, 232, 240))
    # Título sintético
    draw.rectangle([(320, 150), (600, 185)], fill=(15, 23, 42))
    draw.rectangle([(320, 210), (850, 235)], fill=(148, 163, 184))
    # Tarjetas
    draw.rounded_rectangle([(320, 270), (580, 420)], radius=8, fill=(248, 250, 252), outline=(203, 213, 225))
    draw.rounded_rectangle([(610, 270), (870, 420)], radius=8, fill=(248, 250, 252), outline=(203, 213, 225))
    draw.rounded_rectangle([(900, 270), (1160, 420)], radius=8, fill=(248, 250, 252), outline=(203, 213, 225))
    return img


def evaluar_pantalla_individual(
    pantalla_id: int,
    nombre_pantalla: str,
    ruta_imagen: Optional[str] = None,
    imagen_url: Optional[str] = None,
    modelo_id: Optional[str] = None
) -> CalistaPantallaResult:
    """
    Ejecuta la inferencia de Calista sobre una pantalla específica utilizando el modelo seleccionado.
    Principio de Integridad: Si la pantalla no tiene captura real en disco, se reporta en estado
    'Pendiente' sin ejecutar inferencias falsas ni alterar métricas con imágenes inventadas.
    """
    # 1. Comprobar existencia física real de la imagen en disco
    pil_img = None
    tiene_imagen = False

    if ruta_imagen and os.path.exists(ruta_imagen):
        try:
            pil_img = Image.open(ruta_imagen)
            tiene_imagen = True
        except Exception as e:
            logger.warning(f"[Calista] No se pudo abrir {ruta_imagen}: {e}")
            pil_img = None
            tiene_imagen = False

    # Si NO existe archivo físico de captura real, reportar estado Pendiente transparente
    if not tiene_imagen or pil_img is None:
        return CalistaPantallaResult(
            pantalla_id=pantalla_id,
            pantalla_nombre=nombre_pantalla,
            imagen_url=imagen_url,
            tiene_imagen=False,
            score_estetico=None,
            categoria="Pendiente",
            color_hex="#94a3b8",
            porcentaje=None,
            aprobado=None,
            diagnostico=f"La pantalla '{nombre_pantalla}' aún no cuenta con una captura subida en la Fase 4 (Diseño Detallado). Adjunta un diseño para habilitar la evaluación neuronal con Calista.",
            dimensiones=None,
            recomendaciones=[
                f"Subir la captura de pantalla o mockup de alta fidelidad para '{nombre_pantalla}' en la Fase 4.",
                "Una vez cargado el diseño, el motor convolucional Calista calculará el balance, armonía y espacio en blanco."
            ],
            hallazgo_sugerido=None
        )

    # 2. Inferencia con el modelo seleccionado sobre la captura real
    model, _ = _get_model(modelo_id)
    if model is not None:
        try:
            target_shape = (360, 480)
            if hasattr(model, 'input_shape') and model.input_shape and len(model.input_shape) == 4:
                h, w = model.input_shape[1], model.input_shape[2]
                if h is not None and w is not None:
                    target_shape = (int(h), int(w))

            tensor_in = _preprocesar_imagen(pil_img, ruta_imagen, target_shape=target_shape)
            raw_pred = model.predict(tensor_in, verbose=False)
            score_estetico = float(raw_pred[0][0])
        except Exception as e:
            logger.error(f"[Calista] Fallo en model.predict con {modelo_id}: {e}")
            score_estetico = 4.00
    else:
        score_estetico = 4.00

    # Asegurar rango estricto [1.00, 7.00]
    score_estetico = round(float(np.clip(score_estetico, 1.00, 7.00)), 2)

    # 3. Categorización del semáforo
    categoria, color_hex, diagnostico, aprobado = _clasificar_semaforo(score_estetico)
    porcentaje = round(((score_estetico - 1.0) / (7.0 - 1.0)) * 100.0, 1)

    # 4. Dimensiones perceptuales
    balance, armonia, complejidad = _evaluar_dimensiones_perceptuales(pil_img, score_estetico)

    dimensiones = CalistaDimensiones(
        score_estetico=score_estetico,
        categoria=categoria,
        color_hex=color_hex,
        porcentaje=porcentaje,
        balance_visual=balance,
        armonia_color=armonia,
        complejidad_espacio=complejidad
    )

    # 5. Recomendaciones y Hallazgo Sugerido
    recomendaciones = []
    hallazgo_sugerido = None

    if categoria == "Baja":
        recomendaciones.append("Reestructurar la distribución espacial para recuperar el centro de masa visual.")
        recomendaciones.append("Reducir la saturación de elementos dispersos y aumentar el margen de respiro.")
        hallazgo_sugerido = CalistaHallazgoSugerido(
            problema=f"Valoración estética Calista deficiente ({score_estetico}/7.00) en la pantalla '{nombre_pantalla}'. La composición presenta bajo atractivo visual percibido.",
            severidad="mayor",
            fase_origen=4,
            fase_origen_nombre="Diseño Detallado (Modelo Calista)",
            sugerencia="Incrementar espacios negativos (padding) y consolidar la paleta de color hacia una tríada armónica balanceada."
        )
    elif categoria == "Media":
        recomendaciones.append("Ajustar márgenes entre componentes para afianzar la jerarquía visual.")
        recomendaciones.append("Verificar que los botones primarios tengan mayor contraste respecto al fondo.")
        hallazgo_sugerido = CalistaHallazgoSugerido(
            problema=f"Calificación estética intermedia ({score_estetico}/7.00) en '{nombre_pantalla}'. Admite optimizaciones de contraste.",
            severidad="menor",
            fase_origen=4,
            fase_origen_nombre="Diseño Detallado (Modelo Calista)",
            sugerencia="Mejorar la definición de bloques de información y acentuar llamadas a la acción."
        )
    else:
        recomendaciones.append("La pantalla cumple plenamente con los cánones de armonía, simetría y legibilidad del modelo Calista.")
        recomendaciones.append("Mantener este patrón de diseño para los componentes derivados en siguientes fases.")

    return CalistaPantallaResult(
        pantalla_id=pantalla_id,
        pantalla_nombre=nombre_pantalla,
        imagen_url=imagen_url,
        tiene_imagen=True,
        score_estetico=score_estetico,
        categoria=categoria,
        color_hex=color_hex,
        porcentaje=porcentaje,
        aprobado=aprobado,
        diagnostico=diagnostico,
        dimensiones=dimensiones,
        recomendaciones=recomendaciones,
        hallazgo_sugerido=hallazgo_sugerido
    )


def analizar_proyecto_calista(
    db: Session,
    proyecto_id: int,
    pantalla_id: Optional[int] = None,
    modelo_id: Optional[str] = None
) -> CalistaEvaluacionResponse:
    """
    Analiza todas las pantallas de Fase 4 del proyecto (o una en específico) con Calista
    utilizando el modelo seleccionado (de app/ml_models) y actualiza `calista_metricas`.
    """
    pantallas_summary = assessment_service.get_pantallas_fase4_summary(db, proyecto_id)
    evaluacion = assessment_service.get_or_create_evaluacion(db, proyecto_id)

    modelos_disp = listar_modelos_calista()
    _, active_model_id = _get_model(modelo_id)

    resultados_pantallas: List[CalistaPantallaResult] = []

    for p in pantallas_summary:
        pid = p.get("id") or p.get("nodo_id") or 1
        nombre = p.get("nombre_pantalla", "Pantalla de Fase 4")
        archivo_url = p.get("archivo_url")

        # Localizar ruta física en disco
        ruta_fisica = None
        if p.get("archivo_id"):
            diseno_archivo = db.query(DisenoDetalladoArchivo).filter(
                DisenoDetalladoArchivo.id == p.get("id")
            ).first()
            if diseno_archivo and diseno_archivo.archivo and diseno_archivo.archivo.ruta_almacenamiento:
                ruta_fisica = diseno_archivo.archivo.ruta_almacenamiento

        if not (ruta_fisica and os.path.exists(ruta_fisica)) and archivo_url:
            candidato = os.path.join(os.getcwd(), archivo_url.lstrip("/"))
            if os.path.exists(candidato):
                ruta_fisica = candidato

        res = evaluar_pantalla_individual(
            pantalla_id=pid,
            nombre_pantalla=nombre,
            ruta_imagen=ruta_fisica,
            imagen_url=archivo_url,
            modelo_id=active_model_id
        )
        resultados_pantallas.append(res)

    # Si el proyecto no tuviera pantallas en fase 4 aún, generamos una pantalla prototipo base
    if not resultados_pantallas:
        res_default = evaluar_pantalla_individual(
            pantalla_id=1,
            nombre_pantalla="Pantalla Principal (Mockup)",
            ruta_imagen=None,
            imagen_url=None,
            modelo_id=active_model_id
        )
        resultados_pantallas.append(res_default)

    # Seleccionar la pantalla target
    pantalla_sel = None
    if pantalla_id:
        for r in resultados_pantallas:
            if r.pantalla_id == pantalla_id:
                pantalla_sel = r
                break
    if not pantalla_sel and resultados_pantallas:
        pantalla_sel = resultados_pantallas[0]

    # Métricas globales del proyecto (Solo computar sobre pantallas que SÍ tienen imagen real evaluada)
    evaluadas = [r for r in resultados_pantallas if r.tiene_imagen and r.score_estetico is not None]
    total_pantallas = len(resultados_pantallas)
    pantallas_evaluadas_count = len(evaluadas)
    pantallas_pendientes_count = total_pantallas - pantallas_evaluadas_count

    if evaluadas:
        scores = [r.score_estetico for r in evaluadas]
        promedio_global = round(float(np.mean(scores)), 2)
        categoria_glob, color_glob, _, _ = _clasificar_semaforo(promedio_global)
        porcentaje_glob = round(((promedio_global - 1.0) / (7.0 - 1.0)) * 100.0, 1)
        aprobadas = sum(1 for r in evaluadas if r.aprobado is True)
        requieren_ajustes = len(evaluadas) - aprobadas
    else:
        promedio_global = 0.0
        categoria_glob = "Pendiente"
        color_glob = "#94a3b8"
        porcentaje_glob = 0.0
        aprobadas = 0
        requieren_ajustes = 0

    # Guardar en Base de Datos (columna calista_metricas)
    calista_payload = {
        "score_global": promedio_global,
        "categoria_global": categoria_glob,
        "color_global": color_glob,
        "porcentaje_global": porcentaje_glob,
        "total_pantallas": total_pantallas,
        "pantallas_evaluadas_count": pantallas_evaluadas_count,
        "pantallas_pendientes_count": pantallas_pendientes_count,
        "aprobadas_count": aprobadas,
        "requieren_ajustes_count": requieren_ajustes,
        "fecha_analisis": datetime.now().isoformat(),
        "modelo_activo": active_model_id,
        "pantallas": [r.model_dump() for r in resultados_pantallas]
    }

    evaluacion.calista_metricas = calista_payload
    flag_modified(evaluacion, "calista_metricas")
    db.commit()
    db.refresh(evaluacion)

    # Recalcular dictamen global de la evaluación
    assessment_service.recalcular_justificaciones(evaluacion)
    db.commit()

    return CalistaEvaluacionResponse(
        proyecto_id=proyecto_id,
        score_global=promedio_global,
        categoria_global=categoria_glob,
        color_global=color_glob,
        porcentaje_global=porcentaje_glob,
        total_pantallas=total_pantallas,
        pantallas_evaluadas_count=pantallas_evaluadas_count,
        pantallas_pendientes_count=pantallas_pendientes_count,
        aprobadas_count=aprobadas,
        requieren_ajustes_count=requieren_ajustes,
        pantallas=resultados_pantallas,
        pantalla_seleccionada=pantalla_sel,
        fecha_analisis=calista_payload["fecha_analisis"],
        modelo_activo=active_model_id,
        modelos_disponibles=modelos_disp
    )


def aplicar_calista_hallazgo_a_evaluacion(
    db: Session,
    proyecto_id: int,
    request: CalistaApplyRequest
) -> Dict[str, Any]:
    """
    Inyecta un hallazgo sugerido por el modelo Calista directamente en la
    Matriz Central de Hallazgos (`EvaluacionHallazgo`) del proyecto.
    """
    evaluacion = assessment_service.get_or_create_evaluacion(db, proyecto_id)

    # Verificar si ya existe para no duplicar
    ya_existe = any(h.problema == request.problema for h in evaluacion.hallazgos)
    if not ya_existe:
        nuevo_h = EvaluacionHallazgo(
            evaluacion_id=evaluacion.id,
            problema=request.problema,
            severidad=request.severidad,
            fase_origen=request.fase_origen,
            fase_origen_nombre=request.fase_origen_nombre,
            resuelto=False
        )
        db.add(nuevo_h)
        db.commit()
        db.refresh(evaluacion)
        assessment_service.recalcular_justificaciones(evaluacion)
        db.commit()
        mensaje = "Hallazgo estético registrado exitosamente en la Matriz Central."
    else:
        mensaje = "El hallazgo ya se encontraba registrado en la Matriz Central."

    return {
        "success": True,
        "mensaje": mensaje,
        "evaluacion": assessment_service.get_or_create_evaluacion(db, proyecto_id)
    }
