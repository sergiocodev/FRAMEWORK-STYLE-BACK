from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models.assessment_model import EvaluacionEstetica, EvaluacionHallazgo
from app.schemas.assessment_schema import EvaluacionUpdate, HallazgoCreate, HallazgoUpdate, ChecklistItemUpdate
from typing import Optional, List

DEFAULT_SUBCRITERIOS_MAP = {
    "c1": [
        {"id": "c1_s1", "titulo": "Espaciado consistente de 8pt grid entre controles y etiquetas.", "cumple": True},
        {"id": "c1_s2", "titulo": "Agrupación visual clara de inputs y sus textos de ayuda o validación.", "cumple": True},
        {"id": "c1_s3", "titulo": "Separación nítida (al menos doble margen) entre bloques temáticos distintos.", "cumple": True}
    ],
    "c2": [
        {"id": "c2_s1", "titulo": "Botones con misma jerarquía comparten color, radio de esquina y tamaño.", "cumple": True},
        {"id": "c2_s2", "titulo": "Tipografías consistentes para títulos y subtítulos del mismo nivel.", "cumple": True},
        {"id": "c2_s3", "titulo": "Iconografía con estilo gráfico unificado (sin mezclar lineal y relleno).", "cumple": True}
    ],
    "c3": [
        {"id": "c3_s1", "titulo": "Flujo de lectura visual alineado a patrones naturales (Z o F).", "cumple": True},
        {"id": "c3_s2", "titulo": "Secuencia ordenada y progresiva en formularios o embudos de acción.", "cumple": False},
        {"id": "c3_s3", "titulo": "Guías visuales o flechas claras para scroll, paginación y carruseles.", "cumple": False}
    ],
    "c4": [
        {"id": "c4_s1", "titulo": "Tarjetas y contenedores con límites perceptibles (bordes sutiles o sombras).", "cumple": False},
        {"id": "c4_s2", "titulo": "Modales y paneles flotantes con backdrop delimitador nítido.", "cumple": False},
        {"id": "c4_s3", "titulo": "Estructuras modulares sin elementos sueltos o descontextualizados.", "cumple": False}
    ],
    "c5": [
        {"id": "c5_s1", "titulo": "Contraste de color suficiente para textos según WCAG AA (mínimo 4.5:1).", "cumple": True},
        {"id": "c5_s2", "titulo": "Elevación visual nítida en elementos flotantes (menús, tooltips, modales).", "cumple": True},
        {"id": "c5_s3", "titulo": "Fondo neutro que no compite con la información ni con los botones CTA.", "cumple": True}
    ]
}

DEFAULT_CHECKLIST = [
    {
        "id": "c1",
        "titulo": "Proximidad",
        "descripcion": "Los elementos relacionados se agrupan visualmente y se separan de los no vinculados.",
        "cumple": True,
        "estado": "cumple",
        "observacion": "Buen agrupamiento de controles y etiquetas en tarjetas principales.",
        "evaluado_por_ia": False,
        "pantalla_id": None,
        "pantalla_nombre": None,
        "subcriterios": [dict(x) for x in DEFAULT_SUBCRITERIOS_MAP["c1"]]
    },
    {
        "id": "c2",
        "titulo": "Similitud",
        "descripcion": "Los elementos similares en función comparten estilo visual, color y forma.",
        "cumple": True,
        "estado": "cumple",
        "observacion": "Estilos y paleta coherentes en botones primarios y títulos.",
        "evaluado_por_ia": False,
        "pantalla_id": None,
        "pantalla_nombre": None,
        "subcriterios": [dict(x) for x in DEFAULT_SUBCRITERIOS_MAP["c2"]]
    },
    {
        "id": "c3",
        "titulo": "Continuidad",
        "descripcion": "El ojo sigue un flujo visual natural y secuencial sin interrupciones.",
        "cumple": False,
        "estado": "parcial",
        "observacion": "Flujo de lectura adecuado aunque faltan indicadores visuales en pasos secundarios.",
        "evaluado_por_ia": False,
        "pantalla_id": None,
        "pantalla_nombre": None,
        "subcriterios": [dict(x) for x in DEFAULT_SUBCRITERIOS_MAP["c3"]]
    },
    {
        "id": "c4",
        "titulo": "Cierre",
        "descripcion": "La información se percibe como una forma completa y contenida.",
        "cumple": False,
        "estado": "no_cumple",
        "observacion": "Modales y secciones secundarias carecen de delimitación de fondo clara.",
        "evaluado_por_ia": False,
        "pantalla_id": None,
        "pantalla_nombre": None,
        "subcriterios": [dict(x) for x in DEFAULT_SUBCRITERIOS_MAP["c4"]]
    },
    {
        "id": "c5",
        "titulo": "Figura - Fondo",
        "descripcion": "Se distingue claramente el contenido interactivo del fondo.",
        "cumple": True,
        "estado": "cumple",
        "observacion": "Contraste satisfactorio que cumple criterios de legibilidad.",
        "evaluado_por_ia": False,
        "pantalla_id": None,
        "pantalla_nombre": None,
        "subcriterios": [dict(x) for x in DEFAULT_SUBCRITERIOS_MAP["c5"]]
    }
]

