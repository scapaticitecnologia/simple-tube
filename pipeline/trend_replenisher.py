"""
Simple-Tube Trend Discovery & 7-Day Content Queue Replenisher
Lê tendências reais em feeds científicos/tecnológicos (NASA, Phys.org, Space.com,
Google News Ciência/Tecnologia PT-BR e Google Trends BR) sempre que a lista de
publicação esgota e preenche automaticamente uma nova grade de 7 dias para:
  - Autopilot 09h (YouTube 16:9 + YouTube Shorts + Instagram Reels + TikTok)
  - TikTok Slots Exclusivos 16h e 20h (Mini-documentários verticais 1m40s+)
"""

import os
import re
import json
import html
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_QUEUE_FILE = os.path.join(PIPELINE_DIR, "generated_queue.json")
GENERATED_TIKTOK_QUEUE_FILE = os.path.join(PIPELINE_DIR, "generated_tiktok_queue.json")
TRENDS_SNAPSHOT_FILE = os.path.join(PIPELINE_DIR, "trends_snapshot.json")

RSS_FEEDS = [
    ("NASA Breaking", "https://www.nasa.gov/news-release/feed/"),
    ("Phys.org Space", "https://phys.org/rss-feed/space-news/"),
    ("Space.com", "https://www.space.com/feeds/all"),
    ("Google News Ciência BR", "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=pt-BR&gl=BR&ceid=BR:pt-419"),
    ("Google News Tecnologia BR", "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=pt-BR&gl=BR&ceid=BR:pt-419"),
    ("Google Trends BR", "https://trends.google.com/trending/rss?geo=BR"),
]


