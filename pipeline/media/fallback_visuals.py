"""
Simple-Tube Procedural Cosmic Art & Visual Integrity Guard
Garante que NENHUM vídeo falhe por imagem ausente, corrompida ou erro de API externa.
Valida imagens baixadas e, quando necessário, gera ilustrações astronômicas 1920x1080
procedurais em alta definição (nebulosas, campos estelares, grades gravitacionais e flares).
"""

import os
import sys
import math
import random
import hashlib
import argparse
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance


def is_valid_image(path: str, min_bytes: int = 4096) -> bool:
    """Verifica se o arquivo existe, tem tamanho válido e é decodificável pelo Pillow."""
    if not os.path.exists(path) or os.path.getsize(path) < min_bytes:
        return False
    try:
        with Image.open(path) as img:
            img.verify()
        with Image.open(path) as img:
            w, h = img.size
            return w >= 320 and h >= 240
    except Exception:
        return False


def generate_cosmic_artwork(
    out_path: str,
    seed_key: str = "cosmos",
    width: int = 1920,
    height: int = 1080,
) -> str:
    """
    Gera uma arte espacial procedural em alta definição (1920x1080) com nebulosa,
    lente gravitacional / halo estelar e campo profundo de estrelas para fallback seguro.
    """
    digest = hashlib.sha256(seed_key.encode("utf-8", errors="ignore")).hexdigest()
    seed_val = int(digest[:12], 16)
    rng = random.Random(seed_val)

    palettes = [
        ((6, 12, 30), (0, 195, 255), (110, 45, 220), (255, 200, 80)),
        ((10, 8, 26), (40, 220, 255), (220, 60, 140), (255, 225, 130)),
        ((4, 16, 24), (0, 242, 254), (20, 110, 235), (255, 160, 50)),
        ((14, 8, 20), (130, 80, 255), (0, 210, 245), (255, 215, 90)),
    ]
    base_bg, c_primary, c_secondary, c_accent = palettes[seed_val % len(palettes)]

    img = Image.new("RGBA", (width, height), (*base_bg, 255))

    # 1. Nuvens de nebulosa em camadas com blur gaussiano
    nebula = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ndraw = ImageDraw.Draw(nebula)

    cx = rng.randint(int(width * 0.25), int(width * 0.75))
    cy = rng.randint(int(height * 0.25), int(height * 0.75))

    for i in range(18):
        ox = cx + rng.randint(-550, 550)
        oy = cy + rng.randint(-320, 320)
        rx = rng.randint(180, 520)
        ry = rng.randint(120, 360)
        color = c_primary if i % 2 == 0 else c_secondary
        alpha = rng.randint(24, 65)
        ndraw.ellipse([ox - rx, oy - ry, ox + rx, oy + ry], fill=(*color, alpha))

    nebula = nebula.filter(ImageFilter.GaussianBlur(radius=95))
    img = Image.alpha_composite(img, nebula)

    # 2. Anéis gravitacionais / disco de acreção ou ondas cósmicas sutis
    rings = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(rings)
    for r_idx in range(1, 6):
        radius_x = 120 + r_idx * 95
        radius_y = int(radius_x * rng.uniform(0.38, 0.72))
        alpha = max(18, 95 - r_idx * 15)
        col = c_primary if r_idx % 2 else c_accent
        rdraw.ellipse(
            [cx - radius_x, cy - radius_y, cx + radius_x, cy + radius_y],
            outline=(*col, alpha),
            width=rng.randint(2, 5),
        )
    # Núcleo brilhante central
    for g_rad, g_alpha in [(140, 35), (75, 70), (28, 160)]:
        rdraw.ellipse(
            [cx - g_rad, cy - g_rad, cx + g_rad, cy + g_rad],
            fill=(*c_accent, g_alpha),
        )
    rings = rings.filter(ImageFilter.GaussianBlur(radius=6))
    img = Image.alpha_composite(img, rings)

    # 3. Campo estelar profundo (milhares de micro-estrelas e estrelas brilhantes)
    stars = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(stars)
    for _ in range(950):
        sx = rng.randint(0, width - 1)
        sy = rng.randint(0, height - 1)
        sz = rng.choices([1, 2, 3], weights=[75, 20, 5])[0]
        brightness = rng.randint(140, 255)
        tint = (
            brightness,
            brightness if rng.random() > 0.2 else int(brightness * 0.85),
            min(255, brightness + 20) if rng.random() > 0.3 else int(brightness * 0.8),
            rng.randint(130, 255),
        )
        sdraw.ellipse([sx, sy, sx + sz, sy + sz], fill=tint)

    # Algumas estrelas com difração em cruz (estilo Hubble/Webb)
    for _ in range(12):
        sx = rng.randint(80, width - 80)
        sy = rng.randint(80, height - 80)
        flare_len = rng.randint(14, 34)
        sdraw.line([(sx - flare_len, sy), (sx + flare_len, sy)], fill=(220, 248, 255, 190), width=2)
        sdraw.line([(sx, sy - flare_len), (sx, sy + flare_len)], fill=(220, 248, 255, 190), width=2)
        sdraw.ellipse([sx - 4, sy - 4, sx + 4, sy + 4], fill=(255, 255, 255, 245))

    img = Image.alpha_composite(img, stars)

    # 4. Ajuste cinematográfico final e salvamento JPEG garantido
    rgb = img.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.15)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    rgb.save(out_path, format="JPEG", quality=94)
    return out_path


def ensure_image_file(out_path: str, seed_key: str = "cosmos") -> bool:
    """Garante que `out_path` exista como JPEG válido, gerando fallback procedural se necessário."""
    if is_valid_image(out_path):
        return True
    generate_cosmic_artwork(out_path, seed_key=seed_key)
    return is_valid_image(out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validador e gerador procedural de imagens espaciais")
    parser.add_argument("--out", required=True, help="Caminho de saída .jpg")
    parser.add_argument("--seed", default="cosmos", help="Texto-semente para variação visual")
    args = parser.parse_args()
    generate_cosmic_artwork(args.out, seed_key=args.seed)
    print(f"[FALLBACK VISUAL] ✅ Arte procedural gerada em: {args.out}")