DEFAULT_REACTIVOS_MAP = {
    "Simplicidad": "Evaluación de la facilidad de uso y la ausencia de elementos innecesarios que puedan distraer al usuario.",
    "Claridad": "Evaluación del grado en el que el diseño es claro y comprensible.",
    "Diversidad": "Evaluación de la variedad y dinamismo en el diseño que mantienen el interés del usuario.",
    "Armonía": "Evaluación de la cohesión y coherencia de los elementos visuales."
}

DEFAULT_VISAWI = [
    {
        "dimension": "Simplicidad",
        "puntaje": 5.8,
        "target": 6.0,
        "reactivo": "Evaluación de la facilidad de uso y la ausencia de elementos innecesarios que puedan distraer al usuario."
    },
    {
        "dimension": "Claridad",
        "puntaje": 6.1,
        "target": 6.0,
        "reactivo": "Evaluación del grado en el que el diseño es claro y comprensible."
    },
    {
        "dimension": "Diversidad",
        "puntaje": 5.2,
        "target": 5.5,
        "reactivo": "Evaluación de la variedad y dinamismo en el diseño que mantienen el interés del usuario."
    },
    {
        "dimension": "Armonía",
        "puntaje": 5.9,
        "target": 6.0,
        "reactivo": "Evaluación de la cohesión y coherencia de los elementos visuales."
    }
]

# 18 Reactivos psicométricos oficiales de Moshagen & Thielsch extraídos de VISAWIdev.xlsx
DEFAULT_VISAWI_ITEMS = [
    {"id": 1, "dimension": "Simplicidad", "pregunta": "¿Sientes que la pantalla está sobrecargada o tiene demasiados elementos juntos?", "inverso": True},
    {"id": 2, "dimension": "Simplicidad", "pregunta": "¿Es fácil entender cómo está organizada la interfaz a simple vista?", "inverso": False},
    {"id": 3, "dimension": "Simplicidad", "pregunta": "¿Los elementos de la pantalla se ven bien ordenados y con una estructura clara?", "inverso": False},
    {"id": 4, "dimension": "Simplicidad", "pregunta": "¿La interfaz se percibe desarticulada o con partes que parecen puestas al azar?", "inverso": True},
    {"id": 5, "dimension": "Simplicidad", "pregunta": "¿Sientes que todos los elementos visuales guardan coherencia y encajan bien entre sí?", "inverso": False},
    {"id": 6, "dimension": "Claridad", "pregunta": "¿El diseño de la interfaz transmite una apariencia profesional?", "inverso": False},
    {"id": 7, "dimension": "Claridad", "pregunta": "¿El diseño visual se siente anticuado o desactualizado?", "inverso": True},
    {"id": 8, "dimension": "Claridad", "pregunta": "¿Se nota dedicación y cuidado en los detalles del diseño de la interfaz?", "inverso": False},
    {"id": 9, "dimension": "Claridad", "pregunta": "¿Parece que al diseño le falta una idea clara o una línea visual definida?", "inverso": True},
    {"id": 10, "dimension": "Diversidad", "pregunta": "¿El diseño visual te resulta aburrido o poco llamativo?", "inverso": True},
    {"id": 11, "dimension": "Diversidad", "pregunta": "¿La distribución y el diseño de la interfaz muestran creatividad y originalidad?", "inverso": False},
    {"id": 12, "dimension": "Diversidad", "pregunta": "¿El diseño parece monótono o falto de creatividad?", "inverso": True},
    {"id": 13, "dimension": "Diversidad", "pregunta": "¿El diseño de la pantalla transmite dinamismo y agilidad visual?", "inverso": False},
    {"id": 14, "dimension": "Diversidad", "pregunta": "¿La interfaz ofrece una variedad visual agradable sin volverse repetitiva?", "inverso": False},
    {"id": 15, "dimension": "Armonía", "pregunta": "¿La combinación general de colores de la interfaz te resulta atractiva?", "inverso": False},
    {"id": 16, "dimension": "Armonía", "pregunta": "¿Consideras que los colores utilizados chocan entre sí o no combinan?", "inverso": True},
    {"id": 17, "dimension": "Armonía", "pregunta": "¿Sientes que la elección de colores fue desacertada o poco adecuada?", "inverso": True},
    {"id": 18, "dimension": "Armonía", "pregunta": "¿Los colores empleados en la interfaz son agradables a la vista?", "inverso": False}
]

DEFAULT_JUSTIFICACIONES = [
    "Principios de Gestalt cumplidos: 3 cumplidos y 1 con observaciones de 5 evaluados.",
    "Resultados del cuestionario VisAWI con puntuación promedio de 5.8/7.0.",
    "Atención: Existen 1 hallazgo(s) crítico(s) pendientes de resolución."
]

DEFAULT_HALLAZGOS = [
    {"problema": "El botón principal no destaca suficientemente.", "severidad": "mayor", "fase_origen": 3, "fase_origen_nombre": "Diseño Visual"},
    {"problema": "La jerarquía de títulos genera confusión en la lectura.", "severidad": "critico", "fase_origen": 2, "fase_origen_nombre": "Diseño Conceptual"},
    {"problema": "Espaciado entre secciones inconsistente.", "severidad": "menor", "fase_origen": 4, "fase_origen_nombre": "Diseño Detallado"},
    {"problema": "Iconos con estilo mixto (lineal y relleno).", "severidad": "mayor", "fase_origen": 3, "fase_origen_nombre": "Diseño Visual"},
    {"problema": "Texto secundario con bajo contraste.", "severidad": "menor", "fase_origen": 4, "fase_origen_nombre": "Diseño Detallado"}
]

