"""Pixel-art asteroid SVG generation for AstroSurge.

Each asteroid gets 3 rotation variants (0°, 120°, 240°) deterministically
generated from its SPK ID. Output is an inline SVG string — no file storage,
no binary dependencies (pure Python + math module only).
"""

import hashlib
import math
import random
from typing import Optional


# ─── color palettes by asteroid class ─────────────────────────────────────

PALETTES: dict[str, list[tuple[int, int, int]]] = {
    "M": [  # Metallic: mostly gray, subtle copper and purple accents
        (100, 100, 110),  # gray
        (140, 140, 150),  # light gray
        (80, 80, 90),     # dark gray
        (115, 115, 125),  # mid-light gray
        (65, 65, 75),     # dark gray
        (184, 115, 51),   # copper (accent)
        (120, 60, 160),   # purple
        (90, 40, 130),    # dark purple
        (40, 40, 45),     # near black
        (60, 40, 20),     # brown shadow
    ],
    "C": [  # Carbonaceous: gray with subtle blue and purple accents
        (35, 35, 40),     # near black
        (55, 55, 62),     # dark gray
        (75, 75, 83),     # mid-dark gray
        (95, 95, 103),    # mid gray
        (115, 115, 123),  # light gray
        (65, 65, 72),     # shadow gray
        (30, 55, 100),    # muted blue (subtle accent)
        (95, 55, 135),    # purple
        (65, 38, 100),    # dark purple
        (40, 40, 47),     # shadow
    ],
    "S": [  # Stony: gray, purple, brown
        (120, 120, 130),  # gray
        (150, 150, 155),  # light gray
        (90, 90, 100),    # dark gray
        (100, 60, 140),   # purple
        (130, 80, 160),   # light purple
        (70, 40, 100),    # dark purple
        (100, 70, 50),    # brown
        (80, 55, 40),     # dark brown
        (40, 40, 45),     # near black
        (60, 60, 65),     # shadow gray
    ],
}

FALLBACK_PALETTE: list[tuple[int, int, int]] = [
    (100, 100, 110), (60, 60, 70), (80, 80, 90), (40, 40, 45),
]


def _get_palette(asteroid_class: str) -> list[tuple[int, int, int]]:
    return PALETTES.get(asteroid_class.upper(), FALLBACK_PALETTE)


def _seed_rng(spkid: int, variant: int) -> random.Random:
    """Create a deterministic RNG from spkid + variant."""
    seed_str = f"{spkid}-asteroid-image-{variant}"
    digest = hashlib.md5(seed_str.encode()).hexdigest()
    seed = int(digest[:8], 16)
    return random.Random(seed)


def _circular_diff(a: float, b: float) -> float:
    """Shortest angular distance between two angles in radians."""
    return abs(((a - b + math.pi) % (2 * math.pi)) - math.pi)


