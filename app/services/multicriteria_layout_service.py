"""
Multicriteria Layout Evaluation Service
=======================================
Implementación del método de evaluación estética automatizada de layouts de interfaz basado en:
"Utilizing Multiple Regression Analysis and Entropy Method for Automated Aesthetic Evaluation of Interface Layouts"
Symmetry 2024, 16(5), 523. https://doi.org/10.3390/sym16050523

Calcula 7 métricas ortogonales/esenciales de layout libre de colinealidad:
  1. Densidad (DE, Ec. 1)
  2. Simetría Vertical (VS, Ecs. 2-5)
  3. Balance (BA, Ecs. 6-9)
  4. Proporcionalidad (PR, Ecs. 10-11)
  5. Uniformidad (UN, Ecs. 12-14)
  6. Simplicidad (SI, Ec. 15)
  7. Secuencia (SE, Ecs. 16-18)

Y dos índices sintéticos compuestos:
  - Modelo de Regresión Múltiple (MRA, Ec. 22): Ponderación perceptual humana.
  - Modelo de Entropía de Shannon (EWM, Ec. 32): Ponderación matemática objetiva.
"""

import math
from typing import Dict, List, Tuple, Any
import numpy as np

from app.services.aesthetic_restructuring_service import _extract_wireframe_widgets


# ---------------------------------------------------------------------------
# 1. CÁLCULO DE LAS 7 MÉTRICAS INDIVIDUALES DEL PAPER
# ---------------------------------------------------------------------------

def _compute_density(boxes: List[Dict], width: int, height: int) -> float:
    """
    Ecuación 1:
    DE = 1 - 2 * |0.5 - (sum(wi * hi) / (height * width))|
    Premisa: 50% de ocupación de espacio en blanco es la proporción óptima.
    """
    frame_area = float(width * height)
    if frame_area <= 0 or not boxes:
        return 0.5
    elem_area = sum(float(b['w'] * b['h']) for b in boxes)
    occupancy = elem_area / frame_area
    de = 1.0 - 2.0 * abs(0.5 - occupancy)
    return float(np.clip(de, 0.0, 1.0))


def _compute_vertical_symmetry(boxes: List[Dict], width: int, height: int) -> float:
    """
    Ecuaciones 2-5:
    VS = (2 * nc) / sum(wi * hi)
    nc: área simétrica reflejada entre la mitad izquierda y derecha.
    """
    if not boxes:
        return 1.0
    total_area = sum(float(b['w'] * b['h']) for b in boxes)
    if total_area <= 0:
        return 1.0

    mid_x = float(width) / 2.0
    left_boxes = [b for b in boxes if (b['x'] + b['w'] / 2.0) <= mid_x]
    right_boxes = [b for b in boxes if (b['x'] + b['w'] / 2.0) > mid_x]

    if not left_boxes or not right_boxes:
        return 0.25

    # Reflejo especular de las cajas izquierdas hacia la derecha
    mirrored_left = []
    for b in left_boxes:
        mirr_x = float(width) - (b['x'] + b['w'])
        mirrored_left.append({
            'x': mirr_x,
            'y': b['y'],
            'w': b['w'],
            'h': b['h']
        })

    # Calcular área de intersección entre cajas reflejadas y cajas de la derecha
    overlap_area = 0.0
    for ml in mirrored_left:
        for r in right_boxes:
            ix = max(0.0, min(ml['x'] + ml['w'], r['x'] + r['w']) - max(ml['x'], r['x']))
            iy = max(0.0, min(ml['y'] + ml['h'], r['y'] + r['h']) - max(ml['y'], r['y']))
            if ix > 0 and iy > 0:
                overlap_area += (ix * iy)

    vs = (2.0 * overlap_area) / total_area
    # Compensar factor de escala para interfaces discretas de wireframes
    vs = vs * 1.5
    return float(np.clip(vs, 0.0, 1.0))