def calcular_metricas_globales(evaluacion: EvaluacionEstetica) -> dict:
    """
    Calcula el Score Global de Madurez Estética (0 - 100) y Nivel de Madurez:
    - 35% Cumplimiento Gradual de Principios Gestalt (Cumple: 100%, Parcial: 50%, No Cumple: 0%)
    - 35% Percepción de Usuarios VisAWI (escalado a 100)
    - 30% Tasa de Resolución de Hallazgos
    """
    # 1. Gestalt (0 - 100)
    checklist = evaluacion.checklist or []
    items_validos = [item for item in checklist if isinstance(item, dict) and item.get("estado") != "no_aplica"]
    total_gestalt = len(items_validos)
    cumplidos_gestalt = 0
    parciales_gestalt = 0
    no_cumple_gestalt = 0
    puntos_gestalt = 0.0

    if total_gestalt > 0:
        for item in items_validos:
            estado = item.get("estado")
            if estado == "cumple":
                cumplidos_gestalt += 1
                puntos_gestalt += 1.0
            elif estado == "parcial":
                parciales_gestalt += 1
                puntos_gestalt += 0.5
            elif estado == "no_cumple":
                no_cumple_gestalt += 1
                puntos_gestalt += 0.0
            else:
                if item.get("cumple") is True:
                    cumplidos_gestalt += 1
                    puntos_gestalt += 1.0
                else:
                    no_cumple_gestalt += 1
                    puntos_gestalt += 0.0
        gestalt_pct = (puntos_gestalt / total_gestalt) * 100.0
    else:
        gestalt_pct = 70.0

    # 2. VisAWI (0 - 100) en escala Likert 1 a 7 (Moshagen & Thielsch)
    visawi = evaluacion.visawi_metricas or []
    if visawi:
        promedio_visawi = sum(float(m.get("puntaje", 0)) for m in visawi if isinstance(m, dict)) / len(visawi)
    else:
        promedio_visawi = 5.0
    visawi_pct = min(100.0, max(0.0, (promedio_visawi / 7.0) * 100))

    # 3. Hallazgos (0 - 100)
    hallazgos = evaluacion.hallazgos or []
    total_h = len(hallazgos)
    resueltos_h = sum(1 for h in hallazgos if h.resuelto)
    criticos_pendientes = sum(1 for h in hallazgos if h.severidad == "critico" and not h.resuelto)

    if total_h > 0:
        hallazgos_pct = (resueltos_h / total_h) * 100
    else:
        hallazgos_pct = 100.0

    # Ponderación
    score_raw = (gestalt_pct * 0.35) + (visawi_pct * 0.35) + (hallazgos_pct * 0.30)
    
    # Penalización fuerte si hay críticos sin resolver
    if criticos_pendientes > 0:
        score_final = min(score_raw, 68.0) # No puede pasar de 68 si tiene críticos
    else:
        score_final = score_raw

    score_final = round(score_final, 1)

    # Nivel de Madurez
    if score_final >= 88 and criticos_pendientes == 0:
        nivel = "Nivel Platino (Certificación Estética STYLE)"
    elif score_final >= 75 and criticos_pendientes == 0:
        nivel = "Nivel Oro (Aprobado con Observaciones)"
    elif score_final >= 60:
        nivel = "Nivel Plata (Requiere Ajustes Visuales)"
    else:
        nivel = "Nivel Bronce (Bloqueado / No Aprobado)"

    return {
        "score_estetico": score_final,
        "nivel_madurez": nivel,
        "criticos_pendientes": criticos_pendientes,
        "promedio_visawi": round(promedio_visawi, 2),
        "gestalt_cumplidos": cumplidos_gestalt,
        "gestalt_parciales": parciales_gestalt,
        "gestalt_no_cumple": no_cumple_gestalt,
        "gestalt_score_pct": round(gestalt_pct, 1),
        "gestalt_total": total_gestalt
    }

def recalcular_justificaciones(evaluacion: EvaluacionEstetica) -> List[str]:
    justificaciones = []
    metricas = calcular_metricas_globales(evaluacion)
    
    # Gestalt
    if metricas["gestalt_total"] > 0:
        parciales = metricas.get("gestalt_parciales", 0)
        if parciales > 0:
            justificaciones.append(
                f"Principios de Gestalt: {metricas['gestalt_cumplidos']} cumplidos y {parciales} con observaciones de {metricas['gestalt_total']} evaluados."
            )
        else:
            justificaciones.append(
                f"Principios de Gestalt: {metricas['gestalt_cumplidos']} de {metricas['gestalt_total']} principios verificados."
            )
    
    # VisAWI (Escala 1 a 7 oficial de VISAWIdev.xlsx)
    justificaciones.append(f"Índice de Percepción Estética VisAWI: {metricas['promedio_visawi']}/7.0.")

    # Score Global
    justificaciones.append(f"Índice Global de Madurez Estética: {metricas['score_estetico']}/100 ({metricas['nivel_madurez']}).")

    # Hallazgos críticos
    criticos = metricas["criticos_pendientes"]
    if criticos > 0:
        justificaciones.append(f"Alerta Crítica: Existen {criticos} hallazgo(s) crítico(s) de alta fidelidad pendientes de resolución.")
        evaluacion.conclusion_estado = "Requiere Ajustes"
        evaluacion.conclusion_texto = f"Se detectaron {criticos} hallazgo(s) crítico(s) pendientes de resolver antes de la aprobación."
    else:
        justificaciones.append("Control de Calidad: No se identifican hallazgos críticos bloqueantes para la experiencia visual.")
        evaluacion.conclusion_estado = "Aprobado"
        evaluacion.conclusion_texto = f"La interfaz cumple con los estándares estéticos ({metricas['nivel_madurez']})."

    evaluacion.justificaciones = justificaciones
    flag_modified(evaluacion, "justificaciones")
    return justificaciones


