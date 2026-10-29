"""
Multi-Strategy Secretary Bird Optimization Algorithm (MSSBOA)
applied to Aesthetic Color Harmony & UI Graphic Composition.

Derived from research on SBOA (Secretary Bird Optimization Algorithm)
enhanced with:
1. Good Point Set Initialization (GPSI) for uniform exploration.
2. Lens Opposition-Based Learning (LOBL) to escape local optima.
3. Adaptive Cauchy-Gaussian Mutation for fine-tuned exploitation.
"""

import math
import random
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# ==========================================
# 1. Color Models & Conversions
# ==========================================

def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    hex_clean = hex_code.lstrip('#')
    if len(hex_clean) == 3:
        hex_clean = ''.join([c*2 for c in hex_clean])
    if len(hex_clean) != 6:
        return (37, 99, 235) # fallback blue
    return (
        int(hex_clean[0:2], 16),
        int(hex_clean[2:4], 16),
        int(hex_clean[4:6], 16)
    )

def rgb_to_hex(r: int, g: int, b: int) -> str:
    r = max(0, min(255, int(round(r))))
    g = max(0, min(255, int(round(g))))
    b = max(0, min(255, int(round(b))))
    return f"#{r:02x}{g:02x}{b:02x}"

def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
    rf = r / 255.0
    gf = g / 255.0
    bf = b / 255.0
    max_c = max(rf, gf, bf)
    min_c = min(rf, gf, bf)
    diff = max_c - min_c

    l = (max_c + min_c) / 2.0

    if diff == 0:
        h = 0.0
        s = 0.0
    else:
        s = diff / (2.0 - max_c - min_c) if l > 0.5 else diff / (max_c + min_c)
        if max_c == rf:
            h = (gf - bf) / diff + (6.0 if gf < bf else 0.0)
        elif max_c == gf:
            h = (bf - rf) / diff + 2.0
        else:
            h = (rf - gf) / diff + 4.0
        h /= 6.0
    return (h, s, l)

def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    h = h % 1.0
    s = max(0.0, min(1.0, s))
    l = max(0.0, min(1.0, l))

    if s == 0:
        val = int(round(l * 255))
        return (val, val, val)

    def hue_to_rgb(p: float, q: float, t: float) -> float:
        if t < 0: t += 1.0
        if t > 1: t -= 1.0
        if t < 1/6: return p + (q - p) * 6.0 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6.0
        return p

    q = l * (1.0 + s) if l < 0.5 else l + s - l * s
    p = 2.0 * l - q

    r = hue_to_rgb(p, q, h + 1/3)
    g = hue_to_rgb(p, q, h)
    b = hue_to_rgb(p, q, h - 1/3)

    return (
        int(round(r * 255)),
        int(round(g * 255)),
        int(round(b * 255))
    )

def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    def channel_linear(val: int) -> float:
        c = val / 255.0
        return c / 12.92 if c <= 0.03928 else math.pow((c + 0.055) / 1.055, 2.4)
    r_lin = channel_linear(rgb[0])
    g_lin = channel_linear(rgb[1])
    b_lin = channel_linear(rgb[2])
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