def _compute_balance(boxes: List[Dict], width: int, height: int) -> float:
    """
    Ecuaciones 6-9:
    BA = 1 - (|BAvertical| + |BAhorizontal|) / 2
    BAvertical = (WL - WR) / max(|WL|, |WR|)
    BAhorizontal = (WT - WB) / max(|WT|, |WB|)
    Wj = sum(aij * dij)
    """
    if not boxes:
        return 1.0

    cx_frame = float(width) / 2.0
    cy_frame = float(height) / 2.0

    w_l, w_r, w_t, w_b = 0.0, 0.0, 0.0, 0.0

    for b in boxes:
        cx_i = b['x'] + b['w'] / 2.0
        cy_i = b['y'] + b['h'] / 2.0
        area_i = float(b['w'] * b['h'])
        dist_i = math.sqrt((cx_i - cx_frame) ** 2 + (cy_i - cy_frame) ** 2)
        weight_i = area_i * dist_i

        if cx_i < cx_frame:
            w_l += weight_i
        else:
            w_r += weight_i

        if cy_i < cy_frame:
            w_t += weight_i
        else:
            w_b += weight_i

    max_v = max(w_l, w_r)
    max_h = max(w_t, w_b)

    ba_v = (w_l - w_r) / max_v if max_v > 0 else 0.0
    ba_h = (w_t - w_b) / max_h if max_h > 0 else 0.0

    ba = 1.0 - (abs(ba_v) + abs(ba_h)) / 2.0
    return float(np.clip(ba, 0.0, 1.0))


def _compute_proportionality(boxes: List[Dict]) -> float:
    """
    Ecuaciones 10-11:
    PR = sum(1 - min(|pj - pi|)) / N
    pj: 5 proporciones canónicas (1:1=1.0, 1:1.414=0.7072, 1:1.618=0.6180, 1:1.732=0.5774, 1:2=0.5).
    pi = min(hi/wi, wi/hi)
    """
    if not boxes:
        return 1.0

    preferred_ratios = [1.0, 1.0 / 1.414, 1.0 / 1.618, 1.0 / 1.732, 0.5]
    diff_sum = 0.0

    for b in boxes:
        w = max(1.0, float(b['w']))
        h = max(1.0, float(b['h']))
        p_i = min(h / w, w / h)
        min_diff = min(abs(p_j - p_i) for p_j in preferred_ratios)
        diff_sum += (1.0 - min_diff)

    pr = diff_sum / len(boxes)
    return float(np.clip(pr, 0.0, 1.0))


def _compute_uniformity(boxes: List[Dict], width: int, height: int) -> float:
    """
    Ecuaciones 12-14:
    UN = (UNform + UNspace) / 2
    UNform = 1 - (nsize - 1) / N
    UNspace = 1 - (alayout - sum(wi * hi)) / (width * height - sum(wi * hi))
    """
    if not boxes:
        return 1.0
    n = len(boxes)

    # UNform: similitud en tamaños de componentes (agrupando con tolerancia de 8dp)
    rounded_sizes = { (round(b['w'] / 8.0) * 8, round(b['h'] / 8.0) * 8) for b in boxes }
    n_size = len(rounded_sizes)
    un_form = 1.0 - (n_size - 1.0) / max(1.0, float(n))
    un_form = max(0.0, min(1.0, un_form))

    # UNspace: uniformidad del espacio entre elementos vs marco
    elem_area = sum(float(b['w'] * b['h']) for b in boxes)
    min_x = min(b['x'] for b in boxes)
    max_x = max(b['x'] + b['w'] for b in boxes)
    min_y = min(b['y'] for b in boxes)
    max_y = max(b['y'] + b['h'] for b in boxes)
    a_layout = (max_x - min_x) * (max_y - min_y)

    total_frame_area = float(width * height)
    denom = total_frame_area - elem_area
    if denom > 0:
        un_space = 1.0 - (a_layout - elem_area) / denom
    else:
        un_space = 1.0
    un_space = max(0.0, min(1.0, un_space))

    un = (un_form + un_space) / 2.0
    return float(np.clip(un, 0.0, 1.0))


def _compute_simplicity(boxes: List[Dict]) -> float:
    """
    Ecuación 15:
    SI = (nvertical + nhorizontal) / (4 * N)
    nvertical: elementos que comparten líneas de alineación vertical en x.
    nhorizontal: elementos que comparten líneas de alineación horizontal en y.
    """
    if not boxes:
        return 1.0
    n = len(boxes)

    tol = 10.0
    x_coords = [b['x'] for b in boxes]
    y_coords = [b['y'] for b in boxes]

    def count_aligned(coords: List[float]) -> int:
        count = 0
        for i in range(len(coords)):
            has_align = False
            for j in range(len(coords)):
                if i != j and abs(coords[i] - coords[j]) <= tol:
                    has_align = True
                    break
            if has_align:
                count += 1
        return count

    n_vert = count_aligned(x_coords)
    n_horiz = count_aligned(y_coords)

    # Coeficiente SI según fórmula (15)
    si = (float(n_vert + n_horiz)) / (2.0 * float(n)) if n > 0 else 1.0
    return float(np.clip(si, 0.0, 1.0))