def normalizar_checklist(checklist_raw) -> List[dict]:
    if not checklist_raw:
        return [dict(x) for x in DEFAULT_CHECKLIST]

    lista = []
    if isinstance(checklist_raw, list):
        lista = checklist_raw
    elif isinstance(checklist_raw, dict):
        lista = [
            {
                "id": str(k),
                "titulo": str(k).replace("_", " ").title(),
                "descripcion": "Verificación estética del principio.",
                "cumple": bool(v)
            }
            for k, v in checklist_raw.items()
        ]
    else:
        return [dict(x) for x in DEFAULT_CHECKLIST]

    resultado = []
    for raw_item in lista:
        if not isinstance(raw_item, dict):
            continue
        item = dict(raw_item)
        item_id = str(item.get("id", ""))

        # Asegurar estado gradual
        estado = item.get("estado")
        if not estado:
            estado = "cumple" if item.get("cumple") is True else "no_cumple"
        item["estado"] = estado
        item["cumple"] = (estado == "cumple")

        # Asegurar observacion
        if "observacion" not in item or item["observacion"] is None:
            item["observacion"] = ""

        # Asegurar evaluado_por_ia
        if "evaluado_por_ia" not in item:
            item["evaluado_por_ia"] = False

        # Asegurar subcriterios
        subs = item.get("subcriterios")
        if not subs or not isinstance(subs, list):
            default_subs = DEFAULT_SUBCRITERIOS_MAP.get(item_id, [])
            item["subcriterios"] = [dict(s) for s in default_subs]
        else:
            item["subcriterios"] = [dict(s) for s in subs if isinstance(s, dict)]

        resultado.append(item)

    return resultado if resultado else [dict(x) for x in DEFAULT_CHECKLIST]

def normalizar_visawi(visawi_raw) -> List[dict]:
    if not visawi_raw:
        return [dict(x) for x in DEFAULT_VISAWI]
    
    lista = []
    if isinstance(visawi_raw, list):
        lista = visawi_raw
    elif isinstance(visawi_raw, dict):
        for k, v in visawi_raw.items():
            if k == "media_global":
                continue
            try:
                puntaje = float(v)
            except (ValueError, TypeError):
                puntaje = 5.5
            dim = str(k).replace("_", " ").title()
            lista.append({
                "dimension": dim,
                "puntaje": puntaje
            })
    else:
        return [dict(x) for x in DEFAULT_VISAWI]

    # Mapeo de dimensiones a las 4 subescalas canónicas de VISAWIdev.xlsx
    DIMENSION_MAPPING = {
        "Simplicidad": "Simplicidad",
        "Claridad": "Claridad",
        "Artesanado": "Claridad",
        "Diversidad": "Diversidad",
        "Armonía": "Armonía",
        "Armonia": "Armonía",
        "Colorido": "Armonía",
        "Simetría": "Claridad",
        "Simetria": "Claridad",
        "Jerarquía": "Claridad",
        "Jerarquia": "Claridad",
        "Consistencia": "Simplicidad",
        "Estética general": "Armonía",
        "Estetica General": "Armonía"
    }

    # Detectar si vienen en escala 1 a 5 para convertirlas proporcionalmente a 1 a 7
    scores_detectados = []
    for it in lista:
        if isinstance(it, dict) and "puntaje" in it:
            try:
                scores_detectados.append(float(it["puntaje"]))
            except (ValueError, TypeError):
                pass
    escala_5 = len(scores_detectados) > 0 and max(scores_detectados) <= 5.0 and len(lista) == 5

    dimensiones_procesadas = {}
    for item in lista:
        if not isinstance(item, dict):
            continue
        dim_raw = str(item.get("dimension", "")).strip()
        dim_norm = DIMENSION_MAPPING.get(dim_raw, dim_raw)
        try:
            puntaje = float(item.get("puntaje", 5.5))
        except (ValueError, TypeError):
            puntaje = 5.5
        try:
            target = float(item.get("target", 6.0))
        except (ValueError, TypeError):
            target = 6.0

        if escala_5:
            # Conversión de escala 1-5 a escala 1-7
            puntaje = round(1.0 + (puntaje - 1.0) * (6.0 / 4.0), 1)
            target = round(1.0 + (target - 1.0) * (6.0 / 4.0), 1)

        reactivo = DEFAULT_REACTIVOS_MAP.get(dim_norm, item.get("reactivo") or "Evaluación psicométrica del principio.")
        dimensiones_procesadas[dim_norm] = {
            "dimension": dim_norm,
            "puntaje": round(min(7.0, max(1.0, puntaje)), 1),
            "target": round(min(7.0, max(1.0, target)), 1),
            "reactivo": reactivo
        }

    # Asegurar exactamente las 4 dimensiones canónicas
    res = []
    for default_m in DEFAULT_VISAWI:
        dim = default_m["dimension"]
        if dim in dimensiones_procesadas:
            res.append(dimensiones_procesadas[dim])
        else:
            res.append(dict(default_m))

    return res if res else [dict(x) for x in DEFAULT_VISAWI]