def _clean_text(raw: str) -> str:
    if not raw:
        return ""
    text = html.unescape(raw)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_live_trends(max_per_feed: int = 8) -> list:
    """Coleta manchetes reais em alta nos feeds públicos de ciência, astronomia e tecnologia."""
    trends = []
    for source_name, url in RSS_FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw_xml = resp.read()
            root = ET.fromstring(raw_xml)
            for item in root.findall(".//item")[:max_per_feed]:
                title_el = item.find("title")
                desc_el = item.find("description")
                link_el = item.find("link")
                title = _clean_text(title_el.text if title_el is not None else "")
                desc = _clean_text(desc_el.text if desc_el is not None else "")
                link = _clean_text(link_el.text if link_el is not None else "")
                if title:
                    trends.append({
                        "source": source_name,
                        "title": title,
                        "summary": desc[:280],
                        "link": link,
                    })
        except Exception as e:
            print(f"[TRENDS] ⚠️ Aviso ao ler feed {source_name}: {e}", flush=True)

    snapshot = {
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "count": len(trends),
        "items": trends,
    }
    try:
        with open(TRENDS_SNAPSHOT_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return trends


def _next_video_number(completed_ids: set, existing_queue_ids: set) -> int:
    max_num = 20
    all_ids = set(completed_ids) | set(existing_queue_ids)
    projects_dir = os.path.join(PROJECT_DIR, "projects")
    if os.path.isdir(projects_dir):
        all_ids.update(os.listdir(projects_dir))
    for pid in all_ids:
        m = re.match(r"^video-(\d+)-", pid)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return max_num + 1


def _build_scene(sid, stype, visual_theme, headline, narration, highlights, stat_label, stat_val, img_path, pan):
    return {
        "id": sid,
        "type": stype,
        "visual_theme": visual_theme,
        "headline": headline,
        "narration": narration,
        "highlight_words": highlights,
        "stats": {"label": stat_label, "value": stat_val},
        "backgroundImage": img_path,
        "panDirection": pan,
    }


def _cta_scene(project_id: str, headline: str, intro_hook_question: str, stats_value: str = "Scapatici Tecnologia"):
    return _build_scene(
        "scene_8_scapatici_cta",
        "cta",
        "scapatici_space_observatory_community",
        headline,
        (
            f"{intro_hook_question} "
            "Deixe a sua teoria aqui nos comentários, compartilhe este vídeo com quem é fascinado pelos mistérios do universo, "
            "inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!"
        ),
        ["SCAPATICI TECNOLOGIA", "DEIXE SEU COMENTÁRIO", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
        "Comunidade Oficial",
        stats_value,
        f"assets/{project_id}/scene_8.jpg",
        "zoom-out",
    )


def _assemble_episode(blueprint: dict, num: int, matched_trend: dict | None = None) -> dict:
    slug = blueprint["slug"]
    project_id = f"video-{num:03d}-{slug}"
    pan_cycle = ["zoom-in", "pan-right", "pan-left", "hyper-zoom", "dramatic-pulse", "floating-drift", "tilt-down"]

    scenes = []
    for idx, act in enumerate(blueprint["acts"]):
        pan = pan_cycle[idx % len(pan_cycle)]
        stype = act.get("type", "hook" if idx == 0 else ("climax" if idx == 5 else "investigation"))
        narration = act["narration"]
        if idx == 0 and matched_trend:
            narration = (
                f"Novas notícias científicas e observações espaciais voltaram a colocar este tema no centro das atenções em todo o mundo. "
                + narration
            )
        scenes.append(
            _build_scene(
                f"scene_{idx + 1}_{act['key']}",
                stype,
                f"{slug}_{act['key']}",
                act["headline"],
                narration,
                act["highlights"],
                act["stat_label"],
                act["stat_value"],
                f"assets/{project_id}/scene_{idx + 1}.jpg",
                pan,
            )
        )

    scenes.append(_cta_scene(project_id, blueprint["cta_headline"], blueprint["cta_question"]))

    image_queries = {}
    queries_list = list(blueprint["queries"])
    while len(queries_list) < 8:
        queries_list.append("deep space starry universe pillars of creation webb")
    for idx, q in enumerate(queries_list[:8]):
        image_queries[f"scene_{idx + 1}.jpg"] = q
    image_queries["thumbnail.jpg"] = blueprint["thumb_query"]

    # Garante que a narração vertical (Shorts / Reels / TikTok) tenha formato mini-doc rico (~240-300 palavras / ~1m40s)
    shorts_narration = blueprint["shorts_narration"].strip()
    if len(shorts_narration.split()) < 235:
        extra_acts = " ".join(s["narration"] for s in scenes[1:5])
        shorts_narration = (
            f"{scenes[0]['narration']} {extra_acts} "
            "A investigação completa com todos os detalhes e implicações cósmicas está no vídeo principal do YouTube: "
            "acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
        )

    title = blueprint["title"]
    if len(title) > 100:
        title = title[:97].rsplit(" ", 1)[0].rstrip(":,- ")

    trend_note = ""
    if matched_trend:
        trend_note = f"\n🔎 Pauta em destaque nas tendências ({matched_trend['source']}): {matched_trend['title']}\n"

    description = (
        f"{blueprint['summary']}\n"
        f"{trend_note}\n"
        "Neste episódio do canal Scapatici Tecnologia, mergulhamos com rigor científico e dados reais dos observatórios espaciais neste enigma do cosmos.\n\n"
        "🔔 Inscreva-se no canal Scapatici Tecnologia para novos documentários todos os dias!\n\n"
        + " ".join(f"#{t.replace(' ', '')}" for t in blueprint["tags"][:8])
    )

    return {
        "id": project_id,
        "slug": slug,
        "title": title,
        "topic": blueprint["topic"],
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 320,
        "fps": 30,
        "vinheta_duration_frames": 90,
        "bg_music_volume": 0.12,
        "trend_context": matched_trend or {"source": "Curadoria Científica Scapatici", "title": blueprint["title"]},
        "thumbnail_text": blueprint["thumbnail_text"],
        "seo": {
            "title_options": [title] + blueprint.get("alt_titles", []),
            "description": description,
            "tags": blueprint["tags"],
        },
        "shorts_narration": shorts_narration,
        "scenes": scenes,
        "image_queries": image_queries,
    }


# Banco profundo de pautas de Astrofísica, Física Quântica e Tecnologia de Fronteira
# Cada tópico tem 7 atos detalhados (+ CTA = 8 cenas 16:9) + narração longa vertical (~270 palavras / ~1m45s)
DEEP_TREND_BANK = [
    {
        "slug": "voyager-interstellar-edge",
        "keywords": ["voyager", "interstellar", "light day", "heliopause", "sonda"],
        "title": "Voyager 1 a Um Dia-Luz da Terra: O Que Ela Descobriu na Parede de Fogo do Sistema Solar",
        "alt_titles": [
            "O Muro de Plasma de 50 Mil Graus Que a Voyager 1 Atravessou Fora do Sistema Solar",
            "A 26 Bilhões de Km: O Último Mistério da Sonda Voyager 1 no Espaço Interestelar"
        ],
        "topic": "Sonda Voyager 1, Heliopausa, Espaço Interestelar e a Parede de Plasma Solar",
        "summary": "A mais de 25 bilhões de quilômetros da Terra, a Voyager 1 alcança a marca histórica de um dia-luz de distância — onde um único sinal de rádio leva 24 horas para ir e mais 24 para voltar.",
        "tags": ["scapatici tecnologia", "voyager 1", "nasa", "espaco interestelar", "astronomia", "sondas espaciais", "universo", "ciencia"],
        "thumbnail_text": {"line1": "1 DIA-LUZ", "line2": "DA TERRA!", "subtitle": "O SEGREDO QUE A VOYAGER 1 ENCONTROU | SCAPATICI TECNOLOGIA"},
        "thumb_query": "voyager spacecraft interstellar deep space stars nasa",
        "cta_headline": "A MENSAGEM HUMANA NA ETERNIDADE",
        "cta_question": "E você, o que acha da Voyager 1 continuar viajando pela galáxia por bilhões de anos após a nossa era?",
        "shorts_narration": (
            "Neste exato segundo, a nave mais distante já construída pela humanidade acaba de atingir um marco histórico surreal: "
            "a sonda Voyager Um da NASA está a quase um dia-luz completo de distância da Terra — mais de vinte e cinco bilhões de quilômetros no vazio interestelar! "
            "Isso significa que um comando enviado pelas antenas da Terra na velocidade da luz leva vinte e quatro horas inteiras só para chegar até lá, e outras vinte e quatro horas para recebermos qualquer resposta. "
            "Mas o que a Voyager Um descobriu ao atravessar a fronteira do nosso Sistema Solar deixou os astrofísicos em choque: uma verdadeira parede invisível de plasma escaldante entre trinta mil e cinquenta mil graus Kelvin! "
            "Por que a nave não derreteu? Porque apesar da temperatura extrema das partículas energizadas, a densidade desse gás na Heliopausa é trilhões de vezes menor que a do ar que respiramos, quase sem transferência de calor. "
            "Além disso, seus magnetômetros revelaram que o campo magnético da galáxia lá fora está alinhado de forma inexplicável com o campo magnético do próprio Sol, e que a densidade do plasma dispara misteriosamente quanto mais ela avança pela Via Láctea. "
            "A investigação completa com todos os detalhes dessa jornada está no vídeo principal do YouTube: "
            "acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
        ),
        "queries": [
            "voyager spacecraft deep space mission nasa",
            "heliosphere solar wind bubble interstellar space nasa",
            "solar corona plasma magnetic field sdo nasa",
            "deep space network radio telescope dish nasa",
            "interstellar medium nebula dust gas webb",
            "golden record voyager space exploration nasa",
            "milky way galaxy spiral arms stars"
        ],
        "acts": [
            {"key": "hook", "type": "hook", "headline": "A FRONTEIRA DE UM DIA-LUZ", "highlights": ["VOYAGER 1", "UM DIA-LUZ", "25 BILHÕES DE KM"], "stat_label": "Distância Histórica", "stat_value": "~26 Bilhões de km",
             "narration": "A mais de vinte e cinco bilhões de quilômetros de distância, existe um único objeto fabricado por mãos humanas que cruzou a fronteira gravitacional da bolha solar e agora navega pelo espaço interestelar. A sonda Voyager Um, lançada em mil novecentos e setenta e sete, está alcançando a marca simbólica de um dia-luz completo da Terra: um ponto tão remoto que nem a luz consegue cruzar em menos de vinte e quatro horas."},
            {"key": "signal", "type": "investigation", "headline": "48 HORAS PARA UMA CONVERSA", "highlights": ["VELOCIDADE DA LUZ", "DEEP SPACE NETWORK", "SINAL FRACO"], "stat_label": "Tempo de Resposta", "stat_value": "48 Horas (Ida e Volta)",
             "narration": "Quando os engenheiros do Laboratório de Propulsão a Jato da NASA enviam uma correção de código pela Rede de Espaço Profundo, o sinal de rádio viaja a trezentos mil quilômetros por segundo durante um dia inteiro antes de tocar a antena de três vírgula sete metros da Voyager. Quando chega, a potência restante do sinal captado na Terra é menor do que a energia de um bilionésimo de bilionésimo de watt."},
            {"key": "firewall", "type": "revelation", "headline": "A PAREDE DE FOGO DE 50 MIL KELVIN", "highlights": ["HELIOPAUSA", "50.000 KELVIN", "PLASMA"], "stat_label": "Temperatura na Borda", "stat_value": "30.000 a 50.000 K",
             "narration": "Ao cruzar a Heliopausa — o limite onde o vento solar encontra os ventos gelados de outras estrelas — os sensores da Voyager Um registraram uma anomalia chocante: a temperatura do plasma saltou abruptamente para até cinquenta mil Kelvin! Essa barreira foi apelidada pela mídia científica de parede de fogo cósmica, onde partículas colidem sob pressão magnética interestelar."},
            {"key": "density", "type": "investigation", "headline": "POR QUE A SONDA NÃO DERRETEU?", "highlights": ["DENSIDADE QUASE ZERO", "TERMODINÂMICA", "VÁCUO"], "stat_label": "Densidade de Partículas", "stat_value": "0,1 Átomo por cm³",
             "narration": "Como uma nave de alumínio com circuitos dos anos setenta atravessou cinquenta mil graus sem vaporizar? A física responde com a diferença entre temperatura e calor. Embora cada elétron lá fora possua energia altíssima, há menos de uma partícula por centímetro cúbico. Como quase não há colisões com o casco da nave, ela continua congelada em um vácuo quase absoluto."},
            {"key": "magnetism", "type": "investigation", "headline": "O ENIGMA DO CAMPO MAGNÉTICO", "highlights": ["CAMPO MAGNÉTICO", "ANOMALIA INTERESTELAR", "FÍSICA"], "stat_label": "Descoberta Chave", "stat_value": "Alinhamento Inesperado",
             "narration": "Os modelos teóricos previam que, assim que a Voyager deixasse a influência do Sol, a direção das linhas do campo magnético mudaria drasticamente. Em vez disso, os instrumentos detectaram que o campo magnético do espaço interestelar está misteriosamente alinhado com o campo interno do nosso Sistema Solar, sugerindo conexões invisíveis que ainda desafiam a astrofísica."},
            {"key": "power", "type": "climax", "headline": "O CORAÇÃO NUCLEAR QUE ESTÁ SE APAGANDO", "highlights": ["PLUTÔNIO-238", "GERADOR NUCLEAR", "DESLIGAMENTO"], "stat_label": "Queda de Energia", "stat_value": "-4 Watts por Ano",
             "narration": "Tão longe do Sol que os painéis solares seriam completamente inúteis, a Voyager Um sobrevive graças ao decaimento radioativo de esferas de Plutônio duzentos e trinta e oito. Perdendo cerca de quatro watts de potência por ano, a equipe da NASA já desligou quase todos os aquecedores e instrumentos não essenciais, mantendo apenas os detectores mais preciosos vivos enquanto ela transmite seus últimos suspiros."},
            {"key": "legacy", "type": "investigation", "headline": "A CARTA DE AMOR DA HUMANIDADE", "highlights": ["DISCO DE OURO", "40 MIL ANOS", "ETERNIDADE"], "stat_label": "Próxima Estrela", "stat_value": "Gliese 445 (40.000 Anos)",
             "narration": "Preso ao casco da Voyager segue o Disco de Ouro: uma gravação banhada a cobre e ouro contendo sons da Terra, músicas de Bach a Chuck Berry, ondas cerebrais e mapas de pulsares indicando a posição do nosso planeta. Mesmo quando suas baterias morrerem na década de dois mil e trinta, ela continuará orbitando a Via Láctea em silêncio por bilhões de anos como o último monumento da civilização humana."}
        ]
    },
    {
        "slug": "bennu-asteroids-origin-life",
        "keywords": ["bennu", "asteroid", "osiris", "organics", "vida", "asteroide"],
        "title": "Asteroide Bennu: Os Blocos da Vida Encontrados Fora da Terra Pela NASA",
        "alt_titles": [
            "O Que a NASA Encontrou Dentro das Amostras do Asteroide Bennu Mudou Tudo",
            "Os Ingredientes do DNA Vieram do Espaço? O Segredo do Asteroide Bennu"
        ],
        "topic": "Asteroide Bennu, OSIRIS-REx, Origem da Vida e Química Pré-Biótica no Espaço",
        "summary": "A análise de laboratório da poeira intocada do asteroide Bennu revelou moléculas orgânicas complexas, sais minerais antigos e todas as 5 bases nitrogenadas do DNA e do RNA.",
        "tags": ["scapatici tecnologia", "asteroide bennu", "nasa", "osiris rex", "origem da vida", "astrobiologia", "universo", "ciencia"],
        "thumbnail_text": {"line1": "SEGREDO DO", "line2": "ASTEROIDE BENNU!", "subtitle": "A NASA ENCONTROU A ORIGEM DA VIDA? | SCAPATICI TECNOLOGIA"},
        "thumb_query": "asteroid bennu osiris rex surface boulders nasa",
        "cta_headline": "SOMOS FILHOS DOS ASTEROIDES?",
        "cta_question": "E você, acredita que as sementes químicas da vida na Terra vieram de asteroides antigos como o Bennu?",
        "shorts_narration": (
            "Uma pequena cápsula da NASA que pousou no deserto com poeira negra de um asteroide de quatro vírgula cinco bilhões de anos acaba de reescrever o que sabemos sobre a origem da vida na Terra! "
            "Os cientistas analisaram as amostras intocadas do asteroide Bennu, coletadas pela missão OSIRIS-REx antes de qualquer contaminação pela atmosfera terrestre. "
            "E o que encontraram dentro daquela rocha espacial deixou os astrobiólogos em estado de alerta máximo: não havia apenas carbono e água presa em argilas, mas todas as cinco nucleobases fundamentais que formam o DNA e o RNA de todos os seres vivos da Terra! "
            "Além disso, exames recentes identificaram catorze dos vinte aminoácidos usados pelas proteínas humanas e cristais de sais evaporados que provam que o corpo pai de Bennu abrigou lagos ou bolsões de salmoura líquida muito antes da Terra se resfriar! "
            "Mais misterioso ainda: os compostos orgânicos de Bennu exibem assinaturas isotópicas formadas no frio extremo do espaço interestelar, antes mesmo do nascimento do Sol. "
            "Será que chuvas de asteroides semearam oceanos inteiros na Terra jovem? "
            "A investigação completa com todos os dados dessa descoberta está no vídeo principal do YouTube: "
            "acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
        ),
        "queries": [
            "asteroid bennu surface mosaic osiris rex nasa",
            "osiris rex sample return capsule utah desert nasa",
            "johnson space center astromaterials clean room bennu nasa",
            "protoplanetary disk early solar system formation nasa",
            "ancient earth ocean comets asteroid impacts nasa",
            "organic molecules spectroscopy space chemistry nasa",
            "deep space nebula carbon dust pillars webb"
        ],
        "acts": [
            {"key": "hook", "type": "hook", "headline": "O TESOURO NEGRO DE 4,5 BILHÕES DE ANOS", "highlights": ["ASTEROIDE BENNU", "OSIRIS-REX", "ORIGEM DA VIDA"], "stat_label": "Amostra Coletada", "stat_value": "121,6 Gramas Puras",
             "narration": "Por mais de duzentos anos, os cientistas procuram a peça faltante do maior quebra-cabeça da biologia: como moléculas sem vida conseguiram se organizar nos primeiros códigos genéticos da Terra primitiva? Parte dessa resposta não está em nossos oceanos atuais, mas em cento e vinte e um gramas de poeira preta trazidos diretamente do asteroide Bennu pela espaçonave OSIRIS-REx da NASA."},
            {"key": "dna", "type": "revelation", "headline": "TODAS AS PEÇAS DO DNA FORA DA TERRA", "highlights": ["5 NUCLEOBASES", "AMINOÁCIDOS", "DNA E RNA"], "stat_label": "Descoberta Química", "stat_value": "14 de 20 Aminoácidos",
             "narration": "Em salas limpas esterilizadas para evitar qualquer contaminação moderna, pesquisadores descobriram que as amostras de Bennu carregam dezenas de milhares de compostos orgânicos diferentes. O choque foi encontrar todas as cinco bases nitrogenadas que codificam o DNA e o RNA terrestres — adenina, guanina, citosina, timina e uracila — além de catorze dos vinte aminoácidos usados para fabricar proteínas."},
            {"key": "water", "type": "investigation", "headline": "VESTÍGIOS DE OCEANOS ANTIGOS NO ESPAÇO", "highlights": ["SALMOURA LÍQUIDA", "EVAPORAÇÃO", "MINERAIS"], "stat_label": "Idade dos Cristais", "stat_value": "4,5 Bilhões de Anos",
             "narration": "Os exames de microscopia eletrônica também detectaram onze minerais raros de evaporito — incluindo fosfatos e carbonatos de sódio idênticos aos que se formam quando lagos salgados secam na Terra. Isso prova que o protoplaneta original do qual Bennu se fragmentou abrigava bolsões de água líquida salgada e morna nos primeiros milhões de anos do Sistema Solar."},
            {"key": "chirality", "type": "investigation", "headline": "O MISTÉRIO DA QUIRALIDADE", "highlights": ["SIMETRIA", "ISÓTOPOS", "ENIGMA QUÍMICO"], "stat_label": "Mistério Aberto", "stat_value": "Assinatura Simétrica",
             "narration": "A vida na Terra tem uma preferência intrigante: quase todos os nossos aminoácidos giram para o lado esquerdo, como uma luva canhota. No asteroide Bennu, porém, os cientistas encontraram misturas perfeitamente equilibradas entre formas esquerdas e direitas! Esse contraste mostra que a química pré-biótica nasceu simétrica no espaço, mas algum evento misterioso na Terra escolheu apenas um lado."},
            {"key": "impact", "type": "investigation", "headline": "O BOMBARDEIO QUE SEMEOU A TERRA", "highlights": ["PANSPERMIA QUÍMICA", "COMETAS", "EARTH"], "stat_label": "Teoria Reforçada", "stat_value": "Entrega Cósmica",
             "narration": "Há quatro bilhões de anos, durante o Intenso Bombardeio Tardio, milhões de asteroides carbonáceos como Bennu atingiram a Terra recém-formada. Se cada rocha trazia água, fósforo, aminoácidos e nucleobases prontas em seu interior protegido, os nossos oceanos primitivos receberam um verdadeiro kit de partida químico vindo diretamente das estrelas."},
            {"key": "hazard", "type": "climax", "headline": "O ASTEROIDE QUE AINDA PASSA PERTO", "highlights": ["RISCO DE IMPACTO", "ANO 2182", "MONITORAMENTO"], "stat_label": "Aproximação Crítica", "stat_value": "Setembro de 2182",
             "narration": "Além de ser uma cápsula do tempo biológica, Bennu também faz parte da lista dos asteroides mais observados pela Defesa Planetária. Com quase quinhentos metros de diâmetro, os cálculos orbitais apontam uma probabilidade real de cerca de um em dois mil e setecentos de cruzar perigosamente a rota da Terra no ano dois mil cento e oitenta e dois — motivo pelo qual sua estrutura fofa e porosa foi mapeada centímetro a centímetro."},
            {"key": "implication", "type": "investigation", "headline": "VIDA EM OUTROS MUNDOS É INEVITÁVEL?", "highlights": ["ASTROBIOLOGIA", "EXOPLANETAS", "COSMOS"], "stat_label": "Impacto Científico", "stat_value": "Ingredientes Universais",
             "narration": "Se as mesmas moléculas encontradas em Bennu viajam presas na poeira de outros discos protoplanetários pela Via Láctea, então a química básica do DNA não é uma exclusividade rara da Terra. Ela pode ser uma receita padrão espalhada por bilhões de sistemas estelares esperando apenas por água líquida e tempo para despertar."}
        ]
    },
    {
        "slug": "quasar-pair-cosmic-dawn",
        "keywords": ["quasar", "black hole", "buraco negro", "supermassive", "early universe", "pair"],
        "title": "Quasares Gigantes no Início do Tempo: O Mistério Que Desafia Einstein",
        "alt_titles": [
            "Como Dois Buracos Negros Supermassivos Existiam Tão Cedo Após o Big Bang?",
            "O Enigma dos Quasares Binários: Monstros Que Cresceram Rápido Demais"
        ],
        "topic": "Quasares Primordiais, Pares de Buracos Negros e o Crescimento Impossível Após o Big Bang",
        "summary": "Astrônomos identificaram quasares compactos e buracos negros bilionários menos de 900 milhões de anos após o Big Bang — rápido demais para os modelos convencionais.",
        "tags": ["scapatici tecnologia", "quasar", "buraco negro", "james webb", "big bang", "cosmologia", "astrofisica", "universo"],
        "thumbnail_text": {"line1": "MONSTROS NO", "line2": "INÍCIO DO TEMPO!", "subtitle": "POR QUE ESSES QUASARES NÃO DEVERIAM EXISTIR? | SCAPATICI TECNOLOGIA"},
        "thumb_query": "quasar supermassive black hole jet active galaxy nasa",
        "cta_headline": "COMO OS GIGANTES NASCERAM?",
        "cta_question": "E você, acredita que os primeiros buracos negros nasceram já gigantes logo nos primeiros segundos do Big Bang?",
        "shorts_narration": (
            "Como dois buracos negros supermassivos gigantes já brilhavam no início do universo quando o cosmos ainda era apenas um bebê? "
            "A descoberta de quasares primordiais — e até mesmo de pares compactos de quasares fundindo galáxias menos de um bilhão de anos após o Big Bang — colocou os astrofísicos diante de um paradoxo brutal! "
            "Um quasar nasce quando um buraco negro supermassivo devora quantidades colossais de gás e transforma a fricção desse disco em um farol mais brilhante que trilhões de estrelas juntas. "
            "O problema é o limite físico de Eddington: você não pode alimentar um buraco negro rápido demais, porque a própria radiação gerada pelo disco de gás empurra a comida para longe! "
            "Mesmo devorando matéria no limite máximo contínuo sem parar um único segundo, uma estrela comum morta jamais conseguiria crescer até atingir um bilhão de massas solares em tão pouco tempo depois do Big Bang! "
            "Para resolver esse quebra-cabeça, o Telescópio James Webb está investigando duas soluções radicais: ou nuvens gigantescas colapsaram diretamente em buracos negros pesados sem nunca formar estrelas, ou os buracos negros primordiais nasceram nas frações iniciais do Big Bang! "
            "A investigação completa está no vídeo principal do YouTube: "
            "acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
        ),
        "queries": [
            "quasar brightest object universe active galactic nucleus nasa",
            "binary supermassive black holes merging galaxies nasa",
            "james webb early galaxies cosmic dawn infrared",
            "black hole accretion disk relativistic jet chandra",
            "galaxy collision tidal streams hubble",
            "primordial black holes early universe simulation nasa",
            "deep space cosmos clusters galaxies webb"
        ],
        "acts": [
            {"key": "hook", "type": "hook", "headline": "FARÓIS NOS CONFINS DO TEMPO", "highlights": ["QUASARES", "1 BILHÃO DE SÓIS", "BIG BANG"], "stat_label": "Brilho Cósmico", "stat_value": "100x Mais Que a Via Láctea",
             "narration": "Os quasares são os objetos mais luminosos de todo o universo: núcleos galácticos alimentados por buracos negros supermassivos capazes de ofuscar centenas de bilhões de estrelas ao redor. Mas quando telescópios modernos avistaram pares compactos de quasares já ativos menos de novecentos milhões de anos após o Big Bang, a conta matemática da cosmologia simplesmente não fechou."},
            {"key": "eddington", "type": "investigation", "headline": "O LIMITE IMPLACÁVEL DE EDDINGTON", "highlights": ["LIMITE DE EDDINGTON", "RADIAÇÃO", "ALIMENTAÇÃO"], "stat_label": "Barreira Física", "stat_value": "Pressão de Radiação",
             "narration": "Para crescer, um buraco negro precisa sugar gás e poeira em espiral. Contudo, o disco giratório aquece a milhões de graus e dispara tanta luz e pressão de radiação para fora que afasta o gás ao redor — um teto natural conhecido como Limite de Eddington. Mesmo comendo no limite máximo ininterruptamente desde a primeira geração de estrelas, não há tempo suficiente para chegar a bilhões de massas solares tão cedo."},
            {"key": "binary", "type": "revelation", "headline": "DANÇA MORTAL DE QUASARES BINÁRIOS", "highlights": ["QUASARES BINÁRIOS", "COLISÃO GALÁCTICA", "FUSÃO"], "stat_label": "Separação Recorde", "stat_value": "Poucos Milhares de Anos-Luz",
             "narration": "Observações recentes revelaram quasares duplos ainda mais raros: dois monstros supermassivos girando lado a lado durante fusões precoces de galáxias jovens. Encontrar pares tão compactos no alvorecer cósmico sugere que grandes concentrações de matéria escura e gás denso se juntavam em ritmo frenético logo após a formação das primeiras teias cósmicas."},
            {"key": "direct", "type": "investigation", "headline": "SEMENTES DE COLAPSO DIRETO", "highlights": ["COLAPSO DIRETO", "NUVENS PRIMORDIAIS", "SEMENTES PESADAS"], "stat_label": "Massa Inicial", "stat_value": "10.000 a 100.000 Sóis",
             "narration": "A primeira hipótese favorita pelos pesquisadores do James Webb é o Colapso Direto. No universo jovem, nuvens gigantescas de hidrogênio puro, banhadas por radiação ultravioleta de estrelas vizinhas que impediam o resfriamento lento, teriam desabado inteiras de uma só vez formando buracos negros sementes já com cem mil massas solares sem nunca passar pela fase estelar."},
            {"key": "primordial", "type": "investigation", "headline": "CICATRIZES DO PRIMEIRO SEGUNDO", "highlights": ["BURACOS NEGROS PRIMORDIAIS", "INFLAÇÃO CÓSMICA", "SINGULARIDADE"], "stat_label": "Origem Teórica", "stat_value": "10⁻²³ Segundos Pós-Big Bang",
             "narration": "Uma segunda possibilidade ainda mais ousada propõe os Buracos Negros Primordiais: regiões onde o próprio espaço primordial era tão denso logo na primeira fração de segundo após o Big Bang que colapsaram diretamente em gravidade pura, muito antes que o primeiro átomo de hidrogênio existisse. Eles teriam atuado como ímãs gravitacionais construindo galáxias inteiras ao seu redor."},
            {"key": "jets", "type": "climax", "headline": "JATOS QUE MOLDAM GALÁXIAS INTEIRAS", "highlights": ["JATOS RELATIVÍSTICOS", "99% DA LUZ", "VENTOS CÓSMICOS"], "stat_label": "Alcance do Jato", "stat_value": "Milhares de Anos-Luz",
             "narration": "Os campos magnéticos torcidos perto do horizonte de eventos lançam dois feixes de partículas relativísticas a velocidades próximas à da luz. Esses jatos atravessam galáxias inteiras, aquecendo as nuvens interestelares e controlando quando e quantas novas estrelas poderão nascer durante os próximos bilhões de anos."},
            {"key": "lisa", "type": "investigation", "headline": "OUVINDO A FUSÃO PELAS ONDAS GRAVITACIONAIS", "highlights": ["MISSÃO LISA", "ONDAS GRAVITACIONAIS", "FUTURO"], "stat_label": "Observatório Espacial", "stat_value": "Triângulo Laser (ESA/NASA)",
             "narration": "Na próxima década, observatórios espaciais de ondas gravitacionais como a missão LISA detectarão as ondulações exatas no espaço-tempo deixadas por esses pares de quasares quando colidem nos confins do universo — finalmente revelando se os primeiros monstros cósmicos vieram de estrelas gigantes ou do próprio Big Bang."}
        ]
    },
    {
        "slug": "gravitational-waves-exoplanets",
        "keywords": ["ripple", "space-time", "gravitational", "exoplanet", "ligo", "ondulacoes", "exoplanetas"],
        "title": "Ondas no Espaço-Tempo: Como a Gravidade Revela Mundos e Catástrofes Ocultas",
        "alt_titles": [
            "Como Ondas Invisíveis no Espaço-Tempo Podem Descobrir Novos Exoplanetas",
            "Ouvindo o Universo: A Nova Era da Astronomia de Ondas Gravitacionais"
        ],
        "topic": "Ondas Gravitacionais, Exoplanetas, Relatividade Geral e Detectores Laser",
        "summary": "Previstas por Einstein em 1916, as ondulações do espaço-tempo não mostram apenas colisões de buracos negros — novas pesquisas apontam como podem revelar exoplanetas invisíveis à luz.",
        "tags": ["scapatici tecnologia", "ondas gravitacionais", "einstein", "exoplanetas", "ligo", "espaco tempo", "fisica", "ciencia"],
        "thumbnail_text": {"line1": "ONDAS NO", "line2": "ESPAÇO-TEMPO!", "subtitle": "A GRAVIDADE REVELA MUNDOS OCULTOS | SCAPATICI TECNOLOGIA"},
        "thumb_query": "gravitational waves binary black holes ligo space time nasa",
        "cta_headline": "OUVINDO A SINFINIA DA GRAVIDADE",
        "cta_question": "E você, imaginava que tremores microscópicos no próprio tecido do espaço poderiam revelar mundos do outro lado da galáxia?",
        "shorts_narration": (
            "Durante mais de quatrocentos anos, tudo o que soubemos sobre o universo veio apenas da luz! Mas há menos de uma década, a humanidade ganhou um novo sentido para perceber a realidade: passamos a ouvir as vibrações do próprio espaço-tempo! "
            "Quando dois buracos negros ou estrelas de nêutrons colidem a bilhões de anos-luz de distância, eles sacodem o tecido geométrico do cosmos com ondas gravitacionais previstas por Albert Einstein há mais de cem anos! "
            "E aqui está o detalhe alucinante que novos estudos de astrofísica acabam de propor: essas ondulações gravitacionais emitidas por anãs brancas binárias são tão estáveis e precisas como relógios cósmicos que, se um exoplaneta gigante estiver orbitando ao redor delas, sua gravidade puxará o par binário e imprimirá uma modulação mensurável na frequência da onda gravitacional! "
            "Isso significa que futuros detectores espaciais poderão descobrir planetas invisíveis mesmo dentro de nuvens de poeira densas ou em outras galáxias onde telescópios ópticos nunca enxergariam nada! "
            "Pense na precisão: o LIGO na Terra mede variações menores que um décimo de milésimo da largura de um único próton para ouvir colisões de sóis distantes. "
            "A investigação completa está no vídeo principal do YouTube: "
            "acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
        ),
        "queries": [
            "gravitational waves ripples spacetime simulation nasa",
            "ligo interferometer laser gravitational observatory",
            "white dwarf binary stars orbiting space nasa",
            "exoplanet deep space hidden dust nebula nasa",
            "lisa gravitational wave observatory spacecraft esa nasa",
            "neutron star merger explosion optical light hubble",
            "cosmic spacetime curvature einstein gravity"
        ],
        "acts": [
            {"key": "hook", "type": "hook", "headline": "O SEXTO SENTIDO DA HUMANIDADE", "highlights": ["ONDAS GRAVITACIONAIS", "EINSTEIN", "ESPAÇO-TEMPO"], "stat_label": "Velocidade da Onda", "stat_value": "299.792 km/s (Igual à Luz)",
             "narration": "De Galileu ao Telescópio James Webb, toda a astronomia dependia de capturar fótons de luz, raios X ou ondas de rádio. Mas o universo guarda eventos colossais completamente escuros e invisíveis. Tudo mudou quando aprendemos a medir ondas gravitacionais: vibrações reais do próprio espaço-tempo viajando pelo cosmos à velocidade da luz."},
            {"key": "einstein", "type": "investigation", "headline": "A PREVISÃO QUE EINSTEIN DUVIDOU", "highlights": ["RELATIVIDADE GERAL", "1916", "TREMOR CÓSMICO"], "stat_label": "Precisão Exigida", "stat_value": "1/10.000 de um Próton",
             "narration": "Quando Albert Einstein previu as ondas gravitacionais em mil novecentos e dezesseis usando a Relatividade Geral, ele mesmo achou que o sinal seria tão fraco que nenhum equipamento humano jamais conseguiria detectá-lo. Ele subestimou a engenhosidade dos detectores a laser do LIGO, cujos braços de quatro quilômetros medem deformações dez mil vezes menores que o núcleo de um único átomo de hidrogênio!"},
            {"key": "exoplanets", "type": "revelation", "headline": "CAÇANDO EXOPLANETAS SEM USAR LUZ", "highlights": ["EXOPLANETAS", "ANÃS BRANCAS", "EFEITO DOPPLER"], "stat_label": "Novo Método", "stat_value": "Doppler Gravitacional",
             "narration": "Novas pesquisas em astrofísica revelaram um uso surpreendente para essas ondas: encontrar exoplanetas completamente ocultos! Pares de estrelas anãs brancas em órbita fechada emitem ondas gravitacionais contínuas como um metrônomo cósmico perfeito. Quando um planeta orbita esse sistema, ele faz o par oscilar levemente para frente e para trás, alterando o ritmo das ondas de gravidade captadas aqui na Terra."},
            {"key": "galaxy", "type": "investigation", "headline": "ENXERGANDO ATRAVÉS DA POEIRA GALÁCTICA", "highlights": ["NÚCLEO GALÁCTICO", "OUTRAS GALÁXIAS", "TRANSPARÊNCIA"], "stat_label": "Alcance Potencial", "stat_value": "Via Láctea e Além",
             "narration": "Ao contrário da luz visível, que é bloqueada por muralhas de poeira interestelar ou ofuscada pelo brilho das estrelas-mãe, as ondas gravitacionais atravessam planetas, estrelas e galáxias inteiras sem quase nenhuma interferência! Isso abre a porta para mapear mundos sobreviventes em volta de cadáveres estelares até mesmo em galáxias vizinhas."},
            {"key": "pulsar", "type": "investigation", "headline": "A REDE DE PULSARES DA VIA LÁCTEA", "highlights": ["PULSAR TIMING", "ORQUESTRA CÓSMICA", "BURACOS NEGROS"], "stat_label": "Detetor Natural", "stat_value": "Relógios Estelares",
             "narration": "Para capturar ondas gravitacionais ainda maiores — de comprimentos de onda de anos-luz geradas por buracos negros supermassivos no centro de galáxias em fusão — os astrônomos usam estrelas de nêutrons giratórias espalhadas pela Via Láctea como uma antena do tamanho da própria galáxia, medindo atrasos de nanossegundos em seus pulsos de rádio."},
            {"key": "lisa", "type": "climax", "headline": "TRÊS SATÉLITES NO VÁCUO ESPACIAL", "highlights": ["LISA", "LASERS DE 2,5M KM", "2035"], "stat_label": "Braço dos Lasers", "stat_value": "2,5 Milhões de km",
             "narration": "Na próxima década, a missão espacial LISA colocará três espaçonaves em órbita solar formando um triângulo perfeito com dois milhões e meio de quilômetros de cada lado, conectadas por feixes de laser no vácuo absoluto do espaço. Sem o ruído de terremotos ou oceanos terrestres, esse instrumento poderá detectar dezenas de milhares de fontes binárias e seus possíveis planetas."},
            {"key": "future", "type": "investigation", "headline": "O ECO DO PRÓPRIO BIG BANG", "highlights": ["ONDAS PRIMORDIAIS", "INFLAÇÃO CÓSMICA", "ORIGEM DO TEMPO"], "stat_label": "Alvo Definitivo", "stat_value": "Primeiro Trilionésimo de s",
             "narration": "O maior sonho da astronomia gravitacional vai além de planetas e estrelas: um dia, essas antenas podem escutar o fundo primordial de ondas gravitacionais nascidas no primeiro trilionésimo de segundo do universo — revelando diretamente como o Big Bang expandiu o espaço antes mesmo da existência da luz."}
        ]
    },
    {
        "slug": "europa-enceladus-alien-oceans",
        "keywords": ["europa", "enceladus", "ocean", "icy moon", "clipper", "jupiter", "saturn", "water"],
        "title": "Oceanos Sob o Gelo de Europa e Encélado: O Maior Candidato a Vida Alienígena",
        "alt_titles": [
            "O Que Existe no Fundo dos Oceanos Secretos de Europa e Encélado?",
            "Europa Clipper e o Enigma da Vida Alienígena nas Luas Geladas"
        ],
        "topic": "Lua Europa, Encélado, Missão Europa Clipper e Oceanos Subglaciais Habitáveis",
        "summary": "Muito além da Zona Habitável clássica, luas de Júpiter e Saturno escondem oceanos globais com mais água líquida do que todos os oceanos da Terra juntos.",
        "tags": ["scapatici tecnologia", "europa clipper", "encelado", "vida alienigena", "astrobiologia", "jupiter", "nasa", "ciencia"],
        "thumbnail_text": {"line1": "OCEANOS SECRETOS", "line2": "DE ÁGUA LÍQUIDA!", "subtitle": "A VIDA PODE ESTAR EM EUROPA E ENCÉLADO | SCAPATICI TECNOLOGIA"},
        "thumb_query": "europa moon jupiter icy surface cracks spacecraft nasa",
        "cta_headline": "NÃO ESTAMOS SOZINHOS NO SISTEMA SOLAR?",
        "cta_question": "E você, acredita que quando perfurarmos ou analisarmos as plumas de Europa encontraremos microrganismos alienígenas?",
        "shorts_narration": (
            "Durante décadas, a astronomia procurou vida alienígena olhando apenas para planetas que ficam perto o suficiente do Sol para não congelar. Mas o lugar com maior chance real de abrigar vida extraterrestre hoje dentro do nosso próprio Sistema Solar fica lá no frio extremo, perto de Júpiter e Saturno! "
            "Sob uma crosta de gelo de dezenas de quilômetros de espessura, a pequena lua Europa de Júpiter esconde um oceano global de água salgada com cem quilômetros de profundidade — contendo o dobro de toda a água líquida existente em todos os oceanos da Terra somados! "
            "Como essa água não congela tão longe do Sol? Graças à força de maré gravitacional brutal de Júpiter e Saturno, que amassa e estica o núcleo rochoso dessas luas o tempo todo, gerando fontes hidrotermais quentes no fundo do mar, exatamente iguais às chaminés oceânicas onde muitos biólogos acreditam que a vida começou na Terra! "
            "Mais incrível ainda: a sonda Cassini atravessou gêiseres gigantescos disparados para o espaço pelas rachaduras da lua Encélado e detectou hidrogênio molecular, sais minerais, nitrogênio, fósforo e compostos orgânicos complexos! "
            "Com a missão Europa Clipper da NASA já a caminho de Júpiter, estamos prestes a analisar a habitabilidade desse oceano oculto de perto! "
            "A investigação completa está no vídeo principal do YouTube: "
            "acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
        ),
        "queries": [
            "europa clipper spacecraft jupiter icy moon nasa",
            "europa moon surface reddish fractures galileo nasa",
            "enceladus water plumes jets saturn cassini nasa",
            "deep ocean hydrothermal vents earth biology",
            "jupiter great red spot icy moons voyager nasa",
            "saturn rings enceladus backlit cassini nasa",
            "astrobiology water world exoplanet ocean nasa"
        ],
        "acts": [
            {"key": "hook", "type": "hook", "headline": "O DOBRO DE ÁGUA DA TERRA SOB O GELO", "highlights": ["LUA EUROPA", "OCEANOS OCULTOS", "ÁGUA LÍQUIDA"], "stat_label": "Volume de Água", "stat_value": "2x Todos Oceanos da Terra",
             "narration": "Marte já teve rios no passado, mas hoje é um deserto seco e irradiado. Se você quiser encontrar um oceano inteiro de água líquida salgada banhando rochas quentes hoje mesmo, precisa olhar para a lua Europa de Júpiter e a lua Encélado de Saturno: mundos cobertos por uma armadura branca de gelo, mas fervilhando de atividade em suas profundezas."},
            {"key": "tidal", "type": "investigation", "headline": "O MOTOR INVISÍVEL DAS MARÉS", "highlights": ["AQUECIMENTO DE MARÉ", "JÚPITER", "GRAVIDADE"], "stat_label": "Profundidade Oceânica", "stat_value": "~100 Quilômetros",
             "narration": "A quase oitocentos milhões de quilômetros do Sol, a luz solar é vinte e cinco vezes mais fraca que na Terra. O segredo que impede esses oceanos de virarem pedra de gelo sólida é o aquecimento de maré: a gravidade colossal de Júpiter e das luas vizinhas deforma Europa continuamente em sua órbita elíptica, gerando atrito interno capaz de derreter o gelo inferior e alimentar vulcões submarinos."},
            {"key": "enceladus", "type": "revelation", "headline": "GÊISERES QUE REVELARAM OS INGREDIENTES DA VIDA", "highlights": ["ENCÉLADO", "CASSINI", "FÓSFORO E CARBONO"], "stat_label": "Velocidade dos Jatos", "stat_value": "~1.300 Km/h no Espaço",
             "narration": "Em Saturno, a lua Encélado realiza um presente incrível para os cientistas: através de rachaduras conhecidas como listras de tigre no polo sul, ela cospe plumas gigantescas de vapor de água e grãos de gelo oceânico diretamente no espaço! Ao mergulhar por esses jatos, a sonda Cassini detectou água salgada, metano, hidrogênio e recentemente fósforo — o elemento mais raro e essencial para montar moléculas de DNA e energia celular."},
            {"key": "vents", "type": "investigation", "headline": "CHAMINÉS HIDROTERMAIS SEM LUZ SOLAR", "highlights": ["FONTES HIDROTERMAIS", "QUIMIOSSÍNTESE", "SEM SOL"], "stat_label": "Energia Biológica", "stat_value": "Quimiossíntese Profunda",
             "narration": "Na Terra, descobrimos ecossistemas inteiros prosperando na escuridão total a quatro mil metros de profundidade no oceano Atlântico e Pacífico, alimentados não pela fotossíntese do Sol, mas por reações químicas entre água do mar e minerais quentes que brotam de fissuras vulcânicas. É exatamente esse mesmo metabolismo que pode pulsar no assoalho rochoso de Europa e Encélado."},
            {"key": "clipper", "type": "investigation", "headline": "A MISSÃO EUROPA CLIPPER DA NASA", "highlights": ["EUROPA CLIPPER", "RADARES DE GELO", "ESPECTRÔMETROS"], "stat_label": "Sobrevoos Planejados", "stat_value": "~50 Passagens Rasantes",
             "narration": "A maior nave interplanetária planetária já construída pela NASA, a Europa Clipper, equipada com painéis solares gigantescos para capturar a fraca luz perto de Júpiter, realizará cerca de cinquenta sobrevoos rasantes a apenas vinte e cinco quilômetros acima da crosta de Europa. Seus radares de penetração mapearão a espessura exata do gelo e localizarão lagos internos próximos à superfície."},
            {"key": "radiation", "type": "climax", "headline": "O INFERNO RADIOATIVO DE JÚPITER", "highlights": ["RADIAÇÃO LETAL", "COFRE DE TITÂNIO", "ESCUDO"], "stat_label": "Dose Externa", "stat_value": "Letal em Minutos",
             "narration": "Estudar Europa exige sobreviver a um dos ambientes mais hostis do Sistema Solar: os cinturões magnéticos de Júpiter aceleram partículas a níveis de radiação milhões de vezes superiores aos da Terra. Para proteger seus computadores sensíveis durante cada passagem, a nave carrega um cofre blindado com paredes espessas de titânio e alumínio."},
            {"key": "search", "type": "investigation", "headline": "UMA SEGUNDA GÊNESE NO COSMOS", "highlights": ["SEGUNDA GÊNESE", "ASTROBIOLOGIA", "REVOLUÇÃO"], "stat_label": "Impacto Científico", "stat_value": "Mudança de Paradigma",
             "narration": "Se encontrarmos evidências de vida microbiana evoluída de maneira totalmente independente em um oceano oculto em torno de Júpiter ou Saturno, teremos a maior prova científica da história: a vida não é um acidente único da Terra, mas uma consequência natural inevitável da química sempre que água, calor e minerais se encontram pelo universo."}
        ]
    },
    {
        "slug": "dark-energy-desi-collapse",
        "keywords": ["dark energy", "energia escura", "desi", "big rip", "big crunch", "universe expansion"],
        "title": "A Energia Escura Está Mudando? A Descoberta Que Altera o Fim do Universo",
        "alt_titles": [
            "O Maior Mapa 3D do Cosmos Revelou Uma Rachadura na Energia Escura?",
            "Big Freeze ou Big Crunch? O Novo Mistério da Energia Escura pelo Projeto DESI"
        ],
        "topic": "Energia Escura Dinâmica, Projeto DESI, Constante Cosmológica e o Destino Final do Cosmos",
        "summary": "O maior mapa tridimensional de galáxias já feito pelo instrumento DESI trouxe pistas intrigantes de que a Energia Escura pode não ser uma constante imóvel de Einstein.",
        "tags": ["scapatici tecnologia", "energia escura", "desi", "cosmologia", "einstein", "fim do universo", "astrofisica", "ciencia"],
        "thumbnail_text": {"line1": "A ENERGIA ESCURA", "line2": "ESTÁ MUDANDO?", "subtitle": "O DESTINO DO UNIVERSO PODE SER OUTRO | SCAPATICI TECNOLOGIA"},
        "thumb_query": "cosmic web galaxies map dark energy large scale structure nasa",
        "cta_headline": "UM NOVO DESTINO PARA O COSMOS?",
        "cta_question": "E você, o que acha da possibilidade de a Energia Escura estar enfraquecendo e mudar o futuro do universo?",
        "shorts_narration": (
            "Sessenta e oito por cento de tudo o que existe no universo é composto por uma força invisível e misteriosa chamada Energia Escura — a força antigravitacional que empurra as galáxias para longe umas das outras cada vez mais rápido! "
            "Durante vinte e cinco anos, o modelo padrão da cosmologia considerava que essa energia era uma constante absoluta e imutável no tecido do vácuo, exatamente como a constante cosmológica de Albert Einstein. "
            "Mas os novos dados do instrumento DESI — que construiu o maior mapa tridimensional do cosmos observando milhões de galáxias e quasares ao longo de onze bilhões de anos de história — revelaram uma anomalia sísmica: há indícios crescentes de que a Energia Escura pode estar mudando e enfraquecendo ao longo do tempo! "
            "Por que isso importa? Porque todo o destino final do universo depende dessa força! Se ela fosse constante, o cosmos se expandiria para sempre até congelar na escuridão eterna. "
            "Mas se a Energia Escura continuar enfraquecendo — ou até inverter de sinal no futuro distante — a gravidade pode recuperar o controle e puxar todo o universo de volta para um Grande Colapso cósmico! "
            "A investigação completa está no vídeo principal do YouTube: "
            "acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
        ),
        "queries": [
            "dark energy galaxies cosmic web 3d map nasa",
            "kitt peak observatory telescope night sky stars",
            "expanding universe timeline big bang nasa",
            "hubble deep field distant galaxies clusters",
            "galaxy cluster gravitational arcs hubble nasa",
            "euclid space telescope dark universe esa nasa",
            "milky way deep space cosmology stars"
        ],
        "acts": [
            {"key": "hook", "type": "hook", "headline": "68% DO UNIVERSO EM SUSPEITA", "highlights": ["ENERGIA ESCURA", "DESI", "68% DO COSMOS"], "stat_label": "Composição Cósmica", "stat_value": "68% Energia Escura",
             "narration": "Quando você olha para todas as estrelas, planetas, buracos negros e nuvens de gás no universo, tudo isso soma menos de cinco por cento da realidade. Sessenta e oito por cento de todo o orçamento energético do cosmos pertencem à Energia Escura: uma força invisível que acelera a expansão do espaço-tempo como se o vácuo empurrasse as galáxias para fora."},
            {"key": "lambda", "type": "investigation", "headline": "O DOGMA DA CONSTANTE COSMOLÓGICA", "highlights": ["CONSTANTE COSMOLÓGICA", "MODELO LAMBDA", "EINSTEIN"], "stat_label": "Equação Padrão", "stat_value": "Lambda = Constante Fixa",
             "narration": "Desde mil novecentos e noventa e oito, o modelo cosmológico padrão trata a Energia Escura como uma constante imutável do próprio espaço vazio: a letra grega Lambda nas equações de Albert Einstein. Segundo essa regra, cada metro cúbico de espaço novo que nasce carrega exatamente a mesma densidade de energia repulsiva por toda a eternidade."},
            {"key": "desi", "type": "revelation", "headline": "O MAIOR MAPA 3D JÁ CONSTRUÍDO", "highlights": ["PROJETO DESI", "5 MIL OLHOS ROBÓTICOS", "11 BILHÕES DE ANOS"], "stat_label": "Galáxias Mapeadas", "stat_value": "+15 Milhões de Objetos",
             "narration": "Instalado no Arizona, o instrumento espectroscópico DESI utiliza cinco mil fibras ópticas robóticas que apontam simultaneamente para milhares de galáxias em cada exposição. Ao medir as marcas fósseis de ondas acústicas do universo primordial, os cientistas reconstruíram onze bilhões de anos de história da expansão cósmica com precisão sem precedentes."},
            {"key": "evolution", "type": "investigation", "headline": "A ENERGIA ESCURA PODE ESTAR ENFRAQUECENDO", "highlights": ["QUINTESSÊNCIA", "ENERGIA DINÂMICA", "DESVIO DO MODELO"], "stat_label": "Sinal Estatístico", "stat_value": "2,5 a 3,9 Sigma",
             "narration": "Ao cruzar os dados do DESI com explosões de supernovas e o brilho residual do Big Bang, surgiu um sinal inesperado: a expansão parece não se comportar exatamente como uma constante perfeita! Os indícios apontam que a Energia Escura pode ter sido mais forte há bilhões de anos e estar evoluindo como um campo quântico dinâmico chamado Quintessência."},
            {"key": "fate", "type": "climax", "headline": "BIG FREEZE, BIG RIP OU BIG CRUNCH?", "highlights": ["BIG CRUNCH", "BIG FREEZE", "DESTINO FINAL"], "stat_label": "Cenários Cósmicos", "stat_value": "3 Destinos Possíveis",
             "narration": "Se uma constante fixa leva inevitavelmente ao Grande Congelamento — um universo frio, vazio e morto — uma Energia Escura variável abre cenários vertiginosos. Caso ela cresça, pode rasgar átomos no Big Rip; mas se ela continuar enfraquecendo como sugerem algumas interpretações, a expansão poderá frear, reverter e culminar em um colapso gravitacional catastrófico chamado Big Crunch."},
            {"key": "euclid", "type": "investigation", "headline": "A CAÇA DEFINITIVA COM EUCLID E ROMAN", "highlights": ["TELESCÓPIO EUCLID", "NANCY GRACE ROMAN", "PROVA"], "stat_label": "Missões Dedicadas", "stat_value": "Euclid + Roman + DESI",
             "narration": "Na física, três sigma ainda é uma pista forte, não uma sentença final de cinco sigma. Por isso, o telescópio espacial europeu Euclid e o futuro observatório Nancy Grace Roman da NASA estão mapeando bilhões de galáxias distorcidas por lentes gravitacionais para confirmar de vez se Einstein acertou na constante ou se descobrimos uma nova física além do Modelo Padrão."},
            {"key": "vacuum", "type": "investigation", "headline": "O PIOR ERRO TEÓRICO DA HISTÓRIA", "highlights": ["PROBLEMA DO VÁCUO", "120 ORDENS", "FÍSICA QUÂNTICA"], "stat_label": "Discrepância", "stat_value": "10¹²⁰ Vezes Maior",
             "narration": "Descobrir que a Energia Escura muda ao longo do tempo também pode resolver a maior vergonha da física teórica: quando a mecânica quântica calcula a energia do vácuo, o resultado é cento e vinte ordens de grandeza maior do que o valor observado no cosmos. Uma energia dinâmica explicaria por que ela foi diluída para um nível tão pequeno que permitiu que estrelas e vidas existissem."}
        ]
    },
    {
        "slug": "quantum-computing-reality",
        "keywords": ["quantum", "qubit", "computador quantico", "computacao quantica", "willow", "multiverse"],
        "title": "Computação Quântica: Como Um Qubit Calcula na Fronteira da Realidade",
        "alt_titles": [
            "Por Que Um Chip Quântico Quebra Criptografias Que Levariam Trilhões de Anos?",
            "Superposição e Entrelaçamento: A Física Por Trás dos Computadores Quânticos"
        ],
        "topic": "Computação Quântica, Qubits, Superposição, Correção de Erros e Criptografia",
        "summary": "Entenda como processadores resfriados perto do zero absoluto usam superposição e interferência quântica para resolver problemas fora do alcance dos supercomputadores.",
        "tags": ["scapatici tecnologia", "computacao quantica", "qubit", "fisica quantica", "tecnologia", "multiverso", "ciencia"],
        "thumbnail_text": {"line1": "PODER QUÂNTICO", "line2": "INIMAGINÁVEL!", "subtitle": "COMO FUNCIONA UM QUBIT DE VERDADE | SCAPATICI TECNOLOGIA"},
        "thumb_query": "quantum computer dilution refrigerator gold chandelier technology",
        "cta_headline": "A ERA PÓS-CLÁSSICA COMEÇOU",
        "cta_question": "E você, acha que os computadores quânticos vão desvendar a cura de doenças e novos materiais antes do que imaginamos?",
        "shorts_narration": (
            "Um problema matemático que levaria dez septilhões de anos — bilhões de vezes mais do que a idade inteira do universo — para o maior supercomputador clássico da Terra resolver acaba de ser executado em apenas cinco minutos por um processador quântico moderno! "
            "Mas como um chip do tamanho de uma moeda consegue tamanha vantagem? "
            "Tudo começa na diferença radical entre um bit clássico e um qubit! Um bit de celular ou computador comum só pode estar em um único estado de cada vez: zero ou um. "
            "Já um qubit explora a Superposição Quântica: enquanto não é observado, ele existe em uma combinação complexa de zero e um ao mesmo tempo! "
            "Quando você entrelaça apenas trezentos qubits em coerência, eles conseguem manipular simultaneamente mais combinações matemáticas do que o número total de átomos em todo o universo observável! "
            "Mas atenção: o segredo não é testar todas as respostas por força bruta — um computador quântico usa interferência de ondas, fazendo as respostas erradas se cancelarem como ondas opostas na água enquanto a resposta certa é amplificada! "
            "Para manter esse estado frágil livre de ruído térmico, o chip precisa trabalhar suspenso em candelabros dourados a quinze milikelvin — cem vezes mais frio que o espaço profundo! "
            "A investigação completa está no vídeo principal do YouTube: "
            "acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
        ),
        "queries": [
            "quantum computer laboratory superconducting processor nasa",
            "cryogenic refrigerator physics experiment laboratory",
            "quantum entanglement laser optics laboratory",
            "supercomputer data center cluster technology",
            "atomic lattice crystal quantum physics microscope",
            "protein folding molecular chemistry simulation",
            "deep space cosmic computing stars nebula"
        ],
        "acts": [
            {"key": "hook", "type": "hook", "headline": "5 MINUTOS CONTRA A ETERNIDADE", "highlights": ["COMPUTAÇÃO QUÂNTICA", "QUBIT", "SEPTILHÕES DE ANOS"], "stat_label": "Diferença de Escala", "stat_value": "5 Min vs 10²⁵ Anos",
             "narration": "Os processadores clássicos que movem o mundo moderno transformaram a civilização, mas possuem uma limitação fundamental diante de sistemas moleculares e combinações astronômicas. Para simular perfeitamente uma única molécula complexa de catalisador, um supercomputador clássico precisaria de mais memória do que existe matéria na Terra — e é aí que entra a computação quântica."},
            {"key": "superposition", "type": "investigation", "headline": "BIT CLÁSSICO VERSUS QUBIT", "highlights": ["SUPERPOSIÇÃO", "ZERO E UM", "ONDA"], "stat_label": "Estado Quântico", "stat_value": "Esfera de Bloch (Superposição)",
             "narration": "Cada transistor de silício funciona como um interruptor: ligado ou desligado, um ou zero. Um qubit, feito de loops supercondutores ou íons presos por lasers, comporta-se como uma onda quântica capaz de carregar uma amplitude de probabilidade para zero e um simultaneamente, permitindo que o espaço de cálculo cresça exponencialmente a cada novo qubit adicionado."},
            {"key": "interference", "type": "revelation", "headline": "O SEGREDO DA INTERFERÊNCIA QUÂNTICA", "highlights": ["INTERFERÊNCIA", "ALGORITMO", "CONCELAMENTO"], "stat_label": "Mecanismo Real", "stat_value": "Amplificação de Ondas",
             "narration": "Muita gente pensa que o computador quântico testa todas as respostas em paralelo e lê todas juntas. Na prática, se você medir direto, obtém apenas um único resultado aleatório! A genialidade dos algoritmos quânticos como os de Peter Shor e Lov Grover está em programar as fases dessas ondas de probabilidade para que as soluções erradas se destruam por interferência destrutiva, deixando apenas a resposta certa brilhar na medição final."},
            {"key": "cold", "type": "investigation", "headline": "MAIS FRIO QUE O ESPAÇO PROFUNDO", "highlights": ["15 MILIKELVIN", "DECOERÊNCIA", "ZERO ABSOLUTO"], "stat_label": "Temperatura do Chip", "stat_value": "-273,13 °C (15 mK)",
             "narration": "O maior inimigo de um processador quântico é a decoerência: qualquer vibração mecânica, campo magnético ou fóton de calor vindo do ambiente funciona como uma observação não desejada que destrói a superposição em microssegundos. Por isso, os chips supercondutores ficam na base de refrigeradores de diluição dourados a quinze milikelvin — mais frio do que a radiação residual do espaço interestelar."},
            {"key": "correction", "type": "investigation", "headline": "A REVOLUÇÃO DA CORREÇÃO DE ERROS", "highlights": ["CORREÇÃO DE ERROS", "CÓDIGO DE SUPERFÍCIE", "LIMIAR"], "stat_label": "Avanço Crítico", "stat_value": "Erro Cai ao Crescer",
             "narration": "Por décadas, críticos afirmavam que quanto mais qubits você colocasse em um chip, mais erros acumulariam até tornar a máquina inútil. Recentemente, físicos cruzaram o chamado limiar de correção de erros quânticos: combinando dezenas de qubits físicos imperfeitos em um único qubit lógico, o aumento da grade finalmente passou a reduzir exponencialmente a taxa de erro em vez de ampliá-la."},
            {"key": "impact", "type": "climax", "headline": "CRIPTOGRAFIA E MEDICINA TRANSFORMADAS", "highlights": ["ALGORITMO DE SHOR", "BATERIAS", "MEDICINA"], "stat_label": "Área de Impacto", "stat_value": "Materiais e Criptografia",
             "narration": "Quando computadores quânticos tolerantes a falhas atingirem milhares de qubits lógicos, o impacto será duplo. De um lado, o Algoritmo de Shor poderá fatorar números gigantescos em horas, obrigando bancos e governos a migrar para criptografia pós-quântica. De outro, poderemos projetar fertilizantes ecológicos, baterias revolucionárias, supercondutores e novos fármacos com precisão atômica absoluta."},
            {"key": "multiverse", "type": "investigation", "headline": "CALCULANDO EM PARALELO COM A NATUREZA", "highlights": ["DAVID DEUTSCH", "NATUREZA QUÂNTICA", "FRONTEIRA"], "stat_label": "Visão Física", "stat_value": "Simular a Própria Realidade",
             "narration": "Como disse o físico Richard Feynman, a natureza não é clássica; se você quer simular o universo em seu nível fundamental, é melhor construir um computador que fale a língua quântica nativa da realidade."}
        ]
    },
    {
        "slug": "carrington-solar-superstorm",
        "keywords": ["solar storm", "carrington", "sun", "flare", "cme", "solar", "tempestade solar", "apagao"],
        "title": "Supertempestades Solares: Como Uma Erupção do Sol Pode Parar o Planeta",
        "alt_titles": [
            "O Evento Carrington: O Dia em Que o Sol Incendiou Telégrafos na Terra",
            "Tempestade Solar Extrema: Estamos Preparados Para Um Apagão Global?"
        ],
        "topic": "Evento Carrington, Ejeção de Massa Coronal, Tempestades Geomagnéticas e Redes Elétricas",
        "summary": "Em 1859, uma erupção solar gigantesca acendeu auroras nos trópicos e deu choque em telégrafos desligados. O que aconteceria se uma igual atingisse nossa rede digital hoje?",
        "tags": ["scapatici tecnologia", "tempestade solar", "evento carrington", "sol", "astronomia", "tecnologia", "apagao", "ciencia"],
        "thumbnail_text": {"line1": "SUPERTEMPESTADE", "line2": "DO SOL!", "subtitle": "O RISCO REAL PARA NOSSA CIVILIZAÇÃO DIGITAL | SCAPATICI TECNOLOGIA"},
        "thumb_query": "sun coronal mass ejection solar flare sdo nasa",
        "cta_headline": "NOSSO ESCUDO MAGNÉTICO AGUENTA?",
        "cta_question": "E você, sabia que dependemos tanto de satélites e transformadores vulneráveis ao humor do nosso próprio Sol?",
        "shorts_narration": (
            "No dia primeiro de setembro de mil oitocentos e cinquenta e nove, o astrônomo Richard Carrington observava manchas solares quando viu um clarão cegante irromper da superfície do Sol. "
            "Apenas dezessete horas depois — muito mais rápido do que os três dias normais — uma nuvem bilionária de plasma magnetizado atingiu a Terra de frente no que ficou conhecido como o Evento Carrington! "
            "Naquela noite, auroras boreais vermelhas e verdes iluminaram céus tropicais até no Caribe, permitindo ler jornais de madrugada sem lâmpadas, enquanto operadores de telégrafo levavam choques elétricos mesmo com as baterias completamente desligadas! "
            "Na época, o mundo dependia apenas de fios de cobre simples. Hoje, a nossa civilização inteira — energia elétrica, GPS, aviões, hospitais, bancos e internet — roda sobre redes gigantescas conectadas a satélites e transformadores de altíssima tensão! "
            "Se uma supertempestade de classe Carrington acertasse a Terra em cheio hoje, correntes geomagnéticas induzidas no solo poderiam sobrecarregar transformadores gigantes difíceis de substituir, além de desorientar satélites em órbita baixa! "
            "É por isso que sondas como a Parker Solar Probe voam dentro da atmosfera do Sol para prever essas tempestades com antecedência vital. "
            "A investigação completa está no vídeo principal do YouTube: "
            "acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
        ),
        "queries": [
            "solar dynamics observatory x class flare sun nasa",
            "earth magnetosphere solar wind shield simulation nasa",
            "aurora borealis green space station earth nasa",
            "parker solar probe approaching sun corona nasa",
            "earth city lights night power grid space station",
            "satellite constellation earth orbit technology nasa",
            "sunspots active region magnetic loop nasa"
        ],
        "acts": [
            {"key": "hook", "type": "hook", "headline": "17 HORAS ATÉ O IMPACTO SOLAR", "highlights": ["EVENTO CARRINGTON", "1859", "ERUPÇÃO SOLAR"], "stat_label": "Velocidade da CME", "stat_value": "+2.400 Km por Segundo",
             "narration": "O Sol parece calmo e constante no céu de todos os dias, mas é uma bomba de fusão magnetizada que gira de forma desigual, retorcendo suas linhas de campo magnético até que elas se rompem violentamente. Em setembro de mil oitocentos e cinquenta e nove, uma dessas rupturas lançou contra a Terra a maior tempestade geomagnética já registrada pela ciência moderna."},
            {"key": "history", "type": "investigation", "headline": "TELÉGRAFOS FUNCIONANDO SEM BATERIAS", "highlights": ["TELÉGRAFOS", "AURORAS TROPICAIS", "INDUÇÃO"], "stat_label": "Alcance das Auroras", "stat_value": "Até a Linha do Equador",
             "narration": "Durante o Evento Carrington, a magnetosfera terrestre foi comprimida pela metade enquanto bilhões de toneladas de plasma eletrificado despejavam correntes imensas na atmosfera. Auroras brilhavam intensas em Cuba e no Havaí, e as linhas telegráficas absorveram tanta eletricidade induzida do ar que máquinas continuaram transmitindo mensagens mesmo após os técnicos desconectarem todas as pilhas."},
            {"key": "grid", "type": "revelation", "headline": "O PONTO FRACO DA ERA DIGITAL", "highlights": ["TRANSFORMADORES", "CABOS LONGOS", "REDES ELÉTRICAS"], "stat_label": "Tempo de Troca", "stat_value": "Meses por Transformador",
             "narration": "Quando o campo magnético terrestre vibra rapidamente, longas linhas de transmissão metálicas funcionam como antenas gigantes que captam correntes contínuas induzidas pelo solo. Esse excesso elétrico penetra em transformadores pesados de subestações, superaquecendo o óleo isolante e podendo fundir bobinas de cobre de centenas de toneladas fabricadas apenas sob encomenda."},
            {"key": "gps", "type": "investigation", "headline": "O IMPACTO NA ÓRBITA E NA NAVEGAÇÃO", "highlights": ["SATÉLITES", "ARRASTO ATMOSFÉRICO", "GPS"], "stat_label": "Risco Orbital", "stat_value": "Perda de Sinal e Altitude",
             "narration": "Lá em cima, a tempestade aquece e expande a alta atmosfera terrestre, aumentando subitamente o atrito do ar sobre satélites em órbita baixa e derrubando aparelhos desprotegidos. Ao mesmo tempo, explosões de raios X e partículas energéticas embaralham os sinais de rádio de precisão usados por navios, aviões em rotas polares e sistemas de sincronização bancária do GPS."},
            {"key": "near_miss", "type": "climax", "headline": "O QUASE IMPACTO DE 2012", "highlights": ["2012", "9 DIAS DE DIFERENÇA", "CLASSE X"], "stat_label": "Margem de Sorte", "stat_value": "Apenas 9 Dias na Órbita",
             "narration": "Isso não é um risco apenas dos livros de história do século dezenove. Em julho de dois mil e doze, o Sol disparou uma ejeção de massa coronal equivalente em força ao Evento Carrington que cruzou exatamente o ponto da órbita terrestre — com uma diferença de apenas nove dias de onde a Terra estava! Se tivesse acontecido uma semana antes, teríamos enfrentado blecautes regionais históricos."},
            {"key": "miyake", "type": "investigation", "headline": "OS EVENTOS MIYAKE NOS ANÉIS DAS ÁRVORES", "highlights": ["EVENTOS MIYAKE", "CARBONO-14", "10X MAIS FORTE"], "stat_label": "Superexplosão Antiga", "stat_value": "Ano 774 d.C. (10x Maior)",
             "narration": "Estudando picos súbitos de Carbono catorze preservados em anéis de árvores milenares e núcleos de gelo da Antártica, a física Fusa Miyake descobriu marcas de tempestades solares dez vezes mais violentas que a de Carrington ocorridas há mais de mil e duzentos anos — provando que o Sol guarda reservas de fúria ainda maiores em escalas milenares."},
            {"key": "defense", "type": "investigation", "headline": "AS SENTINELAS DE DEFESA ESPACIAL", "highlights": ["SOHO", "PARKER SOLAR PROBE", "PREVISÃO"], "stat_label": "Alerta Precoce", "stat_value": "Monitoramento 24/7",
             "narration": "A grande vantagem do século vinte e um é que não somos mais pegos de surpresa: satélites sentinelas posicionados entre o Sol e a Terra medem o campo magnético das ejeções com minutos a horas de antecedência, permitindo que operadores desliguem preventivamente linhas vulneráveis e coloquem naves em modo de segurança até a onda cósmica passar."}
        ]
    },
    {
        "slug": "oumuamua-interstellar-visitors",
        "keywords": ["oumuamua", "interstellar", "comet", "visitor", "vera rubin", "borisov"],
        "title": "Visitantes Interestelares: O Mistério de Oumuamua e os Próximos Viajantes",
        "alt_titles": [
            "O Que Realmente Era Oumuamua? O Primeiro Mensageiro de Outra Estrela",
            "Por Que Oumuamua Acelerou ao Deixar o Sol Sem Soltar Nenhuma Cauda Visível?"
        ],
        "topic": "Oumuamua, Cometa Borisov, Visitantes Interestelares e Observatório Vera Rubin",
        "summary": "Em 2017, um objeto alongado cruzou o Sistema Solar vindo do espaço entre as estrelas, girou estranhamente e acelerou para longe do Sol sem rastro de cometa visível.",
        "tags": ["scapatici tecnologia", "oumuamua", "visitantes interestelares", "astronomia", "nasa", "vera rubin", "universo", "ciencia"],
        "thumbnail_text": {"line1": "VEIO DE FORA", "line2": "DO SISTEMA SOLAR!", "subtitle": "O MISTÉRIO NÃO RESOLVIDO DE OUMUAMUA | SCAPATICI TECNOLOGIA"},
        "thumb_query": "interstellar asteroid elongated space stars nasa",
        "cta_headline": "QUANTOS ESTÃO PASSANDO AGORA?",
        "cta_question": "E você, acha que o próximo visitante interestelar detectado pelo Observatório Vera Rubin nos trará uma resposta definitiva?",
        "shorts_narration": (
            "Em outubro de dois mil e dezessete, telescópios no Havaí avistaram algo que nunca havia sido visto antes na história da astronomia: uma rocha ou objeto desconhecido atravessando o Sistema Solar tão rápido que não pertencia ao nosso Sol — ele havia chegado de outra estrela na galáxia! "
            "Batizado de Oumuamua, o batedor vindo de longe, o objeto exibiu quatro comportamentos bizarros que iniciaram um dos maiores debates da ciência recente. "
            "Primeiro, suas variações de brilho indicavam um formato extremo — cerca de seis a dez vezes mais comprido do que largo, como um charuto ou uma panqueca espacial girando em queda livre. "
            "Segundo, ele não tinha nenhuma cauda visível de poeira ou vapor d'água como todo cometa comum. "
            "Mas o terceiro ponto acendeu todos os alarmes: ao passar perto do Sol e começar a ir embora, Oumuamua recebeu uma aceleração extra misteriosa que não vinha só da gravidade! "
            "A teoria mais aceita atualmente aponta para hidrogênio molecular aprisionado em gelo comum que evaporou de forma invisível sob o calor solar, funcionando como micropropulsores naturais! "
            "E o novo Observatório Vera Rubin está prestes a descobrir dezenas desses viajantes vindos de outros mundos! "
            "A investigação completa está no vídeo principal do YouTube: "
            "acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
        ),
        "queries": [
            "interstellar object space silhouette stars nasa",
            "pan-starrs observatory haleakala hawaii stars",
            "comet tail ice sublimation solar system nasa",
            "solar system orbit trajectory spacecraft nasa",
            "vera rubin observatory telescope dome stars",
            "milky way stars stellar neighborhood deep space",
            "deep space asteroid rocky surface close up nasa"
        ],
        "acts": [
            {"key": "hook", "type": "hook", "headline": "O PRIMEIRO VIAJANTE DE OUTRA ESTRELA", "highlights": ["OUMUAMUA", "ÓRBITA HIPERBÓLICA", "315 MIL KM/H"], "stat_label": "Velocidade de Entrada", "stat_value": "95.000 km/h (Até 315 mil)",
             "narration": "Todos os asteroides e cometas do nosso Sistema Solar obedecem a órbitas elípticas fechadas, aprisionados eternamente pela gravidade do Sol. Mas em outubro de dois mil e dezessete, um ponto de luz fugaz mostrou uma trajetória hiperbólica aberta tão veloz que era impossível ter nascido aqui: pela primeira vez, testemunhamos um mensageiro sólido vindo do espaço interestelar."},
            {"key": "shape", "type": "investigation", "headline": "UM FORMATO SEM PRECEDENTES", "highlights": ["BRILHO VARIÁVEL", "PANQUECA CÓSMICA", "ROTAÇÃO"], "stat_label": "Proporção Extrema", "stat_value": "Até 10:1 (Comprimento/Largura)",
             "narration": "Pequeno demais para gerar fotos diretas com pixels detalhados, Oumuamua revelava sua geometria pelas pulsações de luz solar refletida a cada oito horas. Seu brilho caía e subia dez vezes mais rápido que o normal — algo que só ocorre com um objeto extremamente achatado ou alongado girando caoticamente depois de algum choque violento no passado."},
            {"key": "acceleration", "type": "revelation", "headline": "A ACELERAÇÃO FANTASMA SEM CAUDA", "highlights": ["ACELERAÇÃO NÃO-GRAVITACIONAL", "SEM CAUDA", "ENIGMA"], "stat_label": "Anomalia Orbital", "stat_value": "Empuxo Extra Sem Poeira",
             "narration": "Quando um cometa comum se aproxima do Sol, o gelo derrete liberando jatos visíveis de água e poeira que empurram o núcleo como pequenos foguetes. Oumuamua mostrou exatamente esse empurrão extra desviando sua saída, porém nem o telescópio Spitzer em infravermelho encontrou um único traço de carbono ou nuvem de poeira ao redor dele."},
            {"key": "hydrogen", "type": "investigation", "headline": "A CHAVE DO HIDROGÊNIO APRISIONADO", "highlights": ["HIDROGÊNIO", "RAIOS CÓSMICOS", "GELO"], "stat_label": "Solução Física", "stat_value": "Sublimação Invisível de H₂",
             "narration": "A explicação científica mais elegante surgiu com um mecanismo sutil: durante milhões de anos viajando fora de estrelas, raios cósmicos bombardeiam um bloco comum de gelo de água, quebrando moléculas e prendendo bolhas de gás hidrogênio lá dentro. Ao aquecer perto do Sol, esse gelo libera um jato invisível de hidrogênio puro — forte o bastante para acelerar um objeto pequeno sem arrastar poeira pesada."},
            {"key": "borisov", "type": "investigation", "headline": "BORISOV: O SEGUNDO VISITANTE CONFIRMA A REGRA", "highlights": ["COMETA BORISOV", "MONÓXIDO DE CARBONO", "2019"], "stat_label": "Visitante #2", "stat_value": "2I/Borisov (Rico em CO)",
             "narration": "Apenas dois anos depois, o astrônomo amador Gennady Borisov descobriu o segundo visitante interestelar confirmado. Ao contrário de Oumuamua, Borisov comportou-se exatamente como um cometa clássico cercado por uma imensa coma brilhante rica em monóxido de carbono, provando que há uma enorme diversidade química entre objetos ejetados de outros sistemas planetários."},
            {"key": "rubin", "type": "climax", "headline": "O OBSERVATÓRIO QUE VAI DESCOBRIR DEZENAS", "highlights": ["VERA RUBIN", "CÂMERA DE 3.2 GIGAPIXELS", "INTERCEPTAÇÃO"], "stat_label": "Nova Capacidade", "stat_value": "Mapeia o Céu Todo em 3 Dias",
             "narration": "Estima-se que, a qualquer instante, vários objetos interestelares estejam passando silenciosamente dentro da órbita de Marte sem que tenhamos notado. Com a câmera de três vírgula dois gigapixels do Observatório Vera Rubin varrendo o céu inteiro repetidamente, estamos entrando em uma era capaz de identificar esses viajantes meses antes de chegarem perto do Sol."},
            {"key": "comet_interceptor", "type": "investigation", "headline": "MISSÕES PRONTAS PARA PERSEGUIR UM ALVO", "highlights": ["COMET INTERCEPTOR", "FOTOGRAFIA DE PERTO", "EXOPLANETAS"], "stat_label": "Estratégia Futura", "stat_value": "Nave Estacionada no Ponto L2",
             "narration": "A Agência Espacial Europeia já prepara a missão Comet Interceptor, uma sonda que ficará estacionada aguardando em órbita pronta para acelerar e interceptar um novo visitante interestelar logo que for avistado — permitindo pela primeira vez tocarmos e fotografarmos de perto um fragmento físico nascido em volta de outra estrela da Via Láctea."}
        ]
    },
    {
        "slug": "alcubierre-warp-drive-physics",
        "keywords": ["warp drive", "alcubierre", "dobra", "wormhole", "buraco de minhoca", "faster than light"],
        "title": "Motor de Dobra de Alcubierre: Como Distorcer o Espaço Sem Quebrar Einstein?",
        "alt_titles": [
            "É Possível Viajar Mais Rápido Que a Luz Sem Desrespeitar a Relatividade?",
            "A Física Real do Motor de Dobra Espacial e o Problema da Energia Negativa"
        ],
        "topic": "Métrica de Alcubierre, Motor de Dobra Espacial, Energia Negativa e Viagem Interestelar",
        "summary": "Em 1994, o físico Miguel Alcubierre encontrou uma brecha matemática exata nas equações de Einstein que permite atravessar anos-luz comprimindo o espaço à frente.",
        "tags": ["scapatici tecnologia", "motor de dobra", "alcubierre", "einstein", "relatividade", "viagem espacial", "fisica", "ciencia"],
        "thumbnail_text": {"line1": "DOBRAR O", "line2": "ESPAÇO-TEMPO!", "subtitle": "A BRECHA REAL NAS EQUAÇÕES DE EINSTEIN | SCAPATICI TECNOLOGIA"},
        "thumb_query": "spacecraft warp space time grid relativity stars",
        "cta_headline": "UM ATALHO ENTRE AS ESTRELAS?",
        "cta_question": "E você, acredita que uma física quântica ainda mais profunda permitirá um dia comprimir o espaço entre estrelas?",
        "shorts_narration": (
            "Nada que possui massa pode viajar através do espaço mais rápido do que a luz. Mas e se você não precisasse se mover através do espaço — e fizesse o próprio espaço se mover por você? "
            "Em mil novecentos e noventa e quatro, o físico mexicano Miguel Alcubierre pegou as equações exatas da Relatividade Geral de Einstein e descobriu uma brecha matemática impressionante! "
            "Na física, nada proíbe o próprio tecido do espaço-tempo de expandir ou contrair mais rápido que a velocidade da luz — foi exatamente isso que aconteceu logo após o Big Bang! "
            "A Métrica de Alcubierre propõe cercar uma nave por uma bolha espacial: ela contrai violentamente o espaço bem à frente da proa e o expande atrás da popa! "
            "Dentro dessa bolha plana, os astronautas ficariam literalmente parados sem sentir nenhuma força G nem dilatação temporal, enquanto surfam a onda espacial cruzando distâncias interestelares rapidamente! "
            "O enorme obstáculo? Os cálculos originais exigiam densidades impossíveis de energia negativa exótica — algo em quantidade maior que a massa de Júpiter! "
            "Contudo, novos artigos recentes já buscaram soluções geométricas que eliminam a necessidade de energia negativa exótica para bolhas subluminais, aproximando a teoria da física conhecida! "
            "A investigação completa está no vídeo principal do YouTube: "
            "acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
        ),
        "queries": [
            "interstellar spacecraft futuristic concept stars",
            "gravitational wave spacetime grid simulation",
            "quantum vacuum casimir effect physics experiment",
            "alpha centauri star system space telescopes",
            "einstein general relativity curved spacetime cosmos",
            "relativistic jet high energy space beam",
            "deep space nebula stars exploration"
        ],
        "acts": [
            {"key": "hook", "type": "hook", "headline": "A PRISÃO DOS 4 ANOS-LUZ", "highlights": ["ALFA CENTAURI", "40 MIL ANOS", "BARREIRA CÓSMICA"], "stat_label": "Estrela Mais Próxima", "stat_value": "4,24 Anos-Luz (40 Trilhões km)",
             "narration": "Mesmo a nossa estrela vizinha mais próxima, Próxima Centauri, fica a mais de quarenta trilhões de quilômetros. Com os melhores foguetes químicos atuais, uma viagem até lá consumiria mais de setenta mil anos. A barreira da velocidade da luz parece transformar a galáxia inteira em um oceano impossível de cruzar dentro de uma vida humana."},
            {"key": "loophole", "type": "investigation", "headline": "O TRUQUE DA ESTEIRA ROLANTE CÓSMICA", "highlights": ["ESPAÇO EXPANDINDO", "BIG BANG", "RELATIVIDADE"], "stat_label": "Regra de Einstein", "stat_value": "O Espaço Pode Expandir > C",
             "narration": "A Relatividade Especial proíbe qualquer objeto de acelerar acima da velocidade da luz em relação ao espaço local ao seu redor. Contudo, a Relatividade Geral mostra que o próprio espaço é dinâmico: galáxias muito distantes se afastam de nós mais rápido do que a luz hoje mesmo porque o tecido entre nós e elas está crescendo. Foi dessa propriedade que nasceu o conceito de dobra espacial."},
            {"key": "alcubierre", "type": "revelation", "headline": "A EQUAÇÃO REAL DE MIGUEL ALCUBIERRE", "highlights": ["MIGUEL ALCUBIERRE", "BOLHA DE DOBRA", "1994"], "stat_label": "Efeito Interno", "stat_value": "Gravidade Zero na Cabine",
             "narration": "Em mil novecentos e noventa e quatro, Miguel Alcubierre publicou uma solução matemática legítima para as equações de Einstein: uma bolha plana de espaço-tempo rodeada por uma casca energética que comprime a distância à frente e a dilata atrás. Dentro do centro calmo dessa bolha, uma espaçonave jamais ultrapassa localmente o limite da luz, escapando até dos efeitos do paradoxo dos gêmeos."},
            {"key": "exotic", "type": "investigation", "headline": "O MURO DA ENERGIA NEGATIVA", "highlights": ["MATÉRIA EXÓTICA", "EFEITO CASIMIR", "MASSA NEGATIVA"], "stat_label": "Custo Original", "stat_value": "Maior Que Toda a Via Láctea",
             "narration": "Onde está o grande problema? Para manter uma bolha superluminal estável na equação original, seria preciso preencher as paredes da nave com enormes quantidades de densidade de energia negativa — algo que na natureza observamos apenas em escalas microscópicas através do Efeito Casimir no vácuo quântico, trilhões de ordens abaixo do necessário para mover uma única molécula."},
            {"key": "new_models", "type": "investigation", "headline": "REFORMULANDO AS SOLUÇÕES SUBLUMINAIS", "highlights": ["LENTZ / BOBRICK", "SEM ENERGIA NEGATIVA", "SUBLUMINAL"], "stat_label": "Avanço Teórico", "stat_value": "Bolhas de Energia Positiva",
             "narration": "Nos últimos anos, grupos de físicos teóricos publicaram novas métricas geométricas demonstrando que bolhas de dobra operando abaixo da velocidade da luz não violam as condições de energia positiva conhecidas! Embora ainda exijam quantidades astronômicas de massa comprimida em camadas finíssimas, essas equações tiraram o tópico do campo puramente impossível."},
            {"key": "hazards", "type": "climax", "headline": "O PERIGO DE CHEGAR AO DESTINO", "highlights": ["RADIAÇÃO DE HAWKING", "PARTÍCULAS PRESAS", "EXPLOSÃO NA PARADA"], "stat_label": "Risco Quântico", "stat_value": "Feixe Letal ao Frear",
             "narration": "Mesmo que um dia dominemos a energia para criar uma bolha superluminal, cálculos adicionais revelam dois riscos extremos: um horizonte interno aqueceria a cabine pela própria Radiação de Hawking, e todas as partículas espaciais varridas pela borda dianteira acumulariam energia infinita, sendo disparadas como um canhão mortal de raios gama no instante em que a nave freasse no destino."},
            {"key": "value", "type": "investigation", "headline": "POR QUE ESTUDAR EQUAÇÕES TÃO EXTREMAS?", "highlights": ["GRAVIDADE QUÂNTICA", "FRONTEIRAS DA FÍSICA", "FUTURO"], "stat_label": "Benefício Real", "stat_value": "Testar Limites da Gravidade",
             "narration": "Estudar métricas extremas como a de Alcubierre serve como laboratório mental indispensável para testar onde a Relatividade Geral de Einstein se choca com a mecânica quântica — guiando os físicos até a tão sonhada Teoria de Tudo."}
        ]
    }
]


def _score_blueprint_against_trends(bp: dict, trends: list) -> tuple[int, dict | None]:
    best_score = 0
    best_match = None
    kws = [k.lower() for k in bp.get("keywords", [])]
    for tr in trends:
        haystack = f"{tr['title']} {tr['summary']}".lower()
        hits = sum(1 for k in kws if k in haystack)
        if hits > best_score:
            best_score = hits
            best_match = tr
    return best_score, best_match


def _synthesize_fallback_from_trend(trend: dict, num: int) -> dict:
    """Sintetiza um projeto completo diretamente de uma tendência ao vivo caso o banco base também esgote."""
    raw_title = trend["title"].split(" - ")[0].strip()
    clean_slug = re.sub(r"[^a-z0-9]+", "-", raw_title.lower()).strip("-")[:32] or "cosmic-discovery"
    project_id = f"video-{num:03d}-{clean_slug}"
    safe_title = f"{raw_title[:78]}: A Ciência Por Trás da Descoberta"
    if len(safe_title) > 100:
        safe_title = safe_title[:97].rstrip()

    query_terms = " ".join(re.findall(r"[a-zA-Z]{4,}", raw_title)[:4]) or "deep space cosmos nasa"

    shorts_narration = (
        f"Uma nova atualização científica acaba de chamar atenção nas tendências de astronomia e tecnologia: {raw_title}. "
        f"{trend.get('summary', '')[:240]}. "
        "Para entender por que esse avanço importa tanto para o futuro da ciência, precisamos olhar para os mecanismos físicos envolvidos e para os novos instrumentos de precisão que a humanidade colocou em operação recentemente. "
        "Cada dado inédito coletado por telescópios espaciais, aceleradores ou sondas profundas revela que o universo e a tecnologia avançam em camadas muito mais sofisticadas do que os modelos tradicionais previam. "
        "No canal Scapatici Tecnologia acompanhamos diariamente cada descoberta que redefine os limites do conhecimento. "
        "A investigação completa está no vídeo principal do YouTube: acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
    )

    acts = [
        {"key": "hook", "type": "hook", "headline": "O NOVO ALERTA NAS TENDÊNCIAS", "highlights": ["DESCOBERTA", "CIÊNCIA", "TENDÊNCIA"], "stat_label": "Fonte Original", "stat_value": trend["source"],
         "narration": f"Nas últimas horas, pesquisadores e observatórios internacionais colocaram este assunto no topo das discussões científicas: {raw_title}. Uma descoberta que merece uma investigação aprofundada sob a ótica da física e da tecnologia moderna."},
        {"key": "context", "type": "investigation", "headline": "O QUE OS DADOS REVELARAM", "highlights": ["DADOS REAIS", "OBSERVATÓRIOS", "PRECISÃO"], "stat_label": "Análise Científica", "stat_value": "Observação Confirmada",
         "narration": f"{trend.get('summary', raw_title)}. Quando colocamos essa descoberta em perspectiva histórica, percebemos como a sensibilidade dos sensores modernos mudou nossa capacidade de medir fenômenos quase imperceptíveis."},
        {"key": "physics", "type": "revelation", "headline": "A FÍSICA FUNDAMENTAL ENVOLVIDA", "highlights": ["LEIS DA FÍSICA", "ANÁLISE", "ESCALA"], "stat_label": "Princípio", "stat_value": "Física de Fronteira",
         "narration": "Por trás de toda manchete científica existe uma cadeia rigorosa de equações, conservação de energia e medições repetíveis. Ao investigar os bastidores desses dados, entendemos como cada variável física aponta novos caminhos para os próximos anos de pesquisa."},
        {"key": "tech", "type": "investigation", "headline": "A ENGENHARIA QUE TORNOU ISSO POSSÍVEL", "highlights": ["ENGENHARIA", "TECNOLOGIA", "SENSORES"], "stat_label": "Infraestrutura", "stat_value": "Instrumentação Avançada",
         "narration": "Descobertas dessa magnitude exigem décadas de engenharia criogênica, espectrometria de altíssima resolução e supercomputação distribuída para separar sinais reais de ruídos aleatórios do ambiente."},
        {"key": "debate", "type": "investigation", "headline": "O IMPACTO NOS MODELOS TEÓRICOS", "highlights": ["REVISÃO TEÓRICA", "MODELOS", "NOVAS PERGUNTAS"], "stat_label": "Próximo Passo", "stat_value": "Novas Observações",
         "narration": "Sempre que um novo conjunto de dados confirma ou tensiona os modelos padrão, equipes ao redor do mundo iniciam campanhas independentes de verificação para testar até onde vão as implicações dessa linha de pesquisa."},
        {"key": "future", "type": "climax", "headline": "O QUE MUDA A PARTIR DE AGORA", "highlights": ["FUTURO", "REVOLUÇÃO", "PRÓXIMA DÉCADA"], "stat_label": "Horizonte", "stat_value": "Nova Fronteira Aberta",
         "narration": "O impacto prático e conceitual desse tema ultrapassa os laboratórios acadêmicos, moldando novas gerações de missões espaciais, tecnologias aplicadas e a nossa própria compreensão sobre o lugar da humanidade no cosmos."},
        {"key": "synthesis", "type": "investigation", "headline": "CONECTANDO TODAS AS PISTAS", "highlights": ["SÍNTESE", "CONHECIMENTO", "COSMOS"], "stat_label": "Status", "stat_value": "Investigação Ativa",
         "narration": "À medida que novos artigos científicos são revisados por pares e publicados, seguimos monitorando cada detalhe técnico para trazer até você ciência explicada com clareza, profundidade e precisão."}
    ]

    bp = {
        "slug": clean_slug,
        "title": safe_title,
        "topic": raw_title,
        "summary": trend.get("summary") or raw_title,
        "tags": ["scapatici tecnologia", "ciencia", "astronomia", "tecnologia", "universo", "descobertas"],
        "thumbnail_text": {"line1": "NOVA DESCOBERTA", "line2": "DA CIÊNCIA!", "subtitle": "ANÁLISE COMPLETA | SCAPATICI TECNOLOGIA"},
        "thumb_query": f"{query_terms} space nasa",
        "cta_headline": "ACOMPANHE A FRONTEIRA DA CIÊNCIA",
        "cta_question": "E você, o que acha que essa descoberta significa para os próximos anos da ciência e da exploração espacial?",
        "shorts_narration": shorts_narration,
        "queries": [
            f"{query_terms} dramatic scientific discovery",
            f"{query_terms} laboratory observatory telemetry",
            f"{query_terms} physical mechanism visualization",
            f"{query_terms} advanced engineering instrument",
            f"{query_terms} theoretical model spacetime",
            f"{query_terms} future mission breakthrough",
            f"{query_terms} cosmic horizon perspective"
        ],
        "acts": acts,
    }
    return _assemble_episode(bp, num, matched_trend=trend)


def load_generated_queue() -> list:
    if os.path.exists(GENERATED_QUEUE_FILE):
        try:
            with open(GENERATED_QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_generated_queue(queue: list):
    with open(GENERATED_QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)


def extract_canonical_slug(identifier: str) -> str:
    """Normaliza qualquer ID de projeto/slot (09h, 16h, 20h) para seu slug temático canônico."""
    if not identifier:
        return ""
    s = str(identifier).strip().lower()
    s = re.sub(r"^tiktok-trend-(?:16h|20h)-", "", s)
    s = re.sub(r"^tiktok-\d+-", "", s)
    s = re.sub(r"^video-\d+-", "", s)
    return s


def get_global_used_slugs(include_queues: bool = True) -> set:
    """
    Inventário Editorial Global: reúne todos os slugs já publicados ou reservados
    entre Autopilot 09h (YouTube/Shorts/Reels/TikTok) e Slots TikTok 16h/20h
    para impedir qualquer duplicidade de tema entre horários ou dias.
    """
    used = set()
    state_paths = [
        os.path.join(PIPELINE_DIR, "autopilot_state.json"),
        os.path.join(PIPELINE_DIR, "publishing", "tiktok_slots_state.json"),
    ]
    for sp in state_paths:
        if os.path.exists(sp):
            try:
                with open(sp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data.get("completed_projects", []) + data.get("published_topics", []):
                    slug = extract_canonical_slug(item)
                    if slug:
                        used.add(slug)
            except Exception:
                pass

    if include_queues:
        for q_item in load_generated_queue():
            slug = q_item.get("slug") or extract_canonical_slug(q_item.get("id", ""))
            if slug:
                used.add(slug)
        tt_q = load_generated_tiktok_queue()
        for slot_name in ("16h", "20h"):
            for item in tt_q.get(slot_name, []):
                slug = extract_canonical_slug(item.get("id", ""))
                if slug:
                    used.add(slug)

    return used


def replenish_weekly_queue(completed_ids: set, existing_catalogue_ids: set, days: int = 7) -> list:
    """
    Lê as tendências ao vivo e preenche uma nova fila de `days` dias (padrão 7 dias)
    para o Autopilot 09h (YouTube 16:9 + YouTube Shorts + Instagram Reels + TikTok),
    respeitando o inventário editorial global para não colidir com os slots 16h/20h.
    """
    print(f"[TRENDS] 📡 Lista de publicação vazia! Lendo tendências reais para preencher os próximos {days} dias...", flush=True)
    trends = fetch_live_trends()
    print(f"[TRENDS] ✅ {len(trends)} tendências coletadas dos feeds oficiais de Ciência, Espaço e Tecnologia.", flush=True)

    queue = load_generated_queue()
    pending_existing = [item for item in queue if item.get("id") not in completed_ids]
    if len(pending_existing) >= days:
        return queue

    used_slugs = get_global_used_slugs(include_queues=True)
    for pid in set(completed_ids) | set(existing_catalogue_ids) | {q.get("id", "") for q in queue}:
        slug = extract_canonical_slug(pid)
        if slug:
            used_slugs.add(slug)

    scored_pool = []
    for bp in DEEP_TREND_BANK:
        if bp["slug"] in used_slugs:
            continue
        score, matched_trend = _score_blueprint_against_trends(bp, trends)
        scored_pool.append((score, bp, matched_trend))

    # Prioriza os temas do banco que têm maior aderência às tendências ao vivo de hoje
    scored_pool.sort(key=lambda x: x[0], reverse=True)

    needed = days - len(pending_existing)
    next_num = _next_video_number(completed_ids, existing_catalogue_ids | {q.get("id", "") for q in queue})

    added = []
    for score, bp, matched_trend in scored_pool[:needed]:
        ep = _assemble_episode(bp, next_num, matched_trend=matched_trend)
        queue.append(ep)
        added.append(ep)
        used_slugs.add(bp["slug"])
        next_num += 1

    # Fallback: se até o DEEP_TREND_BANK estiver completo no futuro, sintetiza direto das tendências RSS inéditas
    if len(added) < needed:
        sci_trends = [t for t in trends if t["source"] != "Google Trends BR"] + trends
        for tr in sci_trends:
            if len(added) >= needed:
                break
            ep = _synthesize_fallback_from_trend(tr, next_num)
            if ep["slug"] not in used_slugs:
                queue.append(ep)
                added.append(ep)
                used_slugs.add(ep["slug"])
                next_num += 1

    save_generated_queue(queue)
    print(f"[TRENDS] 📅 Nova grade semanal gerada com {len(added)} episódios novos em: {GENERATED_QUEUE_FILE}", flush=True)
    for ep in added:
        print(f"   • {ep['id']}: {ep['title']}", flush=True)

    return queue


def _episode_to_tiktok_slot_item(ep: dict, slot_label: str) -> dict:
    """Converte um tópico profundo do banco de tendências para o formato de 6 capítulos do TikTok Slots Manager."""
    chapters = []
    for idx, act in enumerate(ep["scenes"][:6]):
        chapters.append({
            "headline": f"{idx + 1}. {act['headline']}",
            "stats": act["stats"],
            "image_query": ep["image_queries"].get(f"scene_{idx + 1}.jpg", "deep space galaxies hubble"),
        })

    clean_summary = re.sub(r"\s+", " ", ep.get("summary") or ep["seo"]["description"]).strip()
    if len(clean_summary) > 220:
        clean_summary = clean_summary[:217].rsplit(" ", 1)[0].rstrip(" ,;:-") + "..."

    tt_narration = re.sub(
        r"A investigação completa[^!]*acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!",
        "Siga @scapatici.tecnologia, inscreva-se no canal Scapatici Tecnologia no YouTube e até o próximo vídeo!",
        ep["shorts_narration"],
    )

    return {
        "id": f"tiktok-trend-{slot_label}-{ep['slug']}",
        "title": ep["title"],
        "headline": ep["scenes"][0]["headline"],
        "description": clean_summary,
        "narration": tt_narration,
        "tags": ep["seo"]["tags"],
        "chapters": chapters,
    }


def load_generated_tiktok_queue() -> dict:
    if os.path.exists(GENERATED_TIKTOK_QUEUE_FILE):
        try:
            with open(GENERATED_TIKTOK_QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"16h": [], "20h": []}


def replenish_tiktok_slots_queue(
    published_topic_ids: set,
    existing_static_slots: dict,
    days: int = 7,
    rebuild_clean: bool = False,
) -> dict:
    """
    Reabastece 7 dias (14 episódios inéditos: 7x 16h + 7x 20h) de mini-documentários
    exclusivos do TikTok baseados em tendências, com deduplicação editorial global:
    nenhum slug já usado ou agendado para 09h, 16h ou 20h pode se repetir.
    """
    print(f"[TRENDS TIKTOK] 📡 Reabastecendo slots do TikTok com tendências inéditas para {days} dias...", flush=True)
    trends = fetch_live_trends()
    tt_queue = {"16h": [], "20h": []} if rebuild_clean else load_generated_tiktok_queue()

    # Slugs já publicados no 09h ou TikTok + slugs reservados na fila 09h
    blocked_slugs = get_global_used_slugs(include_queues=False)
    for q_item in load_generated_queue():
        s = q_item.get("slug") or extract_canonical_slug(q_item.get("id", ""))
        if s:
            blocked_slugs.add(s)
    for pid in published_topic_ids:
        s = extract_canonical_slug(pid)
        if s:
            blocked_slugs.add(s)

    # Limpa itens já enfileirados que colidam com 09h, já publicados ou duplicados entre 16h/20h
    seen_in_tt_queues = set()
    cleaned_queue = {"16h": [], "20h": []}
    for slot_name in ("16h", "20h"):
        for item in tt_queue.get(slot_name, []):
            item_id = item.get("id", "")
            slug = extract_canonical_slug(item_id)
            if not slug or slug in blocked_slugs or slug in seen_in_tt_queues or item_id in published_topic_ids:
                continue
            seen_in_tt_queues.add(slug)
            cleaned_queue[slot_name].append(item)
    tt_queue = cleaned_queue

    used_slugs = set(blocked_slugs) | set(seen_in_tt_queues)

    # Prepara pool curado restante + tendências RSS ao vivo inéditas
    scored = []
    for bp in DEEP_TREND_BANK:
        if bp["slug"] in used_slugs:
            continue
        score, matched_trend = _score_blueprint_against_trends(bp, trends)
        scored.append((score, bp, matched_trend))
    scored.sort(key=lambda x: x[0], reverse=True)

    sci_trends = [t for t in trends if t.get("source") != "Google Trends BR"] + list(trends)
    candidate_num = 500
    scored_cursor = 0
    trend_cursor = 0

    # Alterna preenchimento entre 16h e 20h para equilibrar temas estratégicos distintos
    for _round in range(days):
        for slot_name in ("16h", "20h"):
            pending_slot = [
                c for c in existing_static_slots.get(slot_name, []) + tt_queue.get(slot_name, [])
                if c["id"] not in published_topic_ids and extract_canonical_slug(c["id"]) not in blocked_slugs
            ]
            if len(pending_slot) >= days:
                continue

            chosen_ep = None
            while scored_cursor < len(scored):
                _, bp, matched = scored[scored_cursor]
                scored_cursor += 1
                if bp["slug"] not in used_slugs:
                    chosen_ep = _assemble_episode(bp, candidate_num, matched_trend=matched)
                    candidate_num += 1
                    break

            while chosen_ep is None and trend_cursor < len(sci_trends):
                tr = sci_trends[trend_cursor]
                trend_cursor += 1
                ep = _synthesize_fallback_from_trend(tr, candidate_num)
                candidate_num += 1
                if ep["slug"] not in used_slugs:
                    chosen_ep = ep
                    break

            if chosen_ep is not None:
                used_slugs.add(chosen_ep["slug"])
                tt_item = _episode_to_tiktok_slot_item(chosen_ep, slot_name)
                tt_queue.setdefault(slot_name, []).append(tt_item)

    with open(GENERATED_TIKTOK_QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(tt_queue, f, indent=2, ensure_ascii=False)

    print(f"[TRENDS TIKTOK] ✅ Fila TikTok estratégica atualizada: 16h={len(tt_queue['16h'])}, 20h={len(tt_queue['20h'])} (0 conflitos).", flush=True)
    return tt_queue


if __name__ == "__main__":
    # Teste rápido de CLI
    trends_list = fetch_live_trends()
    print(f"Tendências coletadas: {len(trends_list)}")
    for t in trends_list[:8]:
        print(f"  [{t['source']}] {t['title']}")