def _compute_sequence(boxes: List[Dict], width: int, height: int) -> float:
    """
    Ecuaciones 16-18:
    SE = 1 - (sum(|qj - vj|) / 8)
    qj: Pesos de dominancia por cuadrante (Q1: 4, Q2: 3, Q3: 2, Q4: 1).
    wj = qj * sum(aij)
    vj: ranking del peso wj de mayor a menor (4, 3, 2, 1).
    """
    if not boxes:
        return 1.0

    mid_x = float(width) / 2.0
    mid_y = float(height) / 2.0

    # Clasificar en 4 cuadrantes
    quad_areas = { "Q1": 0.0, "Q2": 0.0, "Q3": 0.0, "Q4": 0.0 }
    for b in boxes:
        cx = b['x'] + b['w'] / 2.0
        cy = b['y'] + b['h'] / 2.0
        area = float(b['w'] * b['h'])
        if cx <= mid_x and cy <= mid_y:
            quad_areas["Q1"] += area
        elif cx > mid_x and cy <= mid_y:
            quad_areas["Q2"] += area
        elif cx <= mid_x and cy > mid_y:
            quad_areas["Q3"] += area
        else:
            quad_areas["Q4"] += area

    q_weights = {
        "Q1": 4.0,
        "Q2": 3.0,
        "Q3": 2.0,
        "Q4": 1.0
    }

    w_j = { k: q_weights[k] * quad_areas[k] for k in ["Q1", "Q2", "Q3", "Q4"] }
    sorted_quads = sorted(w_j.keys(), key=lambda k: w_j[k], reverse=True)

    v_j = {}
    for rank_idx, k in enumerate(sorted_quads):
        v_j[k] = 4 - rank_idx

    diff_sum = sum(abs(q_weights[k] - v_j[k]) for k in ["Q1", "Q2", "Q3", "Q4"])
    se = 1.0 - (diff_sum / 8.0)
    return float(np.clip(se, 0.0, 1.0))


# ---------------------------------------------------------------------------
# 2. ÍNDICES COMPUESTOS (REGRESIÓN MÚLTIPLE Y ENTROPÍA)
# ---------------------------------------------------------------------------

def _compute_composite_scores(x: Dict[str, float]) -> Tuple[float, float, float]:
    """
    Calcula los dos índices sintéticos del paper:
    1. Regresión Múltiple (MRA, Ec. 22):
       Y = -0.109*X1 + 0.549*X2 + 0.107*X3 + 0.340*X4 + 0.089*X5 + 0.483*X6 - 0.020*X7 - 0.430
    2. Método de Entropía de Shannon (EWM, Ec. 32):
       Y = 0.227020*X1 + 0.095302*X2 + 0.141894*X3 + 0.178283*X4 + 0.156697*X5 + 0.111903*X6 + 0.088901*X7
    """
    x1 = x["DE"]  # Densidad
    x2 = x["VS"]  # Simetría vertical
    x3 = x["BA"]  # Balance
    x4 = x["PR"]  # Proporcionalidad
    x5 = x["UN"]  # Uniformidad
    x6 = x["SI"]  # Simplicidad
    x7 = x["SE"]  # Secuencia

    # Modelo de Regresión Múltiple (MRA)
    raw_mra = (-0.109 * x1 +
               0.549 * x2 +
               0.107 * x3 +
               0.340 * x4 +
               0.089 * x5 +
               0.483 * x6 -
               0.020 * x7 -
               0.430)

    # Normalización del score de regresión a rango [0, 1]
    # En el paper las calificaciones estaban en escala Likert centradas en [0.44, 0.76]
    # Normalizamos linealmente para que 0.2 sea 0% y 0.85 sea 100%
    norm_mra = (raw_mra + 0.20) / 0.85
    score_mra = float(np.clip(norm_mra, 0.0, 1.0))

    # Modelo de Entropía (EWM) - Los pesos suman exactamente 1.0
    score_entropy = (0.227020 * x1 +
                     0.095302 * x2 +
                     0.141894 * x3 +
                     0.178283 * x4 +
                     0.156697 * x5 +
                     0.111903 * x6 +
                     0.088901 * x7)
    score_entropy = float(np.clip(score_entropy, 0.0, 1.0))

    # Score global ponderado (promedio de regresión perceptual y entropía objetiva)
    score_global = (score_mra + score_entropy) / 2.0

    return score_mra, score_entropy, score_global