def normalizar_justificaciones(just_raw) -> List[str]:
    if not just_raw:
        return list(DEFAULT_JUSTIFICACIONES)
    if isinstance(just_raw, list):
        return [str(x) for x in just_raw]
    if isinstance(just_raw, dict):
        return [f"{str(k).replace('_', ' ').title()}: {v}" for k, v in just_raw.items()]
    return [str(just_raw)]

def get_or_create_evaluacion(db: Session, proyecto_id: int) -> EvaluacionEstetica:
    evaluacion = db.query(EvaluacionEstetica).filter(EvaluacionEstetica.proyecto_id == proyecto_id).first()
    if not evaluacion:
        evaluacion = EvaluacionEstetica(
            proyecto_id=proyecto_id,
            metodo_seleccionado="Revisión Heurística (Checklist)",
            estado="en_proceso",
            encuesta_url=f"https://style-eval.com/survey/proj-{proyecto_id}",
            total_respuestas=30,
            respuestas_completadas=30,
            conclusion_estado="Requiere Ajustes",
            conclusion_texto="Se detectaron 1 hallazgo(s) crítico(s) pendientes de resolver antes de la aprobación.",
            checklist=DEFAULT_CHECKLIST,
            visawi_metricas=DEFAULT_VISAWI,
            justificaciones=DEFAULT_JUSTIFICACIONES
        )
        db.add(evaluacion)
        db.commit()
        db.refresh(evaluacion)

        # Crear hallazgos iniciales
        for h in DEFAULT_HALLAZGOS:
            hallazgo = EvaluacionHallazgo(
                evaluacion_id=evaluacion.id,
                problema=h["problema"],
                severidad=h["severidad"],
                fase_origen=h["fase_origen"],
                fase_origen_nombre=h["fase_origen_nombre"]
            )
            db.add(hallazgo)
        db.commit()
        db.refresh(evaluacion)

        # Recalcular por si acaso
        recalcular_justificaciones(evaluacion)
        db.commit()
        db.refresh(evaluacion)
    else:
        # Asegurar que formatos antiguos o incompletos se normalicen automáticamente
        changed = False
        needs_norm = False
        if isinstance(evaluacion.checklist, dict) or not evaluacion.checklist:
            needs_norm = True
        elif isinstance(evaluacion.checklist, list):
            for it in evaluacion.checklist:
                if isinstance(it, dict) and ("subcriterios" not in it or "estado" not in it):
                    needs_norm = True
                    break
        if needs_norm:
            evaluacion.checklist = normalizar_checklist(evaluacion.checklist)
            flag_modified(evaluacion, "checklist")
            changed = True

        needs_visawi_norm = False
        if isinstance(evaluacion.visawi_metricas, dict) or not evaluacion.visawi_metricas:
            needs_visawi_norm = True
        elif isinstance(evaluacion.visawi_metricas, list):
            # Debe tener exactamente las 4 dimensiones de VISAWIdev.xlsx
            dims_presentes = [m.get("dimension") for m in evaluacion.visawi_metricas if isinstance(m, dict)]
            if len(evaluacion.visawi_metricas) != 4 or set(dims_presentes) != {"Simplicidad", "Claridad", "Diversidad", "Armonía"}:
                needs_visawi_norm = True
            else:
                for m in evaluacion.visawi_metricas:
                    if isinstance(m, dict) and ("target" not in m or "reactivo" not in m):
                        needs_visawi_norm = True
                        break
        if needs_visawi_norm:
            evaluacion.visawi_metricas = normalizar_visawi(evaluacion.visawi_metricas)
            flag_modified(evaluacion, "visawi_metricas")
            recalcular_justificaciones(evaluacion)
            changed = True
        if isinstance(evaluacion.justificaciones, dict):
            evaluacion.justificaciones = normalizar_justificaciones(evaluacion.justificaciones)
            flag_modified(evaluacion, "justificaciones")
            changed = True
        
        if changed:
            db.commit()
            db.refresh(evaluacion)
            db.refresh(evaluacion)

    # Calcular score global, nivel de madurez y adjuntar pantallas de Fase 4
    metricas = calcular_metricas_globales(evaluacion)
    evaluacion.score_estetico = metricas["score_estetico"]
    evaluacion.nivel_madurez = metricas["nivel_madurez"]
    evaluacion.pantallas_fase4 = get_pantallas_fase4_summary(db, proyecto_id)

    return evaluacion

def update_evaluacion(db: Session, proyecto_id: int, eval_in: EvaluacionUpdate) -> EvaluacionEstetica:
    evaluacion = get_or_create_evaluacion(db, proyecto_id)
    update_data = eval_in.model_dump(exclude_unset=True) if hasattr(eval_in, 'model_dump') else eval_in.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(evaluacion, field, value)
        if field in ["checklist", "visawi_metricas", "justificaciones"]:
            flag_modified(evaluacion, field)

    # Actualizar justificaciones si no se enviaron explícitas
    if "justificaciones" not in update_data:
        recalcular_justificaciones(evaluacion)

    db.commit()
    db.refresh(evaluacion)
    return evaluacion