def wcag_contrast_ratio(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    l1 = relative_luminance(rgb1)
    l2 = relative_luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def perceptual_distance(rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
    # Weighted Euclidean distance in RGB approximating human vision (redmean)
    r_bar = (rgb1[0] + rgb2[0]) / 2.0
    dr = rgb1[0] - rgb2[0]
    dg = rgb1[1] - rgb2[1]
    db = rgb1[2] - rgb2[2]
    return math.sqrt((2 + r_bar / 256.0) * dr * dr + 4.0 * dg * dg + (2 + (255 - r_bar) / 256.0) * db * db)

# ==========================================
# 2. UI Role Definitions & Harmony Types
# ==========================================

DEFAULT_UI_ROLES = [
    {"uso": "Principal", "nombre": "Color Principal", "token_name": "color.primary"},
    {"uso": "Secundario", "nombre": "Color Secundario", "token_name": "color.secondary"},
    {"uso": "Acento", "nombre": "Color de Acento", "token_name": "color.accent"},
    {"uso": "Fondo", "nombre": "Fondo Principal", "token_name": "color.background"},
    {"uso": "Superficie", "nombre": "Superficie / Tarjetas", "token_name": "color.surface"},
    {"uso": "Borde", "nombre": "Borde / Separadores", "token_name": "color.border"},
    {"uso": "Texto principal", "nombre": "Texto Principal", "token_name": "color.text.primary"},
    {"uso": "Texto secundario", "nombre": "Texto Secundario", "token_name": "color.text.secondary"},
    {"uso": "Éxito", "nombre": "Semántico Éxito", "token_name": "color.success"},
    {"uso": "Advertencia", "nombre": "Semántico Advertencia", "token_name": "color.warning"},
    {"uso": "Error", "nombre": "Semántico Error", "token_name": "color.error"},
    {"uso": "Información", "nombre": "Semántico Información", "token_name": "color.info"},
]

HARMONY_ANGLES = {
    "Analogous": [0.0, 0.083, 0.166],           # ~0, 30, 60 deg
    "Complementary": [0.0, 0.5],                 # 0, 180 deg
    "Triadic": [0.0, 0.333, 0.666],             # 0, 120, 240 deg
    "SplitComplementary": [0.0, 0.416, 0.583],  # 0, 150, 210 deg
    "Tetradic": [0.0, 0.25, 0.5, 0.75],         # 0, 90, 180, 270 deg
    "Matsuda_V": [0.0, 0.166, 0.5],             # V-type template
    "Matsuda_Y": [0.0, 0.05, 0.5, 0.55]         # Y-type template
}

# ==========================================
# 3. MSSBOA Optimization Engine
# ==========================================

class MSSBOAOptimizer:
    def __init__(
        self,
        base_hex: str = "#2563EB",
        harmony_type: str = "Complementary",
        mode: str = "light",
        wcag_target: str = "AA", # "AA" (4.5:1) or "AAA" (7.0:1)
        population_size: int = 30,
        max_iterations: int = 60,
        seed: Optional[int] = None
    ):
        self.base_hex = base_hex
        self.base_rgb = hex_to_rgb(base_hex)
        self.base_hsl = rgb_to_hsl(*self.base_rgb)
        self.harmony_type = harmony_type if harmony_type in HARMONY_ANGLES else "Complementary"
        self.mode = mode.lower() # "light" or "dark"
        self.wcag_target_ratio = 7.0 if wcag_target.upper() == "AAA" else 4.5
        self.pop_size = max(10, population_size)
        self.max_iter = max(20, max_iterations)
        
        if seed is not None:
            random.seed(seed)

        # Number of colors to generate = len(DEFAULT_UI_ROLES) = 12
        # Each color has 3 genes (H, S, L). Color 0 (Principal) is anchored to base_hex!
        self.num_colors = len(DEFAULT_UI_ROLES)
        self.dim = (self.num_colors - 1) * 3

        # Bounds for genes: (H in [0, 1], S in [0.05, 1.0], L in [0.05, 0.95])
        self.lb = []
        self.ub = []
        for i in range(1, self.num_colors):
            uso = DEFAULT_UI_ROLES[i]["uso"]
            
            # H bounds (hue guidance for semantic clarity)
            if uso == "Éxito":
                self.lb.append(0.28) # green ~100 deg
                self.ub.append(0.42) # ~151 deg
            elif uso == "Advertencia":
                self.lb.append(0.07) # amber/orange ~25 deg
                self.ub.append(0.14) # ~50 deg
            elif uso == "Error":
                self.lb.append(0.96) # crimson red ~345 deg to 360 deg
                self.ub.append(1.00)
            elif uso == "Información":
                self.lb.append(0.52) # sky blue/cyan ~187 deg
                self.ub.append(0.60) # ~216 deg
            else:
                self.lb.append(0.0)
                self.ub.append(1.0)
            
            # S & L tailored bounds according to UI role and theme mode
            if uso in ["Fondo", "Superficie"]:
                if self.mode == "light":
                    self.lb.extend([0.0, 0.92]) # Low Saturation, High Lightness
                    self.ub.extend([0.25, 0.99])
                else: # dark mode
                    self.lb.extend([0.0, 0.05]) # Low Saturation, Low Lightness
                    self.ub.extend([0.30, 0.16])
            elif uso == "Borde":
                if self.mode == "light":
                    self.lb.extend([0.0, 0.78]) # Subtle clean border
                    self.ub.extend([0.20, 0.90])
                else: # dark mode border
                    self.lb.extend([0.0, 0.18]) # Dark gray border
                    self.ub.extend([0.25, 0.32])
            elif "Texto" in uso:
                if self.mode == "light":
                    self.lb.extend([0.0, 0.05]) # Dark text
                    self.ub.extend([0.40, 0.35])
                else: # dark mode text
                    self.lb.extend([0.0, 0.80]) # Bright text
                    self.ub.extend([0.25, 0.98])
            elif uso == "Éxito":
                self.lb.extend([0.55, 0.35])
                self.ub.extend([0.95, 0.55])
            elif uso == "Advertencia":
                self.lb.extend([0.70, 0.42])
                self.ub.extend([1.00, 0.58])
            elif uso == "Error":
                self.lb.extend([0.65, 0.40])
                self.ub.extend([0.95, 0.56])
            elif uso == "Información":
                self.lb.extend([0.65, 0.42])
                self.ub.extend([0.95, 0.58])
            else: # Secundario, Acento
                self.lb.extend([0.25, 0.30])
                self.ub.extend([1.0, 0.75])

    # ------------------------------------------
    # Strategy 1: Good Point Set Initialization (GPSI)
    # ------------------------------------------
    def _initialize_population_gpsi(self) -> List[List[float]]:
        # Find smallest prime p >= 2 * dim + 3
        p = 2 * self.dim + 3
        while True:
            is_prime = True
            for d in range(2, int(math.isqrt(p)) + 1):
                if p % d == 0:
                    is_prime = False
                    break
            if is_prime:
                break
            p += 2

        # Construct good point vector r
        r = [math.modf(2.0 * math.cos(2.0 * math.pi * (j + 1) / p))[0] for j in range(self.dim)]
        r = [abs(val) if abs(val) > 1e-4 else (j + 1) / (p + 1) for j, val in enumerate(r)]

        population = []
        for i in range(1, self.pop_size + 1):
            individual = []
            for j in range(self.dim):
                # x_i(j) = mod(r_j * i, 1)
                point = (r[j] * i) % 1.0
                val = self.lb[j] + point * (self.ub[j] - self.lb[j])
                individual.append(val)
            population.append(individual)
        return population

    def _decode_individual(self, ind: List[float]) -> List[Tuple[int, int, int]]:
        colors_rgb = [self.base_rgb] # Color 0 is fixed
        for idx in range(self.num_colors - 1):
            h = ind[idx * 3] % 1.0
            s = max(self.lb[idx * 3 + 1], min(self.ub[idx * 3 + 1], ind[idx * 3 + 1]))
            l = max(self.lb[idx * 3 + 2], min(self.ub[idx * 3 + 2], ind[idx * 3 + 2]))
            colors_rgb.append(hsl_to_rgb(h, s, l))
        return colors_rgb

    # ------------------------------------------
    # Fitness Evaluation Function
    # ------------------------------------------
    def evaluate_fitness(self, ind: List[float]) -> Tuple[float, Dict[str, float]]:
        colors_rgb = self._decode_individual(ind)
        # Roles mapping (12 tokens)
        c_primary = colors_rgb[0]
        c_secondary = colors_rgb[1]
        c_accent = colors_rgb[2]
        c_bg = colors_rgb[3]
        c_surface = colors_rgb[4]
        c_border = colors_rgb[5]
        c_text_primary = colors_rgb[6]
        c_text_secondary = colors_rgb[7]
        c_success = colors_rgb[8]
        c_warning = colors_rgb[9]
        c_error = colors_rgb[10]
        c_info = colors_rgb[11]

        # 1. Contrast Metric (WCAG 2.1)
        cr_text_bg = wcag_contrast_ratio(c_text_primary, c_bg)
        cr_text_surface = wcag_contrast_ratio(c_text_primary, c_surface)
        cr_sec_text_bg = wcag_contrast_ratio(c_text_secondary, c_bg)
        cr_primary_bg = wcag_contrast_ratio(c_primary, c_bg)
        cr_accent_surface = wcag_contrast_ratio(c_accent, c_surface)
        cr_border_surface = wcag_contrast_ratio(c_border, c_surface)
        cr_error_bg = wcag_contrast_ratio(c_error, c_bg)
        cr_success_bg = wcag_contrast_ratio(c_success, c_bg)

        # Contrast score (target WCAG threshold)
        def score_cr(ratio: float, target: float) -> float:
            if ratio >= target:
                return 100.0 + min(20.0, (ratio - target) * 2.0)
            return max(0.0, (ratio / target) * 75.0)

        contrast_score = (
            score_cr(cr_text_bg, self.wcag_target_ratio) * 0.30 +
            score_cr(cr_text_surface, self.wcag_target_ratio) * 0.30 +
            score_cr(cr_sec_text_bg, 3.5) * 0.10 +
            score_cr(cr_primary_bg, 3.0) * 0.10 +
            score_cr(cr_accent_surface, 3.0) * 0.10 +
            score_cr(cr_error_bg, 3.0) * 0.05 +
            score_cr(cr_success_bg, 3.0) * 0.05
        )

        # 2. Matsuda Color Harmony Metric (Hue Wheel Geometry)
        target_offsets = HARMONY_ANGLES.get(self.harmony_type, [0.0, 0.5])
        base_h = self.base_hsl[0]
        
        # Check hues of Secondary and Accent against harmony template
        h_sec = rgb_to_hsl(*c_secondary)[0]
        h_acc = rgb_to_hsl(*c_accent)[0]

        def min_angle_distance(h1: float, h2: float) -> float:
            diff = abs(h1 - h2) % 1.0
            return min(diff, 1.0 - diff)

        # Distance of secondary and accent to closest ideal harmonic target angle
        def best_harmonic_match(h: float) -> float:
            min_dist = 1.0
            for offset in target_offsets:
                ideal_h = (base_h + offset) % 1.0
                dist = min_angle_distance(h, ideal_h)
                if dist < min_dist:
                    min_dist = dist
            return min_dist

        dist_sec = best_harmonic_match(h_sec)
        dist_acc = best_harmonic_match(h_acc)
        # Closer to 0 distance = 100 score
        harmony_score = max(0.0, 100.0 - (dist_sec + dist_acc) * 200.0)

        # 3. Visual Diversity Metric (Perceptual Distinctiveness)
        d_p_s = perceptual_distance(c_primary, c_secondary)
        d_p_a = perceptual_distance(c_primary, c_accent)
        d_s_a = perceptual_distance(c_secondary, c_accent)
        d_err_warn = perceptual_distance(c_error, c_warning)
        d_warn_succ = perceptual_distance(c_warning, c_success)
        d_succ_info = perceptual_distance(c_success, c_info)
        d_bg_surf = perceptual_distance(c_bg, c_surface)
        d_surf_bord = perceptual_distance(c_surface, c_border)

        div_actions = min(100.0, (d_p_s + d_p_a + d_s_a) / 3.0 / 1.5)
        div_semantics = min(100.0, (d_err_warn + d_warn_succ + d_succ_info) / 3.0 / 1.5)
        subtle_diff = (
            (100.0 - abs(d_bg_surf - 25.0) * 2.0) * 0.5 +
            (100.0 - abs(d_surf_bord - 20.0) * 2.0) * 0.5
        )
        diversity_score = max(0.0, min(100.0, (div_actions * 0.4 + div_semantics * 0.4 + subtle_diff * 0.2)))

        # 4. Semantic correctness (Success=green, Warning=amber, Error=red, Info=sky blue)
        h_succ = rgb_to_hsl(*c_success)[0]
        h_warn = rgb_to_hsl(*c_warning)[0]
        h_err = rgb_to_hsl(*c_error)[0]
        h_info = rgb_to_hsl(*c_info)[0]

        dist_succ = min_angle_distance(h_succ, 0.35)  # 0.35 = 126 deg (emerald green)
        dist_warn = min_angle_distance(h_warn, 0.11)  # 0.11 = 40 deg (amber/orange)
        dist_err = min_angle_distance(h_err, 0.98)   # 0.98 = 353 deg (crimson red)
        dist_info = min_angle_distance(h_info, 0.55)  # 0.55 = 198 deg (sky blue/cyan)

        avg_sem_dist = (dist_succ + dist_warn + dist_err + dist_info) / 4.0
        semantic_score = max(0.0, 100.0 - avg_sem_dist * 350.0)

        # Combined Weighted Fitness
        total_fitness = (
            contrast_score * 0.40 +
            harmony_score * 0.25 +
            diversity_score * 0.20 +
            semantic_score * 0.15
        )

        metrics = {
            "contrast_score": round(contrast_score, 1),
            "harmony_score": round(harmony_score, 1),
            "diversity_score": round(diversity_score, 1),
            "fitness_score": round(total_fitness, 1),
            "min_contrast": round(min(cr_text_bg, cr_text_surface), 2),
            "wcag_compliant": min(cr_text_bg, cr_text_surface) >= self.wcag_target_ratio
        }

        return total_fitness, metrics

    # ------------------------------------------
    # Strategy 2: Lens Opposition-Based Learning (LOBL)
    # ------------------------------------------
    def _lens_opposition(self, ind: List[float], t: int) -> List[float]:
        # Lens scaling parameter alpha decreases dynamically
        alpha = 10.0 * (1.0 - t / self.max_iter) + 1.0
        opp_ind = []
        for j in range(self.dim):
            a_j = self.lb[j]
            b_j = self.ub[j]
            # Lens opposition formula:
            x_star = (a_j + b_j) / 2.0 + (a_j + b_j) / (2.0 * alpha) - ind[j] / alpha
            # Clamp to bounds
            opp_ind.append(max(a_j, min(b_j, x_star)))
        return opp_ind

    # ------------------------------------------
    # Strategy 3: Adaptive Cauchy-Gaussian Mutation
    # ------------------------------------------
    def _cauchy_gaussian_mutation(self, best_ind: List[float], t: int) -> List[float]:
        w1 = 1.0 - math.pow(t / self.max_iter, 2) # Cauchy weight (global escape)
        w2 = math.pow(t / self.max_iter, 2)       # Gaussian weight (local refinement)
        
        mutated = []
        for j in range(self.dim):
            # Cauchy random variable ~ tan(pi * (u - 0.5))
            u = random.random()
            cauchy_step = math.tan(math.pi * (u - 0.5))
            # Gaussian random variable ~ N(0, 1)
            gauss_step = random.gauss(0, 1)
            
            step = w1 * cauchy_step * 0.1 + w2 * gauss_step * 0.05
            val = best_ind[j] * (1.0 + step)
            mutated.append(max(self.lb[j], min(self.ub[j], val)))
        return mutated

    # ------------------------------------------
    # Main Optimization Execution Loop
    # ------------------------------------------
    def optimize(self) -> Dict:
        start_time = time.time()
        
        # 1. Initialize with Good Point Set
        population = self._initialize_population_gpsi()
        fitness_list = []
        metrics_list = []

        for ind in population:
            f, m = self.evaluate_fitness(ind)
            fitness_list.append(f)
            metrics_list.append(m)

        # Track global best
        best_idx = max(range(len(fitness_list)), key=lambda i: fitness_list[i])
        best_fitness = fitness_list[best_idx]
        best_individual = list(population[best_idx])
        best_metrics = metrics_list[best_idx]

        convergence_history = [best_fitness]

        # 2. Iteration Loop (Secretary Bird Hunting & Predator Evasion)
        for t in range(1, self.max_iter + 1):
            for i in range(self.pop_size):
                # Stage 1: Hunting (Phase 1: Exploration, Phase 2: Exploitation)
                r_rand1 = random.choice(population)
                r_rand2 = random.choice(population)
                r1 = random.random()

                new_ind = []
                if r1 > 0.5:
                    # Search behavior
                    for j in range(self.dim):
                        step = (r_rand1[j] - r_rand2[j]) * random.uniform(0, 1)
                        val = population[i][j] + step
                        new_ind.append(max(self.lb[j], min(self.ub[j], val)))
                else:
                    # Attack behavior
                    exp_factor = math.exp(math.pow(t / self.max_iter, 2))
                    for j in range(self.dim):
                        step = exp_factor * (random.random() - 0.5) * (population[i][j] - best_individual[j])
                        val = best_individual[j] + step
                        new_ind.append(max(self.lb[j], min(self.ub[j], val)))

                # Stage 2: Predator Evasion
                if random.random() < 0.35:
                    # Flight / Camouflage evasion
                    r_rand = random.choice(population)
                    c1 = random.uniform(0.5, 1.5)
                    for j in range(self.dim):
                        val = best_individual[j] + c1 * random.random() * (new_ind[j] - r_rand[j])
                        new_ind[j] = max(self.lb[j], min(self.ub[j], val))

                # Greedy Selection
                f_new, m_new = self.evaluate_fitness(new_ind)
                if f_new > fitness_list[i]:
                    population[i] = new_ind
                    fitness_list[i] = f_new
                    metrics_list[i] = m_new

                    if f_new > best_fitness:
                        best_fitness = f_new
                        best_individual = list(new_ind)
                        best_metrics = m_new

            # ------------------------------------------
            # Strategy 2: Lens OBL on Worst 30% Individuals
            # ------------------------------------------
            sorted_indices = sorted(range(self.pop_size), key=lambda k: fitness_list[k])
            worst_k = int(self.pop_size * 0.3)
            for idx in sorted_indices[:worst_k]:
                opp_ind = self._lens_opposition(population[idx], t)
                f_opp, m_opp = self.evaluate_fitness(opp_ind)
                if f_opp > fitness_list[idx]:
                    population[idx] = opp_ind
                    fitness_list[idx] = f_opp
                    metrics_list[idx] = m_opp
                    if f_opp > best_fitness:
                        best_fitness = f_opp
                        best_individual = list(opp_ind)
                        best_metrics = m_opp

            # ------------------------------------------
            # Strategy 3: Cauchy-Gaussian Mutation on Best Individual
            # ------------------------------------------
            mut_best = self._cauchy_gaussian_mutation(best_individual, t)
            f_mut, m_mut = self.evaluate_fitness(mut_best)
            if f_mut > best_fitness:
                best_fitness = f_mut
                best_individual = mut_best
                best_metrics = m_mut

            convergence_history.append(round(best_fitness, 2))

        # 3. Format final optimized palette
        final_colors_rgb = self._decode_individual(best_individual)
        optimized_colors = []
        for idx, role_def in enumerate(DEFAULT_UI_ROLES):
            rgb = final_colors_rgb[idx]
            hex_code = rgb_to_hex(*rgb)
            optimized_colors.append({
                "hex_code": hex_code,
                "nombre": role_def["nombre"],
                "token_name": role_def["token_name"],
                "uso": role_def["uso"],
                "orden": idx
            })

        execution_time = (time.time() - start_time) * 1000.0

        return {
            "colores": optimized_colors,
            "metrics": {
                **best_metrics,
                "harmony_template": self.harmony_type,
                "theme_mode": self.mode
            },
            "iterations": self.max_iter,
            "population_size": self.pop_size,
            "execution_time_ms": round(execution_time, 2),
            "convergence_history": convergence_history[::max(1, len(convergence_history) // 15)]
        }