def generate_asteroid_svg(
    spkid: int,
    asteroid_class: str = "M",
    diameter_km: float = 3.0,
    variant: int = 0,
    size: int = 128,
    block_size: int = 4,
) -> str:
    """Generate an SVG string of a pixel-art asteroid.

    Args:
        spkid: SPK ID (deterministic seed for the shape).
        asteroid_class: 'M', 'C', or 'S' (determines color palette).
        diameter_km: Approximate diameter — scales the asteroid size.
        variant: Rotation view — 0 (0°), 1 (120°), or 2 (240°).
        size: SVG viewBox size in pixels (default 128).
        block_size: Pixel block size — 4 = standard, 2 = surveyed (higher fidelity).

    Returns:
        SVG string with transparent background.
    """
    grid = size // block_size
    rng = _seed_rng(spkid, variant)
    palette = _get_palette(asteroid_class)
    rotation = variant * (2.0 * math.pi / 3.0)
    cx = cy = grid // 2

    # ── Base radius (scaled by diameter, capped to fit grid) ──────────
    base_r = 4 + grid * 0.35 * min(1.0, diameter_km / 6.0)
    base_r = min(base_r, grid * 0.42)

    # ── Radius profile (72 rays) ──────────────────────────────────────
    num_rays = 72
    angles = [i * 2.0 * math.pi / num_rays for i in range(num_rays)]

    # 1. Elliptical stretch — mostly oblong (1.5:1 to 4.0:1)
    stretch = 0.3 + rng.random() * 1.0
    stretch_angle = rng.uniform(0, 2.0 * math.pi)
    ellipse_r = []
    for a in angles:
        d = a - stretch_angle
        c = math.cos(d)
        s = math.sin(d)
        r = base_r * (1.0 + stretch) / math.sqrt(c * c + (1.0 + stretch) ** 2 * s * s)
        ellipse_r.append(r)

    # 2. Lobes (1-3 bulges)
    num_lobes = rng.randint(1, 3)
    lobe_angles = [rng.uniform(0, 2.0 * math.pi) for _ in range(num_lobes)]
    lobe_widths = [rng.uniform(0.3, 1.0) for _ in range(num_lobes)]
    lobe_amps = [rng.uniform(0.10, 0.35) for _ in range(num_lobes)]
    lobes = [0.0] * num_rays
    for i in range(num_rays):
        for la, lw, lam in zip(lobe_angles, lobe_widths, lobe_amps):
            d = _circular_diff(angles[i], la)
            lobes[i] += lam * math.exp(-d * d / (2.0 * lw * lw))

    # 3. Extreme protrusion (40% chance)
    spike = [0.0] * num_rays
    if rng.random() < 0.40:
        sa = rng.uniform(0, 2.0 * math.pi)
        sw = rng.uniform(0.05, 0.15)
        sa_amp = rng.uniform(0.3, 0.8)
        for i in range(num_rays):
            d = _circular_diff(angles[i], sa)
            spike[i] = sa_amp * math.exp(-d * d / (2.0 * sw * sw))

    # 4. Craters (0-2 indentations)
    num_craters = rng.randint(0, 2)
    crater_angles = [rng.uniform(0, 2.0 * math.pi) for _ in range(num_craters)]
    crater_depths = [rng.uniform(0.10, 0.30) for _ in range(num_craters)]
    craters = [0.0] * num_rays
    for i in range(num_rays):
        for ca, cd in zip(crater_angles, crater_depths):
            d = _circular_diff(angles[i], ca)
            craters[i] -= cd * math.exp(-d * d / (2.0 * 0.20 * 0.20))

    # 5. Roughness
    roughness = [rng.gauss(0, 0.06) for _ in range(num_rays)]

    # Combine
    radii = [
        ellipse_r[i] * (1.0 + lobes[i] + spike[i] + craters[i] + roughness[i])
        for i in range(num_rays)
    ]

    # Normalise to fit within grid bounds
    max_r = max(radii)
    if max_r > grid * 0.46:
        scale = grid * 0.46 / max_r
        radii = [r * scale for r in radii]
    radii = [max(2.0, min(r, grid * 0.48)) for r in radii]

    # ── Build shape mask on N×N grid ──────────────────────────────────
    mask = [[False] * grid for _ in range(grid)]

    for y in range(grid):
        for x in range(grid):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)
            pa = (math.atan2(dy, dx) - rotation) % (2.0 * math.pi)
            idx = int(pa / (2.0 * math.pi) * num_rays)
            idx = max(0, min(idx, num_rays - 1))
            if dist <= radii[idx]:
                mask[y][x] = True

    # ── Assign colours with terrain shading ──────────────────────────
    colors = [[None] * grid for _ in range(grid)]

    for y in range(grid):
        for x in range(grid):
            if not mask[y][x]:
                continue

            # Deterministic per-cell RNG
            cell_seed = rng.randint(0, 2_000_000_000) + x * 31 + y * 17
            cell_rng = random.Random(cell_seed)

            # Pseudo-height from cell position and sinusoidal terrain
            h = 0.25 + cell_rng.random() * 0.5
            for _ in range(3):
                fx = rng.uniform(0.5, 3.0)
                fy = rng.uniform(0.5, 3.0)
                px = rng.uniform(0, grid)
                py_val = rng.uniform(0, grid)
                amp = rng.uniform(0.05, 0.15)
                h += amp * math.sin(
                    fx * (x - px) / grid * 2.0 * math.pi
                    + fy * (y - py_val) / grid * 2.0 * math.pi
                )
            h = max(0.0, min(1.0, h))

            # Pick palette index based on height
            half = len(palette) // 2
            if h > 0.6:
                idx_color = cell_rng.randint(0, half - 1)
            elif h > 0.3:
                idx_color = cell_rng.randint(0, len(palette) - 1)
            else:
                idx_color = cell_rng.randint(half, len(palette) - 1)

            r, g, b = palette[max(0, min(idx_color, len(palette) - 1))]
            bv = int((h - 0.5) * 30)
            r = max(0, min(255, r + bv))
            g = max(0, min(255, g + bv))
            b = max(0, min(255, b + bv))
            colors[y][x] = (r, g, b)

    # ── Build SVG string ──────────────────────────────────────────────
    rects: list[str] = []
    for y in range(grid):
        for x in range(grid):
            c = colors[y][x]
            if c is None:
                continue
            rects.append(
                f'<rect x="{x * block_size}" y="{y * block_size}" '
                f'width="{block_size}" height="{block_size}" '
                f'fill="rgb({c[0]},{c[1]},{c[2]})"/>'
            )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {size} {size}" width="{size}" height="{size}">\n'
        f'  {"".join(rects)}\n'
        f'</svg>'
    )

    return svg


def generate_svg_bytes(
    spkid: int,
    asteroid_class: str = "M",
    diameter_km: float = 3.0,
    variant: int = 0,
    block_size: int = 4,
) -> bytes:
    """Generate an asteroid SVG and return UTF-8 encoded bytes."""
    svg = generate_asteroid_svg(
        spkid=spkid,
        asteroid_class=asteroid_class,
        diameter_km=diameter_km,
        variant=variant,
        block_size=block_size,
    )
    return svg.encode("utf-8")