def update_checklist_item(db: Session, proyecto_id: int, item_id: str, item_in: ChecklistItemUpdate) -> EvaluacionEstetica:
    evaluacion = get_or_create_evaluacion(db, proyecto_id)
    checklist = [dict(i) for i in (evaluacion.checklist or [])]

    updated = False
    for item in checklist:
        if item.get("id") == item_id:
            # Subcriterio toggle o set
            if item_in.subcriterio_id is not None:
                subs = [dict(s) for s in item.get("subcriterios", [])]
                for s in subs:
                    if s.get("id") == item_in.subcriterio_id:
                        if item_in.subcriterio_cumple is not None:
                            s["cumple"] = item_in.subcriterio_cumple
                        else:
                            s["cumple"] = not s.get("cumple", False)
                        break
                item["subcriterios"] = subs
                
                # Auto-calcular estado gradual si no se fijó explícitamente
                if item_in.estado is None:
                    total_s = len(subs)
                    cumplidos_s = sum(1 for s in subs if s.get("cumple") is True)
                    if cumplidos_s == total_s and total_s > 0:
                        item["estado"] = "cumple"
                        item["cumple"] = True
                    elif cumplidos_s > 0:
                        item["estado"] = "parcial"
                        item["cumple"] = False
                    else:
                        item["estado"] = "no_cumple"
                        item["cumple"] = False

            if item_in.subcriterios is not None:
                item["subcriterios"] = [s.model_dump() if hasattr(s, 'model_dump') else dict(s) for s in item_in.subcriterios]

            if item_in.estado is not None:
                item["estado"] = item_in.estado
                item["cumple"] = (item_in.estado == "cumple")

            if item_in.cumple is not None and item_in.estado is None:
                item["cumple"] = item_in.cumple
                item["estado"] = "cumple" if item_in.cumple else "no_cumple"

            if item_in.observacion is not None:
                item["observacion"] = item_in.observacion

            if item_in.evaluado_por_ia is not None:
                item["evaluado_por_ia"] = item_in.evaluado_por_ia

            updated = True
            break

    if updated:
        evaluacion.checklist = checklist
        flag_modified(evaluacion, "checklist")
        recalcular_justificaciones(evaluacion)
        metricas = calcular_metricas_globales(evaluacion)
        evaluacion.score_estetico = metricas["score_estetico"]
        evaluacion.nivel_madurez = metricas["nivel_madurez"]
        db.commit()
        db.refresh(evaluacion)

    return evaluacion

def toggle_checklist_item(db: Session, proyecto_id: int, item_id: str, cumple: Optional[bool] = None) -> EvaluacionEstetica:
    evaluacion = get_or_create_evaluacion(db, proyecto_id)
    checklist = [dict(i) for i in (evaluacion.checklist or [])]
    
    updated = False
    for item in checklist:
        if item.get("id") == item_id:
            if cumple is not None:
                item["cumple"] = cumple
            else:
                item["cumple"] = not item.get("cumple", False)
            item["estado"] = "cumple" if item["cumple"] else "no_cumple"
            updated = True
            break
            
    if updated:
        evaluacion.checklist = checklist
        flag_modified(evaluacion, "checklist")
        recalcular_justificaciones(evaluacion)
        metricas = calcular_metricas_globales(evaluacion)
        evaluacion.score_estetico = metricas["score_estetico"]
        evaluacion.nivel_madurez = metricas["nivel_madurez"]
        db.commit()
        db.refresh(evaluacion)

    return evaluacion

def add_hallazgo(db: Session, proyecto_id: int, hallazgo_in: HallazgoCreate) -> EvaluacionHallazgo:
    evaluacion = get_or_create_evaluacion(db, proyecto_id)
    data = hallazgo_in.model_dump() if hasattr(hallazgo_in, 'model_dump') else hallazgo_in.dict()
    hallazgo = EvaluacionHallazgo(
        evaluacion_id=evaluacion.id,
        **data
    )
    db.add(hallazgo)
    db.commit()
    db.refresh(hallazgo)
    
    # Recalcular justificaciones de la evaluación
    recalcular_justificaciones(evaluacion)
    db.commit()
    
    return hallazgo

def update_hallazgo(db: Session, hallazgo_id: int, hallazgo_in: HallazgoUpdate) -> Optional[EvaluacionHallazgo]:
    hallazgo = db.query(EvaluacionHallazgo).filter(EvaluacionHallazgo.id == hallazgo_id).first()
    if not hallazgo:
        return None

    update_data = hallazgo_in.model_dump(exclude_unset=True) if hasattr(hallazgo_in, 'model_dump') else hallazgo_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(hallazgo, field, value)

    db.commit()
    db.refresh(hallazgo)
    
    # Recalcular justificaciones
    evaluacion = hallazgo.evaluacion
    if evaluacion:
        recalcular_justificaciones(evaluacion)
        db.commit()

    return hallazgo

def toggle_hallazgo_resuelto(db: Session, hallazgo_id: int) -> Optional[EvaluacionHallazgo]:
    hallazgo = db.query(EvaluacionHallazgo).filter(EvaluacionHallazgo.id == hallazgo_id).first()
    if not hallazgo:
        return None

    hallazgo.resuelto = not bool(hallazgo.resuelto)
    db.commit()
    db.refresh(hallazgo)
    
    evaluacion = hallazgo.evaluacion
    if evaluacion:
        recalcular_justificaciones(evaluacion)
        db.commit()

    return hallazgo