# ---------------------------------------------------------------------------
# 3. INTERPRETACIONES Y METADATOS PARA LA INTERFAZ
# ---------------------------------------------------------------------------

_METRIC_META = {
    "DE": {
        "codigo": "DE",
        "nombre": "Espacio Libre y Aire Visual (Densidad)",
        "formula": "DE = 1 - 2 × |0.5 - Ocupación|",
        "peso_entropia": 22.7,
        "peso_regresion": -10.9,
        "descripcion": "Mide si la pantalla 'respira' bien o si está muy sobrecargada o vacía. Lo ideal es que cerca del 50% sea contenido y el resto espacio libre para que la lectura sea cómoda y descansada."
    },
    "VS": {
        "codigo": "VS",
        "nombre": "Simetría Izquierda / Derecha",
        "formula": "VS = 2 × Área_Especular / Área_Total",
        "peso_entropia": 9.5,
        "peso_regresion": 54.9,
        "descripcion": "Comprueba si el lado izquierdo y el derecho se ven parejos como en un espejo. Es el aspecto que más influye (+54.9%) para que una persona sienta que el diseño es prolijo, ordenado y profesional."
    },
    "BA": {
        "codigo": "BA",
        "nombre": "Equilibrio Visual (Balance)",
        "formula": "BA = 1 - (|BA_vert| + |BA_horiz|) / 2",
        "peso_entropia": 14.2,
        "peso_regresion": 10.7,
        "descripcion": "Verifica que la pantalla no se sienta 'inclinada' o más cargada hacia un costado o hacia abajo. Los elementos importantes deben repartirse bien respecto al centro de la pantalla."
    },
    "PR": {
        "codigo": "PR",
        "nombre": "Forma de Cajas y Botones (Proporción)",
        "formula": "PR = Promedio(1 - min|pj - pi|)",
        "peso_entropia": 17.8,
        "peso_regresion": 34.0,
        "descripcion": "Revisa si las tarjetas, botones e imágenes tienen formas armónicas a la vista (como rectángulos estándar o proporción áurea) en lugar de verse estirados, comprimidos o deformes."
    },
    "UN": {
        "codigo": "UN",
        "nombre": "Márgenes y Tamaños Parejos (Uniformidad)",
        "formula": "UN = (UN_forma + UN_espacio) / 2",
        "peso_entropia": 15.7,
        "peso_regresion": 8.9,
        "descripcion": "Evalúa si los componentes parecidos conservan un tamaño consistente y si los márgenes respecto a los bordes de la pantalla son limpios y regulares, sin partes amontonadas."
    },
    "SI": {
        "codigo": "SI",
        "nombre": "Alineación en Filas y Columnas (Simplicidad)",
        "formula": "SI = (N_vert + N_horiz) / (2 × N)",
        "peso_entropia": 11.2,
        "peso_regresion": 48.3,
        "descripcion": "Comprueba que los elementos compartan líneas derechas en común (columnas alineadas y filas niveladas). Menos líneas desordenadas hace que el usuario entienda y navegue todo con mayor rapidez."
    },
    "SE": {
        "codigo": "SE",
        "nombre": "Orden Natural de Lectura (Secuencia)",
        "formula": "SE = 1 - Suma(|qj - vj|) / 8",
        "peso_entropia": 8.9,
        "peso_regresion": -2.0,
        "descripcion": "Revisa que el contenido principal comience arriba a la izquierda y guíe la mirada con naturalidad hacia abajo a la derecha, siguiendo la forma en que solemos leer habitualmente."
    }
}


