"""
void_intelligence.selen --- SELEN: The Eyes of VOID.

SELEN = SEHEN. The ability to SEE patterns in any data.

Eyes see photons — ONE substrate.
SELEN sees DATA — EVERY substrate.

Eyes are a projection of x.
SELEN IS x, applied.

The Three-Zone Theorem:
    Any force acting on any substrate produces a feature
    detectable by three zones (floor, rim, exterior)
    and one formula (two subtractions, one multiplication).

    score = 0.05 * cbrt(A*B*C*500) + 0.95 * (AB + AC*500 + BC*500) / 3

    Where:
        A = rim_mean - floor_mean       (the feature has a boundary)
        B = max(rim-ext, ext-floor)     (the feature differs from context)
        C = symmetry                     (the feature has regularity)

Works on:
    - Images (lunar craters, sunspots, skin lesions, black holes)
    - Time series (burnout, HRV, sleep, energy cycles)
    - Sequences (contact frequency, account balances, V-Scores)
    - Any measurable signal where force acts on substrate

GR-2026-071: SELEN on 20 physical domains (43,132 detections)
GR-2026-072: Three-Zone Theorem on 25 physical + cognitive domains

Zero parameters. Zero training. Zero dependencies (just math).
"""

from __future__ import annotations



def see(signal: list[float],
        min_width: int = 0,
        max_width: int = 0,
        threshold: float = 0.5) -> list[dict]:
    """
    SELEN Universal Detector for 1D signals. Pure Python, zero deps.

    Sees what FORCE does to SUBSTRATE in any measurable signal.

    Args:
        signal: List of numeric values (any domain)
        min_width: Minimum feature width (0 = auto: len/20)
        max_width: Maximum feature width (0 = auto: len/3)
        threshold: Minimum SELEN score to keep (default 0.5)

    Returns:
        List of detections, each with:
            center: int     - position of feature center
            width: int      - feature width (in samples)
            score: float    - SELEN score (higher = stronger feature)
            A: float        - rim-floor contrast
            B: float        - context contrast
            C: float        - temporal symmetry (0-1)
            mode: str       - 'crater' (temporary dip) or 'pit' (sustained)
            floor_mean: float  - mean value in feature interior
            rim_mean: float    - mean value in transition zone
            ext_mean: float    - mean value in surrounding context
    """
    n = len(signal)
    if n < 10:
        return []

    # Auto-calculate widths
    if min_width <= 0:
        min_width = max(2, n // 20)
    if max_width <= 0:
        max_width = max(min_width + 1, n // 3)

    # Normalize to 0-255 for scoring comparability
    sig_min = min(signal)
    sig_max = max(signal)
    rng = sig_max - sig_min
    if rng < 1e-10:
        return []

    norm = [(v - sig_min) / rng * 255.0 for v in signal]

    # Prefix sums for O(1) range means
    prefix = [0.0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + norm[i]

    def range_mean(start: int, end: int) -> float:
        s = max(0, start)
        e = min(n, end)
        if e <= s:
            return 0.0
        return (prefix[e] - prefix[s]) / (e - s)

    # Geometric width progression
    widths: list[int] = []
    w = min_width
    while w <= max_width:
        widths.append(w)
        w = max(w + 1, int(w * 1.3))

    candidates: list[dict] = []

    for w in widths:
        floor_half = max(1, int(w * 0.45))
        rim_inner = max(2, int(w * 0.70))
        rim_outer = int(w * 1.30)
        ext_inner = int(w * 1.60)
        ext_outer = int(w * 2.50)
        margin = ext_outer + 1
        step = max(w // 2, 1)

        for center in range(margin, n - margin, step):
            # Three zone means
            floor_mean = range_mean(center - floor_half, center + floor_half)
            rim_left = range_mean(center - rim_outer, center - rim_inner)
            rim_right = range_mean(center + rim_inner, center + rim_outer)
            rim_mean = (rim_left + rim_right) / 2.0
            ext_left = range_mean(center - ext_outer, center - ext_inner)
            ext_right = range_mean(center + ext_inner, center + ext_outer)
            ext_mean = (ext_left + ext_right) / 2.0

            # Dual mode detection (IDENTICAL to image SELEN)
            A = rim_mean - floor_mean
            B_crater = rim_mean - ext_mean
            B_pit = ext_mean - floor_mean

            s_crater = max(0.0, A) * max(0.0, B_crater)
            s_pit = max(0.0, A) * max(0.0, B_pit)

            if s_crater >= s_pit:
                mode = 'crater'
                B_val = max(0.0, B_crater)
                A_val = max(0.0, A)
            else:
                mode = 'pit'
                B_val = max(0.0, B_pit)
                A_val = max(0.0, A)

            if A_val * B_val < 0.01:
                continue

            # Temporal symmetry (replaces angular uniformity)
            left_start = max(0, center - w)
            left_vals = norm[left_start:center]
            right_vals = norm[center:min(n, center + w)]
            if len(left_vals) < 2 or len(right_vals) < 2:
                continue

            min_len = min(len(left_vals), len(right_vals))
            left_mirror = list(reversed(left_vals[-min_len:]))
            right_side = right_vals[:min_len]

            asym_sum = sum(abs(l - r) for l, r in zip(left_mirror, right_side))
            asymmetry = asym_sum / min_len

            # Standard deviation of normalized signal
            mean_norm = sum(norm) / n
            var_sum = sum((v - mean_norm) ** 2 for v in norm)
            std_norm = (var_sum / n) ** 0.5
            if std_norm < 1e-10:
                continue

            C = max(0.0, 1.0 - 1.5 * asymmetry / std_norm)
            if C < 0.1:
                continue

            # SELEN SCORE — THE formula
            AB = A_val * B_val
            AC = A_val * C * 500
            BC = B_val * C * 500

            score = 0.05 * (max(0.0, A_val * B_val * C * 500) ** (1/3)) + \
                    0.95 * (AB + AC + BC) / 3.0

            if score < threshold:
                continue

            candidates.append({
                'center': center,
                'width': w,
                'score': score,
                'A': A_val,
                'B': B_val,
                'C': C,
                'mode': mode,
                'floor_mean': floor_mean,
                'rim_mean': rim_mean,
                'ext_mean': ext_mean,
            })

    # NMS
    candidates.sort(key=lambda c: c['score'], reverse=True)
    keep: list[dict] = []
    used: set[int] = set()

    for c in candidates:
        center = c['center']
        w = c['width']
        overlap = any(pos in used for pos in range(center - w, center + w))
        if overlap:
            continue
        keep.append(c)
        used.update(range(center - w, center + w))

    return keep


def narrate(detections: list[dict],
            labels: list[str] | None = None,
            domain: str = "signal",
            force: str = "force",
            substrate: str = "substrate") -> str:
    """
    Turn SELEN detections into natural language.

    Returns a narrative that EXPLAINS what was seen,
    not just numbers. Because seeing is understanding.
    """
    if not detections:
        return (
            f"No features detected in {domain}. "
            f"The {substrate} is stable — no {force} is creating anomalies. "
            f"This is good: a clean signal means a healthy system."
        )

    n = len(detections)
    n_crater = sum(1 for d in detections if d['mode'] == 'crater')
    n_pit = sum(1 for d in detections if d['mode'] == 'pit')
    top = detections[0]

    parts = [f"SELEN sees {n} feature{'s' if n > 1 else ''} in {domain}"]

    if n_pit > 0 and n_crater > 0:
        parts.append(
            f"{n_crater} temporary (crater) and {n_pit} sustained (pit). "
            f"The mix suggests both acute disruptions and chronic patterns."
        )
    elif n_pit > 0:
        parts.append(
            f"All {n_pit} are sustained (pit mode) — {force} is creating "
            f"lasting impact on {substrate}, not just temporary dips."
        )
    else:
        parts.append(
            f"All {n_crater} are temporary (crater mode) — {force} causes "
            f"dips in {substrate} but recovery follows."
        )

    # Top feature detail
    label = labels[top['center']] if labels and top['center'] < len(labels) else f"position {top['center']}"
    parts.append(
        f"Strongest feature at {label} (score {top['score']:.0f}, "
        f"symmetry {top['C']:.0%})."
    )

    # Symmetry insight
    avg_c = sum(d['C'] for d in detections) / n
    if avg_c > 0.7:
        parts.append("High symmetry — the environment is uniform, recovery is balanced.")
    elif avg_c > 0.4:
        parts.append("Moderate symmetry — some asymmetry in impact/recovery.")
    else:
        parts.append("Low symmetry — asymmetric features suggest uneven forces or recovery.")

    return " ".join(parts)


def diagnose(detections: list[dict]) -> dict:
    """
    Map SELEN detections to a health diagnosis.

    Returns VOID-compatible severity levels.
    """
    if not detections:
        return {
            'severity': 'healthy',
            'n_features': 0,
            'message': 'No anomalies. Stable substrate.',
        }

    n = len(detections)
    n_pit = sum(1 for d in detections if d['mode'] == 'pit')
    max_score = max(d['score'] for d in detections)
    avg_c = sum(d['C'] for d in detections) / n

    if n_pit > 0 and max_score > 10000:
        severity = 'critical'
    elif max_score > 5000:
        severity = 'warning'
    elif n > 3:
        severity = 'attention'
    else:
        severity = 'mild'

    return {
        'severity': severity,
        'n_features': n,
        'n_craters': n - n_pit,
        'n_pits': n_pit,
        'max_score': max_score,
        'avg_symmetry': avg_c,
        'message': narrate(detections),
    }
