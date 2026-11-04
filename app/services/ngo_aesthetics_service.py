"""
Ngo Aesthetics Service
======================
Implementa las 14 métricas estéticas de Ngo, Teo y Byrne (2003):
"Modelling interface aesthetics", Information Sciences 152, pp. 25-46.

Todas las fórmulas siguen estrictamente las ecuaciones (1)-(59) del paper.
Los valores retornados están en el rango [0, 1] donde 1 es el ideal.
"""
import os
import math
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image
from scipy import ndimage as ndi


# ---------------------------------------------------------------------------
# EXTRACCIÓN DE BOUNDING BOXES DESDE IMAGEN DE WIREFRAME
# ---------------------------------------------------------------------------

def _extract_bounding_boxes(image_path: str) -> Tuple[List[Dict], int, int]:
    """
    Extrae bounding boxes de elementos de un wireframe usando detección de bordes
    (Sobel) + dilatación morfológica + etiquetado de componentes conectadas.

    Returns:
        (boxes, frame_width, frame_height)
        donde cada box es: {'x': float, 'y': float, 'w': float, 'h': float}
        con coordenadas en píxeles absolutas.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Imagen no encontrada: {image_path}")

    with Image.open(image_path) as img:
        rgb = img.convert("RGB")
        W, H = rgb.size

        # Escalar si es muy grande para mantener latencia razonable
        max_dim = 900
        if max(W, H) > max_dim:
            scale = max_dim / float(max(W, H))
            W, H = int(W * scale), int(H * scale)
            rgb = rgb.resize((W, H), Image.Resampling.BILINEAR)

        np_img = np.array(rgb)

    # Grayscale
    gray = np.dot(np_img[..., :3], [0.2989, 0.5870, 0.1140])

    # Gradiente Sobel para detectar bordes de componentes
    sx = ndi.sobel(gray, axis=0, mode='constant')
    sy = ndi.sobel(gray, axis=1, mode='constant')
    sobel = np.hypot(sx, sy)

    # Umbralización adaptativa
    threshold = np.mean(sobel) + 0.5 * np.std(sobel)
    binary = sobel > threshold

    # Cierre morfológico para agrupar elementos cercanos
    struct = ndi.generate_binary_structure(2, 2)
    dilated = ndi.binary_dilation(binary, structure=struct, iterations=3)

    labeled, _ = ndi.label(dilated)
    slices = ndi.find_objects(labeled)

    # Filtros de área
    min_area = (W * H) * 0.0008   # descartar ruido microscópico
    max_area = (W * H) * 0.65     # descartar fondo completo

    boxes = []
    for sl in slices:
        if sl is None:
            continue
        sy_sl, sx_sl = sl
        bw = float(sx_sl.stop - sx_sl.start)
        bh = float(sy_sl.stop - sy_sl.start)
        area = bw * bh
        if min_area <= area <= max_area:
            boxes.append({
                'x': float(sx_sl.start),
                'y': float(sy_sl.start),
                'w': bw,
                'h': bh,
            })

    # Ordenar por área descendente y tomar los más prominentes
    boxes.sort(key=lambda b: b['w'] * b['h'], reverse=True)
    boxes = boxes[:60]

    return boxes, W, H


# ---------------------------------------------------------------------------
# CÁLCULO DE LAS 14 MÉTRICAS NGO 2003
# ---------------------------------------------------------------------------

def _compute_metrics(boxes: List[Dict], W: int, H: int) -> Dict[str, float]:
    """
    Calcula las 13 métricas estéticas (Eq 1-57) + Overall Measure (Eq 58-59)
    de Ngo et al. 2003 sobre los bounding boxes detectados.

    Args:
        boxes: lista de dicts {'x', 'y', 'w', 'h'} en píxeles.
        W, H: dimensiones del frame (ancho, alto).
    Returns:
        dict con claves BM, EM, SYM, SQM, CM, UM, PM, SMM, DM, RM, ECM, HM, RHM, OM
    """
    n = len(boxes)

    # Caso degenerado: sin elementos
    if n == 0:
        base = {m: 0.0 for m in ['BM','EM','SYM','SQM','CM','UM','PM','SMM','DM','RM','ECM','HM','RHM']}
        base['OM'] = 0.0
        return base

    b_frame = float(W)
    h_frame = float(H)
    xc = b_frame / 2.0   # centro horizontal
    yc = h_frame / 2.0   # centro vertical
    a_frame = b_frame * h_frame

    # Precalcular centros y áreas
    objs = []
    for b in boxes:
        x, y, bw, bh = float(b['x']), float(b['y']), float(b['w']), float(b['h'])
        objs.append({
            'x': x, 'y': y, 'w': bw, 'h': bh,
            'cx': x + bw / 2.0,
            'cy': y + bh / 2.0,
            'a':  bw * bh,
        })

    sum_a = sum(o['a'] for o in objs)

    # ------------------------------------------------------------------
    # 1. BM – Balance  (Eq 1-6)
    # Distribución del peso visual entre mitades izquierda/derecha y
    # superior/inferior usando momento de primer orden ponderado por área.
    # ------------------------------------------------------------------
    wL, wR, wT, wB = 0.0, 0.0, 0.0, 0.0
    for o in objs:
        dx = abs(o['cx'] - xc)
        dy = abs(o['cy'] - yc)
        if o['cx'] < xc:   wL += o['a'] * dx
        elif o['cx'] > xc: wR += o['a'] * dx
        if o['cy'] < yc:   wT += o['a'] * dy
        elif o['cy'] > yc: wB += o['a'] * dy

    den_lr = max(abs(wL), abs(wR))
    bm_v = (wL - wR) / den_lr if den_lr > 0 else 0.0
    den_tb = max(abs(wT), abs(wB))
    bm_h = (wT - wB) / den_tb if den_tb > 0 else 0.0
    BM = max(0.0, min(1.0, 1.0 - (abs(bm_v) + abs(bm_h)) / 2.0))

    # ------------------------------------------------------------------
    # 2. EM – Equilibrium  (Eq 7-10)
    # Distancia del centro de masa visual al centro geométrico del frame.
    # ------------------------------------------------------------------
    sum_ax = sum(o['a'] * (o['cx'] - xc) for o in objs)
    sum_ay = sum(o['a'] * (o['cy'] - yc) for o in objs)
    em_x = (2.0 * sum_ax) / (b_frame * sum_a) if sum_a > 0 else 0.0
    em_y = (2.0 * sum_ay) / (h_frame * sum_a) if sum_a > 0 else 0.0
    EM = max(0.0, min(1.0, 1.0 - (abs(em_x) + abs(em_y)) / 2.0))

    # ------------------------------------------------------------------
    # Partición en cuadrantes (necesaria para SYM, SQM, HM, RHM)
    # UL=arriba-izquierda, UR=arriba-derecha, LL=abajo-izquierda, LR=abajo-derecha
    # ------------------------------------------------------------------
    quads: Dict[str, List[Dict]] = {'UL': [], 'UR': [], 'LL': [], 'LR': []}
    for o in objs:
        if o['cy'] <= yc:
            quads['UL' if o['cx'] <= xc else 'UR'].append(o)
        else:
            quads['LL' if o['cx'] <= xc else 'LR'].append(o)

    def _quad_sum(attr: str) -> Dict[str, float]:
        return {q: sum(o[attr] for o in quads[q]) for q in quads}

    def _quad_abs_sum(attr: str, ref: float) -> Dict[str, float]:
        return {q: sum(abs(o[attr] - ref) for o in quads[q]) for q in quads}

    # ------------------------------------------------------------------
    # 3. SYM – Symmetry  (Eq 11-24)
    # Mide si las cuatro propiedades (posición, tamaño, ángulo, radio)
    # son simétricas respecto a los ejes vertical, horizontal y radial.
    # ------------------------------------------------------------------
    X_q = _quad_abs_sum('cx', xc)
    Y_q = _quad_abs_sum('cy', yc)
    H_q = {q: sum(o['h'] for o in quads[q]) for q in quads}
    B_q = {q: sum(o['w'] for o in quads[q]) for q in quads}

    Theta_q: Dict[str, float] = {}
    R_q: Dict[str, float] = {}
    for q in quads:
        th, r = 0.0, 0.0
        for o in quads[q]:
            dx = abs(o['cx'] - xc)
            dy = abs(o['cy'] - yc)
            th += dy / dx if dx > 1e-4 else 0.0
            r  += math.hypot(dx, dy)
        Theta_q[q] = th
        R_q[q]     = r

    def _norm_quad(d: Dict[str, float]) -> Dict[str, float]:
        m = max(d.values()) if d else 0.0
        return {k: (v / m if m > 0 else 0.0) for k, v in d.items()}

    Xn, Yn = _norm_quad(X_q), _norm_quad(Y_q)
    Hn, Bn = _norm_quad(H_q), _norm_quad(B_q)
    Tn, Rn = _norm_quad(Theta_q), _norm_quad(R_q)

    def _sym_pair(d: Dict[str, float], q1: str, q2: str) -> float:
        return abs(d[q1] - d[q2])

    def _sym_axis(q1a: str, q1b: str, q2a: str, q2b: str) -> float:
        """Simetría para un eje dado (vertical, horizontal o radial)."""
        total = sum(
            _sym_pair(d, q1a, q1b) + _sym_pair(d, q2a, q2b)
            for d in [Xn, Yn, Hn, Bn, Tn, Rn]
        )
        return total / 12.0  # 6 dimensiones × 2 pares

    sym_v = _sym_axis('UL', 'UR', 'LL', 'LR')   # simetría vertical
    sym_h = _sym_axis('UL', 'LL', 'UR', 'LR')   # simetría horizontal
    sym_r = _sym_axis('UL', 'LR', 'UR', 'LL')   # simetría radial
    SYM = max(0.0, min(1.0, 1.0 - (sym_v + sym_h + sym_r) / 3.0))

    # ------------------------------------------------------------------
    # 4. SQM – Sequence  (Eq 25-27)
    # Patrón de lectura occidental (Z/F): UL>UR>LL>LR (pesos 4,3,2,1).
    # ------------------------------------------------------------------
    q_target = {'UL': 4.0, 'UR': 3.0, 'LL': 2.0, 'LR': 1.0}
    area_q = {q: sum(o['a'] for o in quads[q]) for q in quads}
    # Rango real de los cuadrantes según peso visual
    sorted_by_area = sorted(quads.keys(), key=lambda k: area_q[k], reverse=True)
    q_actual = {q: float(4 - i) for i, q in enumerate(sorted_by_area)}
    sqm_err = sum(abs(q_target[q] - q_actual[q]) for q in quads)
    SQM = max(0.0, min(1.0, 1.0 - sqm_err / 8.0))

    # ------------------------------------------------------------------
    # 5. CM – Cohesion  (Eq 28-33)
    # Cociente de aspecto del layout respecto al frame, y de los
    # objetos respecto al layout.
    # ------------------------------------------------------------------
    all_x1 = [o['x'] for o in objs]
    all_x2 = [o['x'] + o['w'] for o in objs]
    all_y1 = [o['y'] for o in objs]
    all_y2 = [o['y'] + o['h'] for o in objs]
    b_layout = max(1.0, max(all_x2) - min(all_x1))
    h_layout = max(1.0, max(all_y2) - min(all_y1))

    r_fl = (h_layout / b_layout) / (h_frame / b_frame)
    cm_fl = r_fl if r_fl <= 1.0 else 1.0 / r_fl   # Eq 29

    cm_lo_sum = 0.0
    for o in objs:
        r_obj = (o['h'] / o['w']) / (h_layout / b_layout) if o['w'] > 0 else 1.0
        cm_lo_sum += r_obj if r_obj <= 1.0 else 1.0 / r_obj
    cm_lo = cm_lo_sum / n                           # Eq 32

    CM = max(0.0, min(1.0, (cm_fl + cm_lo) / 2.0))

    # ------------------------------------------------------------------
    # 6. UM – Unity  (Eq 34-39)
    # Relación de tamaños únicos (UM_form) y distribución de espacios (UM_space).
    # ------------------------------------------------------------------
    sizes = set((round(o['w'], 1), round(o['h'], 1)) for o in objs)
    n_size = max(1, len(sizes))
    um_form = max(0.0, 1.0 - (n_size - 1.0) / n)   # Eq 35

    a_layout = b_layout * h_layout
    space_frame  = a_frame  - sum_a    # espacio libre total
    space_layout = a_layout - sum_a    # espacio dentro del layout
    if space_frame > 0:
        um_space = max(0.0, 1.0 - space_layout / space_frame)  # Eq 38
    else:
        um_space = 1.0

    UM = max(0.0, min(1.0, (um_form + um_space) / 2.0))

    # ------------------------------------------------------------------
    # 7. PM – Proportion  (Eq 40-45)
    # Cercanía a las 5 proporciones estéticas de Marcus (1992):
    # 1:1 | √2:1 | φ:1 | √3:1 | 2:1
    # ------------------------------------------------------------------
    marcus = [1.0, 1.0 / math.sqrt(2), 1.0 / 1.618, 1.0 / math.sqrt(3), 0.5]

    def _p_ratio(w: float, h: float) -> float:
        if w <= 0 or h <= 0:
            return 1.0
        r = h / w
        return r if r <= 1.0 else 1.0 / r

    pm_obj_sum = 0.0
    for o in objs:
        pi = _p_ratio(o['w'], o['h'])
        min_diff = min(abs(mj - pi) for mj in marcus)
        pm_obj_sum += max(0.0, 1.0 - min_diff / 0.5)
    pm_object = pm_obj_sum / n                       # Eq 43

    p_layout = _p_ratio(b_layout, h_layout)
    pm_layout = max(0.0, 1.0 - min(abs(mj - p_layout) for mj in marcus) / 0.5)  # Eq 44

    PM = max(0.0, min(1.0, (pm_object + pm_layout) / 2.0))

    # ------------------------------------------------------------------
    # 8. SMM – Simplicity  (Eq 46)
    # Basada en el número de puntos de alineación vertical y horizontal.
    # SMM = 3 / (n_vap + n_hap + n)
    # ------------------------------------------------------------------
    vap = set(round(o['x'], 1) for o in objs)       # bordes izquierdos únicos
    hap = set(round(o['y'], 1) for o in objs)       # bordes superiores únicos
    n_vap = len(vap)
    n_hap = len(hap)
    SMM = min(1.0, 3.0 / (n_vap + n_hap + n))

    # ------------------------------------------------------------------
    # 9. DM – Density  (Eq 47)
    # Óptimo en 50% de cobertura del frame.
    # ------------------------------------------------------------------
    DM = max(0.0, min(1.0, 1.0 - 2.0 * abs(0.5 - sum_a / a_frame)))

    # ------------------------------------------------------------------
    # 10. RM – Regularity  (Eq 48)
    # Consistencia de alineaciones y espaciados.
    # ------------------------------------------------------------------
    if n <= 1:
        RM = 1.0
    else:
        # Componente de alineación: idealmente n_vap = n_hap = 1
        rm_align = max(0.0, 1.0 - (n_vap + n_hap) / (2.0 * n))

        col_sorted = sorted(vap)
        row_sorted = sorted(hap)
        col_spacings = set(round(col_sorted[i+1] - col_sorted[i], 1)
                           for i in range(len(col_sorted) - 1))
        row_spacings = set(round(row_sorted[i+1] - row_sorted[i], 1)
                           for i in range(len(row_sorted) - 1))
        n_sp = max(1, len(col_spacings) + len(row_spacings))
        rm_space = max(0.0, 1.0 - (n_sp - 1) / (2.0 * (n - 1)))

        RM = max(0.0, min(1.0, (rm_align + rm_space) / 2.0))

    # ------------------------------------------------------------------
    # 11. ECM – Economy  (Eq 49)
    # Mínima cantidad de tamaños distintos de componentes.
    # ------------------------------------------------------------------
    ECM = min(1.0, 1.0 / n_size)

    # ------------------------------------------------------------------
    # 12. HM – Homogeneity  (Eq 50-52)
    # Distribución equiprobable de objetos entre los 4 cuadrantes.
    # Basada en la estadística de Boltzmann: W / Wmax.
    # Wmax es el W de la distribución más uniforme posible (enteros).
    # ------------------------------------------------------------------
    n_q = {q: len(quads[q]) for q in quads}
    n_counts = list(n_q.values())

    def _factorial(k: int) -> int:
        return math.factorial(k)

    def _w(counts: List[int]) -> float:
        total = sum(counts)
        denom = 1
        for c in counts:
            denom *= _factorial(c)
        return math.factorial(total) / denom

    # Distribución más uniforme de n en 4 cuadrantes
    q_div, q_rem = divmod(n, 4)
    wmax_counts = [q_div + 1] * q_rem + [q_div] * (4 - q_rem)
    W_obs  = _w(n_counts)
    W_max  = _w(wmax_counts)
    HM = max(0.0, min(1.0, W_obs / W_max)) if W_max > 0 else 0.0

    # ------------------------------------------------------------------
    # 13. RHM – Rhythm  (Eq 53-57)
    # Variación sistemática de posiciones y áreas entre cuadrantes.
    # ------------------------------------------------------------------
    area_q_d = {q: sum(o['a'] for o in quads[q]) for q in quads}
    An = _norm_quad(area_q_d)

    def _rhm_dim(d: Dict[str, float]) -> float:
        pairs = [('UL','UR'),('UL','LR'),('UL','LL'),('UR','LR'),('UR','LL'),('LR','LL')]
        return sum(abs(d[q1] - d[q2]) for q1, q2 in pairs) / 6.0

    rhm_x    = _rhm_dim(Xn)
    rhm_y    = _rhm_dim(Yn)
    rhm_area = _rhm_dim(An)
    RHM = max(0.0, min(1.0, 1.0 - (rhm_x + rhm_y + rhm_area) / 3.0))

    # ------------------------------------------------------------------
    # 14. OM – Overall Measure  (Eq 58-59)
    # Promedio aritmético de las 13 métricas anteriores.
    # ------------------------------------------------------------------
    all_metrics = [BM, EM, SYM, SQM, CM, UM, PM, SMM, DM, RM, ECM, HM, RHM]
    OM = sum(all_metrics) / 13.0

    return {
        'BM':  round(BM,  4),
        'EM':  round(EM,  4),
        'SYM': round(SYM, 4),
        'SQM': round(SQM, 4),
        'CM':  round(CM,  4),
        'UM':  round(UM,  4),
        'PM':  round(PM,  4),
        'SMM': round(SMM, 4),
        'DM':  round(DM,  4),
        'RM':  round(RM,  4),
        'ECM': round(ECM, 4),
        'HM':  round(HM,  4),
        'RHM': round(RHM, 4),
        'OM':  round(OM,  4),
        'n_elementos': n,
    }


# ---------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE EVALUACIÓN
# ---------------------------------------------------------------------------

def evaluar_wireframe_ngo(image_path: str) -> Dict:
    """
    Punto de entrada: recibe la ruta absoluta a un wireframe (imagen)
    y devuelve las 14 métricas + metadatos para visualización.

    Returns un dict con:
        metrics: {BM, EM, SYM, SQM, CM, UM, PM, SMM, DM, RM, ECM, HM, RHM, OM}
        n_elementos: número de elementos detectados
        frame: {width, height}
        elementos: lista de bounding boxes detectados
        interpretaciones: texto explicativo para cada métrica
        nivel_calidad: 'Alta' | 'Media' | 'Baja'
    """
    boxes, W, H = _extract_bounding_boxes(image_path)
    metrics = _compute_metrics(boxes, W, H)

    # Interpretaciones según umbrales del paper (Tabla 3 implícita)
    interp = _build_interpretations(metrics)
    nivel = _quality_level(metrics['OM'])

    return {
        'metrics': metrics,
        'n_elementos': metrics.pop('n_elementos'),
        'frame': {'width': W, 'height': H},
        'elementos': boxes[:60],
        'interpretaciones': interp,
        'nivel_calidad': nivel,
    }


# ---------------------------------------------------------------------------
# HELPERS DE INTERPRETACIÓN
# ---------------------------------------------------------------------------

_METRIC_INFO = {
    'BM':  ('Balance',         'Distribución del peso visual entre los semiplanos izquierdo/derecho y superior/inferior.'),
    'EM':  ('Equilibrio',      'Distancia del centro de masa visual al centro geométrico del frame.'),
    'SYM': ('Simetría',        'Simetría axial (vertical, horizontal) y radial entre los cuatro cuadrantes.'),
    'SQM': ('Secuencia',       'Coherencia con el patrón de lectura occidental Z/F (superior izquierdo → inferior derecho).'),
    'CM':  ('Cohesión',        'Similitud entre el aspecto del layout y el del frame, y entre objetos y layout.'),
    'UM':  ('Unidad',          'Consistencia de tamaños de componentes y distribución uniforme de espacios.'),
    'PM':  ('Proporción',      'Cercanía de los elementos y del layout a las 5 proporciones clásicas de Marcus.'),
    'SMM': ('Simplicidad',     'Economía de puntos de alineación vertical y horizontal (menos = más simple).'),
    'DM':  ('Densidad',        'Ocupación del frame próxima al 50% óptimo de cobertura.'),
    'RM':  ('Regularidad',     'Consistencia en alineaciones y espaciados entre componentes.'),
    'ECM': ('Economía',        'Uso de la mínima cantidad de tamaños distintos de componentes.'),
    'HM':  ('Homogeneidad',    'Distribución equitativa de elementos entre los cuatro cuadrantes de la pantalla.'),
    'RHM': ('Ritmo',           'Variación sistemática de posiciones y áreas entre cuadrantes.'),
    'OM':  ('Medida Global',   'Promedio aritmético de las 13 métricas anteriores (Ngo et al., 2003).'),
}

def _build_interpretations(metrics: Dict) -> Dict[str, Dict]:
    result = {}
    for key, (nombre, desc) in _METRIC_INFO.items():
        val = metrics.get(key, 0.0)
        if val >= 0.75:
            estado = 'óptimo'
            color  = 'success'
        elif val >= 0.50:
            estado = 'aceptable'
            color  = 'warning'
        else:
            estado = 'mejorable'
            color  = 'danger'
        result[key] = {
            'nombre':    nombre,
            'descripcion': desc,
            'valor':     val,
            'estado':    estado,
            'color':     color,
        }
    return result


def _quality_level(om: float) -> str:
    if om >= 0.70:
        return 'Alta'
    elif om >= 0.50:
        return 'Media'
    else:
        return 'Baja'