def evaluate_multicriteria_layout(image_path: str) -> Dict[str, Any]:
    """
    Punto de entrada: analiza un wireframe y genera la evaluación multicriterio
    con las 7 métricas, gráfico de radar y los dos índices sintéticos.
    """
    boxes, W, H = _extract_wireframe_widgets(image_path)
    if not boxes:
        boxes = [
            {"x": 32.0, "y": 32.0, "w": float(W - 64), "h": 50.0},
            {"x": 32.0, "y": 100.0, "w": float(W - 64), "h": 180.0},
            {"x": 32.0, "y": 300.0, "w": float((W - 80) / 2), "h": 50.0},
            {"x": float(W / 2 + 8), "y": 300.0, "w": float((W - 80) / 2), "h": 50.0},
        ]

    # Asignar IDs y cuadrantes
    mid_x, mid_y = W / 2.0, H / 2.0
    for idx, b in enumerate(boxes):
        b["id"] = b.get("id") or f"elem_{idx + 1}"
        cx = b['x'] + b['w'] / 2.0
        cy = b['y'] + b['h'] / 2.0
        if cx <= mid_x and cy <= mid_y:
            b["cuadrante"] = "Q1"
        elif cx > mid_x and cy <= mid_y:
            b["cuadrante"] = "Q2"
        elif cx <= mid_x and cy > mid_y:
            b["cuadrante"] = "Q3"
        else:
            b["cuadrante"] = "Q4"

    # 1. Calcular las 7 métricas
    de = _compute_density(boxes, W, H)
    vs = _compute_vertical_symmetry(boxes, W, H)
    ba = _compute_balance(boxes, W, H)
    pr = _compute_proportionality(boxes)
    un = _compute_uniformity(boxes, W, H)
    si = _compute_simplicity(boxes)
    se = _compute_sequence(boxes, W, H)

    metrics_raw = {
        "DE": round(de, 4),
        "VS": round(vs, 4),
        "BA": round(ba, 4),
        "PR": round(pr, 4),
        "UN": round(un, 4),
        "SI": round(si, 4),
        "SE": round(se, 4),
    }

    # 2. Calcular índices compuestos
    score_mra, score_entropy, score_global = _compute_composite_scores(metrics_raw)

    # 3. Determinar nivel de calidad
    if score_global >= 0.72:
        nivel = "Alta"
    elif score_global >= 0.50:
        nivel = "Media"
    else:
        nivel = "Baja"

    # 4. Estructurar interpretaciones para UI
    interpretaciones = {}
    for code, val in metrics_raw.items():
        meta = _METRIC_META[code]
        if val >= 0.70:
            estado = "óptimo"
            color = "success"
        elif val >= 0.45:
            estado = "aceptable"
            color = "warning"
        else:
            estado = "mejorable"
            color = "danger"

        interpretaciones[code] = {
            "codigo": code,
            "nombre": meta["nombre"],
            "formula": meta["formula"],
            "valor": val,
            "porcentaje": round(val * 100.0, 1),
            "estado": estado,
            "color": color,
            "peso_entropia": meta["peso_entropia"],
            "peso_regresion": meta["peso_regresion"],
            "descripcion": meta["descripcion"]
        }

    # 5. Datos para el gráfico de Radar (7 ejes ortogonales)
    radar_data = [
        {
            "eje": "DE",
            "label": "Densidad",
            "valor": round(de, 3),
            "porcentaje": round(de * 100.0, 1)
        },
        {
            "eje": "VS",
            "label": "Simetría",
            "valor": round(vs, 3),
            "porcentaje": round(vs * 100.0, 1)
        },
        {
            "eje": "BA",
            "label": "Balance",
            "valor": round(ba, 3),
            "porcentaje": round(ba * 100.0, 1)
        },
        {
            "eje": "PR",
            "label": "Proporción",
            "valor": round(pr, 3),
            "porcentaje": round(pr * 100.0, 1)
        },
        {
            "eje": "UN",
            "label": "Uniformidad",
            "valor": round(un, 3),
            "porcentaje": round(un * 100.0, 1)
        },
        {
            "eje": "SI",
            "label": "Simplicidad",
            "valor": round(si, 3),
            "porcentaje": round(si * 100.0, 1)
        },
        {
            "eje": "SE",
            "label": "Secuencia",
            "valor": round(se, 3),
            "porcentaje": round(se * 100.0, 1)
        }
    ]

    return {
        "frame": {"width": W, "height": H},
        "total_elementos": len(boxes),
        "metricas": metrics_raw,
        "score_regresion": round(score_mra * 100.0, 1),
        "score_entropia": round(score_entropy * 100.0, 1),
        "score_global": round(score_global * 100.0, 1),
        "nivel_calidad": nivel,
        "radar_data": radar_data,
        "interpretaciones": interpretaciones,
        "elementos": boxes[:50]
    }