def delete_hallazgo(db: Session, hallazgo_id: int) -> bool:
    hallazgo = db.query(EvaluacionHallazgo).filter(EvaluacionHallazgo.id == hallazgo_id).first()
    if not hallazgo:
        return False

    evaluacion = hallazgo.evaluacion
    db.delete(hallazgo)
    db.commit()

    if evaluacion:
        recalcular_justificaciones(evaluacion)
        db.commit()

    return True

def get_pantallas_fase4_summary(db: Session, proyecto_id: int) -> List[dict]:
    """
    Obtiene las pantallas diseñadas en Fase 4 para este proyecto con sus archivos y alertas.
    """
    import os
    from app.models.diseno_conceptual_model import NodoPantalla
    from app.models.diseno_detallado_model import DisenoDetalladoArchivo
    # Buscar todos los diseños detallados existentes para este proyecto
    disenos_proyecto = db.query(DisenoDetalladoArchivo).join(
        NodoPantalla, DisenoDetalladoArchivo.nodo_id == NodoPantalla.id
    ).filter(
        NodoPantalla.proyecto_id == proyecto_id
    ).all()
    
    # También incluir cualquier nodo de fase 4 que esté pendiente de diseño
    nodos_fase4 = db.query(NodoPantalla).filter(
        NodoPantalla.proyecto_id == proyecto_id,
        NodoPantalla.fase_creacion == 4
    ).all()
    
    nodos_vistos = set()
    resultado = []

    for diseno in disenos_proyecto:
        n = diseno.nodo
        if not n:
            continue
        nodos_vistos.add(n.id)
        
        archivo_url = None
        estado_diseno = diseno.estado.value if hasattr(diseno.estado, 'value') else str(diseno.estado)
        total_alertas = len(diseno.alertas)
        alertas_list = [
            {
                "id": a.id,
                "tipo": a.tipo.value if hasattr(a.tipo, 'value') else str(a.tipo),
                "elemento": a.elemento,
                "mensaje": a.mensaje,
                "detectado": a.detectado,
                "esperado": a.esperado
            }
            for a in diseno.alertas
        ]
        
        if diseno.archivo:
            archivo_url = f"/uploads/diseno_detallado/{os.path.basename(diseno.archivo.ruta_almacenamiento)}"

        resultado.append({
            "id": diseno.id,
            "nodo_id": n.id,
            "nombre_pantalla": n.nombre,
            "archivo_id": diseno.archivo_id,
            "archivo_url": archivo_url,
            "estado_diseno": estado_diseno,
            "total_alertas": total_alertas,
            "alertas": alertas_list
        })

    for n in nodos_fase4:
        if n.id not in nodos_vistos:
            nodos_vistos.add(n.id)
            resultado.append({
                "id": n.id,
                "nodo_id": n.id,
                "nombre_pantalla": n.nombre,
                "archivo_id": None,
                "archivo_url": None,
                "estado_diseno": "sin_diseno",
                "total_alertas": 0,
                "alertas": []
            })

        
    return resultado

def sync_fase4_alertas_to_hallazgos(db: Session, proyecto_id: int) -> dict:
    """
    Importa automáticamente las alertas reales de Fase 4 como hallazgos en la matriz de Fase 5 si aún no existen.
    """
    evaluacion = get_or_create_evaluacion(db, proyecto_id)
    pantallas = get_pantallas_fase4_summary(db, proyecto_id)
    
    importados = 0
    hallazgos_existentes = {h.problema.strip().lower() for h in evaluacion.hallazgos}
    
    for p in pantallas:
        for al in p.get("alertas", []):
            tipo = al.get("tipo", "info")
            if tipo == "info":
                continue  # Solo alertas de atención o error
            
            severidad = "critico" if tipo == "error" else "mayor"
            texto_problema = f"[{p['nombre_pantalla']}] {al['elemento']}: {al['mensaje']}"
            
            if texto_problema.strip().lower() not in hallazgos_existentes:
                nuevo_h = EvaluacionHallazgo(
                    evaluacion_id=evaluacion.id,
                    problema=texto_problema,
                    severidad=severidad,
                    fase_origen=4,
                    fase_origen_nombre="Diseño Detallado",
                    resuelto=False
                )
                db.add(nuevo_h)
                hallazgos_existentes.add(texto_problema.strip().lower())
                importados += 1
                
    if importados > 0:
        db.commit()
        db.refresh(evaluacion)
        recalcular_justificaciones(evaluacion)
        db.commit()
        db.refresh(evaluacion)
        
    return {"importados": importados, "total_hallazgos": len(evaluacion.hallazgos)}

