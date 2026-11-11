"""
Simple-Tube Daily Autopilot
Orquestrador 100% autônomo para criação e publicação diária de conteúdo.
Executado diariamente às 09h pelo Agendador de Tarefas do Windows (Task Scheduler).
"""

import os
import sys
import json
import time
import datetime
import urllib.request
import urllib.parse
import io
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_BASE = os.path.join(PROJECT_DIR, "projects")
STATE_FILE = os.path.join(PROJECT_DIR, "pipeline", "autopilot_state.json")
LOG_FILE = os.path.join(PROJECT_DIR, "pipeline", "autopilot.log")

def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{now}] {msg}"
    print(formatted, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def run_cmd(cmd):
    log(f"> Executando: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=PROJECT_DIR)
    if res.returncode != 0:
        raise RuntimeError(f"Comando falhou com código {res.returncode}: {cmd}")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_run_date": None, "completed_projects": []}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_nasa_image_url(query, used_urls=None):
    if used_urls is None:
        used_urls = set()
    # Tenta a query completa e, se não achar inédita, tenta sub-termos para garantir variedade
    words = query.split()
    search_attempts = [query]
    if len(words) > 3:
        search_attempts.append(" ".join(words[:3]))
        search_attempts.append(" ".join(words[-3:]))
    search_attempts.extend(["nebula hubble", "supernova remnant chandra", "spiral galaxy webb", "black hole accretion", "star cluster hubble"])

    for q in search_attempts:
        url = f"https://images-api.nasa.gov/search?q={urllib.parse.quote(q)}&media_type=image"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                items = data.get("collection", {}).get("items", [])
                for item in items[:25]:
                    href = item.get("href")
                    if not href:
                        continue
                    m_req = urllib.request.Request(href, headers={"User-Agent": "Mozilla/5.0"})
                    try:
                        with urllib.request.urlopen(m_req, timeout=15) as m_resp:
                            assets = json.loads(m_resp.read().decode())
                            candidates = [a for a in assets if not a.endswith(".tif") and not a.endswith(".tiff") and a.lower().endswith(".jpg")]
                            chosen = None
                            for pref in ["~large.jpg", "~orig.jpg", "~medium.jpg"]:
                                for c in candidates:
                                    if pref in c:
                                        chosen = c
                                        break
                                if chosen:
                                    break
                            if not chosen and candidates:
                                chosen = candidates[0]
                            if chosen and chosen not in used_urls:
                                used_urls.add(chosen)
                                return chosen
                    except Exception:
                        continue
        except Exception as e:
            log(f"⚠️ Erro ao buscar imagem NASA ({q}): {e}")
    return None

def download_and_crop(url, out_path, target_width=1920, target_height=1080):
    last_err = None
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                img_bytes = resp.read()
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
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
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            img.save(out_path, format="JPEG", quality=95)
            return True
        except Exception as e:
            last_err = e
            if attempt < 3:
                time.sleep(2 * attempt)
    raise RuntimeError(f"Falha após 3 tentativas ao baixar {url}: {last_err}")

def _load_font(size):
    for font_name in ["impact.ttf", "arialbd.ttf", "segoeuib.ttf", "calibrib.ttf"]:
        for folder in [r"C:\Windows\Fonts", ""]:
            fp = os.path.join(folder, font_name) if folder else font_name
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()

def render_thumbnail_overlay(img_path, target_project):
    """Estiliza a thumbnail com contraste cinematográfico e título 3D neon de alto impacto."""
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size

    # Aumenta saturação e contraste da imagem base
    rgb = img.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.25)
    rgb = ImageEnhance.Color(rgb).enhance(1.35)
    img = rgb.convert("RGBA")

    # Vinheta escura + gradiente dramático para leitura perfeita do título
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for y in range(h):
        top_factor = max(0.0, (0.45 - (y / h)) / 0.45) * 0.72
        bot_factor = max(0.0, ((y / h) - 0.35) / 0.65) * 0.85
        alpha = int(min(255, max(top_factor, bot_factor) * 255))
        odraw.line([(0, y), (w, y)], fill=(4, 6, 18, alpha))
    img = Image.alpha_composite(img, overlay)

    thumb_meta = target_project.get("thumbnail_text")
    if not thumb_meta:
        hook_headline = target_project.get("scenes", [{}])[0].get("headline", target_project.get("title", "").upper())
        words = hook_headline.split()
        mid = max(1, len(words) // 2)
        thumb_meta = {
            "line1": " ".join(words[:mid]),
            "line2": " ".join(words[mid:]) + "?",
            "subtitle": "O MISTÉRIO DO COSMOS | SCAPATICI TECNOLOGIA"
        }

    line1 = thumb_meta.get("line1", "").upper()
    line2 = thumb_meta.get("line2", "").upper()
    subtitle = thumb_meta.get("subtitle", "SCAPATICI TECNOLOGIA").upper()

    font_main = _load_font(132)
    font_sub = _load_font(48)

    text_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(text_layer)
    gdraw = ImageDraw.Draw(glow_layer)

    def draw_centered_3d(y_pos, text, font, fill_color, glow_color, stroke_width=8):
        if not text:
            return
        bbox = tdraw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        # Reduz a fonte automaticamente se ultrapassar a largura segura
        cur_font = font
        cur_size = getattr(font, "size", 120)
        while tw > w - 140 and cur_size > 56:
            cur_size -= 8
            cur_font = _load_font(cur_size)
            bbox = tdraw.textbbox((0, 0), text, font=cur_font)
            tw = bbox[2] - bbox[0]
        x_pos = (w - tw) // 2
        # Glow externo
        for dx in (-6, 0, 6):
            for dy in (-6, 0, 6):
                gdraw.text((x_pos + dx, y_pos + dy), text, font=cur_font, fill=glow_color)
        # Sombra 3D profunda
        for depth in range(12, 0, -2):
            tdraw.text((x_pos + depth, y_pos + depth), text, font=cur_font, fill=(0, 0, 0, 230))
        # Texto principal com contorno escuro
        tdraw.text((x_pos, y_pos), text, font=cur_font, fill=fill_color, stroke_width=stroke_width, stroke_fill=(5, 10, 25, 255))

    draw_centered_3d(130, line1, font_main, (0, 242, 254, 255), (0, 180, 255, 160))
    draw_centered_3d(290, line2, font_main, (255, 210, 0, 255), (255, 140, 0, 160))
    draw_centered_3d(475, subtitle, font_sub, (255, 255, 255, 255), (0, 242, 254, 110), stroke_width=4)

    glow_blurred = glow_layer.filter(ImageFilter.GaussianBlur(radius=18))
    out = Image.alpha_composite(img, glow_blurred)
    out = Image.alpha_composite(out, text_layer)
    out.convert("RGB").save(img_path, format="JPEG", quality=95)

# Catálogo editorial sequencial de temas em alta para os próximos dias
CATALOGUE = [
    {
        "id": "video-009-bootes-void",
        "title": "O Vazio de Boötes: A Região do Espaço Onde 2.000 Galáxias Simplesmente Desapareceram",
        "topic": "Vazio de Boötes, Anomalias Cosmológicas, Civilizações Tipo III e Esferas de Dyson Galácticas",
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 330,
        "fps": 30,
        "vinheta_duration_frames": 90,
        "bg_music_volume": 0.12,
        "seo": {
            "title_options": [
                "O Vazio de Boötes: A Região do Espaço Onde 2.000 Galáxias Simplesmente Desapareceram",
                "O Que Está Escondido no Grande Nada do Universo? O Mistério do Vazio de Boötes",
                "Uma Civilização Cobriu 2.000 Galáxias? A Física Sombria do Vazio de Boötes"
            ],
            "description": "Imagine viajar trezentos e trinta milhões de anos-luz pelo cosmos e não encontrar absolutamente nada. Nem estrelas, nem planetas, nem luz. Em 1981, astrônomos descobriram uma das anomalias mais aterrorizantes da cosmologia moderna: o Vazio de Boötes, conhecido como o Grande Nada.\n\nNeste nono episódio do canal Scapatici Tecnologia, investigamos por que uma região do cosmos que deveria abrigar mais de duas mil galáxias contém apenas sessenta. Seria o resultado de uma colossal guerra cósmica, um império interestelar de Escala Kardashev Tipo III cobrindo estrelas com Esferas de Dyson, ou uma falha bizarra na evolução do tecido do espaço-tempo?\n\n🔔 Inscreva-se no canal Scapatici Tecnologia para desvendar os maiores enigmas do cosmos e da ciência de ponta.\n\n#ScapaticiTecnologia #VazioDeBootes #Astrofisica #Cosmos #MisteriosDoUniverso #Galaxias #Ciencia",
            "tags": ["scapatici tecnologia", "vazio de bootes", "bootes void", "astrofisica", "universo", "galaxias", "esfera de dyson", "kardashev", "misterios do universo"]
        },
        "scenes": [
            {
                "id": "scene_1_hook",
                "type": "hook",
                "visual_theme": "deep_space_cosmic_void_abyss",
                "headline": "O GRANDE NADA DO UNIVERSO OBSERVÁVEL",
                "narration": "Se você fosse colocado no centro exato da região mais aterrorizante do universo observável, você olharia para todas as direções da escuridão e não veria nem uma única estrela. O céu noturno seria um vácuo negro, absoluto e sufocante. Você estaria no Vazio de Boötes, uma anomalia astronômica com trezentos e trinta milhões de anos-luz de diâmetro. Para colocar em perspectiva, uma região desse tamanho deveria conter pelo menos duas mil galáxias repletas de trilhões de sistemas solares. Mas os telescópios encontram apenas sessenta galáxias espalhadas como fantasmas solitários. Para onde foi toda a matéria que deveria estar ali? E por que alguns dos maiores astrofísicos do mundo cogitam que esse vazio não é um acidente natural... Mas a assinatura de uma civilização cósmica hiperavançada?",
                "highlight_words": ["330 MILHÕES DE ANOS-LUZ", "VAZIO DE BOÖTES", "DUAS MIL GALÁXIAS", "ESCURIDÃO TOTAL"],
                "stats": {"label": "Diâmetro do Vazio", "value": "330 Milhões Anos-Luz"},
                "backgroundImage": "assets/video-009-bootes-void/scene_1.jpg",
                "panDirection": "zoom-in"
            },
            {
                "id": "scene_2_discovery_1981",
                "type": "investigation",
                "visual_theme": "astronomers_discovering_void_telescope_data",
                "headline": "A DESCOBERTA QUE CHATOU A ASTRONOMIA",
                "narration": "Em 1981, o astrônomo Robert Kirshner e sua equipe realizavam um mapeamento sistemático dos desvios para o vermelho das galáxias para entender a teia cósmica em grande escala. Eles esperavam encontrar galáxias distribuídas em filamentos uniformes puxados pela gravidade. Em vez disso, seus dados revelaram uma gigantesca esfera de vácuo quase perfeito, tão desproporcional que desafiava os modelos consagrados de formação cósmica após o Big Bang. Não havia tempo suficiente na idade do universo para que a gravidade tivesse esvaziado uma bolha tão colossal de matéria.",
                "highlight_words": ["1981", "ROBERT KIRSHNER", "DESVIO PARA O VERMELHO", "TEIA CÓSMICA"],
                "stats": {"label": "Galáxias Esperadas", "value": "+2.000 Galáxias"},
                "backgroundImage": "assets/video-009-bootes-void/scene_2.jpg",
                "panDirection": "pan-right"
            },
            {
                "id": "scene_3_greg_egan_quote",
                "type": "investigation",
                "visual_theme": "lonely_galaxy_in_dark_void",
                "headline": "A SOLIDÃO DA GALÁXIA ISOLADA",
                "narration": "O escritor e cientista Greg Egan resumiu a poesia assustadora desse lugar em uma frase célebre: se a nossa Terra estivesse localizada no centro do Vazio de Boötes, nós nunca teríamos sabido que outras galáxias existiam no cosmos até a invenção dos telescópios mais potentes na década de 1960. A humanidade teria crescido acreditando que estava completamente só no universo. O silêncio cósmico não seria uma questão de falta de comunicação... Seria uma barreira física de milhões de anos-luz de escuridão impenetrável.",
                "highlight_words": ["GREG EGAN", "SOLIDÃO TOTAL", "DÉCADA DE 1960", "ESCURIDÃO IMPENETRÁVEL"],
                "stats": {"label": "Galáxias Reais", "value": "Apenas 60 no Vazio"},
                "backgroundImage": "assets/video-009-bootes-void/scene_3.jpg",
                "panDirection": "pan-left"
            },
            {
                "id": "scene_4_coalescence_theory",
                "type": "investigation",
                "visual_theme": "merging_cosmic_bubbles_simulation",
                "headline": "A TEORIA DA FUSÃO DE BOLHAS DE VÁCUO",
                "narration": "A explicação da física convencional é que o Vazio de Boötes não nasceu como uma única estrutura gigante. Ele seria o resultado da fusão catastrófica de várias bolhas menores de vácuo primordial, como bolhas de sabão que colidem e formam uma cavidade cavernosa na teia de matéria escura. Contudo, simulações em supercomputadores mostram que, mesmo com essa fusão, a gravidade deveria ter deixado pequenos aglomerados residuais no centro. Mas o centro de Boötes permanece assustadoramente limpo e desolado.",
                "highlight_words": ["FUSÃO DE BOLHAS", "BOLHAS PRIMORDIAIS", "MATÉRIA ESCURA", "CENTRO DESOLADO"],
                "stats": {"label": "Densidade", "value": "1% do Cosmos Normal"},
                "backgroundImage": "assets/video-009-bootes-void/scene_4.jpg",
                "panDirection": "floating-drift"
            },
            {
                "id": "scene_5_kardashev_theory",
                "type": "climax",
                "visual_theme": "dyson_swarms_galactic_scale_kardashev_3",
                "headline": "A HIPÓTESE DA CIVILIZAÇÃO TIPO TRÊS",
                "narration": "É aqui que a astrofísica teórica encontra a teoria dos jogos e a Escala de Kardashev. E se as duas mil galáxias que faltam em Boötes não desapareceram, mas foram artificialmente encobertas? Uma civilização cósmica de Nível Três, capaz de manipular a energia de galáxias inteiras, teria a necessidade de envelopar estrelas em Enxames de Dyson para capturar cada fóton de energia. Conforme essa civilização se expandiu em escala exponencial ao longo de bilhões de anos, galáxia após galáxia foi apagada da luz visível, emitindo apenas uma radiação residual infravermelha que nossos instrumentos ainda têm dificuldade de decifrar.",
                "highlight_words": ["ESCALA KARDASHEV", "ENXAMES DE DYSON", "CIVILIZAÇÃO TIPO 3", "LUZ APAGADA"],
                "stats": {"label": "Classificação", "value": "Império Kardashev III"},
                "backgroundImage": "assets/video-009-bootes-void/scene_5.jpg",
                "panDirection": "hyper-zoom"
            },
            {
                "id": "scene_6_radio_anomalies",
                "type": "technology",
                "visual_theme": "radio_telescope_scanning_void_signals",
                "headline": "OS TUBOS DE DADOS E O ALINHAMENTO DAS 60 GALÁXIAS",
                "narration": "Quando os astrônomos examinaram com detalhe as sessenta raras galáxias que sobrevivem dentro do vazio, descobriram uma coincidência bizarra. Elas não estão espalhadas aleatoriamente: quase todas estão enfileiradas em uma linha perfeitamente reta, como um tubo luminoso cruzando o abismo. Além disso, essas galáxias possuem taxas de nascimento de estrelas anormalmente altas e emissões de rádio que sugerem jatos cósmicos altamente energéticos. Elas parecem pontes sobreviventes em um mar de escuridão.",
                "highlight_words": ["TUBO LUMINOSO", "LINHA RETA", "SESSENTA GALÁXIAS", "JATOS ENERGÉTICOS"],
                "stats": {"label": "Padrão Visual", "value": "Tubo Alinhado Perfeito"},
                "backgroundImage": "assets/video-009-bootes-void/scene_6.jpg",
                "panDirection": "tilt-down"
            },
            {
                "id": "scene_7_cosmic_warning",
                "type": "climax",
                "visual_theme": "dying_stars_silence_galactic_veil",
                "headline": "O AVISO DO ABISMO PARA O FUTURO DA FÍSICA",
                "narration": "O Vazio de Boötes nos lembra que o universo é muito mais misterioso e implacável do que nossas equações supunham. Seja o resultado de dinâmicas gravitacionais desconhecidas que exigem uma revisão da teoria da relatividade geral de Einstein, ou o rastro de uma megaengenharia cósmica inconcebível, ele prova que a nossa Via Láctea é apenas uma fagulha microscópica cercada por abismos insondáveis de silêncio.",
                "highlight_words": ["RELATIVIDADE GERAL", "ALÉM DE EINSTEIN", "MEGAENGENHARIA", "ABISMO SILENCIOSO"],
                "stats": {"label": "Veredito da Ciência", "value": "Enigma Inexplicado"},
                "backgroundImage": "assets/video-009-bootes-void/scene_7.jpg",
                "panDirection": "dramatic-pulse"
            },
            {
                "id": "scene_8_scapatici_cta",
                "type": "cta",
                "visual_theme": "scapatici_space_observatory_community",
                "headline": "O QUE EXISTE NO MEIO DO NADA?",
                "narration": "E você, o que acha desse mistério cósmico? Acredita que o Vazio de Boötes é um fenômeno puramente natural ou você acha que civilizações cósmicas podem realmente ter manipulado aquela região do espaço? Deixe sua teoria nos comentários, compartilhe este vídeo com quem ama astrofísica e mistérios do universo, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!",
                "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SUA TEORIA", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
                "stats": {"label": "Comunidade Oficial", "value": "Scapatici Tecnologia"},
                "backgroundImage": "assets/video-009-bootes-void/scene_8.jpg",
                "panDirection": "zoom-out"
            }
        ],
        "image_queries": {
            "scene_1.jpg": "deep space darkness cosmic void stars",
            "scene_2.jpg": "hubble deep field distant galaxies",
            "scene_3.jpg": "single spiral galaxy isolated in darkness",
            "scene_4.jpg": "dark matter cosmic web simulation hubble",
            "scene_5.jpg": "dyson sphere megastructure space concept",
            "scene_6.jpg": "chandra x ray galaxy jet radio emission",
            "scene_7.jpg": "supermassive black hole gravitational lens void",
            "scene_8.jpg": "astronaut looking into deep starry cosmos",
            "thumbnail.jpg": "deep cosmic void black hole galaxy space"
        }
    },
    {
        "id": "video-010-great-attractor",
        "title": "O Grande Atrator: A Força Invisível Que Está Arrastando a Via Láctea a 2 Milhões de Km/h",
        "topic": "O Grande Atrator, Zona de Evitação, Superaglomerado Laniakea e Anomalias Gravitacionais",
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 330,
        "fps": 30,
        "vinheta_duration_frames": 90,
        "bg_music_volume": 0.12,
        "seo": {
            "title_options": [
                "O Grande Atrator: A Força Invisível Que Está Arrastando a Via Láctea a 2 Milhões de Km/h",
                "O Que Está Sugando 100.000 Galáxias Para o Mesmo Ponto do Espaço?",
                "Por Que Não Conseguimos Ver o Monstro Gravitacional Que Puxa a Nossa Galáxia?"
            ],
            "description": "Neste exato segundo, a Terra, o Sol e toda a Via Láctea estão sendo arremessados pelo espaço a mais de dois milhões de quilômetros por hora em direção a um ponto específico e misterioso do universo. E não estamos indo sozinhos: outras cem mil galáxias estão sendo sugadas para o mesmo abismo gravitacional.\n\nNeste décimo episódio especial do canal Scapatici Tecnologia, investigamos o Grande Atrator, uma anomalia colossal equivalente a quadrilhões de sóis que se esconde exatamente atrás da Zona de Evitação da nossa própria galáxia. O que os telescópios de raios X finalmente descobriram do outro lado da poeira estelar? E o que é o Superaglomerado de Shapley?\n\n🔔 Inscreva-se no canal Scapatici Tecnologia para desvendar os maiores enigmas do cosmos e da ciência de ponta.\n\n#ScapaticiTecnologia #GrandeAtrator #ViaLactea #Astrofisica #Cosmos #Laniakea #MisteriosDoUniverso #Ciencia",
            "tags": ["scapatici tecnologia", "grande atrator", "great attractor", "via lactea", "laniakea", "zona de evitacao", "astrofisica", "universo", "galaxias", "misterios do universo"]
        },
        "scenes": [
            {
                "id": "scene_1_hook",
                "type": "hook",
                "visual_theme": "milky_way_pulled_into_gravitational_anomaly",
                "headline": "A QUEDA LIVRE DE CEM MIL GALÁXIAS",
                "narration": "Neste exato segundo, enquanto você assiste a este vídeo, o planeta Terra, o Sol e todas as quatrocentas bilhões de estrelas da Via Láctea estão despencando pelo espaço a uma velocidade alucinante de dois vírgula dois milhões de quilômetros por hora. Mas o detalhe mais perturbador não é a velocidade. É o destino. A nossa galáxia, junto com outras cem mil galáxias vizinhas, está sendo sugada em direção a um único ponto invisível do universo, contra a própria expansão do espaço-tempo. Os astrofísicos batizaram essa anomalia de O Grande Atrator: uma entidade gravitacional com a massa de dezenas de quadrilhões de sóis. E o pior de tudo? Ele está escondido no único ponto cego do céu onde os nossos telescópios ópticos são incapazes de enxergar.",
                "highlight_words": ["2,2 MILHÕES DE KM/H", "CEM MIL GALÁXIAS", "O GRANDE ATRATOR", "PONTO CEGO"],
                "stats": {"label": "Velocidade de Queda", "value": "2,2 Milhões km/h"},
                "backgroundImage": "assets/video-010-great-attractor/scene_1.jpg",
                "panDirection": "zoom-in"
            },
            {
                "id": "scene_2_cosmic_flow_anomaly",
                "type": "investigation",
                "visual_theme": "cosmic_microwave_background_dipole_map",
                "headline": "A ANOMALIA NA EXPANSÃO DO UNIVERSO",
                "narration": "Desde que Edwin Hubble descobriu que o universo está se expandindo, a regra parecia simples: todas as galáxias deveriam se afastar umas das outras em um ritmo previsível. Mas nas décadas de 1970 e 1980, um grupo de astrônomos conhecido como Os Sete Samurais notou um erro grave nas equações. Ao medir o fundo cósmico de micro-ondas, eles descobriram que todo o nosso setor do cosmos estava sofrendo um desvio gravitacional violento em direção às constelações de Hidra e Centauro. Algo descomunal estava vencendo a expansão inicial do Big Bang na nossa vizinhança cósmica.",
                "highlight_words": ["OS SETE SAMURAIS", "DESVIO GRAVITACIONAL", "HIDRA E CENTAURO", "EXPANSÃO CÓSMICA"],
                "stats": {"label": "Distância Estimada", "value": "220 Milhões Anos-Luz"},
                "backgroundImage": "assets/video-010-great-attractor/scene_2.jpg",
                "panDirection": "pan-right"
            },
            {
                "id": "scene_3_zone_of_avoidance",
                "type": "investigation",
                "visual_theme": "milky_way_dust_band_blocking_view",
                "headline": "ESCONDIDO NA ZONA DE EVITAÇÃO",
                "narration": "Por uma ironia quase cruel da geometria cósmica, o Grande Atrator está localizado exatamente atrás do plano galáctico da própria Via Láctea. Essa região é chamada pelos astrônomos de Zona de Evitação: uma muralha impenetrável de poeira interestelar, gás denso e bilhões de estrelas brilhantes do centro da nossa galáxia que bloqueiam noventa e nove por cento da luz visível que vem lá de trás. Durante décadas, sabíamos que havia um colosso gravitacional nos puxando, mas tentar observá-lo com telescópios comuns era como tentar enxergar através de uma parede de chumbo iluminada por holofotes.",
                "highlight_words": ["ZONA DE EVITAÇÃO", "PONTO CEGO", "POEIRA INTERESTELAR", "PAREDE DE CHUMBO"],
                "stats": {"label": "Luz Visível Bloqueada", "value": "99% de Obstrução"},
                "backgroundImage": "assets/video-010-great-attractor/scene_3.jpg",
                "panDirection": "pan-left"
            },
            {
                "id": "scene_4_xray_revelation",
                "type": "technology",
                "visual_theme": "xray_and_radio_telescopes_penetrating_dust",
                "headline": "O OLHAR DE RAIOS X ATRAVÉS DA ESCURIDÃO",
                "narration": "A barreira só começou a cair quando a humanidade apontou radiotelescópios como o Parkes e observatórios espaciais de raios X diretamente para a Zona de Evitação. As ondas de rádio e os fótons de raios X de alta energia atravessam a poeira da Via Láctea como se ela fosse vidro transparente. O que apareceu nos sensores deixou os cientistas perplexos: no coração do Grande Atrator estava o Aglomerado do Esquadro, um cemitério titânico onde milhares de galáxias antigas estão colidindo e se fundindo em um mar de gás superaquecido a milhões de graus.",
                "highlight_words": ["RAIOS X", "AGLOMERADO DO ESQUADRO", "COLISÃO DE GALÁXIAS", "GÁS SUPERAQUECIDO"],
                "stats": {"label": "Massa Equivalente", "value": "10 Quadrilhões de Sóis"},
                "backgroundImage": "assets/video-010-great-attractor/scene_4.jpg",
                "panDirection": "hyper-zoom"
            },
            {
                "id": "scene_5_laniakea_discovery",
                "type": "climax",
                "visual_theme": "laniakea_supercluster_filaments_simulation",
                "headline": "LANIAKEA: O CÉU IMENSURÁVEL",
                "narration": "Em 2014, a astrofísica Brent Tully e sua equipe na Universidade do Havaí usaram supercomputadores para mapear os rios gravitacionais de mais de oito mil galáxias. O mapa resultante revelou uma estrutura de tirar o fôlego batizada de Laniakea, que significa Céu Imensurável. Descobrimos que a Via Láctea é apenas um ponto luminoso na periferia de uma bacia hidrográfica cósmica com quinhentos milhões de anos-luz de extensão, onde todas as correntes de matéria escura e galáxias deságuam diretamente no vale central do Grande Atrator.",
                "highlight_words": ["LANIAKEA", "CÉU IMENSURÁVEL", "500 MILHÕES DE ANOS-LUZ", "RIOS GRAVITACIONAIS"],
                "stats": {"label": "Superaglomerado", "value": "Laniakea (100.000 Galáxias)"},
                "backgroundImage": "assets/video-010-great-attractor/scene_5.jpg",
                "panDirection": "floating-drift"
            },
            {
                "id": "scene_6_shapley_twist",
                "type": "climax",
                "visual_theme": "shapley_supercluster_massive_gravity_well",
                "headline": "A REVIRAVOLTA: O MONSTRO ATRÁS DO MONSTRO",
                "narration": "Mas a maior reviravolta da cosmologia moderna veio logo depois. Quando os físicos somaram toda a massa do Aglomerado do Esquadro e do Grande Atrator, a conta ainda não fechava. A gravidade ali não era suficiente para explicar a velocidade absurda da nossa queda. Ao olhar ainda mais fundo, a seiscentos e cinquenta milhões de anos-luz de distância, eles encontraram o verdadeiro titã: o Superaglomerado de Shapley, a maior concentração de massa do universo próximo, que está puxando não apenas a Via Láctea, mas o próprio Grande Atrator inteiro em sua direção.",
                "highlight_words": ["SUPERAGLOMERADO DE SHAPLEY", "CONTA NÃO FECHAVA", "650 MILHÕES DE ANOS-LUZ", "VERDADEIRO TITÃ"],
                "stats": {"label": "Atrator Supremo", "value": "Superaglomerado Shapley"},
                "backgroundImage": "assets/video-010-great-attractor/scene_6.jpg",
                "panDirection": "dramatic-pulse"
            },
            {
                "id": "scene_7_dark_energy_fate",
                "type": "investigation",
                "visual_theme": "dark_energy_tearing_cosmic_web_apart",
                "headline": "A GUERRA ENTRE GRAVIDADE E ENERGIA ESCURA",
                "narration": "A pergunta inevitável é: a Via Láctea vai ser esmagada nessa fornalha intergaláctica? A resposta envolve a força mais misteriosa da física: a Energia Escura. Embora estejamos caindo em direção ao Grande Atrator e a Shapley a milhões de quilômetros por hora, a Energia Escura está acelerando a expansão do espaço entre os superaglomerados. Em alguns bilhões de anos, a expansão cósmica vencerá esse cabo de guerra, rasgando as pontes de Laniakea antes que possamos atingir o centro do abismo.",
                "highlight_words": ["ENERGIA ESCURA", "CABO DE GUERRA", "EXPANSÃO ACELERADA", "DESTINO CÓSMICO"],
                "stats": {"label": "Vencedor Final", "value": "Expansão da Energia Escura"},
                "backgroundImage": "assets/video-010-great-attractor/scene_7.jpg",
                "panDirection": "tilt-down"
            },
            {
                "id": "scene_8_scapatici_cta",
                "type": "cta",
                "visual_theme": "scapatici_space_observatory_community",
                "headline": "NAVEGANDO NO OCEANO GRAVITACIONAL",
                "narration": "E você, já tinha parado para pensar que nunca estivemos parados no espaço e que estamos surfando uma onda gravitacional de proporções inimagináveis? Deixe sua opinião aqui nos comentários, compartilhe este vídeo com quem é fascinado pelos mistérios do universo, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!",
                "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SEU COMENTÁRIO", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
                "stats": {"label": "Comunidade Oficial", "value": "Scapatici Tecnologia"},
                "backgroundImage": "assets/video-010-great-attractor/scene_8.jpg",
                "panDirection": "zoom-out"
            }
        ],
        "image_queries": {
            "scene_1.jpg": "galaxy cluster gravitational lensing hubble",
            "scene_2.jpg": "cosmic microwave background planck map",
            "scene_3.jpg": "milky way galactic center dust infrared spitzer",
            "scene_4.jpg": "chandra x ray galaxy cluster collision",
            "scene_5.jpg": "cosmic web dark matter filaments simulation",
            "scene_6.jpg": "massive galaxy cluster abell hubble",
            "scene_7.jpg": "deep space dark energy expansion galaxies",
            "scene_8.jpg": "james webb space telescope deep field galaxies",
            "thumbnail.jpg": "galaxy cluster collision gravitational anomaly space"
        }
    },
    {
        "id": "video-011-jwst-impossible-galaxies",
        "title": "As Galáxias Impossíveis do James Webb: O Descoberta Que Quebrou o Modelo do Big Bang",
        "topic": "Telescópio Espacial James Webb, Galáxias Primordiais Massivas, Cosmologia e Crise no Modelo Padrão",
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 330,
        "fps": 30,
        "vinheta_duration_frames": 90,
        "bg_music_volume": 0.12,
        "seo": {
            "title_options": [
                "As Galáxias Impossíveis do James Webb: A Descoberta Que Quebrou o Modelo do Big Bang",
                "O James Webb Enxergou Galáxias Antigas Demais Para Existirem? O Mistério dos Pontos Vermelhos",
                "O Universo É Duas Vezes Mais Velho do Que Pensávamos? O Enigma do Telescópio James Webb"
            ],
            "description": "Quando o Telescópio Espacial James Webb apontou seus espelhos banhados a ouro para o início do tempo, os cientistas esperavam ver apenas pequenos fragmentos de estrelas recém-nascidas. Em vez disso, encontraram seis colossos galácticos maduros que simplesmente não deveriam existir tão cedo após o Big Bang.\n\nNeste episódio do canal Scapatici Tecnologia, exploramos os chamados 'Quebradores de Universo': galáxias e buracos negros supermassivos primordiais que estão forçando a astrofísica a repensar a história do cosmos.\n\n🔔 Inscreva-se no canal Scapatici Tecnologia para desvendar os maiores enigmas do cosmos e da ciência de ponta.\n\n#ScapaticiTecnologia #JamesWebb #BigBang #GalaxiasImpossiveis #Astrofisica #Cosmos #Ciencia",
            "tags": ["scapatici tecnologia", "james webb", "jwst", "galaxias impossiveis", "big bang", "astrofisica", "universo", "buracos negros", "misterios do universo"]
        },
        "scenes": [
            {
                "id": "scene_1_hook",
                "type": "hook",
                "visual_theme": "jwst_deep_field_red_dots_anomaly",
                "headline": "OS SEIS PONTOS QUE CHOCARAM A FÍSICA",
                "narration": "Quando o Telescópio Espacial James Webb enviou suas primeiras imagens do abismo mais profundo do espaço-tempo, os astrofísicos encontraram seis pequenos pontos vermelhos brilhando na escuridão primordial. À primeira vista, pareciam apenas ruído nos sensores infravermelhos. Mas quando os supercomputadores calcularam a distância e a massa daqueles objetos, o pânico silencioso tomou conta dos observatórios. Aqueles pontos eram galáxias colossais, tão maduras e repletas de estrelas quanto a nossa Via Láctea, existindo apenas quinhentos milhões de anos após o Big Bang. Segundo todas as leis da cosmologia moderna, não havia tempo nem matéria suficiente para elas existirem. Os próprios cientistas deram a elas um apelido oficial: As Quebradoras de Universo.",
                "highlight_words": ["QUEBRADORAS DE UNIVERSO", "JAMES WEBB", "500 MILHÕES DE ANOS", "PONTOS VERMELHOS"],
                "stats": {"label": "Era Cósmica", "value": "3% da Idade do Universo"},
                "backgroundImage": "assets/video-011-jwst-impossible-galaxies/scene_1.jpg",
                "panDirection": "zoom-in"
            },
            {
                "id": "scene_2_time_machine_infrared",
                "type": "technology",
                "visual_theme": "james_webb_gold_mirror_infrared_spectrum",
                "headline": "A MÁQUINA DO TEMPO DE OURO E INFRAVERMELHO",
                "narration": "Para entender por que o Telescópio Hubble nunca viu esses monstros, precisamos entender como o espaço estica a própria luz. Conforme a luz das primeiras estrelas viaja por mais de treze bilhões de anos até nós, a expansão do universo estica suas ondas, transformando o brilho ultravioleta e visível em radiação infravermelha invisível aos olhos humanos. Com seu espelho hexagonal de seis metros e meio revestido de ouro puro e refrigerado perto do zero absoluto, o James Webb foi projetado especificamente para enxergar através desse véu temporal.",
                "highlight_words": ["TREZE BILHÕES DE ANOS", "LUZ ESTICADA", "ESPELHO DE OURO", "INFRAVERMELHO"],
                "stats": {"label": "Alcance Temporal", "value": "13,5 Bilhões de Anos"},
                "backgroundImage": "assets/video-011-jwst-impossible-galaxies/scene_2.jpg",
                "panDirection": "pan-right"
            },
            {
                "id": "scene_3_standard_model_expectation",
                "type": "investigation",
                "visual_theme": "early_universe_baby_galaxies_simulation",
                "headline": "O QUE DEVERIA ESTAR LÁ NO INÍCIO?",
                "narration": "O Modelo Padrão da Cosmologia, conhecido como Lambda-CDM, previa que a infância do universo fosse lenta e caótica. Após o Big Bang, nuvens de gás hidrogênio deveriam levar bilhões de anos se aglutinando lentamente dentro de halos de matéria escura para formar pequenas galáxias anãs irregulares. Encontrar uma galáxia com cem bilhões de estrelas já pronta na aurora cósmica é o equivalente biológico a entrar em uma maternidade e encontrar um recém-nascido de dois dias de vida com a altura e o peso de um adulto de trinta anos.",
                "highlight_words": ["MODELO PADRÃO", "MATÉRIA ESCURA", "CEM BILHÕES DE ESTRELAS", "PARADOXO TEMPORAL"],
                "stats": {"label": "Massa Estelar", "value": "+100 Bilhões de Sóis"},
                "backgroundImage": "assets/video-011-jwst-impossible-galaxies/scene_3.jpg",
                "panDirection": "pan-left"
            },
            {
                "id": "scene_4_impossible_efficiency",
                "type": "climax",
                "visual_theme": "hyper_efficient_star_formation_furnace",
                "headline": "A FÁBRICA DE ESTRELAS 100% EFICIENTE",
                "narration": "Quando o astrofísico Ivo Labbé e sua equipe publicaram os dados na revista Nature, o cálculo mais assustador veio à tona: para aquelas galáxias terem crescido tão rápido no tempo disponível desde o Big Bang, elas precisariam ter convertido quase cem por cento de todo o gás disponível no universo primordial diretamente em estrelas, instantaneamente. Na física conhecida, nenhuma galáxia consegue converter mais do que dez a vinte por cento do seu gás, porque a própria explosão das primeiras supernovas sopra o restante do gás para longe.",
                "highlight_words": ["IVO LABBÉ", "REVISTA NATURE", "100% DE EFICIÊNCIA", "FÍSICA IMPOSSÍVEL"],
                "stats": {"label": "Taxa de Conversão", "value": "Acima do Limite Físico"},
                "backgroundImage": "assets/video-011-jwst-impossible-galaxies/scene_4.jpg",
                "panDirection": "hyper-zoom"
            },
            {
                "id": "scene_5_primordial_black_holes",
                "type": "investigation",
                "visual_theme": "supermassive_black_hole_quasar_early_cosmos",
                "headline": "OS BURACOS NEGROS QUE NASCERAM GIGANTES",
                "narration": "O mistério ficou ainda mais denso quando o espectrógrafo do James Webb analisou o interior desses pequenos pontos vermelhos. Alguns deles não eram apenas aglomerados de estrelas, mas abrigavam buracos negros supermassivos engolindo matéria em um ritmo frenético. O problema é o mesmo: um buraco negro que nasce da morte de uma estrela comum jamais teria tempo de crescer até atingir bilhões de massas solares tão cedo. Isso reacendeu uma teoria fascinante: as sementes de colapso direto, onde nuvens titânicas de gás primordial colapsaram direto em buracos negros gigantes sem nunca terem sido estrelas.",
                "highlight_words": ["COLAPSO DIRETO", "BURACOS NEGROS PRIMORDIAIS", "SEMENTES CÓSMICAS", "QUASARES"],
                "stats": {"label": "Anomalia Central", "value": "Buracos Negros Gigantes"},
                "backgroundImage": "assets/video-011-jwst-impossible-galaxies/scene_5.jpg",
                "panDirection": "dramatic-pulse"
            },
            {
                "id": "scene_6_alternative_cosmology",
                "type": "investigation",
                "visual_theme": "cosmic_timeline_expansion_equations",
                "headline": "O BIG BANG ESTÁ ERRADO OU INCOMPLETO?",
                "narration": "Essas descobertas geraram manchetes no mundo inteiro afirmando que o Big Bang havia sido refutado. Alguns físicos teóricos chegaram a propor modelos radicais que dobrariam a idade do universo para vinte e seis vírgula sete bilhões de anos. Porém, a maioria dos cosmólogos alerta que o Big Bang continua sustentado por provas sólidas, como a radiação cósmica de fundo. O que o James Webb realmente quebrou foi a nossa compreensão sobre como as primeiras estruturas se formaram e como a energia escura primordial atuou nos primeiros milhões de anos.",
                "highlight_words": ["26,7 BILHÕES DE ANOS", "ENERGIA ESCURA PRIMORDIAL", "NOVA FÍSICA", "AURORA CÓSMICA"],
                "stats": {"label": "Impacto Científico", "value": "Revisão da Formação Galáctica"},
                "backgroundImage": "assets/video-011-jwst-impossible-galaxies/scene_6.jpg",
                "panDirection": "floating-drift"
            },
            {
                "id": "scene_7_population_iii_stars",
                "type": "climax",
                "visual_theme": "population_iii_hypergiant_first_stars",
                "headline": "A CAÇADA ÀS ESTRELAS DE POPULAÇÃO TRÊS",
                "narration": "A peça final desse quebra-cabeça pode estar nas lendárias estrelas de População Três: os primeiros astros do universo, forjados puramente de hidrogênio e hélio, milhares de vezes mais massivos e brilhantes do que o nosso Sol. Se essas estrelas titânicas dominaram as primeiras galáxias, o brilho delas teria enganado nossos cálculos, fazendo galáxias menores parecerem colossos impossíveis. O James Webb está apenas no início de sua missão, e cada nova imagem nos aproxima do instante zero da criação.",
                "highlight_words": ["POPULAÇÃO TRÊS", "PRIMEIRAS ESTRELAS", "MILHARES DE SÓIS", "INSTANTE ZERO"],
                "stats": {"label": "Próxima Fronteira", "value": "As Primeiras Estrelas"},
                "backgroundImage": "assets/video-011-jwst-impossible-galaxies/scene_7.jpg",
                "panDirection": "tilt-down"
            },
            {
                "id": "scene_8_scapatici_cta",
                "type": "cta",
                "visual_theme": "scapatici_space_observatory_community",
                "headline": "OS SEGREDOS DO INÍCIO DO TEMPO",
                "narration": "E você, o que acha das descobertas do James Webb? Acredita que apenas entendemos errado o nascimento das primeiras estrelas ou que a física está prestes a passar pela maior revolução desde Albert Einstein? Deixe sua teoria aqui nos comentários, compartilhe este vídeo com quem é fascinado pelos mistérios do universo, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!",
                "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SUA TEORIA", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
                "stats": {"label": "Comunidade Oficial", "value": "Scapatici Tecnologia"},
                "backgroundImage": "assets/video-011-jwst-impossible-galaxies/scene_8.jpg",
                "panDirection": "zoom-out"
            }
        ],
        "image_queries": {
            "scene_1.jpg": "james webb space telescope deep field galaxies",
            "scene_2.jpg": "james webb space telescope mirror gold",
            "scene_3.jpg": "hubble ultra deep field distant galaxies",
            "scene_4.jpg": "starburst galaxy intense star formation webb",
            "scene_5.jpg": "supermassive black hole quasar accretion disk",
            "scene_6.jpg": "cosmic web simulation early universe",
            "scene_7.jpg": "first stars early universe nebula webb",
            "scene_8.jpg": "carina nebula cosmic cliffs james webb",
            "thumbnail.jpg": "james webb space telescope deep field galaxy"
        }
    },
    {
        "id": "video-012-tabbys-star-megastructure",
        "title": "A Estrela de Tabby: O Objeto Que Bloqueou 22% da Luz de um Sol a 1.470 Anos-Luz",
        "topic": "Estrela de Tabby (KIC 8462852), Telescópio Kepler, Esfera de Dyson e Anomalias Estelares",
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 330,
        "fps": 30,
        "vinheta_duration_frames": 90,
        "bg_music_volume": 0.12,
        "seo": {
            "title_options": [
                "A Estrela de Tabby: O Objeto Que Bloqueou 22% da Luz de um Sol a 1.470 Anos-Luz",
                "A Estrela Mais Misteriosa da Via Láctea: Megaestrutura Alienígena ou Anomalia Cósmica?",
                "Por Que a Estrela KIC 8462852 Está Escurecendo de Forma Impossível?"
            ],
            "description": "Quando um planeta gigante como Júpiter passa na frente de uma estrela, ele bloqueia apenas 1% da luz dela. Mas em 2015, a astrônoma Tabetha Boyajian descobriu uma estrela a 1.470 anos-luz da Terra cujo brilho despencou absurdos 22% de forma irregular e aperiódica.\n\nNeste episódio do canal Scapatici Tecnologia, investigamos o enigma da Estrela de Tabby (KIC 8462852): por que os dados do Telescópio Espacial Kepler levaram cientistas de Harvard e da Penn State a apontar os maiores radiotelescópios do mundo em busca de uma megaestrutura alienígena?\n\n🔔 Inscreva-se no canal Scapatici Tecnologia para desvendar os maiores enigmas do cosmos e da ciência de ponta.\n\n#ScapaticiTecnologia #EstrelaDeTabby #EsferaDeDyson #Kepler #Astrofisica #Cosmos #Ciencia",
            "tags": ["scapatici tecnologia", "estrela de tabby", "kic 8462852", "esfera de dyson", "megaestrutura alienigena", "kepler", "astrofisica", "universo", "misterios do universo"]
        },
        "scenes": [
            {
                "id": "scene_1_hook",
                "type": "hook",
                "visual_theme": "alien_megastructure_eclipsing_star_kepler",
                "headline": "A SOMBRA IMPOSSÍVEL NA CONSTELAÇÃO DO CISNE",
                "narration": "Quando o maior planeta do nosso Sistema Solar, Júpiter, passa exatamente na frente do Sol visto de longe, ele bloqueia apenas um por cento da luz solar. Essa é a regra básica que o Telescópio Espacial Kepler usou para descobrir milhares de exoplanetas. Mas ao analisar a estrela KIC oitenta e quatro, meia dois, oito cinco dois, a mil quatrocentos e setenta anos-luz da Terra, os cientistas encontraram algo que gelou a espinha da astronomia moderna. Algo colossal passou na frente daquela estrela e bloqueou absurdos vinte e dois por cento da sua luz. Para produzir uma sombra tão monstruosa, o objeto precisaria ser dezenas de vezes maior que um planeta gigante e ter um formato completamente assimétrico. Seria o primeiro registro de um Enxame de Dyson em construção?",
                "highlight_words": ["22% DA LUZ BLOQUEADA", "ESTRELA DE TABBY", "1.470 ANOS-LUZ", "SOMBRA COLOSSAL"],
                "stats": {"label": "Queda de Brilho", "value": "22% (22x Júpiter)"},
                "backgroundImage": "assets/video-012-tabbys-star-megastructure/scene_1.jpg",
                "panDirection": "zoom-in"
            },
            {
                "id": "scene_2_planet_hunters_discovery",
                "type": "investigation",
                "visual_theme": "kepler_light_curve_irregular_dips",
                "headline": "O GRÁFICO QUE OS COMPUTADORES REJEITARAM",
                "narration": "O mais impressionante é que essa anomalia quase passou despercebida. Os algoritmos da NASA estavam programados para buscar quedas de brilho perfeitamente repetitivas, como o tique-taque de um relógio planetário. Foi um grupo de cientistas cidadãos do projeto Planet Hunters, liderado pela astrônoma Tabetha Boyajian da Universidade de Yale, que notou a curva de luz mais bizarra da história. Em vez de um círculo suave, o gráfico mostrava quedas brutais, caóticas e sem nenhum padrão fixo, durando de cinco a oitenta dias seguidos.",
                "highlight_words": ["TABETHA BOYAJIAN", "PLANET HUNTERS", "CURVA CAÓTICA", "OITENTA DIAS"],
                "stats": {"label": "Código Oficial", "value": "KIC 8462852"},
                "backgroundImage": "assets/video-012-tabbys-star-megastructure/scene_2.jpg",
                "panDirection": "pan-right"
            },
            {
                "id": "scene_3_ruling_out_young_star",
                "type": "investigation",
                "visual_theme": "protoplanetary_disk_infrared_check",
                "headline": "POR QUE NÃO É UM PLANETA EM FORMAÇÃO?",
                "narration": "A primeira tentativa de explicação natural foi simples: talvez a Estrela de Tabby fosse uma estrela recém-nascida cercada por discos caóticos de poeira e rochas protoplanetárias. Mas havia uma falha fatal nessa hipótese. A Estrela de Tabby é uma estrela adulta de classe F, mais quente e maior que o nosso Sol. Além disso, qualquer disco de poeira jovem absorveria a luz da estrela e brilharia intensamente no infravermelho. Quando o Telescópio Spitzer verificou a estrela, não havia excesso de calor infravermelho nenhum.",
                "highlight_words": ["ESTRELA CLASSE F", "SEM INFRAVERMELHO", "TELESCÓPIO SPITZER", "HIPÓTESE DESCARTADA"],
                "stats": {"label": "Excesso Infravermelho", "value": "Zero Detectado"},
                "backgroundImage": "assets/video-012-tabbys-star-megastructure/scene_3.jpg",
                "panDirection": "pan-left"
            },
            {
                "id": "scene_4_comet_swarm_paradox",
                "type": "investigation",
                "visual_theme": "exocomet_swarm_disintegrating_orbit",
                "headline": "A TEORIA DOS SEISCENTOS COMETAS GIGANTES",
                "narration": "Desesperados por uma solução natural, os astrofísicos propuseram a hipótese de uma família de exocometas gigantes que teriam se despedaçado perto da estrela, criando uma nuvem de fragmentos. Mas quando os cálculos matemáticos foram feitos, a ideia esbarrou em outro absurdo estatístico: seriam necessários mais de seiscentos cometas de duzentos quilômetros de diâmetro passando em fila indiana bem na nossa linha de visão, sem deixar o rastro gasoso típico que cometas reais deixam.",
                "highlight_words": ["SEISCENTOS COMETAS", "200 KM DE DIÂMETRO", "ABSURDO ESTATÍSTICO", "FILA INDIANA"],
                "stats": {"label": "Probabilidade Casual", "value": "Extremamente Baixa"},
                "backgroundImage": "assets/video-012-tabbys-star-megastructure/scene_4.jpg",
                "panDirection": "floating-drift"
            },
            {
                "id": "scene_5_wright_dyson_hypothesis",
                "type": "climax",
                "visual_theme": "dyson_swarm_solar_collectors_megastructure",
                "headline": "A HIPÓTESE DA MEGAESTRUTURA DE JASON WRIGHT",
                "narration": "Foi então que o astrofísico Jason Wright, da Universidade Estadual da Pensilvânia, publicou o estudo que abalou a comunidade científica. Ele demonstrou que a curva de luz assimétrica da Estrela de Tabby coincidia exatamente com os modelos teóricos de uma civilização Tipo Dois na Escala de Kardashev construindo um Enxame de Dyson: bilhões de painéis coletores solares gigantescos em órbitas escalonadas para drenar a energia da estrela. Pela primeira vez na história, o instituto SETI apontou o Allen Telescope Array diretamente para uma estrela por suspeita de engenharia estelar.",
                "highlight_words": ["JASON WRIGHT", "CIVILIZAÇÃO TIPO 2", "ENXAME DE DYSON", "ENGENHARIA ESTELAR"],
                "stats": {"label": "Escala Kardashev", "value": "Suspeita Tipo II"},
                "backgroundImage": "assets/video-012-tabbys-star-megastructure/scene_5.jpg",
                "panDirection": "hyper-zoom"
            },
            {
                "id": "scene_6_secular_dimming_mystery",
                "type": "climax",
                "visual_theme": "century_long_photographic_plates_harvard",
                "headline": "CEM ANOS APAGANDO EM SILÊNCIO",
                "narration": "Para testar se a estrela sempre foi assim, o astrônomo Bradley Schaefer vasculhou chapas fotográficas de vidro arquivadas na Universidade de Harvard desde o ano de 1890. O que ele descobriu deixou o mistério dez vezes mais assustador: além das quedas bruscas de dias, a Estrela de Tabby perdeu quase vinte por cento do seu brilho total de forma contínua ao longo de um século inteiro. Nenhuma estrela normal daquela categoria apaga vinte por cento em apenas cem anos.",
                "highlight_words": ["DESDE 1890", "ARQUIVOS DE HARVARD", "20% EM UM SÉCULO", "APAGANDO LENTAMENTE"],
                "stats": {"label": "Queda Secular", "value": "-20% em 100 Anos"},
                "backgroundImage": "assets/video-012-tabbys-star-megastructure/scene_6.jpg",
                "panDirection": "dramatic-pulse"
            },
            {
                "id": "scene_7_wavelength_clue",
                "type": "technology",
                "visual_theme": "multi_wavelength_spectrum_analysis_observatory",
                "headline": "A PISTA DAS CORES DA LUZ EM 2017",
                "narration": "Em 2017, quando a estrela começou a escurecer novamente ao vivo, dezenas de telescópios terrestres e espaciais mediram o fenômeno em diferentes cores da luz simultaneamente. Eles descobriram que a luz azul era mais bloqueada do que a luz vermelha. Isso indicava que o objeto não era inteiramente opaco como metal sólido, mas continha partículas microscópicas translúcidas, talvez resultantes de uma lua inteira que foi vaporizada pela estrela. Ainda assim, nenhum modelo físico explica todas as anomalias da Estrela de Tabby ao mesmo tempo.",
                "highlight_words": ["LUZ AZUL E VERMELHA", "LUA VAPORIZADA", "POEIRA TRANSLÚCIDA", "ENIGMA ABERTO"],
                "stats": {"label": "Status Científico", "value": "Anomalia Sem Par"},
                "backgroundImage": "assets/video-012-tabbys-star-megastructure/scene_7.jpg",
                "panDirection": "tilt-down"
            },
            {
                "id": "scene_8_scapatici_cta",
                "type": "cta",
                "visual_theme": "scapatici_space_observatory_community",
                "headline": "FENÔMENO EXÓTICO OU ENGENHARIA CÓSMICA?",
                "narration": "E você, qual é o seu veredito sobre a Estrela de Tabby? Acredita que estamos diante dos destroços de uma lua destruída ou que um Enxame de Dyson a mil quatrocentos e setenta anos-luz não pode ser totalmente descartado? Deixe sua opinião aqui nos comentários, compartilhe este vídeo com quem é fascinado pelos mistérios do universo, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!",
                "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SEU COMENTÁRIO", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
                "stats": {"label": "Comunidade Oficial", "value": "Scapatici Tecnologia"},
                "backgroundImage": "assets/video-012-tabbys-star-megastructure/scene_8.jpg",
                "panDirection": "zoom-out"
            }
        ],
        "image_queries": {
            "scene_1.jpg": "dyson sphere star megastructure concept nasa",
            "scene_2.jpg": "kepler space telescope exoplanet transit",
            "scene_3.jpg": "spitzer infrared protoplanetary disk star",
            "scene_4.jpg": "comet breakup fragments space hubble",
            "scene_5.jpg": "solar flare star corona sdo nasa",
            "scene_6.jpg": "cygnus constellation deep sky stars",
            "scene_7.jpg": "exoplanet atmosphere spectrum james webb",
            "scene_8.jpg": "radio telescope array night sky stars",
            "thumbnail.jpg": "bright star eclipse dark anomaly space"
        }
    },
    {
        "id": "video-013-false-vacuum-decay",
        "title": "Decaimento do Falso Vácuo: O Gatilho Quântico Que Pode Apagar o Universo à Velocidade da Luz",
        "topic": "Decaimento do Falso Vácuo, Campo de Higgs, Tunelamento Quântico e Estabilidade do Cosmos",
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 330,
        "fps": 30,
        "vinheta_duration_frames": 90,
        "bg_music_volume": 0.12,
        "seo": {
            "title_options": [
                "Decaimento do Falso Vácuo: O Gatilho Quântico Que Pode Apagar o Universo à Velocidade da Luz",
                "A Bolha da Morte Quântica: O Erro no Campo de Higgs Que Pode Reescrever as Leis da Física",
                "E Se o Nosso Universo Estiver em um Falso Vácuo? O Cenário Mais Aterrorizante da Física"
            ],
            "description": "E se o espaço vazio ao nosso redor não estiver no seu estado mais estável? Quando os físicos do CERN mediram a massa exata do Bóson de Higgs em 2012, descobriram um número perturbador: o nosso universo pode estar equilibrado em um 'Falso Vácuo'.\n\nNeste episódio do canal Scapatici Tecnologia, exploramos o Decaimento do Falso Vácuo, o fenômeno quântico capaz de gerar uma bolha de vácuo verdadeiro que se expande à velocidade da luz, reescrevendo a química e a física por onde passa sem nenhum aviso prévio.\n\n🔔 Inscreva-se no canal Scapatici Tecnologia para desvendar os maiores enigmas do cosmos e da ciência de ponta.\n\n#ScapaticiTecnologia #FalsoVacuo #BosonDeHiggs #FisicaQuantica #Cosmos #CERN #Ciencia",
            "tags": ["scapatici tecnologia", "falso vacuo", "false vacuum decay", "boson de higgs", "fisica quantica", "cern", "universo", "astrofisica", "misterios do universo"]
        },
        "scenes": [
            {
                "id": "scene_1_hook",
                "type": "hook",
                "visual_theme": "quantum_vacuum_bubble_expanding_light_speed",
                "headline": "A BOLHA QUE REESCREVE A REALIDADE",
                "narration": "Imagine que, em algum ponto distante do universo, uma flutuação quântica invisível aconteça no tecido do espaço vazio. No instante seguinte, uma esfera microscópica nasce e começa a se expandir em todas as direções à exata velocidade da luz. Dentro dessa bolha, as leis da física deixam de funcionar: os elétrons perdem a capacidade de orbitar átomos, a química é aniquilada e as estrelas se dissolvem instantaneamente. Como a parede dessa bolha viaja na velocidade da luz, nenhum telescópio jamais veria ela chegando. Nós simplesmente deixaríamos de existir em um piscar de olhos. Isso não é ficção científica: é o Decaimento do Falso Vácuo, uma previsão real da física de partículas moderna.",
                "highlight_words": ["FALSO VÁCUO", "VELOCIDADE DA LUZ", "FIM DA QUÍMICA", "SEM AVISO PRÉVIO"],
                "stats": {"label": "Velocidade da Bolha", "value": "300.000 km/s (Luz)"},
                "backgroundImage": "assets/video-013-false-vacuum-decay/scene_1.jpg",
                "panDirection": "zoom-in"
            },
            {
                "id": "scene_2_energy_valleys_concept",
                "type": "investigation",
                "visual_theme": "quantum_field_energy_valley_diagram",
                "headline": "A REGRA FUNDAMENTAL DA PREGUIÇA CÓSMICA",
                "narration": "Tudo na natureza busca o estado de menor energia possível. Uma bola no topo de uma montanha rola para baixo até parar no fundo do vale; a lenha queima até virar cinza fria. Na física quântica, até mesmo o espaço completamente vazio possui campos invisíveis que permeiam todo o universo, e todos eles já rolaram até o fundo de seus vales energéticos após o Big Bang. Todos, exceto um: o Campo de Higgs, o campo responsável por dar massa a todas as partículas que formam o seu corpo e as galáxias.",
                "highlight_words": ["MENOR ENERGIA", "CAMPO DE HIGGS", "ORIGEM DA MASSA", "VALE ENERGÉTICO"],
                "stats": {"label": "Campo Crítico", "value": "Campo de Higgs"},
                "backgroundImage": "assets/video-013-false-vacuum-decay/scene_2.jpg",
                "panDirection": "pan-right"
            },
            {
                "id": "scene_3_cern_2012_measurement",
                "type": "technology",
                "visual_theme": "cern_large_hadron_collider_higgs_discovery",
                "headline": "O NÚMERO PERTURBADOR DE 125 GIGAELETRON-VOLTS",
                "narration": "Em quatro de julho de 2012, quando o Grande Colisor de Hádrons do CERN finalmente descobriu o Bóson de Higgs, os cientistas mediram sua massa com precisão cirúrgica: cento e vinte e cinco vírgula um gigaeletron-volts. Quando os físicos teóricos cruzaram esse número com a massa do quark top, os gráficos revelaram algo desconcertante. O nosso Campo de Higgs não está necessariamente no fundo absoluto do vale do universo, mas preso em uma pequena depressão na encosta da montanha: um estado metaestável conhecido como Falso Vácuo.",
                "highlight_words": ["CERN 2012", "125 GIGAELETRON-VOLTS", "ESTADO METAESTÁVEL", "BÓSON DE HIGGS"],
                "stats": {"label": "Massa do Higgs", "value": "125,1 GeV (Metaestável)"},
                "backgroundImage": "assets/video-013-false-vacuum-decay/scene_3.jpg",
                "panDirection": "pan-left"
            },
            {
                "id": "scene_4_quantum_tunneling_trigger",
                "type": "climax",
                "visual_theme": "quantum_tunneling_barrier_breach",
                "headline": "O EFEITO DE TUNELAMENTO QUÂNTICO",
                "narration": "No mundo clássico, se uma bola está presa em uma depressão na encosta da montanha, ela precisa de um empurrão gigantesco para passar por cima da barreira e cair no abismo verdadeiro lá embaixo. Mas no mundo subatômico existe uma regra fantasmagórica chamada Tunelamento Quântico. Uma partícula ou campo pode simplesmente atravessar a parede da montanha como um fantasma, aparecendo do outro lado no Vácuo Verdadeiro. Se um único ponto do espaço fizer esse tunelamento, ele puxa todo o espaço vizinho com ele em uma reação em cadeia imparável.",
                "highlight_words": ["TUNELAMENTO QUÂNTICO", "ATRAVESSAR A BARREIRA", "VÁCUO VERDADEIRO", "REAÇÃO EM CADEIA"],
                "stats": {"label": "Mecanismo Físico", "value": "Tunelamento Quântico"},
                "backgroundImage": "assets/video-013-false-vacuum-decay/scene_4.jpg",
                "panDirection": "hyper-zoom"
            },
            {
                "id": "scene_5_inside_true_vacuum",
                "type": "climax",
                "visual_theme": "atoms_dissolving_new_physics_constants",
                "headline": "O QUE ACONTECE DENTRO DO VÁCUO VERDADEIRO?",
                "narration": "O físico Sidney Coleman, de Harvard, calculou o que aconteceria no interior dessa bolha de Vácuo Verdadeiro. As constantes fundamentais da natureza mudariam instantaneamente. Os elétrons ficariam milhares de vezes mais pesados ou mudariam sua interação com os prótons, fazendo com que nenhuma molécula química pudesse existir. Além disso, a própria geometria gravitacional dentro da bolha entraria em colapso imediato, formando um universo interno incompatível com a matéria que conhecemos.",
                "highlight_words": ["SIDNEY COLEMAN", "CONSTANTES DA FÍSICA", "COLAPSO ATÔMICO", "NOVA REALIDADE"],
                "stats": {"label": "Consequência Física", "value": "Novas Leis da Natureza"},
                "backgroundImage": "assets/video-013-false-vacuum-decay/scene_5.jpg",
                "panDirection": "dramatic-pulse"
            },
            {
                "id": "scene_6_cosmic_rays_safety",
                "type": "investigation",
                "visual_theme": "ultra_high_energy_cosmic_rays_shield",
                "headline": "POR QUE OS COLISORES DE PARTÍCULAS SÃO SEGUROS?",
                "narration": "Quando essa teoria se popularizou, muitas pessoas temeram que os aceleradores de partículas na Terra pudessem disparar esse gatilho acidentalmente. Mas os astrofísicos trazem uma prova tranquilizadora: todos os dias, a atmosfera da Terra e as estrelas de nêutrons são bombardeadas por raios cósmicos naturais com energias milhões de vezes superiores ao máximo que o Grande Colisor de Hádrons do CERN jamais conseguirá produzir. Se colisões subatômicas pudessem rasgar o Falso Vácuo facilmente, o universo já teria decaído bilhões de anos atrás.",
                "highlight_words": ["RAIOS CÓSMICOS", "MILHÕES DE VEZES", "PROVA NATURAL", "ESTABILIDADE"],
                "stats": {"label": "Segurança Cósmica", "value": "Testado há 13,8 Bi Anos"},
                "backgroundImage": "assets/video-013-false-vacuum-decay/scene_6.jpg",
                "panDirection": "floating-drift"
            },
            {
                "id": "scene_7_eternity_timescale",
                "type": "investigation",
                "visual_theme": "deep_future_universe_expansion_shield",
                "headline": "A ESCALA DE TEMPO E A SALVAÇÃO PELA EXPANSÃO",
                "narration": "De acordo com os cálculos mais recentes do Modelo Padrão, a probabilidade de o tunelamento acontecer é tão infinitesimal que o tempo médio estimado para o decaimento do nosso setor é de dez elevado a cem anos: um número muito maior do que a própria vida útil de todas as estrelas do cosmos. E mesmo que uma bolha nascesse hoje a bilhões de anos-luz de distância, a expansão acelerada do espaço-tempo provocada pela Energia Escura impediria que essa bolha jamais alcançasse a Via Láctea.",
                "highlight_words": ["10 ELEVADO A 100 ANOS", "ENERGIA ESCURA", "EXPANSÃO PROTETORA", "FUTURO PROFUNDO"],
                "stats": {"label": "Expectativa de Vida", "value": "10^100 Anos"},
                "backgroundImage": "assets/video-013-false-vacuum-decay/scene_7.jpg",
                "panDirection": "tilt-down"
            },
            {
                "id": "scene_8_scapatici_cta",
                "type": "cta",
                "visual_theme": "scapatici_space_observatory_community",
                "headline": "O EQUILÍBRIO DELICADO DA EXISTÊNCIA",
                "narration": "E você, o que acha do fato de toda a nossa realidade estar equilibrada na precisão milimétrica do Campo de Higgs? Acredita que existe uma física ainda desconhecida protegendo a estabilidade do universo? Deixe sua opinião aqui nos comentários, compartilhe este vídeo com quem é fascinado pelos mistérios do universo, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!",
                "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SEU COMENTÁRIO", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
                "stats": {"label": "Comunidade Oficial", "value": "Scapatici Tecnologia"},
                "backgroundImage": "assets/video-013-false-vacuum-decay/scene_8.jpg",
                "panDirection": "zoom-out"
            }
        ],
        "image_queries": {
            "scene_1.jpg": "supernova shockwave bubble expansion hubble",
            "scene_2.jpg": "quantum field particle physics simulation",
            "scene_3.jpg": "high energy particle collision detector",
            "scene_4.jpg": "pulsar magnetic field quantum space",
            "scene_5.jpg": "planetary nebula glowing sphere hubble",
            "scene_6.jpg": "cosmic ray shower gamma ray fermi",
            "scene_7.jpg": "deep space distant galaxies expansion webb",
            "scene_8.jpg": "nebula starbirth pillars of creation webb",
            "thumbnail.jpg": "cosmic shockwave sphere glowing space"
        }
    },
    {
        "id": "video-014-quasi-stars",
        "title": "Quasi-Estrelas: As Estrelas Gigantes Alimentadas por Buracos Negros no Início do Tempo",
        "topic": "Quasi-Estrelas, Buracos Negros Primordiais, População III e a Aurora Cósmica",
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 330,
        "fps": 30,
        "vinheta_duration_frames": 90,
        "bg_music_volume": 0.12,
        "thumbnail_text": {
            "line1": "ESTRELAS COM BURACO NEGRO",
            "line2": "DENTRO DO CORAÇÃO?",
            "subtitle": "O MISTÉRIO DAS QUASI-ESTRELAS | SCAPATICI TECNOLOGIA"
        },
        "seo": {
            "title_options": [
                "Quasi-Estrelas: As Estrelas Gigantes Alimentadas por Buracos Negros no Início do Tempo",
                "O Monstro Cósmico Que Tinha um Buraco Negro no Núcleo: O Mistério das Quasi-Estrelas",
                "Como Nasceram os Primeiros Buracos Negros do Universo? O Enigma Revelado pelo James Webb"
            ],
            "description": "Imagine uma estrela tão gigantesca que o nosso Sol pareceria um grão de poeira ao seu lado. Uma estrela cujo diâmetro engoliria todo o Sistema Solar até a órbita de Saturno. Mas o detalhe mais aterrorizante não era o seu tamanho: no coração dessa estrela não havia fusão nuclear, mas um buraco negro supermassivo devorando o astro de dentro para fora.\n\nNeste décimo quarto episódio do canal Scapatici Tecnologia, investigamos as Quasi-Estrelas (ou Estrelas de Buraco Negro), os monstros colossais que reinaram na aurora cósmica e que finalmente explicam como buracos negros supermassivos surgiram tão rápido após o Big Bang.\n\n🔔 Inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia.\n\n#ScapaticiTecnologia #QuasiEstrelas #BuracoNegro #Astrofisica #Cosmos #JamesWebb #Ciencia",
            "tags": ["scapatici tecnologia", "quasi estrelas", "black hole stars", "buraco negro", "james webb", "astrofisica", "universo", "big bang", "misterios do universo"]
        },
        "scenes": [
            {
                "id": "scene_1_hook",
                "type": "hook",
                "visual_theme": "hypergiant_quasi_star_black_hole_core",
                "headline": "O MONSTRO QUE DEVORAVA A SI MESMO",
                "narration": "Imagine olhar para o céu primordial e ver uma estrela com dez bilhões de quilômetros de diâmetro. Um colosso tão desproporcional que, se fosse colocado no lugar do nosso Sol, engoliria Mercúrio, Vênus, a Terra, Marte, Júpiter e alcançaria os anéis de Saturno. Mas o segredo mais perturbador não estava na sua superfície dourada e incandescente: estava no seu coração. Diferente de todas as estrelas conhecidas pela física moderna, esse monstro não gerava luz por fusão nuclear. No centro exato do seu núcleo residia um buraco negro voraz, devorando a própria estrela de dentro para fora a cada fração de segundo. Os astrofísicos chamam essas anomalias de Quasi-Estrelas: os titãs mais brutais que já existiram na história do universo.",
                "highlight_words": ["DEZ BILHÕES DE KM", "QUASI-ESTRELAS", "BURACO NEGRO NO NÚCLEO", "DEVORANDO A SI MESMO"],
                "stats": {"label": "Diâmetro Estimado", "value": "10 Bilhões de Km (Até Saturno)"},
                "backgroundImage": "assets/video-014-quasi-stars/scene_1.jpg",
                "panDirection": "zoom-in"
            },
            {
                "id": "scene_2_eddington_limit_paradox",
                "type": "investigation",
                "visual_theme": "gas_infall_radiation_pressure_balance",
                "headline": "O LIMITE DE EDDINGTON E A RADIAÇÃO SALVADORA",
                "narration": "Em qualquer situação normal da física, quando um buraco negro começa a se alimentar de uma estrela, o astro é rasgado e destruído em poucos dias. Mas nas Quasi-Estrelas, a quantidade de gás primordial era tão descomunal que a gravidade da camada externa esmagava o buraco negro com força infinita. A matéria ao cair no horizonte de eventos atingia temperaturas de milhões de graus, gerando uma pressão de radiação tão colossal que empurrava o restante do gás para fora. Foi o equilíbrio perfeito entre a fome do abismo e a fúria da luz: uma estrela sustentada pela própria agonia do seu núcleo devorador.",
                "highlight_words": ["LIMITE DE EDDINGTON", "PRESSÃO DE RADIAÇÃO", "EQUILÍBRIO PERFEITO", "FÚRIA DA LUZ"],
                "stats": {"label": "Massa Estelar", "value": "+1.000 Sóis"},
                "backgroundImage": "assets/video-014-quasi-stars/scene_2.jpg",
                "panDirection": "pan-right"
            },
            {
                "id": "scene_3_the_seed_mystery",
                "type": "investigation",
                "visual_theme": "primordial_gas_cloud_direct_collapse",
                "headline": "A SOLUÇÃO PARA O MAIOR QUEBRA-CABEÇA DA ASTRONOMIA",
                "narration": "Durante décadas, os astrônomos enfrentaram um paradoxo insolúvel: como o universo jovem conseguiu criar buracos negros com bilhões de massas solares em menos de seiscentos milhões de anos após o Big Bang? Estrelas normais que morrem como supernovas deixam buracos negros bebês, que levariam bilhões de anos comendo para atingir esse tamanho. As Quasi-Estrelas são a peça que faltava no quebra-cabeça. Elas eram verdadeiros berçários de hiperalimentação rápida, permitindo que o buraco negro interno engordasse dez mil vezes mais rápido do que qualquer equação clássica considerava possível.",
                "highlight_words": ["PARADOXO INSOLÚVEL", "HIPERALIMENTAÇÃO", "SETE BILHÕES DE SÓIS", "PEÇA QUE FALTAVA"],
                "stats": {"label": "Taxa de Crescimento", "value": "10.000x Mais Rápida"},
                "backgroundImage": "assets/video-014-quasi-stars/scene_3.jpg",
                "panDirection": "pan-left"
            },
            {
                "id": "scene_4_the_stellar_death",
                "type": "climax",
                "visual_theme": "quasi_star_envelope_dissipation_quasar_birth",
                "headline": "A MORTE DO INVÓLUCRO E O NASCIMENTO DO QUASAR",
                "narration": "A vida de uma Quasi-Estrela era curta e violenta, durando cerca de sete milhões de anos: um piscar de olhos na escala cósmica. Conforme o buraco negro central crescia para dezenas de milhares de vezes a massa do Sol, a radiação interna se tornava tão insuportável que soprava todo o envelope estelar para o vácuo interestelar. A pele da estrela evaporava, revelando no meio do cosmos um quasar nu e brilhante, cuspindo jatos relativísticos de energia através de galáxias inteiras.",
                "highlight_words": ["SETE MILHÕES DE ANOS", "NASCIMENTO DO QUASAR", "JATOS RELATIVÍSTICOS", "ENVELOPE EVAPORADO"],
                "stats": {"label": "Tempo de Vida", "value": "7 Milhões de Anos"},
                "backgroundImage": "assets/video-014-quasi-stars/scene_4.jpg",
                "panDirection": "hyper-zoom"
            },
            {
                "id": "scene_5_jwst_red_dots",
                "type": "technology",
                "visual_theme": "james_webb_infrared_spectrum_little_red_dots",
                "headline": "OS PONTOS VERMELHOS DO JAMES WEBB",
                "narration": "O que antes era apenas uma teoria matemática elegante agora está ganhando provas materiais concretas. As observações recentes do Telescópio Espacial James Webb descobriram os misteriosos pequenos pontos vermelhos no amanhecer do cosmos: objetos ultracompactos, intensamente avermelhados e supermassivos que não se encaixam no modelo de galáxias normais. Vários astrofísicos de Oxford e Harvard agora suspeitam que alguns desses pontos possam ser nada menos que o primeiro vislumbre de Quasi-Estrelas em ação.",
                "highlight_words": ["JAMES WEBB", "PONTOS VERMELHOS", "OXFORD E HARVARD", "PROVAS CONCRETAS"],
                "stats": {"label": "Detecção JWST", "value": "Amanhecer Cósmico (z > 7)"},
                "backgroundImage": "assets/video-014-quasi-stars/scene_5.jpg",
                "panDirection": "floating-drift"
            },
            {
                "id": "scene_6_why_they_cant_form_today",
                "type": "investigation",
                "visual_theme": "heavy_elements_cooling_gas_nebula",
                "headline": "POR QUE ELAS NUNCA MAIS PODERÃO EXISTIR?",
                "narration": "Você nunca verá uma Quasi-Estrela nascer hoje no universo contemporâneo. Para que uma nuvem de gás colapse diretamente sem se fragmentar em milhares de estrelinhas pequenas, o gás precisava ser cem por cento puro: apenas hidrogênio e hélio primordiais, sem nenhum traço de carbono, oxigênio ou ferro. Quando as primeiras gerações de estrelas explodiram e semearam a tabela periódica pelo cosmos, elas 'envenenaram' o gás primordial, extinguindo para sempre a receita física que dava vida a esses titãs.",
                "highlight_words": ["NUNCA MAIS", "GÁS PRIMORDIAL PURO", "TABELA PERIÓDICA", "RECEITA EXTINTA"],
                "stats": {"label": "Metalicitade Exigida", "value": "Zero Absoluto (Pop. III)"},
                "backgroundImage": "assets/video-014-quasi-stars/scene_6.jpg",
                "panDirection": "tilt-down"
            },
            {
                "id": "scene_7_legacy_supermassive_seeds",
                "type": "climax",
                "visual_theme": "milky_way_sagittarius_a_star_origin",
                "headline": "A HERANÇA NO CENTRO DA NOSSA GALÁXIA",
                "narration": "O legado das Quasi-Estrelas não está perdido no passado: ele está vivo bem no coração da nossa própria casa. O buraco negro supermassivo Sagitário A estrela, com quatro milhões de massas solares ancorando a rotação de toda a Via Láctea, pode ser o descendente direto de uma Quasi-Estrela primordial. Sem esses gigantes devoradores do início do tempo, as galáxias espirais como a nossa talvez nunca tivessem tido gravidade suficiente para se aglutinar.",
                "highlight_words": ["SAGITÁRIO A*", "CENTRO DA VIA LÁCTEA", "HERANÇA CÓSMICA", "ÂNCORA GRAVITACIONAL"],
                "stats": {"label": "Resultado Atual", "value": "Buracos Negros Supermassivos"},
                "backgroundImage": "assets/video-014-quasi-stars/scene_7.jpg",
                "panDirection": "dramatic-pulse"
            },
            {
                "id": "scene_8_scapatici_cta",
                "type": "cta",
                "visual_theme": "scapatici_space_observatory_community",
                "headline": "O ECO DOS PRIMEIROS MONSTROS DO COSMOS",
                "narration": "E você, já imaginava que existiram estrelas que tinham um buraco negro devorador no próprio coração? Acredita que o James Webb vai confirmar de vez a existência das Quasi-Estrelas? Deixe sua teoria aqui nos comentários, compartilhe este vídeo com quem é fascinado pelos mistérios do universo, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!",
                "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SEU COMENTÁRIO", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
                "stats": {"label": "Comunidade Oficial", "value": "Scapatici Tecnologia"},
                "backgroundImage": "assets/video-014-quasi-stars/scene_8.jpg",
                "panDirection": "zoom-out"
            }
        ],
        "image_queries": {
            "scene_1.jpg": "supergiant star black hole accretion disk concept",
            "scene_2.jpg": "radiation pressure accretion disk astrophysics hubble",
            "scene_3.jpg": "primordial cloud early universe stars webb",
            "scene_4.jpg": "quasar relativistic jet deep space chandra",
            "scene_5.jpg": "james webb deep field red dots little red dots",
            "scene_6.jpg": "stellar nursery gas dust carina webb",
            "scene_7.jpg": "sagittarius a black hole center milky way eht",
            "scene_8.jpg": "deep space galaxy cluster gravitational lensing hubble",
            "thumbnail.jpg": "hypergiant star glowing black hole core space"
        }
    },
    {
        "id": "video-015-magnetars",
        "title": "Magnetars: Os Objetos Mais Magnéticos do Universo Que Podem Desintegrar Átomos a Mil Quilômetros",
        "topic": "Magnetars, Estrelas de Nêutrons, Starquakes e os Campos Magnéticos Mais Extremos da Física",
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 330,
        "fps": 30,
        "vinheta_duration_frames": 90,
        "bg_music_volume": 0.12,
        "thumbnail_text": {
            "line1": "O OBJETO MAIS LETAL",
            "line2": "DO ESPAÇO!",
            "subtitle": "A FÚRIA DOS MAGNETARS | SCAPATICI TECNOLOGIA"
        },
        "seo": {
            "title_options": [
                "Magnetars: Os Objetos Mais Magnéticos do Universo Que Podem Desintegrar Átomos a Mil Quilômetros",
                "O Que Aconteceria Se um Magnetar Entrasse no Nosso Sistema Solar?",
                "Terremotos Estelares de Magnetars: A Explosão Que Quebrou Satélites na Terra a 50.000 Anos-Luz"
            ],
            "description": "Se você chegasse a mil quilômetros de um Magnetar, a força magnética não apenas apagaria todos os cartões de crédito da Terra: ela distorceria as nuvens de elétrons dos seus átomos em cilindros microscópicos, dissolvendo a sua estrutura molecular instantaneamente.\n\nNeste décimo quinto episódio do canal Scapatici Tecnologia, investigamos os Magnetars, os remanescentes estelares mais magneticamente furiosos do universo, cujos terremotos na crosta de ferro podem cegar satélites na órbita da Terra a 50 mil anos-luz de distância.\n\n🔔 Inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia.\n\n#ScapaticiTecnologia #Magnetar #EstrelaDeNeutrons #Astrofisica #Cosmos #FisicaQuantica #Ciencia",
            "tags": ["scapatici tecnologia", "magnetar", "estrela de neutrons", "campo magnetico", "starquake", "astrofisica", "universo", "fisica", "misterios do universo"]
        },
        "scenes": [
            {
                "id": "scene_1_hook",
                "type": "hook",
                "visual_theme": "magnetar_pulsar_extreme_magnetic_field_lines",
                "headline": "A MURALHA MAGNÉTICA DA MORTE MOLECULAR",
                "narration": "Se uma única moeda feita com a matéria de um Magnetar caísse na superfície da Terra, o impacto seria comparável a milhares de bombas atômicas. Mas a verdadeira força dessa anomalia não é apenas a sua densidade descomunal: é o seu campo magnético. Um Magnetar possui um campo magnético um quadrilhão de vezes mais poderoso que o do planeta Terra. Se um ser humano se aproximasse a mil quilômetros desse astro, não seria a gravidade que o mataria primeiro: a força magnética pura seria tão violenta que distorceria as órbitas dos seus elétrons em cilindros finos como agulhas, destruindo toda a química orgânica e dissolvendo o seu corpo em nível atômico em milésimos de segundo.",
                "highlight_words": ["1 QUADRILHÃO DE VEZES", "MAGNETAR", "DISSOLUÇÃO ATÔMICA", "MIL QUILÔMETROS"],
                "stats": {"label": "Intensidade Magnética", "value": "100 Bilhões de Teslas"},
                "backgroundImage": "assets/video-015-magnetars/scene_1.jpg",
                "panDirection": "zoom-in"
            },
            {
                "id": "scene_2_birth_of_a_magnetar",
                "type": "investigation",
                "visual_theme": "supernova_core_collapse_dynamo_effect",
                "headline": "O EFEITO DÍNAMO QUE FORJA O MONSTRO",
                "narration": "Como a natureza cria um objeto tão extremo? Quando uma estrela hipergigante com trinta vezes a massa do Sol encerra sua vida em uma explosão de supernova, o seu núcleo colapsa sob a gravidade esmagadora em uma esfera de apenas vinte quilômetros de diâmetro. Se essa esfera estiver girando a centenas de voltas por segundo no momento exato do colapso, ela dispara o chamado Efeito Dínamo: a convecção de matéria nuclear superdensa amplifica as linhas magnéticas da estrela morta a patamares que beiram os limites máximos permitidos pela física quântica.",
                "highlight_words": ["SUPERNOVA", "20 QUILÔMETROS", "EFEITO DÍNAMO", "LIMITE QUÂNTICO"],
                "stats": {"label": "Diâmetro Médio", "value": "Apenas 20 km de Diâmetro"},
                "backgroundImage": "assets/video-015-magnetars/scene_2.jpg",
                "panDirection": "pan-right"
            },
            {
                "id": "scene_3_the_starquake_2004",
                "type": "climax",
                "visual_theme": "sgr_1806_20_starquake_gamma_ray_burst",
                "headline": "O TERREMOTO ESTELAR DE 27 DE DEZEMBRO DE 2004",
                "narration": "Em vinte e sete de dezembro de 2004, os satélites de defesa e telescópios espaciais da Terra foram cegados por uma rajada devastadora de raios gama. O pulso de radiação foi tão brutal que alterou a ionosfera da Terra e queimou sensores em órbita. Mas a origem não estava no nosso Sistema Solar: veio do Magnetar SGR dezoito zero seis traço vinte, a cinquenta mil anos-luz de distância. Uma trinca microscópica de apenas um milímetro na sua crosta de ferro superdenso liberou, em um décimo de segundo, mais energia do que o nosso Sol emite em duzentos e cinquenta mil anos inteiros.",
                "highlight_words": ["27 DE DEZEMBRO DE 2004", "50 MIL ANOS-LUZ", "IONOSFERA DA TERRA", "250 MIL ANOS DE SOL"],
                "stats": {"label": "Energia Liberada", "value": "10^39 Joules em 0,1s"},
                "backgroundImage": "assets/video-015-magnetars/scene_3.jpg",
                "panDirection": "hyper-zoom"
            },
            {
                "id": "scene_4_quantum_electrodynamics",
                "type": "investigation",
                "visual_theme": "quantum_vacuum_birefringence_light_splitting",
                "headline": "QUANDO O VÁCUO SE TRANSFORMA EM PRISMA",
                "narration": "Perto de um Magnetar, o próprio espaço vazio deixa de ser neutro. O campo magnético é tão avassalador que ele quebra as leis da Eletrodinâmica Quântica, provocando um fenômeno previsto por Werner Heisenberg chamado Birrefringência do Vácuo. O tecido do vácuo ao redor do astro se comporta como um cristal transparente que divide a luz polarizada em duas direções diferentes. Fótons de raios X colidem com o campo magnético e se dividem espontaneamente em elétrons e pós-étrons no nada.",
                "highlight_words": ["ELETRODINÂMICA QUÂNTICA", "HEISENBERG", "BIRREFRINGÊNCIA DO VÁCUO", "CRISTAL DE ESPAÇO"],
                "stats": {"label": "Fenômeno Físico", "value": "Birrefringência do Vácuo"},
                "backgroundImage": "assets/video-015-magnetars/scene_4.jpg",
                "panDirection": "floating-drift"
            },
            {
                "id": "scene_5_fast_radio_bursts",
                "type": "technology",
                "visual_theme": "chime_radio_telescope_fast_radio_burst_detection",
                "headline": "A RESPOSTA PARA AS RAJADAS RÁPIDAS DE RÁDIO",
                "narration": "Durante mais de uma década, o maior mistério da radioastronomia eram as Rajadas Rápidas de Rádio: sinais intensos de milissegundos vindos de cantos distantes do cosmos. Em 2020, o radiotelescópio CHIME no Canadá flagrou uma rajada de rádio violenta disparando em sincronia perfeita com um surto de raios X vindo de um Magnetar dentro da nossa própria Via Láctea. O mistério estava solucionado: os espasmos magnéticos desses titãs são os motores por trás dos sinais mais energéticos do céu.",
                "highlight_words": ["RAJADAS RÁPIDAS DE RÁDIO", "TELESCÓPIO CHIME", "VIA LÁCTEA", "MISTÉRIO SOLUCIONADO"],
                "stats": {"label": "Duração do Pulso", "value": "Milissegundos Extremos"},
                "backgroundImage": "assets/video-015-magnetars/scene_5.jpg",
                "panDirection": "pan-left"
            },
            {
                "id": "scene_6_short_lifespan",
                "type": "investigation",
                "visual_theme": "magnetar_cooling_down_into_regular_pulsar",
                "headline": "A FÚRIA QUE SE CONSOME EM DEZ MIL ANOS",
                "narration": "Apesar do seu poder aterrador, a fase ativa de um Magnetar é uma das mais breves de todo o zoológico cósmico. Toda essa fúria magnética consome a própria rotação e energia do astro em apenas dez mil anos. Conforme suas linhas de campo se retorcem e dissipam calor na forma de radiação gama, o Magnetar desacelera e esfria, transformando-se em uma estrela de nêutrons comum e dormente que navegará pelo silêncio cósmico por trilhões de anos.",
                "highlight_words": ["DEZ MIL ANOS", "ENERGIA DISSIPADA", "ESTRELA DORMENTE", "FÚRIA BREVE"],
                "stats": {"label": "Vida Ativa", "value": "Apenas 10.000 Anos"},
                "backgroundImage": "assets/video-015-magnetars/scene_6.jpg",
                "panDirection": "dramatic-pulse"
            },
            {
                "id": "scene_7_what_if_near_earth",
                "type": "climax",
                "visual_theme": "magnetar_passing_solar_system_aurora_disaster",
                "headline": "E SE UM MAGNETAR PASSASSE PERTO DA TERRA?",
                "narration": "Se um Magnetar passasse a meio caminho entre a Terra e a Lua, a humanidade testemunharia o fim da era tecnológica em minutos. Antes mesmo da gravidade perturbar as marés, o campo magnético apagaria permanentemente todos os servidores, discos rígidos e redes elétricas do planeta. As auroras polares cobririam o céu inteiro de verde e roxo incandescente sob um bombardeio de radiação letal. Felizmente, o Magnetar mais próximo está a milhares de anos-luz de distância.",
                "highlight_words": ["FIM DA ERA DIGITAL", "PANE ELÉTRICA GLOBAL", "AURORAS TOTAIS", "DISTÂNCIA SEGURA"],
                "stats": {"label": "Magnetar Mais Próximo", "value": "+9.000 Anos-Luz da Terra"},
                "backgroundImage": "assets/video-015-magnetars/scene_7.jpg",
                "panDirection": "tilt-down"
            },
            {
                "id": "scene_8_scapatici_cta",
                "type": "cta",
                "visual_theme": "scapatici_space_observatory_community",
                "headline": "O LIMITE EXTREMO DA MATÉRIA",
                "narration": "E você, o que achou da física aterradora dos Magnetars? Acredita que a humanidade conseguirá um dia compreender totalmente essas forças que desafiam a mecânica quântica? Deixe sua teoria aqui nos comentários, compartilhe este vídeo com quem é fascinado pelos mistérios do universo, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!",
                "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SEU COMENTÁRIO", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
                "stats": {"label": "Comunidade Oficial", "value": "Scapatici Tecnologia"},
                "backgroundImage": "assets/video-015-magnetars/scene_8.jpg",
                "panDirection": "zoom-out"
            }
        ],
        "image_queries": {
            "scene_1.jpg": "magnetar neutron star magnetic field chandra",
            "scene_2.jpg": "supernova remnant core collapse hubble",
            "scene_3.jpg": "gamma ray burst cosmic explosion fermi nasa",
            "scene_4.jpg": "quantum vacuum birefringence magnetic field simulation",
            "scene_5.jpg": "radio telescope array night stars fast radio burst",
            "scene_6.jpg": "pulsar isolated in deep space hubble",
            "scene_7.jpg": "aurora borealis northern lights geomagnetic storm",
            "scene_8.jpg": "crab nebula pulsar center chandra hubble",
            "thumbnail.jpg": "magnetar glowing magnetic field lines pulsar space"
        }
    },
    {
        "id": "video-016-hubble-tension",
        "title": "A Crise da Tensão de Hubble: Por Que o Universo Está se Expandindo em Duas Velocidades Diferentes?",
        "topic": "Tensão de Hubble, Constante de Hubble, James Webb, Cosmologia e Crise no Modelo Padrão",
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 330,
        "fps": 30,
        "vinheta_duration_frames": 90,
        "bg_music_volume": 0.12,
        "thumbnail_text": {
            "line1": "A FÍSICA QUEBROU?",
            "line2": "DUAS VELOCIDADES NO ESPAÇO",
            "subtitle": "A TENSÃO DE HUBBLE | SCAPATICI TECNOLOGIA"
        },
        "seo": {
            "title_options": [
                "A Crise da Tensão de Hubble: Por Que o Universo Está se Expandindo em Duas Velocidades Diferentes?",
                "O Maior Erro da Cosmologia Moderna: A Tensão de Hubble Confirmada Pelo James Webb",
                "O Universo Não Deveria Estar Fazendo Isso: A Crise Que Quebrou as Equações de Einstein"
            ],
            "description": "Imagine medir a velocidade de expansão do universo usando a luz da infância cósmica e obter um resultado; depois medir usando as estrelas modernas e obter outro completamente diferente. Esse abismo estatístico é a Tensão de Hubble: a maior crise da física contemporânea.\n\nNeste episódio do canal Scapatici Tecnologia, investigamos como o Telescópio Espacial James Webb testou as medições da Constante de Hubble e confirmou que a anomalia não é erro de medição: a física fundamental pode estar faltando uma peça cósmica inteira.\n\n🔔 Inscreva-se no canal Scapatici Tecnologia para desvendar os maiores enigmas da ciência e da tecnologia.\n\n#ScapaticiTecnologia #TensaoDeHubble #ConstanteDeHubble #Cosmologia #Astrofisica #JamesWebb #Ciencia",
            "tags": ["scapatici tecnologia", "tensao de hubble", "hubble tension", "constante de hubble", "james webb", "big bang", "astrofisica", "universo", "misterios do universo"]
        },
        "scenes": [
            {
                "id": "scene_1_hook",
                "type": "hook",
                "visual_theme": "expanding_universe_split_velocities_divergence",
                "headline": "A MAIOR CRISE DA FÍSICA MODERNA",
                "narration": "Se você medir a velocidade de um carro olhando pelo velocímetro e seu amigo medir olhando por um radar na estrada, os números devem bater perfeitamente. Mas quando os maiores astrofísicos do planeta apontam os telescópios mais sofisticados da história para medir a velocidade em que o universo está se expandindo, os dois melhores métodos da ciência chegam a respostas incompatíveis. Pior ainda: a margem de erro estatístico é de uma chance em cem milhões de ser coincidência. Bem-vindo à Tensão de Hubble: a crise matemática mais profunda da física do século vinte e um, que sugere que o nosso modelo padrão do cosmos está fundamentalmente quebrado.",
                "highlight_words": ["TENSÃO DE HUBBLE", "RESPOSTAS INCOMPATÍVEIS", "UMA EM CEM MILHÕES", "FÍSICA QUEBRADA"],
                "stats": {"label": "Nível de Significância", "value": "Acima de 5 Sigma (Definitivo)"},
                "backgroundImage": "assets/video-016-hubble-tension/scene_1.jpg",
                "panDirection": "zoom-in"
            },
            {
                "id": "scene_2_hubble_law_history",
                "type": "investigation",
                "visual_theme": "edwin_hubble_mount_wilson_discovery",
                "headline": "A EQUAÇÃO QUE EXPANDIU A MENTE HUMANA",
                "narration": "Em 1929, o astrônomo Edwin Hubble mudou a história da humanidade ao provar que as galáxias distantes estão se afastando de nós: quanto mais longe uma galáxia está, mais rápido ela parece se mover. Essa taxa de velocidade por distância é a famosa Constante de Hubble. Se soubermos o valor exato dessa constante, podemos calcular a idade precisa do universo, o seu tamanho observável e o destino final do espaço-tempo. Mas o universo se recusou a nos dar um número único.",
                "highlight_words": ["1929", "EDWIN HUBBLE", "CONSTANTE DE HUBBLE", "DESTINO DO ESPAÇO"],
                "stats": {"label": "Descoberta", "value": "Expansão Universal (1929)"},
                "backgroundImage": "assets/video-016-hubble-tension/scene_2.jpg",
                "panDirection": "pan-right"
            },
            {
                "id": "scene_3_the_two_camps",
                "type": "climax",
                "visual_theme": "planck_cmb_vs_supernova_cepheid_split",
                "headline": "O CONFLITO DOS DOIS NÚMEROS: 67 VERSUS 73",
                "narration": "O conflito é direto e implacável. De um lado, o satélite Planck da Agência Espacial Europeia olhou para a radiação fóssil do Big Bang emitida há treze vírgula oito bilhões de anos e calculou que o cosmos se expande a sessenta e sete vírgula quatro quilômetros por segundo por megaparsec. Do outro lado, astrônomos liderados pelo Prêmio Nobel Adam Riess mediram supernovas e estrelas Cefeidas no universo moderno e encontraram setenta e três vírgula zero. Uma diferença de quase nove por cento que não deveria existir de acordo com as equações de Albert Einstein.",
                "highlight_words": ["SESSENTA E SETE", "SETENTA E TRÊS", "PRÊMIO NOBEL", "NOVE POR CENTO"],
                "stats": {"label": "Divergência", "value": "67.4 vs 73.0 km/s/Mpc"},
                "backgroundImage": "assets/video-016-hubble-tension/scene_3.jpg",
                "panDirection": "hyper-zoom"
            },
            {
                "id": "scene_4_jwst_verdict",
                "type": "technology",
                "visual_theme": "james_webb_sharp_resolution_cepheid_stars",
                "headline": "O VEREDITO DO JAMES WEBB EM 2024",
                "narration": "Muitos físicos céticos acreditavam que o valor de setenta e três era apenas uma ilusão provocada pela poeira estelar ou resolução limitada do antigo Telescópio Hubble. Mas quando o Telescópio Espacial James Webb apontou seus espelhos infravermelhos ultraprecisos para as mesmas estrelas Cefeidas, o resultado chocou a comunidade: o James Webb confirmou os dados com precisão inédita. Não era erro de instrumento. O universo moderno realmente está se expandindo mais rápido do que o modelo prevê a partir do início dos tempos.",
                "highlight_words": ["JAMES WEBB 2024", "CONFIRMAÇÃO DEFINITIVA", "NÃO É ERRO", "UNIVERSO MODERNO"],
                "stats": {"label": "Verificação JWST", "value": "Erro Sistemático Descartado"},
                "backgroundImage": "assets/video-016-hubble-tension/scene_4.jpg",
                "panDirection": "floating-drift"
            },
            {
                "id": "scene_5_early_dark_energy",
                "type": "investigation",
                "visual_theme": "early_dark_energy_acceleration_infancy",
                "headline": "A HIPÓTESE DA ENERGIA ESCURA PRIMORDIAL",
                "narration": "Se os dois números estão corretos, o que está quebrado? Uma das teorias mais fascinantes é a Energia Escura Primordial. E se a energia escura não for uma constante imutável, mas tiver sofrido um surto temporário de aceleração logo antes dos átomos se formarem no Big Bang? Esse breve espasmo de aceleração cósmica resolveria as equações, mas exigiria reescrever os livros didáticos de termodinâmica e cosmologia.",
                "highlight_words": ["ENERGIA ESCURA PRIMORDIAL", "SURTO TEMPORÁRIO", "REESCREVER LIVROS", "NOVA FORÇA"],
                "stats": {"label": "Candidato Teórico", "value": "Early Dark Energy"},
                "backgroundImage": "assets/video-016-hubble-tension/scene_5.jpg",
                "panDirection": "pan-left"
            },
            {
                "id": "scene_6_decaying_dark_matter",
                "type": "investigation",
                "visual_theme": "dark_matter_decaying_into_dark_radiation",
                "headline": "A MATÉRIA ESCURA QUE SE DESINTEGRA",
                "narration": "Outra explicação assustadora envolve a própria matéria escura. E se as partículas de matéria escura forem instáveis e estiverem se decompondo lentamente ao longo dos bilhões de anos em radiação escura invisível? Conforme o universo envelheceu, a gravidade que segurava os aglomerados de galáxias teria enfraquecido, permitindo que o universo atual se acelerasse em um ritmo muito mais agressivo do que no passado.",
                "highlight_words": ["MATÉRIA ESCURA INSTÁVEL", "RADIAÇÃO ESCURA", "GRAVIDADE ENFRAQUECIDA", "RITMO AGRESSIVO"],
                "stats": {"label": "Modelo Alternativo", "value": "Decaimento de Matéria Escura"},
                "backgroundImage": "assets/video-016-hubble-tension/scene_6.jpg",
                "panDirection": "tilt-down"
            },
            {
                "id": "scene_7_beyond_einstein",
                "type": "climax",
                "visual_theme": "einstein_general_relativity_modifications",
                "headline": "O FIM DA RELATIVIDADE GERAL OU UMA NOVA FÍSICA?",
                "narration": "A Tensão de Hubble é o presente mais valioso que a natureza poderia dar aos cientistas: ela prova que ainda não sabemos tudo. Assim como as anomalias na órbita de Mercúrio provaram que a física de Newton estava incompleta e abriram caminho para Albert Einstein, esse abismo na velocidade do cosmos pode ser a primeira fresta para a tão esperada Teoria de Tudo que unificará a gravidade com a física quântica.",
                "highlight_words": ["ALÉM DE EINSTEIN", "TEORIA DE TUDO", "ÓRBITA DE MERCÚRIO", "PRIMEIRA FRESTA"],
                "stats": {"label": "Veredito da Ciência", "value": "Necessidade de Nova Física"},
                "backgroundImage": "assets/video-016-hubble-tension/scene_7.jpg",
                "panDirection": "dramatic-pulse"
            },
            {
                "id": "scene_8_scapatici_cta",
                "type": "cta",
                "visual_theme": "scapatici_space_observatory_community",
                "headline": "O DESTINO FINAL DA EXPANSÃO CÓSMICA",
                "narration": "E você, qual é a sua aposta sobre a Tensão de Hubble? Acredita que existe uma nova forma de energia desconhecida acelerando o cosmos ou que a própria gravidade de Einstein precisa ser atualizada? Deixe sua teoria aqui nos comentários, compartilhe este vídeo com quem é fascinado pelos mistérios do universo, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!",
                "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SUA TEORIA", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
                "stats": {"label": "Comunidade Oficial", "value": "Scapatici Tecnologia"},
                "backgroundImage": "assets/video-016-hubble-tension/scene_8.jpg",
                "panDirection": "zoom-out"
            }
        ],
        "image_queries": {
            "scene_1.jpg": "universe expansion acceleration galaxies deep space",
            "scene_2.jpg": "hubble space telescope deep space red shift",
            "scene_3.jpg": "cosmic microwave background planck radiation sky",
            "scene_4.jpg": "james webb space telescope deep field cepheid stars",
            "scene_5.jpg": "dark energy acceleration cosmic web simulation",
            "scene_6.jpg": "dark matter filaments gravitational lensing hubble",
            "scene_7.jpg": "einstein space time curvature gravitational wave",
            "scene_8.jpg": "distant galaxies expanding deep cosmos webb",
            "thumbnail.jpg": "universe expansion split speed cosmic crisis"
        }
    },
    {
        "id": "video-017-hercules-corona-wall",
        "title": "A Grande Muralha de Hércules-Corona Borealis: A Estrutura de Dez Bilhões de Anos-Luz Que Quebrou a Cosmologia",
        "topic": "Grande Muralha de Hércules-Corona Borealis, Princípio Cosmológico, Rajadas de Raios Gama e a Maior Estrutura do Universo",
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 330,
        "fps": 30,
        "vinheta_duration_frames": 90,
        "bg_music_volume": 0.12,
        "thumbnail_text": {
            "line1": "A MAIOR COISA",
            "line2": "DO UNIVERSO!",
            "subtitle": "A MURALHA DE 10 BILHÕES DE ANOS-LUZ | SCAPATICI TECNOLOGIA"
        },
        "seo": {
            "title_options": [
                "A Grande Muralha de Hércules-Corona Borealis: A Estrutura de Dez Bilhões de Anos-Luz Que Quebrou a Cosmologia",
                "A Maior Estrutura do Universo Não Deveria Existir: O Mistério de Hércules-Corona Borealis",
                "Como Uma Muralha de Dez Bilhões de Anos-Luz Quebrou o Princípio Cósmico do Big Bang?"
            ],
            "description": "Imagine uma estrutura cósmica tão colossal que ela se estende por mais de dez bilhões de anos-luz. Uma muralha de matéria e galáxias que ocupa mais de dez por cento do diâmetro de todo o universo observável.\n\nNeste episódio do canal Scapatici Tecnologia, investigamos a Grande Muralha de Hércules-Corona Borealis: por que a sua própria existência viola frontalmente o Princípio Cosmológico e coloca em xeque a cronologia oficial de formação de estruturas após o Big Bang.\n\n🔔 Inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia.\n\n#ScapaticiTecnologia #GrandeMuralha #HerculesCoronaBorealis #Cosmologia #Astrofisica #Universo #Ciencia",
            "tags": ["scapatici tecnologia", "grande muralha hercules", "hercules corona borealis", "maior estrutura do universo", "principio cosmologico", "astrofisica", "universo", "big bang", "misterios do universo"]
        },
        "scenes": [
            {
                "id": "scene_1_hook",
                "type": "hook",
                "visual_theme": "hercules_corona_borealis_great_wall_spanning_cosmos",
                "headline": "A ESTRUTURA QUE NÃO PODERIA CABER NO TEMPO",
                "narration": "O universo observável tem cerca de noventa e três bilhões de anos-luz de diâmetro. Agora imagine uma única estrutura contínua de matéria, gás e galáxias que se estende por dez bilhões de anos-luz através do cosmos. Isso significa que essa titânica muralha de aglomerados ocupa mais de dez por cento de tudo o que os nossos olhos e telescópios conseguem enxergar no universo inteiro. Ela é a Grande Muralha de Hércules-Corona Borealis: a maior coisa já descoberta pela humanidade. Mas há um detalhe que tira o sono dos cosmólogos modernos: de acordo com a velocidade máxima da gravidade e a idade do universo após o Big Bang, essa estrutura simplesmente não teve tempo suficiente para se formar.",
                "highlight_words": ["DEZ BILHÕES DE ANOS-LUZ", "DEZ POR CENTO DO UNIVERSO", "GRANDE MURALHA", "NÃO TEVE TEMPO"],
                "stats": {"label": "Extensão Total", "value": "10 Bilhões de Anos-Luz"},
                "backgroundImage": "assets/video-017-hercules-corona-wall/scene_1.jpg",
                "panDirection": "zoom-in"
            },
            {
                "id": "scene_2_gamma_ray_burst_mapping",
                "type": "investigation",
                "visual_theme": "gamma_ray_burst_coordinate_distribution_map",
                "headline": "O MAPA DAS EXPLOSÕES MAIS PODEROSAS DO CÉU",
                "narration": "Como os astrônomos conseguiram enxergar algo tão imenso que ultrapassa o campo de visão de qualquer telescópio individual? Em 2013, o astrofísico István Horváth e sua equipe na Universidade Nacional de Serviço Público da Hungria decidiram mapear a distribuição das Rajadas de Raios Gama: as explosões estelares mais luminosas e violentas do cosmos. Como essas rajadas rastreiam onde a matéria densa e as estrelas estão concentradas, a surpresa foi monumental ao notar que centenas de explosões estavam agrupadas em uma faixa contínua e gigantesca nas constelações de Hércules e Corona Borealis.",
                "highlight_words": ["2013", "ISTVÁN HORVÁTH", "RAJADAS DE RAIOS GAMA", "AGRUPAMENTO ANORMAL"],
                "stats": {"label": "Distância da Terra", "value": "10 Bilhões Anos-Luz"},
                "backgroundImage": "assets/video-017-hercules-corona-wall/scene_2.jpg",
                "panDirection": "pan-right"
            },
            {
                "id": "scene_3_cosmological_principle_violation",
                "type": "climax",
                "visual_theme": "homogenous_universe_assumption_shattered",
                "headline": "A QUEBRA DO PRINCÍPIO COSMOLÓGICO",
                "narration": "Desde a época de Albert Einstein, a pedra angular de toda a cosmologia é o Princípio Cosmológico: a ideia fundamental de que, em escalas suficientemente grandes, o universo deve ser homogêneo e isotrópico: parecer igual e uniforme em todas as direções. Os cálculos matemáticos diziam que nenhuma estrutura unida pela gravidade poderia ultrapassar um vírgula dois bilhão de anos-luz. A Muralha de Hércules tem mais de oito vezes esse limite de segurança física, despedaçando a premissa de homogeneidade do cosmos.",
                "highlight_words": ["PRINCÍPIO COSMOLÓGICO", "HOMOGÊNEO E UNIFORME", "OITO VEZES O LIMITE", "PREMISSA DESPEDAÇADA"],
                "stats": {"label": "Limite Teórico Máximo", "value": "1,2 Bilhão Anos-Luz"},
                "backgroundImage": "assets/video-017-hercules-corona-wall/scene_3.jpg",
                "panDirection": "hyper-zoom"
            },
            {
                "id": "scene_4_gravity_speed_paradox",
                "type": "investigation",
                "visual_theme": "cosmic_speed_of_gravity_clustering_time",
                "headline": "O PARADOXO DA VELOCIDADE DA GRAVIDADE",
                "narration": "A gravidade se propaga rigorosamente na velocidade da luz: trezentos mil quilômetros por segundo. Quando olhamos para a Muralha de Hércules, nós a vemos como ela era há dez bilhões de anos atrás: apenas três vírgula oito bilhões de anos após o Big Bang. Não há tempo fisicamente possível para que a gravidade tenha puxado e organizado tantas dezenas de milhares de galáxias em um filamento tão contínuo e ordenado nesse período. É como encontrar uma metrópole de arranha-céus construída no primeiro dia da Idade da Pedra.",
                "highlight_words": ["VELOCIDADE DA GRAVIDADE", "3,8 BILHÕES DE ANOS", "FILAMENTO ORDENADO", "IDADE DA PEDRA"],
                "stats": {"label": "Tempo Decorrido", "value": "Apenas 3,8 Bi Anos Pós-Big Bang"},
                "backgroundImage": "assets/video-017-hercules-corona-wall/scene_4.jpg",
                "panDirection": "floating-drift"
            },
            {
                "id": "scene_5_primordial_inflation_scars",
                "type": "investigation",
                "visual_theme": "cosmic_inflation_quantum_fluctuation_imprint",
                "headline": "A CICATRIZ DA INFLAÇÃO CÓSMICA PRIMORDIAL",
                "narration": "Se a gravidade comum não conseguiu construir essa muralha a tempo, qual foi o gatilho? A hipótese mais aceita pelos teóricos é que ela é a cicatriz direta da Inflação Cósmica: o período no primeiro trilionésimo de segundo após o Big Bang onde o espaço se expandiu mais rápido que a luz. Flutuações quânticas microscópicas teriam sido esticadas em dimensões cósmicas inimagináveis, criando vales hiperdensos de matéria escura antes mesmo dos primeiros átomos existirem.",
                "highlight_words": ["INFLAÇÃO CÓSMICA", "PRIMEIRO TRILIONÉSIMO", "FLUTUAÇÕES QUÂNTICAS", "VALES DE MATÉRIA ESCURA"],
                "stats": {"label": "Origem Hipotética", "value": "Flutuação da Inflação Cósmica"},
                "backgroundImage": "assets/video-017-hercules-corona-wall/scene_5.jpg",
                "panDirection": "pan-left"
            },
            {
                "id": "scene_6_giant_arc_and_large_quasar_group",
                "type": "technology",
                "visual_theme": "huge_large_quasar_group_sky_survey",
                "headline": "A FAMÍLIA DOS GIGANTES IMPOSSÍVEIS",
                "narration": "A Muralha de Hércules não está sozinha. Nos últimos anos, pesquisas como o Sloan Digital Sky Survey revelaram outros gigantes rebeldes: o Grande Grupo de Quasares com quatro bilhões de anos-luz de extensão e o Arco Gigante de três vírgula três bilhões de anos-luz descoberto pela astrônoma Alexia Lopez. Cada nova megraestrutura catalogada reforça a suspeita de que a distribuição da matéria no universo obedece a regras de simetria muito mais profundas do que pensávamos.",
                "highlight_words": ["SLOAN DIGITAL", "GRUPO DE QUASARES", "ARCO GIGANTE", "ALEXIA LOPEZ"],
                "stats": {"label": "Outros Gigantes", "value": "Arco Gigante (3,3 Bi Anos-Luz)"},
                "backgroundImage": "assets/video-017-hercules-corona-wall/scene_6.jpg",
                "panDirection": "dramatic-pulse"
            },
            {
                "id": "scene_7_the_ultimate_lesson",
                "type": "climax",
                "visual_theme": "observer_looking_at_cosmic_web_perspective",
                "headline": "A LIÇÃO DE HUMILDADE DO COSMOS PROFUNDO",
                "narration": "A Grande Muralha de Hércules-Corona Borealis nos lembra da nossa insignificância diante das escalas cósmicas. A nossa Via Láctea, com cem mil anos-luz de ponta a ponta, é cem mil vezes menor do que essa muralha colossal. Nós somos apenas uma partícula microscópica de poeira suspensa em um filamento cósmico que começou a ser tecido antes que o nosso planeta existisse.",
                "highlight_words": ["CEM MIL VEZES MENOR", "INSIGNIFICÂNCIA", "POEIRA SUSPENSA", "FILAMENTO CÓSMICO"],
                "stats": {"label": "Escala Comparativa", "value": "100.000x a Via Láctea"},
                "backgroundImage": "assets/video-017-hercules-corona-wall/scene_7.jpg",
                "panDirection": "tilt-down"
            },
            {
                "id": "scene_8_scapatici_cta",
                "type": "cta",
                "visual_theme": "scapatici_space_observatory_community",
                "headline": "O LIMITE DA NOSSA COMPREENSÃO",
                "narration": "E você, o que acha da existência dessa muralha colossal de dez bilhões de anos-luz? Acredita que o Princípio Cosmológico precisa ser reformulado ou que novas forças ainda desconhecidas moldaram o cosmos? Deixe sua teoria aqui nos comentários, compartilhe este vídeo com quem é fascinado pelos mistérios do universo, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!",
                "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SUA TEORIA", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
                "stats": {"label": "Comunidade Oficial", "value": "Scapatici Tecnologia"},
                "backgroundImage": "assets/video-017-hercules-corona-wall/scene_8.jpg",
                "panDirection": "zoom-out"
            }
        ],
        "image_queries": {
            "scene_1.jpg": "cosmic web massive galaxy filaments hubble simulation",
            "scene_2.jpg": "gamma ray burst swift satellite fermi space",
            "scene_3.jpg": "universe large scale structure dark matter web",
            "scene_4.jpg": "gravitational wave distortion space time simulation",
            "scene_5.jpg": "cosmic microwave background inflation fluctuation planck",
            "scene_6.jpg": "distant quasar group galaxy survey sdss",
            "scene_7.jpg": "milky way galaxy isolated deep field cosmos",
            "scene_8.jpg": "deep space galaxy cluster gravitational lens webb",
            "thumbnail.jpg": "cosmic web massive glowing structure universe space"
        }
    },
    {
        "id": "video-018-strange-matter",
        "title": "Matéria Estranha: O Estado da Matéria Capaz de Transformar Todo o Universo em uma Reação em Cadeia",
        "topic": "Matéria Estranha, Strangelets, Quarks Strange, Estrelas Estranhas e o Hipotético Fim da Matéria",
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 330,
        "fps": 30,
        "vinheta_duration_frames": 90,
        "bg_music_volume": 0.12,
        "thumbnail_text": {
            "line1": "A MATÉRIA QUE DEVORA",
            "line2": "ÁTOMOS NORMAIS!",
            "subtitle": "O ENIGMA DOS STRANGELETS | SCAPATICI TECNOLOGIA"
        },
        "seo": {
            "title_options": [
                "Matéria Estranha: O Estado da Matéria Capaz de Transformar Todo o Universo em uma Reação em Cadeia",
                "A Matéria Mais Perigosa do Universo: E Se Uma Gota Disso Atingir a Terra?",
                "Strangelets: A Substância Quântica Que Pode Desintegrar Qualquer Átomo Conhecido"
            ],
            "description": "Tudo o que você toca e vê é feito de prótons e nêutrons formados apenas por dois tipos de partículas: quarks Up e quarks Down. Mas no coração hiperdenso das estrelas de nêutrons, a física quântica prevê a existência do quark Strange.\n\nNeste episódio do canal Scapatici Tecnologia, investigamos a Hipótese da Matéria Estranha de Edward Witten: um estado da matéria teoricamente mais estável do que o nosso próprio vácuo, capaz de converter qualquer átomo que encoste nele em uma reação em cadeia contagiosa e irreversível.\n\n🔔 Inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia.\n\n#ScapaticiTecnologia #MateriaEstranha #Strangelets #FisicaQuantica #EstrelaDeNeutrons #Quarks #Ciencia",
            "tags": ["scapatici tecnologia", "materia estranha", "strange matter", "strangelets", "quarks", "fisica quantica", "estrela de neutrons", "universo", "misterios do universo"]
        },
        "scenes": [
            {
                "id": "scene_1_hook",
                "type": "hook",
                "visual_theme": "strangelet_infecting_normal_matter_atomic_chain_reaction",
                "headline": "A INFECÇÃO SUBATÔMICA MAIS LETAL DA FÍSICA",
                "narration": "Tudo o que existe no universo observável, desde o seu próprio corpo até a estrela mais distante da galáxia, é feito exatamente dos mesmos blocos fundamentais: prótons e nêutrons, compostos exclusivamente por dois tipos de partículas chamadas quarks Up e quarks Down. Mas e se toda a matéria que conhecemos for apenas um estado frágil e temporário da natureza? E se existir um terceiro tipo de substância, tão perfeita e energeticamente estável que, ao encostar em um único átomo comum, ela o converte instantaneamente para a sua forma, disparando uma reação em cadeia irreversível que consumiria um planeta inteiro em minutos? Essa é a Hipótese da Matéria Estranha: o pesadelo quântico mais perturbador da física nuclear.",
                "highlight_words": ["QUARKS UP E DOWN", "MATÉRIA ESTRANHA", "REAÇÃO EM CADEIA", "PESADELO QUÂNTICO"],
                "stats": {"label": "Classificação", "value": "Estado Hipotético de Menor Energia"},
                "backgroundImage": "assets/video-018-strange-matter/scene_1.jpg",
                "panDirection": "zoom-in"
            },
            {
                "id": "scene_2_edward_witten_hypothesis",
                "type": "investigation",
                "visual_theme": "edward_witten_bodmer_strange_quark_matter_diagram",
                "headline": "A HIPÓTESE DE BODMER E EDWARD WITTEN",
                "narration": "Em 1984, o físico teórico Edward Witten, de Princeton, formalizou uma ideia que chocou a comunidade científica. Segundo os cálculos da Cromodinâmica Quântica, se você comprimir a matéria além de qualquer limite imaginável, como no centro de uma estrela de nêutrons morta, os prótons e nêutrons se dissolvem em uma sopa densa de quarks livres. Sob essa pressão esmagadora, metade dos quarks Down se transforma espontaneamente em quarks Strange, criando a chamada Matéria de Quarks Estranhos. Witten demonstrou que essa sopa pode ser o verdadeiro estado fundamental de menor energia do universo.",
                "highlight_words": ["EDWARD WITTEN", "1984", "CROMODINÂMICA QUÂNTICA", "QUARKS STRANGE"],
                "stats": {"label": "Proposição Teórica", "value": "Hipótese de Witten (1984)"},
                "backgroundImage": "assets/video-018-strange-matter/scene_2.jpg",
                "panDirection": "pan-right"
            },
            {
                "id": "scene_3_what_is_a_strangelet",
                "type": "investigation",
                "visual_theme": "microscopic_strangelet_droplet_glowing_nucleus",
                "headline": "STRANGELETS: AS GOTAS CONTAGIOSAS DO COSMOS",
                "narration": "Fragmentos microscópicos dessa substância são chamados de Strangelets: gotas ultraminúsculas e superdensas de quarks livres. Por serem mais estáveis que qualquer núcleo atômico comum, se um Strangelet entrar em contato com um átomo normal de oxigênio ou ferro, o núcleo atômico é forçado a ceder: os quarks normais caem no vale energético e se transformam em matéria estranha. O átomo vira outro Strangelet, liberando energia pura e contagiando o próximo átomo vizinho em uma avalanche imparável.",
                "highlight_words": ["STRANGELETS", "VALE ENERGÉTICO", "AVALANCHE IMPARÁVEL", "ÁTOMOS TRANSFORMADOS"],
                "stats": {"label": "Tamanho Típico", "value": "Escala Subatômica (Femtômetros)"},
                "backgroundImage": "assets/video-018-strange-matter/scene_3.jpg",
                "panDirection": "hyper-zoom"
            },
            {
                "id": "scene_4_strange_stars_collision",
                "type": "climax",
                "visual_theme": "neutron_star_collision_ejecting_strange_matter",
                "headline": "A COLISÃO DE ESTRELAS DE NÊUTRONS",
                "narration": "Se os Strangelets existem apenas nas profundezas das estrelas de nêutrons, como eles poderiam escapar para o espaço aberto? A resposta está nas Kilonovas: quando duas estrelas de nêutrons colidem em uma espiral da morte, o choque ejeta trilhões de toneladas de matéria nuclear no vácuo interestelar. Pedaços de matéria estranha poderiam estar vagando pela Via Láctea agora mesmo como projéteis silenciosos e invisíveis, acelerados a frações da velocidade da luz por campos gravitacionais titânicos.",
                "highlight_words": ["KILONOVAS", "ESPIRAL DA MORTE", "TRILHÕES DE TONELADAS", "PROJÉTEIS INVISÍVEIS"],
                "stats": {"label": "Evento de Liberação", "value": "Fusão de Estrelas de Nêutrons"},
                "backgroundImage": "assets/video-018-strange-matter/scene_4.jpg",
                "panDirection": "floating-drift"
            },
            {
                "id": "scene_5_what_if_hits_earth",
                "type": "climax",
                "visual_theme": "planet_earth_turning_into_strange_matter_sphere",
                "headline": "E SE UM STRANGELET ATINGISSE A TERRA?",
                "narration": "O cenário apocalíptico de um Strangelet atingindo a Terra é uma das simulações mais assustadoras da astrofísica. O fragmento microscópico afundaria direto para o centro do planeta devido à sua densidade infinita. Ao chegar no núcleo de ferro da Terra, a reação de conversão começaria a consumir a matéria de dentro para fora. Em questão de horas, toda a massa do nosso planeta seria condensada em uma esfera superdensa de matéria estranha com apenas cem metros de diâmetro, sem atmosfera e sem vida.",
                "highlight_words": ["CENTRO DA TERRA", "NÚCLEO DE FERRO", "CEM METROS DE DIÂMETRO", "HORAS DE REAÇÃO"],
                "stats": {"label": "Resultado Teórico", "value": "Terra Reduzida a 100 Metros"},
                "backgroundImage": "assets/video-018-strange-matter/scene_5.jpg",
                "panDirection": "dramatic-pulse"
            },
            {
                "id": "scene_6_why_we_are_still_here",
                "type": "investigation",
                "visual_theme": "lunar_surface_bombarded_by_cosmic_rays_safe",
                "headline": "A PROVA DA LUA E DOS RAIOS CÓSMICOS",
                "narration": "Mas se esse perigo é real, por que a Terra, a Lua e os outros planetas ainda estão intactos após quatro bilhões e meio de anos? Os astrofísicos apontam para a Lua como prova definitiva de segurança: por não ter atmosfera, a superfície lunar é bombardeada por raios cósmicos de altíssima energia há bilhões de anos, e nenhuma conversão em matéria estranha jamais ocorreu. Isso sugere que os Strangelets carregam uma carga elétrica positiva que repele núcleos atômicos normais sob temperaturas amenas, agindo como um escudo natural contra o contágio.",
                "highlight_words": ["PROVA DA LUA", "4,5 BILHÕES DE ANOS", "ESCUDO NATURAL", "CARGA POSITIVA"],
                "stats": {"label": "Barreira Repulsiva", "value": "Repulsão Coulombiana"},
                "backgroundImage": "assets/video-018-strange-matter/scene_6.jpg",
                "panDirection": "pan-left"
            },
            {
                "id": "scene_7_cern_and_cosmic_rays",
                "type": "technology",
                "visual_theme": "cern_alice_heavy_ion_collision_quark_gluon",
                "headline": "A CAÇADA NO GRANDE COLISOR DE HÁDRONS",
                "narration": "Experimentos no Grande Colisor de Hádrons do CERN, como o detector ALICE, colidem núcleos de chumbo para recriar o plasma de quarks e glúons primordial e medir as propriedades exatas dos quarks Strange. Até hoje, nenhum Strangelet estável foi criado em laboratório humano. A Matéria Estranha permanece como uma das fronteiras teóricas mais fascinantes e misteriosas da física de partículas moderna.",
                "highlight_words": ["CERN ALICE", "NÚCLEOS DE CHUMBO", "PLASMA DE QUARKS", "FRONTEIRA TEÓRICA"],
                "stats": {"label": "Detecção Humana", "value": "Nenhum Strangelet Livre Encontrado"},
                "backgroundImage": "assets/video-018-strange-matter/scene_7.jpg",
                "panDirection": "tilt-down"
            },
            {
                "id": "scene_8_scapatici_cta",
                "type": "cta",
                "visual_theme": "scapatici_space_observatory_community",
                "headline": "O EQUILÍBRIO DA NOSSA MATÉRIA",
                "narration": "E você, já conhecia a aterrorizante hipótese da Matéria Estranha? Acredita que as estrelas de nêutrons escondem substâncias capazes de reescrever a tabela periódica? Deixe sua teoria aqui nos comentários, compartilhe este vídeo com quem é fascinado pelos mistérios do universo, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!",
                "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SUA TEORIA", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
                "stats": {"label": "Comunidade Oficial", "value": "Scapatici Tecnologia"},
                "backgroundImage": "assets/video-018-strange-matter/scene_8.jpg",
                "panDirection": "zoom-out"
            }
        ],
        "image_queries": {
            "scene_1.jpg": "quark gluon plasma heavy ion collision cern",
            "scene_2.jpg": "neutron star interior subatomic particles simulation",
            "scene_3.jpg": "quantum subatomic particle droplet glowing energy",
            "scene_4.jpg": "neutron star collision kilonova gravitational wave",
            "scene_5.jpg": "planet core compression dense matter simulation",
            "scene_6.jpg": "moon surface craters deep space cosmos hubble",
            "scene_7.jpg": "cern particle accelerator tunnel alice detector",
            "scene_8.jpg": "star cluster glowing nebula deep space webb",
            "thumbnail.jpg": "strange matter droplet glowing subatomic space"
        }
    },
    {
        "id": "video-019-white-holes",
        "title": "Buracos Brancos: O Oposto Impossível dos Buracos Negros Onde o Tempo Corre ao Contrário",
        "topic": "Buracos Brancos, Gravidade Quântica em Loop, Pontes de Einstein-Rosen e a Origem do Big Bang",
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 330,
        "fps": 30,
        "vinheta_duration_frames": 90,
        "bg_music_volume": 0.12,
        "thumbnail_text": {
            "line1": "O OPOSTO DO",
            "line2": "BURACO NEGRO!",
            "subtitle": "O MISTÉRIO DOS BURACOS BRANCOS | SCAPATICI TECNOLOGIA"
        },
        "seo": {
            "title_options": [
                "Buracos Brancos: O Oposto Impossível dos Buracos Negros Onde o Tempo Corre ao Contrário",
                "E Se o Big Bang Foi o Nascimento de um Buraco Branco? O Enigma Que Inverte o Tempo",
                "A Matemática Que Previu os Buracos Brancos: O Que Acontece no Fim de um Buraco Negro?"
            ],
            "description": "Se um buraco negro é uma região do espaço de onde absolutamente nada consegue escapar, a matemática da Relatividade Geral de Albert Einstein possui uma solução inversa exata e perturbadora: os Buracos Brancos, regiões de onde nada consegue entrar.\n\nNeste décimo nono episódio do canal Scapatici Tecnologia, investigamos a física dos Buracos Brancos, a hipótese de ricochete quântico de Carlo Rovelli e a fascinante teoria de que o próprio nascimento do nosso universo possa ter sido a explosão de um buraco branco.\n\n🔔 Inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia.\n\n#ScapaticiTecnologia #BuracosBrancos #BuracoNegro #RelatividadeGeral #FisicaQuantica #BigBang #Ciencia",
            "tags": ["scapatici tecnologia", "buracos brancos", "white holes", "buraco negro", "relatividade geral", "einstein", "carlo rovelli", "big bang", "misterios do universo"]
        },
        "scenes": [
            {
                "id": "scene_1_hook",
                "type": "hook",
                "visual_theme": "white_hole_ejecting_blinding_matter_light_space",
                "headline": "A PORTA CÓSMICA ONDE NADA PODE ENTRAR",
                "narration": "Todo mundo sabe como funciona um buraco negro: um poço gravitacional tão implacável que nada no universo, nem mesmo a luz, consegue escapar do seu horizonte de eventos. Mas as mesmas equações matemáticas da Relatividade Geral de Albert Einstein que previram os buracos negros possuem outra solução perfeitamente válida e simétrica: os Buracos Brancos. Em um buraco branco, a física funciona exatamente ao contrário. Ele é uma fonte contínua de luz e matéria cuspida para o espaço, protegida por um horizonte de eventos onde absolutamente nada consegue entrar, não importa quão veloz ou poderoso você seja. Tentar entrar em um buraco branco exigiria mais energia do que toda a massa existente no universo observável.",
                "highlight_words": ["BURACOS BRANCOS", "SIMETRIA TEMPORAL", "NADA PODE ENTRAR", "ENERGIA INFINITA"],
                "stats": {"label": "Previsão Matemática", "value": "Solução Exata da Relatividade Geral"},
                "backgroundImage": "assets/video-019-white-holes/scene_1.jpg",
                "panDirection": "zoom-in"
            },
            {
                "id": "scene_2_time_reversal_symmetry",
                "type": "investigation",
                "visual_theme": "einstein_field_equations_time_symmetry_diagram",
                "headline": "A SIMETRIA TEMPORAL DA FÍSICA CLÁSSICA",
                "narration": "As leis fundamentais da física que governam a gravidade e o movimento não têm preferência pela direção do tempo. Se você filmar a Terra orbitando o Sol e rodar o vídeo de trás para frente, as equações de Einstein continuam perfeitamente corretas. Um buraco branco é simplesmente um buraco negro onde o tempo está correndo na direção oposta. Se a matéria colapsa para dentro em direção a uma singularidade no futuro, o buraco branco nasce de uma singularidade no passado e expele tudo o que foi engolido de volta para a realidade.",
                "highlight_words": ["DIREÇÃO DO TEMPO", "RODAR DE TRÁS PRA FRENTE", "PASSADO E FUTURO", "SINGULARIDADE INVERTIDA"],
                "stats": {"label": "Propriedade Física", "value": "Invariância por Reversão Temporal"},
                "backgroundImage": "assets/video-019-white-holes/scene_2.jpg",
                "panDirection": "pan-right"
            },
            {
                "id": "scene_3_einstein_rosen_bridges",
                "type": "investigation",
                "visual_theme": "wormhole_connecting_black_hole_to_white_hole",
                "headline": "A PONTE DE EINSTEIN-ROSEN E BURACOS DE MINHOCA",
                "narration": "Em 1935, Albert Einstein e o físico Nathan Rosen calcularam a primeira geometria matemática de um buraco de minhoca. Nessa estrutura, um buraco negro em uma região do cosmos atua como um ralo de entrada, conectado através de uma garganta do espaço-tempo a um buraco branco que atua como uma torneira de saída em outra região distante do universo, ou até mesmo em outro universo paralelo. Tudo o que é sugado pelo abismo de um lado seria expelido sob a forma de luz pura e partículas do outro lado.",
                "highlight_words": ["1935", "EINSTEIN E ROSEN", "BURACO DE MINHOCA", "RALO E TORNEIRA"],
                "stats": {"label": "Estrutura Geométrica", "value": "Ponte de Einstein-Rosen"},
                "backgroundImage": "assets/video-019-white-holes/scene_3.jpg",
                "panDirection": "hyper-zoom"
            },
            {
                "id": "scene_4_thermodynamics_problem",
                "type": "climax",
                "visual_theme": "entropy_second_law_arrow_of_time_cosmos",
                "headline": "A SEGUNDA LEI DA TERMODINÂMICA E A ENTROPIA",
                "narration": "Se os buracos brancos são matematicamente permitidos, por que os nossos telescópios nunca avistaram nenhum com certeza? O obstáculo não está na gravidade, mas na Segunda Lei da Termodinâmica. A entropia, que mede o grau de desordem do universo, só pode aumentar com o tempo. Um buraco branco pareceria diminuir a entropia localmente, expelindo matéria altamente organizada. Durante décadas, os físicos consideraram que os buracos brancos eram apenas monstros teóricos descartados pelas leis do calor e da desordem cósmica.",
                "highlight_words": ["SEGUNDA LEI", "TERMODINÂMICA", "ENTROPIA", "DESORDEM CÓSMICA"],
                "stats": {"label": "Barreira Física", "value": "Segunda Lei da Termodinâmica"},
                "backgroundImage": "assets/video-019-white-holes/scene_4.jpg",
                "panDirection": "floating-drift"
            },
            {
                "id": "scene_5_carlo_rovelli_quantum_bounce",
                "type": "technology",
                "visual_theme": "loop_quantum_gravity_planck_star_bounce_rovelli",
                "headline": "A VIRADA QUÂNTICA DE CARLO ROVELLI",
                "narration": "A revolução teórica veio com a Gravidade Quântica em Loop e o físico italiano Carlo Rovelli. Na física quântica, o espaço não é contínuo, mas feito de grânulos mínimos chamados Comprimento de Planck. Quando a matéria colapsa dentro de um buraco negro, ela não pode ser esmagada em um ponto infinitesimal infinito: ela para na barreira de Planck, formando uma Estrela de Planck que ricocheteia como uma bola elástica. Devido à dilatação extrema do tempo provocada pela gravidade, o que para a estrela leva uma fração de segundo, para nós do lado de fora leva bilhões de anos: o buraco negro eventualmente explode e se transforma em um buraco branco.",
                "highlight_words": ["CARLO ROVELLI", "GRAVIDADE QUÂNTICA EM LOOP", "ESTRELA DE PLANCK", "RICOCHETE QUÂNTICO"],
                "stats": {"label": "Teoria Moderna", "value": "Transição Buraco Negro -> Branco"},
                "backgroundImage": "assets/video-019-white-holes/scene_5.jpg",
                "panDirection": "pan-left"
            },
            {
                "id": "scene_6_dark_matter_connection",
                "type": "investigation",
                "visual_theme": "microscopic_white_hole_relicts_dark_matter",
                "headline": "ELES SÃO A MATÉRIA ESCURA QUE BUSCAMOS?",
                "narration": "Se os buracos negros primordiais formados logo após o Big Bang já tiveram tempo de ricochetear e se transformar em buracos brancos microscópicos, o universo estaria repleto de remanescentes estáveis do tamanho de um grão de poeira, mas com a massa de montanhas inteiras. Vários físicos teóricos sugerem que esses resíduos de buracos brancos não interagem com a luz, possuem gravidade intensa e poderiam ser a resposta exata para a identidade da misteriosa Matéria Escura.",
                "highlight_words": ["REMANESCENTES MICROSCÓPICOS", "GRÃO DE POEIRA", "MASSA DE MONTANHAS", "RESPOSTA DA MATÉRIA ESCURA"],
                "stats": {"label": "Massa do Remanescente", "value": "Massa de Planck (~20 microgramas)"},
                "backgroundImage": "assets/video-019-white-holes/scene_6.jpg",
                "panDirection": "dramatic-pulse"
            },
            {
                "id": "scene_7_was_the_big_bang_a_white_hole",
                "type": "climax",
                "visual_theme": "big_bang_origin_white_hole_cosmic_genesis",
                "headline": "E SE O BIG BANG FOI UM BURACO BRANCO?",
                "narration": "A hipótese mais grandiosa de todas conecta o início da nossa própria existência aos buracos brancos. Pense na definição de um buraco branco: um evento a partir do qual toda a matéria, energia e luz são expelidas instantaneamente sem que nada do lado de fora possa intervir. O Big Bang que gerou o nosso universo compartilhou exatamente essas propriedades. O nosso próprio cosmos pode ser o interior em expansão de um gigantesco buraco branco que nasceu da morte de um buraco negro em outro universo ancestral.",
                "highlight_words": ["BIG BANG", "NOSSA EXISTÊNCIA", "UNIVERSO ANCESTRAL", "NASCIMENTO DO COSMOS"],
                "stats": {"label": "Hipótese Cosmológica", "value": "Cosmologia do Big Bounce"},
                "backgroundImage": "assets/video-019-white-holes/scene_7.jpg",
                "panDirection": "tilt-down"
            },
            {
                "id": "scene_8_scapatici_cta",
                "type": "cta",
                "visual_theme": "scapatici_space_observatory_community",
                "headline": "O CICLO INFINITO DA GRAVIDADE",
                "narration": "E você, o que acha do conceito fascinante dos Buracos Brancos? Acredita que o Big Bang pode ter sido a explosão de um buraco branco ou que um dia os telescópios encontrarão um deles brilhando no céu? Deixe sua teoria aqui nos comentários, compartilhe este vídeo com quem é fascinado pelos mistérios do universo, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!",
                "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SUA TEORIA", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
                "stats": {"label": "Comunidade Oficial", "value": "Scapatici Tecnologia"},
                "backgroundImage": "assets/video-019-white-holes/scene_8.jpg",
                "panDirection": "zoom-out"
            }
        ],
        "image_queries": {
            "scene_1.jpg": "white hole glowing energy ejection deep space concept",
            "scene_2.jpg": "space time geometry einstein general relativity simulation",
            "scene_3.jpg": "wormhole tunnel connecting black hole white hole",
            "scene_4.jpg": "thermodynamics entropy cosmos deep space nebula",
            "scene_5.jpg": "loop quantum gravity spin network planck star simulation",
            "scene_6.jpg": "dark matter halos cosmic web simulation hubble",
            "scene_7.jpg": "big bang cosmic expansion glowing explosion origin webb",
            "scene_8.jpg": "deep space galaxy field pillars of creation webb",
            "thumbnail.jpg": "white hole luminous explosion center deep space"
        }
    },
    {
        "id": "video-020-hawking-radiation-paradox",
        "title": "O Paradoxo da Informação de Hawking: O Que Realmente Acontece Quando Você Cai em um Buraco Negro?",
        "topic": "Radiação Hawking, Paradoxo da Informação, Holografia Cósmica e a Batalha Entre Quântica e Gravidade",
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 330,
        "fps": 30,
        "vinheta_duration_frames": 90,
        "bg_music_volume": 0.12,
        "thumbnail_text": {
            "line1": "A INFORMAÇÃO PODE",
            "line2": "SER DESTRUÍDA?",
            "subtitle": "O PARADOXO DE HAWKING | SCAPATICI TECNOLOGIA"
        },
        "seo": {
            "title_options": [
                "O Paradoxo da Informação de Hawking: O Que Realmente Acontece Quando Você Cai em um Buraco Negro?",
                "Stephen Hawking Estava Errado? A Guerra Teórica de 40 Anos Sobre os Buracos Negros",
                "O Que Acontece com a Sua Alma Quântica Dentro de um Buraco Negro? O Paradoxo Revelado"
            ],
            "description": "Em 1974, Stephen Hawking descobriu que buracos negros não são completamente pretos: eles evaporam lentamente emitindo uma névoa quântica de calor. Mas essa descoberta desencadeou o Paradoxo da Informação, a guerra científica mais feroz da física contemporânea.\n\nNeste vigésimo episódio histórico do canal Scapatici Tecnologia, investigamos a batalha intelectual entre Stephen Hawking e Leonard Susskind: a informação quântica é destruída para sempre quando um buraco negro evapora, ou nós vivemos em um holograma cósmico?\n\n🔔 Inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia.\n\n#ScapaticiTecnologia #ParadoxoDaInformacao #StephenHawking #RadiaçaoHawking #BuracoNegro #FisicaQuantica #Ciencia",
            "tags": ["scapatici tecnologia", "paradoxo da informacao", "stephen hawking", "radiacao hawking", "buraco negro", "leonard susskind", "principio holografico", "fisica quantica", "misterios do universo"]
        },
        "scenes": [
            {
                "id": "scene_1_hook",
                "type": "hook",
                "visual_theme": "astronaut_falling_into_event_horizon_quantum_information",
                "headline": "A REGRA DE OURO QUE NADA PODE APAGAR",
                "narration": "Na mecânica quântica, existe uma lei sagrada da qual toda a física depende: a informação nunca pode ser destruída. Se você queimar um livro em uma fogueira, as cinzas, a fumaça e a radiação emitida contêm, em teoria, cada átomo e cada palavra gravada; se você tivesse um computador quântico perfeito, poderia reconstruir o livro original molécula por molécula. Mas em 1974, o brilhante físico Stephen Hawking descobriu algo que fez a física de partículas estremecer. Ele provou que os buracos negros evaporam lentamente até desaparecerem por completo, e a radiação que eles cospem parece ser puramente aleatória. Para onde foi a história de tudo o que caiu lá dentro? O Paradoxo da Informação de Hawking colocou a mecânica quântica em rota de colisão frontal contra a teoria da relatividade geral de Einstein.",
                "highlight_words": ["INFORMAÇÃO NUNCA DESTRUÍDA", "1974", "STEPHEN HAWKING", "ROTA DE COLISÃO"],
                "stats": {"label": "Princípio Quântico", "value": "Unitariedade da Mecânica Quântica"},
                "backgroundImage": "assets/video-020-hawking-radiation-paradox/scene_1.jpg",
                "panDirection": "zoom-in"
            },
            {
                "id": "scene_2_hawking_radiation_mechanism",
                "type": "investigation",
                "visual_theme": "quantum_vacuum_fluctuation_virtual_particles_event_horizon",
                "headline": "COMO UM BURACO NEGRO PODE EVAPORAR?",
                "narration": "O mecanismo de Hawking acontece exatamente na borda do abismo: o horizonte de eventos. Na escala microscópica do vácuo quântico, pares de partículas e antipartículas virtuais estão constantemente brotando do nada e se aniquilando. Mas quando esse par nasce na beira do horizonte de eventos, uma das partículas pode cair dentro do buraco negro com energia negativa, enquanto a outra partícula escapa para o espaço livre com energia positiva. Para quem olha de fora, o buraco negro parece emitir uma radiação térmica fraca e perde massa continuamente, encolhendo ao longo de eons.",
                "highlight_words": ["HORIZONTE DE EVENTOS", "PARTÍCULAS VIRTUAIS", "ENERGIA NEGATIVA", "RADIAÇÃO HAWKING"],
                "stats": {"label": "Descoberta Teórica", "value": "Radiação Hawking (1974)"},
                "backgroundImage": "assets/video-020-hawking-radiation-paradox/scene_2.jpg",
                "panDirection": "pan-right"
            },
            {
                "id": "scene_3_the_black_hole_war",
                "type": "climax",
                "visual_theme": "susskind_vs_hawking_intellectual_battle_black_hole_war",
                "headline": "A GUERRA DOS BURACOS NEGROS DE TRINTA ANOS",
                "narration": "Quando Hawking afirmou que a informação desaparecia para sempre no fim da evaporação, o físico Leonard Susskind e o Prêmio Nobel Gerard 't Hooft entraram em choque. Se a informação pudesse ser destruída em um buraco negro, as probabilidades na física deixariam de somar cem por cento: o determinismo da ciência seria desmantelado. Teve início a lendária Guerra dos Buracos Negros: três décadas de debates intelectuais fervorosos para provar que Stephen Hawking estava cometendo um erro sutil em seus cálculos pioneiros.",
                "highlight_words": ["LEONARD SUSSKIND", "GERARD 'T HOOFT", "GUERRA DOS BURACOS NEGROS", "DETERMINISMO"],
                "stats": {"label": "Duração do Debate", "value": "30 Anos de Batalha Teórica"},
                "backgroundImage": "assets/video-020-hawking-radiation-paradox/scene_3.jpg",
                "panDirection": "hyper-zoom"
            },
            {
                "id": "scene_4_black_hole_complementarity",
                "type": "investigation",
                "visual_theme": "black_hole_complementarity_dual_observer_reality",
                "headline": "A COMPLEMENTARIDADE: DOIS PONTOS DE VISTA REAIS",
                "narration": "Para salvar a mecânica quântica, Susskind propôs a Complementaridade dos Buracos Negros. Para um observador que fica do lado de fora, ele nunca vê você cruzar o horizonte: ele vê você sendo esticado, desacelerado pela gravidade e incinerado na superfície quente do buraco negro, com a sua informação codificada na casca externa. Mas do seu próprio ponto de vista ao cair, você cruza o horizonte sem sentir nada de estranho imediatamente. Ambas as descrições são rigorosamente verdadeiras para cada observador, sem que nenhum paradoxo viole as leis físicas.",
                "highlight_words": ["COMPLEMENTARIDADE", "DOIS PONTOS DE VISTA", "INCINERADO NA SUPERFÍCIE", "AMBAS VERDADEIRAS"],
                "stats": {"label": "Conceito Chave", "value": "Complementaridade de Susskind"},
                "backgroundImage": "assets/video-020-hawking-radiation-paradox/scene_4.jpg",
                "panDirection": "floating-drift"
            },
            {
                "id": "scene_5_the_holographic_principle",
                "type": "technology",
                "visual_theme": "holographic_principle_ads_cft_maldacena",
                "headline": "O PRINCÍPIO HOLOGRÁFICO E JUAN MALDACENA",
                "narration": "A solução definitiva ganhou forma com o Princípio Holográfico e a correspondência do físico Juan Maldacena. Eles provaram que toda a física tridimensional do interior de um buraco negro pode ser perfeitamente mapeada como um holograma na sua superfície bidimensional externa. Em 2004, após trinta anos de disputa, Stephen Hawking admitiu publicamente a sua derrota em uma conferência em Dublin, reconhecendo que a informação quântica é de fato preservada e codificada de volta na radiação Hawking ao longo do tempo.",
                "highlight_words": ["PRINCÍPIO HOLOGRÁFICO", "JUAN MALDACENA", "2004 EM DUBLIN", "HAWKING ADMITIU A DERROTA"],
                "stats": {"label": "Desfecho Histórico", "value": "Hawking Reconhece Preservação (2004)"},
                "backgroundImage": "assets/video-020-hawking-radiation-paradox/scene_5.jpg",
                "panDirection": "pan-left"
            },
            {
                "id": "scene_6_the_firewall_paradox",
                "type": "investigation",
                "visual_theme": "firewall_paradox_polchinski_burning_horizon",
                "headline": "O DILEMA DO MURO DE FOGO DE POLCHINSKI",
                "narration": "Mas quando a física parecia pacificada, em 2012 os físicos liderados por Joseph Polchinski lançaram uma nova bomba: o Paradoxo do Muro de Fogo. Eles demonstraram que, para a informação escapar da radiação de Hawking sem quebrar o entrelaçamento quântico, o horizonte de eventos precisaria abrigar uma muralha caótica de partículas de energia infinita que vaporizaria qualquer astronauta antes mesmo de entrar. O mistério ainda queima no topo da pesquisa contemporânea.",
                "highlight_words": ["2012", "JOSEPH POLCHINSKI", "MURO DE FOGO", "VAPORIZAÇÃO INSTANTÂNEA"],
                "stats": {"label": "Novo Paradoxo", "value": "AMPS Firewall (2012)"},
                "backgroundImage": "assets/video-020-hawking-radiation-paradox/scene_6.jpg",
                "panDirection": "dramatic-pulse"
            },
            {
                "id": "scene_7_quantum_gravity_future",
                "type": "climax",
                "visual_theme": "quantum_entanglement_wormholes_er_epr_conjecture",
                "headline": "ER IGUAL A EPR: O ESPAÇO TECIDO POR ENTRELAÇAMENTO",
                "narration": "A resposta final pode ser a mais profunda já concebida: a conjectura ER igual a EPR, proposta por Leonard Susskind e Juan Maldacena. Ela afirma que os buracos de minhoca na relatividade geral são equivalentes ao entrelaçamento quântico entre partículas. O próprio tecido do espaço-tempo que une o universo pode ser mantido unido por fios invisíveis de informação quântica. Se isso for verdade, os buracos negros não são monstros destruidores, mas os próprios teares que costuram a realidade.",
                "highlight_words": ["ER = EPR", "ENTRELAÇAMENTO QUÂNTICO", "BURACOS DE MINHOCA", "TEARES DA REALIDADE"],
                "stats": {"label": "Fronteira Máxima", "value": "Espaço-Tempo Emergente (ER = EPR)"},
                "backgroundImage": "assets/video-020-hawking-radiation-paradox/scene_7.jpg",
                "panDirection": "tilt-down"
            },
            {
                "id": "scene_8_scapatici_cta",
                "type": "cta",
                "visual_theme": "scapatici_space_observatory_community",
                "headline": "A ETERNIDADE DA SUA INFORMAÇÃO",
                "narration": "E você, o que acha desse duelo épico entre a gravidade de Einstein e a mecânica quântica de Hawking? Conforta saber que, de acordo com as leis fundamentais do universo, a sua informação jamais poderá ser apagada do cosmos? Deixe sua teoria aqui nos comentários, compartilhe este vídeo com quem é fascinado pelos mistérios do universo, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!",
                "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SUA TEORIA", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
                "stats": {"label": "Comunidade Oficial", "value": "Scapatici Tecnologia"},
                "backgroundImage": "assets/video-020-hawking-radiation-paradox/scene_8.jpg",
                "panDirection": "zoom-out"
            }
        ],
        "image_queries": {
            "scene_1.jpg": "event horizon supermassive black hole astronaut space",
            "scene_2.jpg": "quantum vacuum virtual particles hawking radiation diagram",
            "scene_3.jpg": "black hole accretion disk relativistic jet chandra",
            "scene_4.jpg": "black hole event horizon time dilation gravitational lensing",
            "scene_5.jpg": "holographic principle cosmic hologram surface projection",
            "scene_6.jpg": "firewall quantum energy barrier black hole simulation",
            "scene_7.jpg": "quantum entanglement wormhole er epr space time web",
            "scene_8.jpg": "deep space starry universe cosmic web pillars of creation",
            "thumbnail.jpg": "black hole hawking radiation glowing quantum horizon"
        }
    }
]

def _rotate_log_if_large(max_mb: float = 5.0):
    """Mantém os arquivos de log sob controle evitando consumo excessivo de disco."""
    for log_name in ["autopilot.log", "autopilot_runner.log", "tiktok_runner.log"]:
        lp = os.path.join(PROJECT_DIR, "pipeline", log_name)
        try:
            if os.path.exists(lp) and os.path.getsize(lp) > max_mb * 1024 * 1024:
                with open(lp, "rb") as f:
                    f.seek(-int(1.5 * 1024 * 1024), os.SEEK_END)
                    tail = f.read()
                with open(lp, "wb") as f:
                    f.write(b"[LOG ROTATED - PRESERVING RECENT TAIL]\n" + tail)
        except Exception:
            pass


def _run_cmd_unattended(cmd: str, retries: int = 1, retry_delay: int = 12):
    """Executa comando sem permitir travamentos OAuth interativos e com retry opcional."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "AUTOPILOT_UNATTENDED": "1"}
    last_code = 1
    for attempt in range(1, retries + 1):
        log(f"> Executando (tentativa {attempt}/{retries}): {cmd}")
        res = subprocess.run(cmd, shell=True, cwd=PROJECT_DIR, env=env)
        if res.returncode == 0:
            return True
        last_code = res.returncode
        if attempt < retries:
            log(f"⚠️ Comando retornou código {last_code}. Tentando novamente em {retry_delay}s...")
            time.sleep(retry_delay)
    raise RuntimeError(f"Comando falhou com código {last_code}: {cmd}")


def _get_ordered_queue(state: dict) -> list:
    """Retorna todos os projetos (catálogo + fila dinâmica), reabastecendo 7 dias proativamente se < 3 pendentes."""
    completed_ids = set(state.get("completed_projects", []))
    from trend_replenisher import load_generated_queue, replenish_weekly_queue

    generated_queue = load_generated_queue()
    all_projects = list(CATALOGUE) + list(generated_queue)
    pending = [p for p in all_projects if p["id"] not in completed_ids]

    if len(pending) < 3:
        log(f"📡 Estoque de pautas baixo ({len(pending)} restante(s)). Lendo tendências para garantir 7 dias cheios...")
        existing_catalogue_ids = {p["id"] for p in CATALOGUE}
        generated_queue = replenish_weekly_queue(completed_ids, existing_catalogue_ids, days=7)
        all_projects = list(CATALOGUE) + list(generated_queue)
        pending = [p for p in all_projects if p["id"] not in completed_ids]

    return pending


def prepare_project_assets_and_render(target_project: dict, state: dict):
    """Garante roteiro, 100% das mídias (com fallback procedural anti-404), TTS e renderização 16:9 + 9:16."""
    from media.fallback_visuals import is_valid_image, generate_cosmic_artwork

    project_id = target_project["id"]
    project_dir = os.path.join(PROJECTS_BASE, project_id)
    assets_dir = os.path.join(project_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    # 1. Salva script.json
    script_path = os.path.join(project_dir, "script.json")
    script_data = {k: v for k, v in target_project.items() if k != "image_queries"}
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2, ensure_ascii=False)
    log(f"📄 Roteiro estruturado salvo em: {script_path}")

    # 2. Download e enquadramento de imagens da NASA com fallback procedural garantido
    used_urls = set(state.get("used_image_urls", []))
    queries = dict(target_project.get("image_queries", {}))
    # Garante que toda cena referenciada no roteiro tenha entrada em queries
    for idx, sc in enumerate(target_project.get("scenes", [])):
        bg = sc.get("backgroundImage", "")
        if bg and not bg.startswith("http"):
            fname = os.path.basename(bg)
            queries.setdefault(fname, sc.get("visual_theme", "deep space cosmos nasa"))
    queries.setdefault("thumbnail.jpg", "deep space glowing nebula cosmos nasa")

    log(f"🔭 Validando/obtendo {len(queries)} mídias visuais para '{project_id}'...")
    for filename, query in queries.items():
        out_dest = os.path.join(project_dir, filename) if filename.startswith("thumbnail") else os.path.join(assets_dir, filename)
        if not is_valid_image(out_dest):
            downloaded = False
            log(f"   - Baixando {filename} (query: {query})...")
            url = get_nasa_image_url(query, used_urls)
            if url:
                try:
                    download_and_crop(url, out_dest)
                    downloaded = is_valid_image(out_dest)
                except Exception as dl_err:
                    log(f"     ⚠️ Erro no download ({dl_err}). Acionando gerador visual procedural...")
            if not downloaded:
                generate_cosmic_artwork(out_dest, seed_key=f"{project_id}_{filename}_{query}")
                log(f"     🎨 Arte espacial procedural 1080p gerada como fallback seguro: {filename}")
            if filename.startswith("thumbnail"):
                render_thumbnail_overlay(out_dest, target_project)
                log(f"     🎨 Título estilizado aplicado na thumbnail: {filename}")
            else:
                log(f"     ✅ Mídia validada com sucesso: {filename}")
        else:
            log(f"   - Mídia íntegra já existente: {filename}")

    state["used_image_urls"] = list(used_urls)[-400:]
    save_state(state)

    # 3. Geração de Voz Neural com Edge-TTS (verifica também audio_shorts.mp3)
    if not os.path.exists(os.path.join(project_dir, "audio.mp3")) or not os.path.exists(os.path.join(project_dir, "audio_shorts.mp3")):
        log("🎙️ Sintetizando narração neural e extraindo timings de legendas...")
        _run_cmd_unattended(f"node pipeline/orchestrator.js tts {project_id}", retries=2, retry_delay=8)
    else:
        log("🎙️ Áudios neurais já existentes. Pulando etapa TTS.")

    # 4. Renderização Vídeo Longo (16:9)
    if not os.path.exists(os.path.join(project_dir, "output_16x9.mp4")):
        log("🎬 Renderizando vídeo longo oficial 1080p (16:9)...")
        _run_cmd_unattended(f"node pipeline/orchestrator.js render {project_id} 16x9", retries=2, retry_delay=10)
    else:
        log("🎬 Vídeo 16:9 já renderizado. Pulando etapa 16:9.")

    # 5. Renderização Shorts / Reels / TikTok (9:16 Denso)
    if not os.path.exists(os.path.join(project_dir, "output_shorts.mp4")):
        log("📱 Renderizando versão vertical densa com Ambient Canvas (9:16)...")
        _run_cmd_unattended(f"node pipeline/orchestrator.js render {project_id} shorts", retries=2, retry_delay=10)
    else:
        log("📱 Vídeo vertical (9:16) já renderizado. Pulando etapa Shorts.")


def run_daily_production(prepare_only: bool = False):
    _rotate_log_if_large()
    log("=" * 60)
    log("🚀 SIMPLE-TUBE AUTOPILOT: INICIANDO ROTINA DIÁRIA (ARQUITETURA RESILIENTE)")
    log("=" * 60)

    today_str = datetime.date.today().isoformat()
    state = load_state()

    pending = _get_ordered_queue(state)
    if not pending:
        log("❌ Não foi possível obter projetos pendentes mesmo após leitura de tendências.")
        return

    if prepare_only:
        nxt = pending[0]
        log(f"🛠️ MODO PRE-RENDER: Preparando antecipadamente '{nxt['id']}'...")
        prepare_project_assets_and_render(nxt, state)
        log(f"✅ Pre-render concluído para '{nxt['id']}'!")
        return

    if state.get("last_run_date") == today_str:
        log(f"✅ O conteúdo de hoje ({today_str}) já foi publicado anteriormente.")
        # Aproveita para pré-renderizar o episódio de amanhã caso ainda não esteja pronto
        if pending:
            try:
                log(f"⚡ Garantindo buffer pré-renderizado para amanhã: {pending[0]['id']}...")
                prepare_project_assets_and_render(pending[0], state)
            except Exception as pe:
                log(f"⚠️ Aviso no pré-render antecipado: {pe}")
        return

    target_project = pending[0]
    project_id = target_project["id"]
    project_dir = os.path.join(PROJECTS_BASE, project_id)
    log(f"🎯 Projeto Selecionado para Hoje ({today_str}): {project_id} - '{target_project['title']}'")

    # Prepara mídias, áudio e renders (16:9 + Shorts denso)
    prepare_project_assets_and_render(target_project, state)

    # 6. Publicação isolada por plataforma (nenhuma plataforma bloqueia as demais)
    platform_results = {}

    # 6.1 YouTube 16:9
    yt_16x9_info = os.path.join(project_dir, "youtube_16x9_info.json")
    if os.path.exists(yt_16x9_info):
        log("📤 YouTube 16:9 já publicado anteriormente. Pulando para evitar duplicata.")
        platform_results["youtube_16x9"] = True
    else:
        try:
            log("📤 Publicando vídeo longo no YouTube (16:9)...")
            _run_cmd_unattended(f"node pipeline/orchestrator.js publish {project_id} public", retries=2, retry_delay=15)
            platform_results["youtube_16x9"] = True
        except Exception as e:
            log(f"❌ Falha isolada no YouTube 16:9: {e}")
            platform_results["youtube_16x9"] = False

    # 6.2 YouTube Shorts
    yt_shorts_info = os.path.join(project_dir, "youtube_shorts_info.json")
    if os.path.exists(yt_shorts_info):
        log("📤 YouTube Shorts já publicado anteriormente. Pulando.")
        platform_results["youtube_shorts"] = True
    else:
        try:
            log("📤 Publicando YouTube Shorts (formato vertical denso)...")
            _run_cmd_unattended(f"node pipeline/orchestrator.js publish-shorts {project_id} public", retries=2, retry_delay=15)
            platform_results["youtube_shorts"] = True
        except Exception as e:
            log(f"❌ Falha isolada no YouTube Shorts: {e}")
            platform_results["youtube_shorts"] = False

    # 6.3 Instagram Reels
    insta_info = os.path.join(project_dir, "instagram_info.json")
    if os.path.exists(insta_info):
        log("📸 Instagram Reels já publicado anteriormente. Pulando.")
        platform_results["instagram"] = True
    else:
        try:
            log("📸 Publicando no Instagram Reels e fixando comentário com link...")
            _run_cmd_unattended(f"node pipeline/orchestrator.js instagram {project_id}", retries=2, retry_delay=15)
            platform_results["instagram"] = True
        except Exception as e:
            log(f"❌ Falha isolada no Instagram Reels: {e}")
            platform_results["instagram"] = False

    # 6.4 TikTok (Slot 09h)
    tiktok_session = os.path.join(PROJECT_DIR, "pipeline", "publishing", "tiktok_session.json")
    tiktok_info = os.path.join(project_dir, "tiktok_info.json")
    if os.path.exists(tiktok_session):
        if os.path.exists(tiktok_info):
            log("🎵 TikTok (Slot 09h) já publicado anteriormente. Pulando.")
            platform_results["tiktok"] = True
        else:
            try:
                log("🎵 Publicando no TikTok (Slot 09h)...")
                _run_cmd_unattended(f"node pipeline/orchestrator.js tiktok {project_id}", retries=2, retry_delay=10)
                platform_results["tiktok"] = True
            except Exception as te:
                log(f"⚠️ Falha isolada no TikTok: {te}")
                platform_results["tiktok"] = False

    # Salva status detalhado por plataforma
    core_ok = platform_results.get("youtube_16x9", False) and platform_results.get("youtube_shorts", False) and platform_results.get("instagram", False)
    if core_ok:
        state["last_run_date"] = today_str
        if project_id not in state["completed_projects"]:
            state["completed_projects"].append(project_id)
        save_state(state)
        log("=" * 60)
        log(f"🎉 CICLO DIÁRIO CONCLUÍDO COM SUCESSO ABSOLUTO: {project_id} ({today_str})")
        log("=" * 60)

        # Pré-renderiza o episódio de AMANHÃ em background imediato para publicar pontualmente às 09:00!
        next_pending = [p for p in pending if p["id"] != project_id]
        if next_pending:
            try:
                log(f"⚡ BUFFER PROATIVO: Pré-renderizando o episódio de amanhã ({next_pending[0]['id']})...")
                prepare_project_assets_and_render(next_pending[0], state)
                log(f"✅ Episódio de amanhã ({next_pending[0]['id']}) já pronto para upload imediato às 09:00!")
            except Exception as pe:
                log(f"⚠️ Aviso no buffer antecipado de amanhã (não afeta hoje): {pe}")
    else:
        save_state(state)
        failed = [k for k, v in platform_results.items() if not v]
        log(f"⚠️ Ciclo parcial concluído ({platform_results}). Plataformas com falha para reprocessamento: {failed}")
        raise RuntimeError(f"Falha parcial nas plataformas: {failed}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simple-Tube Daily Autopilot")
    parser.add_argument("--prepare-only", action="store_true", help="Apenas prepara mídias e renderiza o próximo episódio sem publicar")
    args = parser.parse_args()
    try:
        run_daily_production(prepare_only=args.prepare_only)
    except Exception as e:
        log(f"❌ [ERRO CRÍTICO NO AUTOPILOT]: {e}")
        sys.exit(1)
