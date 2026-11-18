"""
Cinematic Media Engine para Simple-Tube
Direção de fotografia com IA generativa (Pollinations Flux), clipes de vídeo MP4 reais da NASA,
fotografia científica do Wikimedia Commons e fallback procedural anti-404.
"""

import io
import os
import json
import time
import hashlib
import urllib.parse
import urllib.request
from PIL import Image

from media.fallback_visuals import is_valid_image, generate_cosmic_artwork

USER_AGENT = "SimpleTube-CinematicEngine/2.0 (https://github.com/scapaticitecnologia/simple-tube)"


def is_valid_video(path: str, min_bytes: int = 100_000) -> bool:
    """Valida se o arquivo de vídeo MP4 existe e possui tamanho mínimo saudável."""
    return os.path.exists(path) and os.path.getsize(path) >= min_bytes


def build_cinematic_prompt(
    scene: dict,
    project_title: str,
    scene_idx: int = 0,
    is_vertical: bool = False,
) -> str:
    """Constrói um prompt de direção de fotografia cinematográfica alinhado à narrativa da cena."""
    headline = (scene.get("headline") or "").strip()
    visual_theme = (scene.get("visual_theme") or "").strip()
    narration = (scene.get("narration") or "").strip()
    scene_type = (scene.get("type") or "investigation").strip().lower()

    mood_map = {
        "hook": "dramatic high-contrast opening shot, volumetric rim lighting, awe-inspiring scale, anamorphic lens flare",
        "investigation": "scientific documentary cinematography, crisp architectural detail, deep atmospheric depth, moody cyan and amber lighting",
        "revelation": "breathtaking revelation shot, golden and electric cyan glow, ultra-detailed textures, sharp focus",
        "climax": "epic cosmic climax, intense energy dynamics, dramatic chiaroscuro, IMAX 70mm film look",
        "cta": "vast serene cosmic horizon, inspiring infinite perspective, deep twilight blues and subtle starlight",
    }
    mood = mood_map.get(scene_type, mood_map["investigation"])
    framing = "vertical 9:16 composition, centered hero subject" if is_vertical else "widescreen 16:9 cinema composition, rule of thirds"

    narrative_hint = ""
    if narration:
        words = [w for w in narration.replace("\n", " ").split() if len(w) > 3][:18]
        narrative_hint = " ".join(words)

    core_subject = visual_theme or headline or project_title
    prompt = (
        f"Photorealistic cinema still, {core_subject}. "
        f"Context: {project_title}. {headline}. {narrative_hint}. "
        f"{mood}, {framing}, photorealistic 8k, hyper-detailed, Unreal Engine 5 realism, "
        f"film grain, no text, no subtitles, no watermark, no UI, no letters"
    )
    return prompt[:480]