async def auditar_estetica_con_ia(db: Session, proyecto_id: int) -> dict:
    """
    Utiliza Gemini AI Vision para inspeccionar los prototipos reales de Fase 4,
    evaluar principios Gestalt y estimar métricas psicométricas VisAWI.
    """
    import os
    import json
    import PIL.Image
    # pyrefly: ignore [missing-import]
    import google.generativeai as genai
    from starlette.concurrency import run_in_threadpool
    from app.core.config import settings
    from app.models.diseno_conceptual_model import NodoPantalla
    from app.models.diseno_detallado_model import DisenoDetalladoArchivo

    evaluacion = get_or_create_evaluacion(db, proyecto_id)
    
    # Buscar pantallas con archivos en Fase 4
    disenos = db.query(DisenoDetalladoArchivo).join(NodoPantalla, DisenoDetalladoArchivo.nodo_id == NodoPantalla.id).filter(
        NodoPantalla.proyecto_id == proyecto_id
    ).all()
    
    # Obtener imágenes disponibles
    imagenes_paths = []
    for d in disenos:
        if d.archivo and os.path.exists(d.archivo.ruta_almacenamiento):
            imagenes_paths.append((d.nodo.nombre, d.archivo.ruta_almacenamiento))
            
    api_key = settings.GEMINI_API_KEY
    if api_key and imagenes_paths:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            prompt = """Eres un evaluador y auditor experto en Estética de Interfaces UI/UX, Psicología de la Gestalt y psicometría de VisAWI.
Analiza la imagen o pantalla del prototipo de alta fidelidad adjunta.
Evalúa con rigor profesional y devuelve un JSON EXACTO con esta estructura:
{
  "gestalt": [
    {"id": "c1", "titulo": "Proximidad", "descripcion": "Los elementos relacionados se agrupan visualmente.", "cumple": true, "estado": "cumple", "observacion": "Texto breve técnico"},
    {"id": "c2", "titulo": "Similitud", "descripcion": "Los elementos similares se perciben como un grupo.", "cumple": true, "estado": "cumple", "observacion": "Texto breve técnico"},
    {"id": "c3", "titulo": "Continuidad", "descripcion": "El ojo sigue un flujo visual natural.", "cumple": true, "estado": "parcial", "observacion": "Texto breve técnico"},
    {"id": "c4", "titulo": "Cierre", "descripcion": "La información se percibe como una forma completa.", "cumple": true, "estado": "no_cumple", "observacion": "Texto breve técnico"},
    {"id": "c5", "titulo": "Figura - Fondo", "descripcion": "Se distingue claramente el contenido del fondo.", "cumple": true, "estado": "cumple", "observacion": "Texto breve técnico"}
  ],
  "visawi": [
    {"dimension": "Claridad", "puntaje": 4.5},
    {"dimension": "Simetría", "puntaje": 4.2},
    {"dimension": "Jerarquía", "puntaje": 4.4},
    {"dimension": "Consistencia", "puntaje": 4.6},
    {"dimension": "Estética general", "puntaje": 4.3}
  ],
  "hallazgos_detectados": [
    {"problema": "Descripción técnica del problema detectado", "severidad": "mayor|menor|critico"}
  ],
  "dictamen_ia": "Breve párrafo con la conclusión ejecutiva de calidad estética."
}
No devuelvas explicaciones fuera del bloque JSON."""

            def _analizar():
                # Tomamos la primera o principal pantalla
                nombre_p, ruta_p = imagenes_paths[0]
                img = PIL.Image.open(ruta_p)
                return model.generate_content([prompt, f"Pantalla: {nombre_p}", img])

            resp = await run_in_threadpool(_analizar)
            raw = resp.text.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
                
            data = json.loads(raw.strip())
            
            # Aplicar resultados a la evaluación
            if "gestalt" in data and isinstance(data["gestalt"], list):
                # Normalizar y marcar evaluado por IA
                norm_gestalt = normalizar_checklist(data["gestalt"])
                for it in norm_gestalt:
                    it["evaluado_por_ia"] = True
                evaluacion.checklist = norm_gestalt
                flag_modified(evaluacion, "checklist")
                
            if "visawi" in data and isinstance(data["visawi"], list):
                evaluacion.visawi_metricas = data["visawi"]
                flag_modified(evaluacion, "visawi_metricas")
                
            if "hallazgos_detectados" in data and isinstance(data["hallazgos_detectados"], list):
                for hd in data["hallazgos_detectados"]:
                    prob = f"[{imagenes_paths[0][0]}] {hd.get('problema', '')}"
                    sev = hd.get("severidad", "mayor")
                    # evitar duplicados
                    if not any(h.problema == prob for h in evaluacion.hallazgos):
                        nh = EvaluacionHallazgo(
                            evaluacion_id=evaluacion.id,
                            problema=prob,
                            severidad=sev,
                            fase_origen=4,
                            fase_origen_nombre="Auditoría IA Fase 4",
                            resuelto=False
                        )
                        db.add(nh)
                        
            db.commit()
            db.refresh(evaluacion)
            recalcular_justificaciones(evaluacion)
            db.commit()
            db.refresh(evaluacion)
            
            return {
                "success": True,
                "mensaje": "Auditoría estética con IA completada exitosamente a partir de los prototipos Hi-Fi de Fase 4.",
                "dictamen": data.get("dictamen_ia", "Evaluación estética completada.")
            }
        except Exception as e:
            import traceback
            traceback.print_exc()

    # Si no hay API key o no hay imágenes, o falla la red, sincronizamos heurística inteligente:
    sync_fase4_alertas_to_hallazgos(db, proyecto_id)
    recalcular_justificaciones(evaluacion)
    db.commit()
    db.refresh(evaluacion)
    
    return {
        "success": True,
        "mensaje": "Auditoría heurística completada. Se sincronizaron las alertas y estándares visuales de las pantallas de Fase 4.",
        "dictamen": evaluacion.conclusion_texto
    }

