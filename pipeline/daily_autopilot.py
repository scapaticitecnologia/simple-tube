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
from PIL import Image

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

def get_nasa_image_url(query):
    url = f"https://images-api.nasa.gov/search?q={urllib.parse.quote(query)}&media_type=image"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            items = data.get("collection", {}).get("items", [])
            for item in items[:8]:
                href = item.get("href")
                m_req = urllib.request.Request(href, headers={"User-Agent": "Mozilla/5.0"})
                try:
                    with urllib.request.urlopen(m_req, timeout=15) as m_resp:
                        assets = json.loads(m_resp.read().decode())
                        candidates = [a for a in assets if not a.endswith(".tif") and not a.endswith(".tiff") and a.lower().endswith(".jpg")]
                        for pref in ["~large.jpg", "~orig.jpg", "~medium.jpg"]:
                            for c in candidates:
                                if pref in c:
                                    return c
                        if candidates:
                            return candidates[0]
                except Exception:
                    continue
    except Exception as e:
        log(f"⚠️ Erro ao buscar imagem NASA ({query}): {e}")
    return None

def download_and_crop(url, out_path, target_width=1920, target_height=1080):
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
    }
]

def run_daily_production():
    log("=" * 60)
    log("🚀 SIMPLE-TUBE AUTOPILOT: INICIANDO ROTINA DIÁRIA")
    log("=" * 60)
    
    today_str = datetime.date.today().isoformat()
    state = load_state()
    
    if state.get("last_run_date") == today_str:
        log(f"✅ O conteúdo de hoje ({today_str}) já foi produzido e publicado com sucesso anteriormente. Encerrando execução.")
        return

    completed_ids = set(state.get("completed_projects", []))
    
    # Encontra o próximo tema do catálogo ainda não publicado
    target_project = None
    for p in CATALOGUE:
        if p["id"] not in completed_ids:
            target_project = p
            break
            
    if not target_project:
        log("ℹ️ Todos os projetos do catálogo foram concluídos. Adicione novos projetos ao CATALOGUE.")
        return

    project_id = target_project["id"]
    log(f"🎯 Projeto Selecionado: {project_id} - '{target_project['title']}'")
    
    project_dir = os.path.join(PROJECTS_BASE, project_id)
    assets_dir = os.path.join(project_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    # 1. Salva script.json
    script_path = os.path.join(project_dir, "script.json")
    script_data = {k: v for k, v in target_project.items() if k != "image_queries"}
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2, ensure_ascii=False)
    log(f"📄 Roteiro estruturado salvo em: {script_path}")
    
    # 2. Download e enquadramento de imagens da NASA
    queries = target_project.get("image_queries", {})
    log(f"🔭 Obtendo {len(queries)} mídias em alta resolução da NASA...")
    for filename, query in queries.items():
        out_dest = os.path.join(project_dir, filename) if filename.startswith("thumbnail") else os.path.join(assets_dir, filename)
        if not os.path.exists(out_dest):
            log(f"   - Baixando {filename} (query: {query})...")
            url = get_nasa_image_url(query)
            if not url:
                url = get_nasa_image_url("deep space galaxy hubble")
            if url:
                download_and_crop(url, out_dest)
                log(f"     ✅ Salvo com sucesso: {filename}")
            else:
                log(f"     ⚠️ Falha ao obter URL para {query}")
        else:
            log(f"   - Mídia já existente: {filename}")

    # 3. Geração de Voz Neural com Edge-TTS
    log("🎙️ Sintetizando narração neural e extraindo timings de legendas...")
    run_cmd(f"node pipeline/orchestrator.js tts {project_id}")

    # 4. Renderização Vídeo Longo (16:9)
    log("🎬 Renderizando vídeo longo oficial 1080p (16:9)...")
    run_cmd(f"node pipeline/orchestrator.js render {project_id} 16x9")

    # 5. Renderização Shorts / Reels (9:16)
    log("📱 Renderizando versão vertical com Ambient Canvas (9:16)...")
    run_cmd(f"node pipeline/orchestrator.js render {project_id} shorts")

    # 6. Publicação no YouTube (Vídeo Longo)
    log("📤 Publicando vídeo longo no canal Scapatici Tecnologia no YouTube...")
    run_cmd(f"node pipeline/orchestrator.js publish {project_id} public")

    # 7. Publicação no YouTube Shorts
    log("📤 Publicando YouTube Shorts...")
    run_cmd(f"node pipeline/orchestrator.js publish-shorts {project_id} public")

    # 8. Publicação no Instagram Reels (com primeiro comentário contendo o link do YouTube)
    log("📸 Publicando no Instagram Reels e fixando comentário com o link...")
    run_cmd(f"node pipeline/orchestrator.js instagram {project_id}")

    # Atualiza estado de execução
    state["last_run_date"] = today_str
    state["completed_projects"].append(project_id)
    save_state(state)
    
    log("=" * 60)
    log(f"🎉 CICLO DIÁRIO CONCLUÍDO COM SUCESSO ABSOLUTO: {project_id} ({today_str})")
    log("=" * 60)

if __name__ == "__main__":
    try:
        run_daily_production()
    except Exception as e:
        log(f"❌ [ERRO CRÍTICO NO AUTOPILOT]: {e}")
        sys.exit(1)