def generate_ai_image(
    prompt: str,
    out_path: str,
    width: int = 1920,
    height: int = 1080,
    seed: int = 42,
) -> bool:
    """Gera imagem cinematográfica inédita via Pollinations.ai (sem necessidade de API key)."""
    encoded = urllib.parse.quote(prompt, safe="")
    # Usa dimensões múltiplas de 16 otimizadas para geração rápida e nítida
    gen_w = 1088 if width < height else 1280
    gen_h = 1920 if width < height else 720
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={gen_w}&height={gen_h}&seed={seed}&nologo=true&enhance=true"

    for attempt in range(1, 3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read()
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            img.save(out_path, format="JPEG", quality=94)
            if is_valid_image(out_path):
                return True
        except Exception as exc:
            if attempt == 1:
                time.sleep(2)
            else:
                print(f"[MEDIA IA] ⚠️ Falha Pollinations ({exc})", flush=True)
    return False


def fetch_nasa_video_clip(
    query: str,
    out_mp4_path: str,
    used_urls: set,
    max_mb: float = 24.0,
) -> bool:
    """Busca e baixa um clipe MP4 real da NASA pertinente ao tema da cena."""
    clean_words = [w for w in query.split() if w.lower() not in ("nasa", "webb", "hubble", "8k", "4k")]
    attempts = [query]
    if len(clean_words) >= 2:
        attempts.append(" ".join(clean_words[:3]))

    for q in attempts:
        search_url = f"https://images-api.nasa.gov/search?q={urllib.parse.quote(q)}&media_type=video"
        try:
            req = urllib.request.Request(search_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            items = data.get("collection", {}).get("items", [])
            for item in items[:12]:
                href = item.get("href")
                if not href:
                    continue
                try:
                    m_req = urllib.request.Request(href, headers={"User-Agent": USER_AGENT})
                    with urllib.request.urlopen(m_req, timeout=12) as m_resp:
                        assets = json.loads(m_resp.read().decode("utf-8"))
                    mp4s = [a for a in assets if isinstance(a, str) and a.lower().endswith(".mp4")]
                    chosen = None
                    for pref in ["~medium.mp4", "~small.mp4", "~large.mp4", "~orig.mp4"]:
                        for candidate in mp4s:
                            if pref in candidate and candidate not in used_urls:
                                chosen = candidate
                                break
                        if chosen:
                            break
                    if not chosen:
                        continue

                    head_req = urllib.request.Request(chosen, method="HEAD", headers={"User-Agent": USER_AGENT})
                    try:
                        with urllib.request.urlopen(head_req, timeout=10) as h_resp:
                            cl = int(h_resp.headers.get("Content-Length", "0") or 0)
                            if cl > max_mb * 1024 * 1024:
                                continue
                    except Exception:
                        pass

                    dl_req = urllib.request.Request(chosen, headers={"User-Agent": USER_AGENT})
                    with urllib.request.urlopen(dl_req, timeout=45) as v_resp:
                        video_bytes = v_resp.read()
                    if len(video_bytes) < 100_000 or len(video_bytes) > max_mb * 1024 * 1024:
                        continue

                    os.makedirs(os.path.dirname(os.path.abspath(out_mp4_path)), exist_ok=True)
                    with open(out_mp4_path, "wb") as vf:
                        vf.write(video_bytes)
                    if is_valid_video(out_mp4_path):
                        used_urls.add(chosen)
                        return True
                except Exception:
                    continue
        except Exception:
            continue
    return False


def fetch_wikimedia_image(
    query: str,
    out_path: str,
    used_urls: set,
    width: int = 1920,
    height: int = 1080,
) -> bool:
    """Busca fotografia científica/tecnológica real em alta resolução no Wikimedia Commons."""
    params = urllib.parse.urlencode({
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": 6,
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
        "format": "json",
    })
    url = f"https://commons.wikimedia.org/w/api.php?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        pages = list((data.get("query") or {}).get("pages", {}).values())
        for page in pages:
            info = (page.get("imageinfo") or [{}])[0]
            img_url = info.get("url")
            mime = info.get("mime", "")
            w = info.get("width", 0)
            if not img_url or img_url in used_urls or mime not in ("image/jpeg", "image/png") or w < 900:
                continue
            try:
                dl_req = urllib.request.Request(img_url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(dl_req, timeout=25) as r:
                    img = Image.open(io.BytesIO(r.read())).convert("RGB")
                img = _center_crop_resize(img, width, height)
                os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
                img.save(out_path, format="JPEG", quality=94)
                if is_valid_image(out_path):
                    used_urls.add(img_url)
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def _center_crop_resize(img: Image.Image, target_width: int, target_height: int) -> Image.Image:
    orig_w, orig_h = img.size
    target_ratio = target_width / target_height
    orig_ratio = orig_w / orig_h
    if orig_ratio > target_ratio:
        new_w = int(orig_h * target_ratio)
        left = (orig_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, orig_h))
    else:
        new_h = int(orig_w / target_ratio)
        top = (orig_h - new_h) // 2
        img = img.crop((0, top, orig_w, top + new_h))
    return img.resize((target_width, target_height), Image.Resampling.LANCZOS)


def acquire_scene_media(
    scene: dict,
    scene_idx: int,
    project_id: str,
    project_title: str,
    assets_dir: str,
    used_urls: set,
    query_override: str = "",
    is_vertical: bool = False,
    allow_video: bool = True,
) -> tuple:
    """
    Obtém mídia cinematográfica dinâmica para uma cena:
    1) Vídeo MP4 real da NASA em cenas-chave de movimento/clímax (quando `allow_video=True`)
    2) Arte cinematográfica inédita gerada por IA (Pollinations Flux) fiel à narrativa
    3) Fotografia real do Wikimedia Commons (ótimo para física/tecnologia/laboratórios)
    4) NASA Image API estritamente relacionada ao tema
    5) Arte cósmica procedural 1080p como fallback final
    Retorna: (kind: 'video'|'image', relative_asset_path: str, source_label: str)
    """
    img_name = f"scene_{scene_idx + 1}.jpg"
    vid_name = f"scene_{scene_idx + 1}.mp4"
    img_dest = os.path.join(assets_dir, img_name)
    vid_dest = os.path.join(assets_dir, vid_name)

    target_w, target_h = (1080, 1920) if is_vertical else (1920, 1080)
    query = (query_override or scene.get("visual_theme") or scene.get("headline") or project_title).strip()
    seed_int = int(hashlib.sha256(f"{project_id}_{scene_idx}_{query}".encode("utf-8")).hexdigest()[:8], 16)

    # Se já existir vídeo ou imagem válida, reutiliza
    if allow_video and is_valid_video(vid_dest):
        return ("video", f"assets/{project_id}/{vid_name}", "cache-video")
    if is_valid_image(img_dest) and not (allow_video and scene_idx in (0, 2, 4)):
        return ("image", f"assets/{project_id}/{img_name}", "cache-image")

    # 1. Cenas estratégicas de movimento/clímax tentam vídeo MP4 real da NASA primeiro
    wants_video = allow_video and (scene_idx in (0, 2, 4) or scene.get("type") == "climax")
    if wants_video and fetch_nasa_video_clip(query, vid_dest, used_urls):
        return ("video", f"assets/{project_id}/{vid_name}", "nasa-mp4")

    # 2. Geração dinâmica por IA alinhada ao roteiro exato da cena
    if not is_valid_image(img_dest):
        ai_prompt = build_cinematic_prompt(scene, project_title, scene_idx=scene_idx, is_vertical=is_vertical)
        if generate_ai_image(ai_prompt, img_dest, width=target_w, height=target_h, seed=seed_int):
            return ("image", f"assets/{project_id}/{img_name}", "ai-pollinations")

        # 3. Wikimedia Commons (fotos reais de laboratórios, telescópios, física, tecnologia)
        if fetch_wikimedia_image(query, img_dest, used_urls, width=target_w, height=target_h):
            return ("image", f"assets/{project_id}/{img_name}", "wikimedia")

        # 4. NASA Image API estritamente para a query (sem fallback cego para nebulosas genéricas)
        if _fetch_strict_nasa_image(query, img_dest, used_urls, width=target_w, height=target_h):
            return ("image", f"assets/{project_id}/{img_name}", "nasa-image")

        # 5. Fallback procedural garantido
        generate_cosmic_artwork(img_dest, seed_key=f"{project_id}_{img_name}_{query}")
        return ("image", f"assets/{project_id}/{img_name}", "procedural-fallback")

    return ("image", f"assets/{project_id}/{img_name}", "cache-image")


def _fetch_strict_nasa_image(
    query: str,
    out_path: str,
    used_urls: set,
    width: int = 1920,
    height: int = 1080,
) -> bool:
    """Busca imagem NASA apenas para a query temática real, sem recorrer a nebulosas repetidas."""
    url = f"https://images-api.nasa.gov/search?q={urllib.parse.quote(query)}&media_type=image"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for item in data.get("collection", {}).get("items", [])[:15]:
            href = item.get("href")
            if not href:
                continue
            try:
                m_req = urllib.request.Request(href, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(m_req, timeout=12) as m_resp:
                    assets = json.loads(m_resp.read().decode("utf-8"))
                candidates = [a for a in assets if isinstance(a, str) and a.lower().endswith(".jpg")]
                chosen = next((c for pref in ("~large.jpg", "~orig.jpg", "~medium.jpg") for c in candidates if pref in c and c not in used_urls), None)
                if not chosen:
                    continue
                dl_req = urllib.request.Request(chosen, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(dl_req, timeout=25) as r:
                    img = Image.open(io.BytesIO(r.read())).convert("RGB")
                img = _center_crop_resize(img, width, height)
                os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
                img.save(out_path, format="JPEG", quality=94)
                if is_valid_image(out_path):
                    used_urls.add(chosen)
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False
