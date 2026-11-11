"""
Simple-Tube TikTok Slots Manager
Gerencia a grade de publicação do TikTok 3x ao dia (09h, 16h, 20h)
com mini-documentários verticais profundos (1m40s a 2m05s, 6 atos visuais e HUD de dados científicos)
sob medida para retenção máxima e o programa de vídeos >1 minuto do algoritmo do TikTok.
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, "tiktok_slots_state.json")

# Grade de mini-documentários exclusivos para os slots da Tarde (16h) e Noite (20h)
# Cada episódio possui ~260-300 palavras (~105s-125s de duração), 6 cenas visuais da NASA
# e 6 capítulos progressivos com HUD de dados científicos reais.
TIKTOK_EXCLUSIVE_SLOTS = {
    "16h": [
        {
            "id": "tiktok-001-olbers-paradox",
            "title": "Se o Universo tem infinitas estrelas, por que a noite é escura?",
            "headline": "O PARADOXO DA ESCURIDÃO CÓSMICA",
            "description": "Entenda a física por trás do Paradoxo de Olbers, o horizonte cosmológico e o desvio para o vermelho captado pelo Telescópio James Webb.",
            "narration": (
                "Se o universo abriga mais de dois trilhões de galáxias e sextilhões de estrelas, por que o céu noturno é escuro em vez de brilhar com a intensidade ofuscante da superfície do Sol em todas as direções? "
                "Esse enigma intrigou astrônomos como Johannes Kepler e Heinrich Olbers por séculos. Se o cosmos fosse infinito, eterno e estático, qualquer linha de visão que você apontasse para o céu terminaria inevitavelmente na superfície de uma estrela. "
                "Mas a física moderna resolveu esse mistério com duas descobertas monumentais. A primeira é que o universo não existe desde sempre: ele tem treze vírgula oito bilhões de anos. "
                "Como a velocidade da luz é finita, viajando a trezentos mil quilômetros por segundo, a luz de galáxias situadas além do nosso horizonte cosmológico simplesmente ainda não teve tempo de chegar até os nossos olhos. "
                "A segunda razão é ainda mais fascinante: o próprio tecido do espaço está se expandindo de forma acelerada. "
                "Enquanto os fótons das primeiras estrelas e da radiação cósmica de fundo viajam por bilhões de anos-luz, a expansão do espaço estica literalmente o comprimento dessas ondas luminosas. "
                "Esse fenômeno, chamado desvio para o vermelho cosmológico, transforma a luz visível brilhante do universo primordial em radiação infravermelha e micro-ondas invisíveis ao olho humano. "
                "É exatamente por isso que o Telescópio Espacial James Webb foi construído com espelhos banhados a ouro para enxergar no infravermelho: para ver o brilho oculto na escuridão. "
                "Siga o perfil, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
            ),
            "tags": ["scapaticitecnologia", "paradoxodeolbers", "astronomia", "fisica", "jameswebb", "cosmologia", "foryou", "universo"],
            "chapters": [
                {
                    "headline": "1. O PARADOXO DE OLBERS",
                    "stats": {"label": "GALÁXIAS NO COSMOS", "value": "+2 TRILHÕES"},
                    "image_query": "deep space dark night stars distant galaxies hubble"
                },
                {
                    "headline": "2. A HIPÓTESE DO CÉU INFINITO",
                    "stats": {"label": "ESTRELAS ESTIMADAS", "value": "1 SEXTILHÃO"},
                    "image_query": "hubble ultra deep field thousands of galaxies"
                },
                {
                    "headline": "3. O HORIZONTE COSMOLÓGICO",
                    "stats": {"label": "IDADE DO UNIVERSO", "value": "13,8 BILHÕES DE ANOS"},
                    "image_query": "cosmic microwave background planck space"
                },
                {
                    "headline": "4. A EXPANSÃO DO ESPAÇO-TEMPO",
                    "stats": {"label": "TAXA DE EXPANSÃO", "value": "~70 KM/S POR MEGAPARSEC"},
                    "image_query": "expanding universe galaxies dark energy nasa"
                },
                {
                    "headline": "5. O DESVIO PARA O VERMELHO",
                    "stats": {"label": "REDSHIFT PRIMORDIAL", "value": "Z > 13 (INFRAVERMELHO)"},
                    "image_query": "james webb infrared deep field redshift galaxies"
                },
                {
                    "headline": "6. A VISÃO DO JAMES WEBB",
                    "stats": {"label": "ESPELHO DE BERÍLIO E OURO", "value": "6,5 METROS"},
                    "image_query": "james webb space telescope mirror gold cosmos"
                }
            ]
        },
        {
            "id": "tiktok-002-light-speed-limit",
            "title": "Por que absolutamente NADA no universo pode superar a velocidade da luz?",
            "headline": "A BARREIRA IMPLACÁVEL DE EINSTEIN",
            "description": "Por que 299.792 km/s é a velocidade máxima da própria causalidade no tecido do espaço-tempo? A física completa da Relatividade Especial.",
            "narration": (
                "Por que absolutamente nada no universo pode viajar mais rápido do que duzentos e noventa e nove mil setecentos e noventa e dois quilômetros por segundo? "
                "O maior erro é achar que a velocidade da luz é uma propriedade exclusiva dos fótons. Na verdade, na física moderna, a constante C não é a velocidade da luz: ela é a velocidade máxima da causalidade, o limite máximo com que qualquer informação ou causa e efeito pode se propagar pelo tecido do espaço-tempo. "
                "Segundo a Relatividade Especial de Albert Einstein, expressa na famosa equação que relaciona energia, massa e o fator de Lorentz, qualquer objeto que possui massa de repouso sofre uma transformação dramática ao acelerar. "
                "Quando uma espaçonave ou uma partícula atinge noventa por cento da velocidade da luz, a energia que você injeta nos motores deixa de aumentar significativamente a velocidade e passa a se converter em inércia relativística. "
                "A noventa e nove vírgula nove nove nove por cento da velocidade da luz — velocidade que os prótons atingem dentro do Grande Colisor de Hádrons do CERN, na Suíça — um único próton comporta-se como se fosse milhares de vezes mais pesado do que quando está parado. "
                "Para alcançar exatamente cem por cento da velocidade da luz, o denominador da equação de Einstein chega a zero, o que exigiria uma quantidade literalmente infinita de energia — mais energia do que todas as estrelas e galáxias do universo observável somadas! "
                "Apenas partículas sem nenhuma massa de repouso, como os fótons da luz e os glúons, nascem obrigadas a viajar nessa velocidade limite no vácuo. "
                "E se algo quebrasse essa barreira, o efeito aconteceria antes da causa, destruindo a linha do tempo do universo. "
                "Siga o perfil, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
            ),
            "tags": ["scapaticitecnologia", "velocidadedaluz", "einstein", "relatividade", "fisicaquantica", "ciencia", "foryou"],
            "chapters": [
                {
                    "headline": "1. A VELOCIDADE DA CAUSALIDADE",
                    "stats": {"label": "CONSTANTE C NO VÁCUO", "value": "299.792,458 KM/S"},
                    "image_query": "warp speed light beam cosmos einstein space time"
                },
                {
                    "headline": "2. O FATOR DE LORENTZ",
                    "stats": {"label": "EQUAÇÃO RELATIVÍSTICA", "value": "E = γ·m·c²"},
                    "image_query": "relativistic jet quasar light speed hubble"
                },
                {
                    "headline": "3. O AUMENTO DA INÉRCIA",
                    "stats": {"label": "A 99,9% DE C", "value": "INÉRCIA 22X MAIOR"},
                    "image_query": "active galactic nucleus jet m87 black hole"
                },
                {
                    "headline": "4. ACELERADOR DE PARTÍCULAS CERN",
                    "stats": {"label": "PRÓTONS NO LHC", "value": "99,9999991% DE C"},
                    "image_query": "particle accelerator collision light energy cern"
                },
                {
                    "headline": "5. A BARREIRA DA ENERGIA INFINITA",
                    "stats": {"label": "ENERGIA PARA 100% DE C", "value": "INFINITA (IMPOSSÍVEL)"},
                    "image_query": "supernova explosion gamma ray burst high energy"
                },
                {
                    "headline": "6. PROTEÇÃO DA LINHA DO TEMPO",
                    "stats": {"label": "MASSA DE REPOUSO DO FÓTON", "value": "ZERO ABSOLUTO"},
                    "image_query": "gravitational wave space time fabric simulation"
                }
            ]
        },
        {
            "id": "tiktok-003-neutron-star-teaspoon",
            "title": "Uma colher de chá deste objeto pesa mais que o Monte Everest!",
            "headline": "A MATÉRIA MAIS DENSA DO UNIVERSO",
            "description": "Como uma estrela de 20 massas solares é esmagada em uma esfera de 20 km girando 700 vezes por segundo? A astrofísica extrema das Estrelas de Nêutrons.",
            "narration": (
                "Se você pudesse coletar apenas uma colher de chá da matéria de uma Estrela de Nêutrons e trazê-la para a Terra, essa única colherada pesaria cerca de quatro bilhões de toneladas — mais do que todo o Monte Everest comprimido do tamanho de um cubo de açúcar! "
                "Mas como a natureza consegue fabricar algo tão brutalmente denso sem formar um buraco negro? "
                "Tudo começa quando uma estrela gigante, com oito a vinte vezes a massa do nosso Sol, esgota seu combustível nuclear e explode em uma Supernova. "
                "Enquanto as camadas externas são ejetadas para o espaço, o núcleo central sofre um colapso gravitacional catastrófico em menos de um segundo. "
                "A pressão é tão inconcebível que vence a repulsão eletromagnética dos átomos: os elétrons são literalmente esmagados para dentro dos prótons no núcleo atômico, fundindo-se através do decaimento beta inverso para criar uma sopa ultradensa de nêutrons puros. "
                "Toda a massa de quase dois sóis inteiros fica espremida dentro de uma esfera de apenas vinte quilômetros de diâmetro — o tamanho de uma única cidade! "
                "A gravidade na superfície é duzentos bilhões de vezes mais forte que a da Terra: se você deixasse cair um objeto de apenas um metro de altura lá, ele atingiria o chão a sete milhões de quilômetros por hora. "
                "E por conservação do momento angular, essas estrelas giram como piões alucinados: o pulsar PSR J1748 gira setecentas e dezesseis vezes por segundo, com seu equador movendo-se a quase um quarto da velocidade da luz! "
                "Siga o perfil, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
            ),
            "tags": ["scapaticitecnologia", "estreladeneutrons", "neutronstar", "densidade", "astrofisica", "universo", "fatos"],
            "chapters": [
                {
                    "headline": "1. A DENSIDADE NUCLEAR EXTREMA",
                    "stats": {"label": "1 COLHER DE CHÁ", "value": "~4 BILHÕES DE TONELADAS"},
                    "image_query": "neutron star glowing magnetic field dense core space"
                },
                {
                    "headline": "2. O COLAPSO DA SUPERNOVA",
                    "stats": {"label": "DIÂMETRO DO NÚCLEO", "value": "APENAS ~20 KM"},
                    "image_query": "supernova remnant crab nebula pulsar hubble"
                },
                {
                    "headline": "3. ESMAGANDO ÁTOMOS INTEIROS",
                    "stats": {"label": "FUSÃO QUÂNTICA", "value": "PRÓTON + ELÉTRON = NÊUTRON"},
                    "image_query": "cassiopeia a supernova remnant chandra x-ray"
                },
                {
                    "headline": "4. GRAVIDADE DE 200 BILHÕES DE G",
                    "stats": {"label": "VELOCIDADE DE ESCAPE", "value": "~150.000 KM/S (50% DE C)"},
                    "image_query": "vela pulsar x-ray jet chandra space observatory"
                },
                {
                    "headline": "5. ROTAÇÃO DE MILISSEGUNDOS",
                    "stats": {"label": "RECORDE DE ROTAÇÃO", "value": "716 GIROS POR SEGUNDO"},
                    "image_query": "pulsar relativistic beams magnetic poles nasa"
                },
                {
                    "headline": "6. FÁBRICA DE OURO E PLATINA",
                    "stats": {"label": "COLISÃO KILONOVA", "value": "ONDAS GRAVITACIONais LIGO"},
                    "image_query": "kilonova neutron star merger gravitational wave"
                }
            ]
        },
        {
            "id": "tiktok-004-time-dilation-speed",
            "title": "O Paradoxo dos Gêmeos: Como a velocidade e a gravidade permitem viajar para o futuro?",
            "headline": "A FÍSICA DA VIAGEM NO TEMPO",
            "description": "A viagem para o futuro não é ficção científica: é comprovada por relógios atômicos e pelo GPS. Entenda a Dilatação Temporal de Einstein.",
            "narration": (
                "Viajar para o futuro não é ficção científica: é uma lei comprovada da natureza que acontece todos os dias nos satélites acima da sua cabeça. "
                "Até mil novecentos e cinco, a humanidade acreditava que um segundo na Terra durava exatamente o mesmo que um segundo em qualquer lugar do cosmos. "
                "Mas Albert Einstein descobriu que o espaço e o tempo formam um único tecido flexível, e que existem duas formas reais de desacelerar a passagem do seu tempo em relação ao resto do universo: a velocidade extrema e a gravidade extrema. "
                "Imagine o famoso Paradoxo dos Gêmeos: dois irmãos de vinte anos se despedem. Um fica na Terra, e o outro embarca em uma nave viajando a noventa e nove vírgula cinco por cento da velocidade da luz rumo a uma estrela distante. "
                "Para o astronauta a bordo da nave, o tempo passa normalmente durante uma viagem de ida e volta de cinco anos. Mas quando ele pousa de volta na Terra, ele tem apenas vinte e cinco anos, enquanto seu irmão gêmeo que ficou aqui envelheceu cinquenta anos e agora tem setenta anos de idade! "
                "Isso já foi provado em laboratório com relógios atômicos de césio em aviões supersônicos e também com partículas chamadas múons, que vivem trinta vezes mais tempo quando caem da atmosfera a velocidades relativísticas. "
                "Mais impressionante ainda: os satélites de GPS que guiam o mapa do seu celular precisam corrigir seus relógios atômicos em trinta e oito microssegundos todos os dias por causa da Relatividade de Einstein; sem essa correção, o GPS erraria sua localização em dez quilômetros a cada dia! "
                "Siga o perfil, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
            ),
            "tags": ["scapaticitecnologia", "dilatacaodotempo", "einstein", "viagemnotempo", "paradoxo", "fisica", "foryou"],
            "chapters": [
                {
                    "headline": "1. O TEMPO NÃO É ABSOLUTO",
                    "stats": {"label": "DESCOBERTA DE EINSTEIN", "value": "RELATIVIDADE (1905 / 1915)"},
                    "image_query": "time dilation clock space warp relativity einstein"
                },
                {
                    "headline": "2. O PARADOXO DOS GÊMEOS",
                    "stats": {"label": "VELOCIDADE DA NAVE", "value": "99,5% DA LUZ (FATOR 10X)"},
                    "image_query": "spacecraft interstellar travel starlight"
                },
                {
                    "headline": "3. 5 ANOS NA NAVE = 50 NA TERRA",
                    "stats": {"label": "DIFERENÇA DE IDADE", "value": "45 ANOS NO FUTURO"},
                    "image_query": "astronaut looking at earth from space station"
                },
                {
                    "headline": "4. DILATAÇÃO GRAVITACIONAL",
                    "stats": {"label": "PERTO DE BURACO NEGRO", "value": "1 HORA = ANOS EXTERNOS"},
                    "image_query": "black hole event horizon gravitational time dilation"
                },
                {
                    "headline": "5. PROVA COM RELÓGIOS ATÔMICOS",
                    "stats": {"label": "PRECISÃO DO CÉSIO-133", "value": "1 SEGUNDO EM 100 MILHÕES DE ANOS"},
                    "image_query": "deep space atomic clock nasa technology"
                },
                {
                    "headline": "6. A RELATIVIDADE NO SEU GPS",
                    "stats": {"label": "CORREÇÃO DIÁRIA DO GPS", "value": "38 MICROSSEGUNDOS/DIA"},
                    "image_query": "earth from deep space orbit satellites"
                }
            ]
        },
        {
            "id": "tiktok-009-quantum-tunneling-sun",
            "title": "Por que o Sol não deveria conseguir brilhar segundo a física clássica?",
            "headline": "O FANTASMA QUÂNTICO QUE ACENDE O SOL",
            "description": "O núcleo do Sol é frio demais para vencer a repulsão dos prótons pela física clássica. Descubra como o Tunelamento Quântico mantém nossa estrela viva.",
            "narration": (
                "Se dependesse apenas das leis da física clássica, o nosso Sol jamais teria se acendido e a Terra seria uma rocha congelada na escuridão. "
                "Para que o Sol brilhe, ele precisa fundir núcleos de hidrogênio — que são prótons com carga positiva — para formar hélio em seu núcleo. "
                "O problema é a Barreira de Coulomb: duas cargas positivas se repelem com uma força eletromagnética brutal quando tentam se aproximar. "
                "Quando os físicos calcularam a temperatura necessária para que os prótons tivessem velocidade térmica suficiente para vencer essa barreira de frente, descobriram que o núcleo do Sol precisaria estar a mais de dez bilhões de graus Celsius. "
                "Mas o núcleo do nosso Sol tem apenas quinze milhões de graus — quase mil vezes mais frio do que o necessário! Pela física tradicional, os prótons deveriam apenas bater na barreira invisível e ricochetear para sempre. "
                "Em mil novecentos e vinte e oito, o físico George Gamow revelou o segredo: o Tunelamento Quântico. "
                "Na mecânica quântica, um próton não é uma bolinha sólida, mas sim uma onda de probabilidade. "
                "Mesmo sem ter energia suficiente para saltar por cima do muro eletromagnético, existe uma pequena chance matemática de a função de onda do próton atravessar a parede como um fantasma e aparecer fundido do outro lado! "
                "A chance de isso acontecer para um único próton é de uma em bilhões de anos, mas como o Sol possui um octilhão de prótons colidindo sem parar, seiscentos milhões de toneladas de hidrogênio atravessam o túnel quântico a cada segundo! "
                "Siga o perfil, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
            ),
            "tags": ["scapaticitecnologia", "tunelamentoquantico", "sol", "fisicaquantica", "astrofisica", "ciencia", "foryou"],
            "chapters": [
                {
                    "headline": "1. O PARADOXO DO NÚCLEO SOLAR",
                    "stats": {"label": "TEMPERATURA REAL DO SOL", "value": "15 MILHÕES °C"},
                    "image_query": "sun solar flare coronal mass ejection sdo nasa"
                },
                {
                    "headline": "2. A BARREIRA DE COULOMB",
                    "stats": {"label": "TEMPERATURA CLÁSSICA EXIGIDA", "value": "10 BILHÕES °C"},
                    "image_query": "solar dynamics observatory extreme ultraviolet sun"
                },
                {
                    "headline": "3. ONDAS DE PROBABILIDADE",
                    "stats": {"label": "DUALIDADE ONDA-PARTÍCULA", "value": "EQUAÇÃO DE SCHRÖDINGER"},
                    "image_query": "quantum physics particle wave collision cern"
                },
                {
                    "headline": "4. O TUNELAMENTO QUÂNTICO",
                    "stats": {"label": "EFEITO FANTASMA", "value": "ATRAVESSA A BARREIRA"},
                    "image_query": "sun core nuclear fusion plasma energy nasa"
                },
                {
                    "headline": "5. A ESTATÍSTICA QUE SALVA A VIDA",
                    "stats": {"label": "FUSÃO NO SOL POR SEGUNDO", "value": "600 MILHÕES DE TONELADAS"},
                    "image_query": "parker solar probe close to sun corona nasa"
                },
                {
                    "headline": "6. LUZ QUE DEMORA 100 MIL ANOS",
                    "stats": {"label": "JORNADA DO FÓTON NO SOL", "value": "~100.000 ANOS ATÉ A SUPERFÍCIE"},
                    "image_query": "sunlight earth sunrise from space station"
                }
            ]
        },
        {
            "id": "tiktok-010-kardashev-scale-civilizations",
            "title": "Os 3 Níveis da Escala de Kardashev: Em qual nível a humanidade está hoje?",
            "headline": "AS SUPER-CIVILIZAÇÕES DO COSMOS",
            "description": "De dominar um planeta inteiro a envolver estrelas com Esferas de Dyson e controlar buracos negros: conheça a Escala de Kardashev completa.",
            "narration": (
                "Em mil novecentos e sessenta e quatro, o astrofísico soviético Nikolai Kardashev criou a métrica definitiva para classificar o nível tecnológico de qualquer civilização inteligente no universo com base na quantidade de energia que ela consegue dominar. "
                "Uma Civilização Tipo Um, ou Planetária, é aquela capaz de capturar e utilizar cem por cento de toda a energia que chega ao seu planeta a partir de sua estrela-mãe — cerca de dez elevado a dezesseis watts. Ela controlaria o clima global, terremotos, vulcões e a fusão nuclear em escala planetária. "
                "Já uma Civilização Tipo Dois, ou Estelar, esgotou os recursos de seu mundo e construiu uma megaestrutura ao redor de sua própria estrela — a famosa Esfera ou Enxame de Dyson — capturando toda a potência luminosa de um sol inteiro, equivalente a quatro vezes dez elevado a vinte e seis watts! "
                "E o ápice clássico é a Civilização Tipo Três, ou Galáctica: uma espécie imortal que colonizou sistemas estelares inteiros e extrai energia não apenas de bilhões de estrelas, mas também do giro de buracos negros supermassivos no centro de sua galáxia através do Processo de Penrose. "
                "Mas onde a humanidade está hoje nessa escala cósmica? "
                "Segundo o físico Carl Sagan, que refinou a fórmula matemática de Kardashev, nós ainda nem chegamos ao Tipo Um! "
                "Atualmente, com todo o nosso consumo elétrico e industrial, a humanidade está exatamente no nível zero vírgula sete três da Escala de Kardashev, e levará cerca de cem a duzentos anos de avanço em energia solar e fusão nuclear para nos tornarmos oficialmente uma civilização Tipo Um! "
                "Siga o perfil, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
            ),
            "tags": ["scapaticitecnologia", "escaladekardashev", "esferadedyson", "futurismo", "astronomia", "tecnologia", "foryou"],
            "chapters": [
                {
                    "headline": "1. A ESCALA DE KARDASHEV (1964)",
                    "stats": {"label": "MÉTRICA CÓSMICA", "value": "DOMÍNIO DE ENERGIA (WATTS)"},
                    "image_query": "futuristic earth night city lights from space station"
                },
                {
                    "headline": "2. CIVILIZAÇÃO TIPO I (PLANETÁRIA)",
                    "stats": {"label": "POTÊNCIA EXIGIDA", "value": "10¹⁶ WATTS (PLANETA INTEIRO)"},
                    "image_query": "earth atmosphere aurora borealis space station nasa"
                },
                {
                    "headline": "3. CIVILIZAÇÃO TIPO II (ESTELAR)",
                    "stats": {"label": "ESFERA DE DYSON", "value": "4 × 10²⁶ WATTS (SOL INTEIRO)"},
                    "image_query": "bright star solar corona energy spacecraft nasa"
                },
                {
                    "headline": "4. CIVILIZAÇÃO TIPO III (GALÁCTICA)",
                    "stats": {"label": "IMPÉRIO GALÁCTICO", "value": "10³⁶ WATTS (VIA LÁCTEA)"},
                    "image_query": "andromeda spiral galaxy billions of stars hubble"
                },
                {
                    "headline": "5. ENERGIA DE BURACOS NEGROS",
                    "stats": {"label": "PROCESSO DE PENROSE", "value": "EXTRAÇÃO DA ERGOSFERA"},
                    "image_query": "supermassive black hole accretion disk jet"
                },
                {
                    "headline": "6. O NÍVEL ATUAL DA HUMANIDADE",
                    "stats": {"label": "ÍNDICE HUMANO ATUAL", "value": "TIPO 0,73 (RUMO AO TIPO I)"},
                    "image_query": "international space station earth horizon sunrise"
                }
            ]
        }
    ],
    "20h": [
        {
            "id": "tiktok-005-big-freeze-end-of-time",
            "title": "O que acontecerá no universo quando a última estrela se apagar?",
            "headline": "O GRANDE CONGELAMENTO CÓSMICO",
            "description": "Uma viagem até o ano 10 elevado a 100: da morte da última anã vermelha à Era dos Buracos Negros e à evaporação final por Radiação de Hawking.",
            "narration": (
                "Nós vivemos na primavera luminosa do cosmos, a chamada Era Estelífera, mas ela representa apenas um piscar de olhos na história do tempo. O que acontecerá quando o universo ficar completamente sem combustível? "
                "Daqui a cerca de cem trilhões de anos, todo o gás hidrogênio das nebulosas terá se esgotado. As últimas estrelas vivas serão as pequenas Anãs Vermelhas, que queimam seu combustível tão devagar que duram trilhões de anos. "
                "Quando a última anã vermelha finalmente se apagar, o universo mergulhará na Era Degenerada: um cemitério escuro povoado apenas por cadáveres estelares — anãs brancas, estrelas de nêutrons e buracos negros. "
                "Com o passar de dez elevado a quarenta anos, até mesmo os prótons que formam a matéria comum dos planetas e das anãs brancas deverão se desintegrar em radiação pura. "
                "Então começará a época mais longa e sombria de todas: a Era dos Buracos Negros. "
                "No vazio absoluto, sem nenhuma estrela no céu, buracos negros supermassivos com bilhões de massas solares reinarão soberanos na escuridão gélida. "
                "Mas nem eles são eternos. Segundo Stephen Hawking, flutuações quânticas na borda do horizonte de eventos fazem com que os buracos negros percam massa lentamente através da Radiação de Hawking. "
                "Após um googol de anos — o número um seguido de cem zeros — até o maior buraco negro supermassivo evaporará em um último clarão de luz. "
                "Restará apenas um vácuo quase no zero absoluto, onde fótons solitários viajam pela eternidade: a Morte Térmica do Universo. "
                "Siga o perfil, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
            ),
            "tags": ["scapaticitecnologia", "bigfreeze", "mortetermica", "fimdouniverso", "buracosnegros", "cosmologia", "foryou"],
            "chapters": [
                {
                    "headline": "1. O FIM DA ERA DAS ESTRELAS",
                    "stats": {"label": "ÚLTIMA ESTRELA APAGA EM", "value": "100 TRILHÕES DE ANOS"},
                    "image_query": "dark universe dead stars dying galaxies deep freeze webb"
                },
                {
                    "headline": "2. A MORTE DAS ANÃS VERMELHAS",
                    "stats": {"label": "LONGEVIDADE ESTELAR", "value": "ATÉ 10 TRILHÕES DE ANOS"},
                    "image_query": "red dwarf star fading deep space"
                },
                {
                    "headline": "3. A ERA DEGENERADA",
                    "stats": {"label": "CADÁVERES CÓSMICOS", "value": "ANÃS BRANCAS E PULSARES"},
                    "image_query": "white dwarf planetary nebula helix hubble"
                },
                {
                    "headline": "4. A ERA DOS BURACOS NEGROS",
                    "stats": {"label": "DURAÇÃO DA ERA", "value": "10⁴⁰ A 10¹⁰⁰ ANOS"},
                    "image_query": "supermassive black hole accretion disk event horizon"
                },
                {
                    "headline": "5. A RADIAÇÃO DE HAWKING",
                    "stats": {"label": "EVAPORAÇÃO QUÂNTICA", "value": "1 GOOGOL DE ANOS (10¹⁰⁰)"},
                    "image_query": "event horizon telescope black hole glowing ring"
                },
                {
                    "headline": "6. A MORTE TÉRMICA ETERNA",
                    "stats": {"label": "TEMPERATURA FINAL", "value": "PRÓXIMA AO ZERO ABSOLUTO"},
                    "image_query": "deep cosmic void dark space hubble"
                }
            ]
        },
        {
            "id": "tiktok-006-simulation-hypothesis-evidence",
            "title": "As 4 evidências físicas que sustentam a Hipótese da Simulação",
            "headline": "VIVEMOS EM UMA SIMULAÇÃO CÓSMICA?",
            "description": "Do limite de clock da velocidade da luz ao pixel do Comprimento de Planck e à renderização quântica: a análise física da Hipótese da Simulação.",
            "narration": (
                "A ideia de que o nosso universo inteiro pode ser uma simulação computacional avançada deixou de ser apenas roteiro de cinema e tornou-se um debate sério entre físicos quânticos e filósofos da Universidade de Oxford, como Nick Bostrom. "
                "Quando analisamos as leis fundamentais da física, encontramos quatro características que funcionam exatamente como otimizações de um software de computador. "
                "A primeira é a própria velocidade da luz: por que o universo tem uma velocidade máxima absoluta de trezentos mil quilômetros por segundo? Em uma simulação, esse limite equivale exatamente à frequência máxima de clock do processador; nada pode se mover mais rápido do que o tempo que o sistema leva para atualizar um ciclo! "
                "A segunda evidência é a pixelização do espaço: em mil oitocentos e noventa e nove, Max Planck descobriu o Comprimento de Planck — um vírgula seis vezes dez elevado a menos trinta e cinco metros. Abaixo dessa escala, a própria geometria do espaço deixa de fazer sentido, funcionando exatamente como o pixel mínimo tridimensional da nossa realidade. "
                "A terceira pista vem do Experimento da Dupla Fenda na mecânica quântica: elétrons e fótons se comportam como ondas de possibilidades difusas e só assumem uma posição física definida quando são medidos ou interagem com um detector — idêntico à técnica de renderização sob demanda usada em motores gráficos modernos para economizar memória! "
                "E a quarta é que todo o universo obedece a equações matemáticas rigorosas e códigos de informação quântica que nunca falham. "
                "Siga o perfil, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
            ),
            "tags": ["scapaticitecnologia", "hipotesedasimulacao", "matrix", "fisicaquantica", "filosofia", "realidade", "foryou"],
            "chapters": [
                {
                    "headline": "1. O ARGUMENTO DE OXFORD",
                    "stats": {"label": "TESE DE NICK BOSTROM", "value": "SIMULAÇÃO DE ANCESTRAIS"},
                    "image_query": "digital matrix cosmic web universe code quantum reality"
                },
                {
                    "headline": "2. O CLOCK MÁXIMO DO PROCESSADOR",
                    "stats": {"label": "LIMITE DE PROCESSAMENTO", "value": "C = 299.792 KM/S"},
                    "image_query": "light speed relativistic beam cosmos hubble"
                },
                {
                    "headline": "3. O PIXEL DA REALIDADE",
                    "stats": {"label": "COMPRIMENTO DE PLANCK", "value": "1,616 × 10⁻³⁵ METROS"},
                    "image_query": "quantum entanglement subatomic particles glowing"
                },
                {
                    "headline": "4. RENDERIZAÇÃO SOB DEMANDA",
                    "stats": {"label": "COLAPSO QUÂNTICO", "value": "EXPERIMENTO DA DUPLA FENDA"},
                    "image_query": "particle detector cern collision quantum tracks"
                },
                {
                    "headline": "5. A TEIA CÓSMICA MATEMÁTICA",
                    "stats": {"label": "ESTRUTURA DO UNIVERSO", "value": "REDE NEURAL GRAVITACIONAL"},
                    "image_query": "cosmic web dark matter simulation supercomputer"
                },
                {
                    "headline": "6. INFORMAÇÃO NUNCA É DESTRUÍDA",
                    "stats": {"label": "PRINCÍPIO HOLOGRÁFICO", "value": "DADOS NA BORDA DO COSMOS"},
                    "image_query": "james webb deep field galaxies structure"
                }
            ]
        },
        {
            "id": "tiktok-007-nasa-black-hole-sound",
            "title": "A NASA revelou o som real de um Buraco Negro Supermassivo e a física por trás é incrível!",
            "headline": "O ECO DO ABISMO GRAVITACIONAL",
            "description": "Como ondas acústicas viajam pelo gás de 50 milhões de graus no Aglomerado de Perseu a 250 milhões de anos-luz da Terra? A descoberta do observatório Chandra.",
            "narration": (
                "Você sempre aprendeu na escola que no espaço não existe som porque o espaço é um vácuo absoluto, certo? "
                "Na maior parte do cosmos isso é verdade, mas a duzentos e cinquenta milhões de anos-luz da Terra, no coração do gigantesco Aglomerado de Galáxias de Perseu, a natureza quebrou essa regra de forma monumental. "
                "Centenas de galáxias nesse aglomerado estão mergulhadas em uma imensa nuvem de gás intraconglomerado aquecido a mais de cinquenta milhões de graus Celsius. "
                "Quando o Telescópio de Raios-X Chandra da NASA apontou seus sensores para o centro de Perseu, os astrônomos descobriram ondas concêntricas gigantescas — cada uma com mais de cem mil anos-luz de largura — propagando-se através desse gás fervente. "
                "Essas ondas são literalmente ondas sonoras de pressão acústica disparadas pelos jatos relativísticos do buraco negro supermassivo central do aglomerado! "
                "Os cientistas calcularam a nota musical exata emitida pelo buraco negro: é um Si bemol, mas cinquenta e sete oitavas abaixo do Dó central de um piano! "
                "Isso corresponde-se a uma frequência de uma oscilação a cada dez milhões de anos — quatrilhões de vezes mais grave do que o limite da audição humana. "
                "Quando os engenheiros de áudio da NASA comprimiram e elevaram essas ondas reais em cinquenta e sete oitavas para a faixa audível, o resultado revelou um rugido cavernoso, metálico e hipnótico ecoando pelo espaço profundo há bilhões de anos. "
                "Siga o perfil, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
            ),
            "tags": ["scapaticitecnologia", "somdoburaconegro", "nasa", "buraconegro", "perseuscluster", "astrofisica", "fatos"],
            "chapters": [
                {
                    "headline": "1. SOM NO ESPAÇO PROFUNDO?",
                    "stats": {"label": "LOCALIZAÇÃO", "value": "AGLOMERADO DE PERSEU"},
                    "image_query": "perseus galaxy cluster black hole sonic wave nasa"
                },
                {
                    "headline": "2. DISTÂNCIA DA TERRA",
                    "stats": {"label": "VIAGEM DA LUZ", "value": "250 MILHÕES DE ANOS-LUZ"},
                    "image_query": "galaxy cluster deep space hubble"
                },
                {
                    "headline": "3. O OCEANO DE PLASMA FERVENTE",
                    "stats": {"label": "TEMPERATURA DO GÁS", "value": "+50 MILHÕES °C"},
                    "image_query": "chandra x-ray perseus cluster ripples gas"
                },
                {
                    "headline": "4. ONDAS DE CHOQUE ACÚSTICAS",
                    "stats": {"label": "TAMANHO DA ONDA", "value": "+100.000 ANOS-LUZ"},
                    "image_query": "black hole shockwave hot gas galaxy cluster"
                },
                {
                    "headline": "5. A NOTA MAIS GRAVE DO COSMOS",
                    "stats": {"label": "FREQUÊNCIA REAL", "value": "57 OITAVAS ABAIXO DO DÓ"},
                    "image_query": "event horizon telescope black hole shadow"
                },
                {
                    "headline": "6. SONIFICAÇÃO OFICIAL DA NASA",
                    "stats": {"label": "PERÍODO DE OSCILAÇÃO", "value": "1 CICLO A CADA 10 MILHÕES DE ANOS"},
                    "image_query": "chandra x-ray space telescope observatory nasa"
                }
            ]
        },
        {
            "id": "tiktok-008-rogue-planets-mystery",
            "title": "Mundos sem Sol: Por que existem trilhões de Planetas Órfãos vagando na escuridão?",
            "headline": "OS MUNDOS FANTASMAS ERRANTES",
            "description": "Sem estrela, sem dia e vagando no escuro interestelar: como o James Webb descobriu pares de planetas gigantes flutuantes e por que alguns podem abrigar vida!",
            "narration": (
                "Imagine estar na superfície de um planeta onde nunca existiu um nascer do sol, onde o céu é uma abóbada eterna de estrelas congeladas e a escuridão interestelar reina absoluta. "
                "Esses são os Planetas Órfãos, ou planetas errantes: mundos que não orbitam nenhuma estrela e vagam sozinhos pelo vazio da Via Láctea. "
                "Durante décadas, os astrônomos acharam que esses objetos eram raros, mas pesquisas recentes usando microlentes gravitacionais e o Telescópio Espacial James Webb revelaram uma realidade chocante: podem existir até vinte vezes mais planetas órfãos na nossa galáxia do que estrelas — somando trilhões de mundos errantes! "
                "Eles nascem de duas maneiras: alguns se formam em sistemas solares jovens e caóticos, mas são violentamente arremessados para fora como estilingues quando passam perto de planetas gigantes como Júpiter. "
                "Outros se formam diretamente do colapso de pequenas nuvens de gás frio no espaço, exatamente como estrelas em miniatura que nunca tiveram massa suficiente para iniciar a fusão nuclear. "
                "Na Nebulosa de Órion, o James Webb chegou a fotografar quarenta pares de planetas gigantes flutuando juntos em órbitas binárias sem nenhuma estrela por perto! "
                "E o detalhe mais impressionante da astrobiologia: um planeta órfão rochoso com um núcleo radioativo quente e uma atmosfera espessa de hidrogênio ou uma crosta de gelo quilométrica pode manter oceanos inteiros de água líquida aquecida por fontes hidrotermais no subsolo, abrigando vida alienígena mesmo na escuridão eterna do espaço profundo! "
                "Siga o perfil, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
            ),
            "tags": ["scapaticitecnologia", "planetasorfaos", "rogueplanets", "jameswebb", "astronomia", "fatos", "foryou"],
            "chapters": [
                {
                    "headline": "1. OS MUNDOS SEM SOL",
                    "stats": {"label": "ESTIMATIVA NA VIA LÁCTEA", "value": "TRILHÕES DE PLANETAS"},
                    "image_query": "dark rogue planet drifting in deep interstellar space"
                },
                {
                    "headline": "2. EXPULSOS DO SISTEMA SOLAR",
                    "stats": {"label": "EFEITO ESTILINGUE", "value": "CAOS GRAVITACIONAL"},
                    "image_query": "protoplanetary disk alma telescope planet formation"
                },
                {
                    "headline": "3. LENTES GRAVITACIONAIS",
                    "stats": {"label": "TÉCNICA DE DETECÇÃO", "value": "MICROLENTE DE EINSTEIN"},
                    "image_query": "gravitational lensing galaxy cluster hubble"
                },
                {
                    "headline": "4. DESCOBERTA DO JAMES WEBB",
                    "stats": {"label": "NEBULOSA DE ÓRION", "value": "40 PARES DE JÚPITERES BINÁRIOS"},
                    "image_query": "orion nebula james webb infrared stars protoplanets"
                },
                {
                    "headline": "5. OCEANOS SOB O GELO ETERNO",
                    "stats": {"label": "CALOR INTERNO", "value": "GEOTERMIA E HIDROGÊNIO"},
                    "image_query": "europa icy moon ocean plume nasa"
                },
                {
                    "headline": "6. VIDA NA ESCURIDÃO INTERESTELAR?",
                    "stats": {"label": "MISSÃO FUTURA NASA", "value": "TELESCÓPIO NANCY GRACE ROMAN"},
                    "image_query": "milky way dark dust clouds interstellar medium"
                }
            ]
        },
        {
            "id": "tiktok-011-fermi-paradox-great-filter",
            "title": "O Paradoxo de Fermi e o Grande Filtro: Por que ainda não encontramos civilizações alienígenas?",
            "headline": "O SILÊNCIO ASSUSTADOR DO COSMOS",
            "description": "Com 40 bilhões de planetas habitáveis só na Via Láctea e bilhões de anos de vantagem, onde estão todos? A teoria do Grande Filtro explicada.",
            "narration": (
                "Existem cerca de duzentas a quatrocentas bilhões de estrelas apenas na nossa galáxia, a Via Láctea, e dados do telescópio Kepler mostram que há pelo menos quarenta bilhões de planetas rochosos na zona habitável de suas estrelas. "
                "Muitos desses mundos se formaram cinco bilhões de anos antes da Terra. Mesmo que uma civilização viajasse a apenas um por cento da velocidade da luz, ela conseguiria colonizar a galáxia inteira em menos de dez milhões de anos. "
                "Então, como perguntou o físico Enrico Fermi em mil novecentos e cinquenta: onde estão todos? Por que não vemos sondas, sinais de rádio ou megaestruturas alienígenas em nenhum lugar? "
                "A resposta mais perturbadora da ciência é a hipótese do Grande Filtro, formulada pelo economista e pesquisador Robin Hanson. "
                "O Grande Filtro propõe que, no caminho evolutivo entre a química pré-biótica e uma civilização interplanetária avançada, existe uma barreira quase intransponível que aniquila praticamente todas as espécies. "
                "Isso nos coloca diante de dois cenários igualmente arrepiantes. "
                "No primeiro cenário, o Grande Filtro está no nosso passado: o surgimento da primeira célula viva ou do cérebro humano inteligente é um milagre estatístico tão raro que nós somos uma das primeiras civilizações de toda a galáxia. "
                "No segundo cenário — muito mais assustador — a vida surge facilmente no cosmos, mas o Grande Filtro está no nosso futuro: toda civilização tecnológica acaba destruindo a si mesma assim que descobre armas nucleares, inteligência artificial descontrolada ou engenharia climática extrema! "
                "Siga o perfil, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
            ),
            "tags": ["scapaticitecnologia", "paradoxodefermi", "grandefiltro", "extraterrestre", "astrobiologia", "universo", "foryou"],
            "chapters": [
                {
                    "headline": "1. OS NÚMEROS DA VIA LÁCTEA",
                    "stats": {"label": "PLANETAS HABITÁVEIS", "value": "~40 BILHÕES NA GALÁXIA"},
                    "image_query": "milky way galaxy core billions of stars nasa"
                },
                {
                    "headline": "2. A PERGUNTA DE ENRICO FERMI",
                    "stats": {"label": "TEMPO DE COLONIZAÇÃO", "value": "APENAS 10 MILHÕES DE ANOS"},
                    "image_query": "exoplanet earth like habitable zone kepler nasa"
                },
                {
                    "headline": "3. O SILÊNCIO DO RÁDIO (SETI)",
                    "stats": {"label": "BUSCA POR SINAIS", "value": "NENHUMA TRANSMISSÃO CONFIRMADA"},
                    "image_query": "radio telescope array deep space network nasa"
                },
                {
                    "headline": "4. A TEORIA DO GRANDE FILTRO",
                    "stats": {"label": "AUTOR DA HIPÓTESE", "value": "ROBIN HANSON (1996)"},
                    "image_query": "supernova shockwave cosmic catastrophe hubble"
                },
                {
                    "headline": "5. CENÁRIO 1: SOMOS OS PRIMEIROS?",
                    "stats": {"label": "FILTRO NO PASSADO", "value": "ORIGEM DA VIDA COMPLEXA"},
                    "image_query": "pillars of creation eagle nebula james webb"
                },
                {
                    "headline": "6. CENÁRIO 2: O FILTRO ESTÁ À FRENTE?",
                    "stats": {"label": "DESAFIO HUMANO", "value": "TORNAR-SE MULTIPLANETÁRIO"},
                    "image_query": "mars planet surface perseverance rover nasa"
                }
            ]
        },
        {
            "id": "tiktok-012-spaghettification-black-hole",
            "title": "O que realmente aconteceria com o seu corpo se você caísse em um Buraco Negro?",
            "headline": "DENTRO DO HORIZONTE DE EVENTOS",
            "description": "A diferença surpreendente entre cair em um buraco negro estelar e em um supermassivo como o Gargantua: espaguetificação, horizonte de eventos e relatividade.",
            "narration": (
                "O que aconteceria segundo a física real se você caísse dentro de um buraco negro? A resposta depende crucialmente do tamanho do monstro gravitacional! "
                "Se você se aproximasse de um buraco negro estelar, com cerca de dez vezes a massa do Sol e apenas trinta quilômetros de diâmetro, você morreria muito antes de cruzar o horizonte de eventos. "
                "Isso acontece porque a gravidade diminui com o quadrado da distância: a força gravitacional puxando os seus pés seria milhões de vezes mais intensa do que a força puxando a sua cabeça! "
                "Essa força de maré extrema esticaria o seu corpo verticalmente e comprimiria seus ombros lateralmente até transformar suas células e átomos em um fino fio de plasma subatômico — o processo que Stephen Hawking batizou de Espaguetificação. "
                "Porém, se você caísse em um buraco negro supermassivo gigantesco, como o TON 618 ou o Sagitário A Estrela no centro da Via Láctea, com milhões ou bilhões de massas solares, algo surpreendente aconteceria: "
                "Como o horizonte de eventos fica a milhões de quilômetros do centro, a diferença de gravidade entre seus pés e sua cabeça na borda é quase zero! "
                "Você cruzaria o horizonte de eventos vivo, sem sentir nenhum solavanco! "
                "Olhando para trás, você veria toda a luz do universo externo concentrada em um círculo brilhante e acelerado no tempo, enquanto um observador fora do buraco negro veria a sua imagem congelar e ficar cada vez mais vermelha na borda pela eternidade! "
                "Siga o perfil, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
            ),
            "tags": ["scapaticitecnologia", "buraconegro", "espaguetificacao", "horizontedeeventos", "astrofisica", "relatividade", "foryou"],
            "chapters": [
                {
                    "headline": "1. DOIS DESTINOS DIFERENTES",
                    "stats": {"label": "FATOR DECISIVO", "value": "MASSA DO BURACO NEGRO"},
                    "image_query": "black hole accretion disk gravitational lensing nasa"
                },
                {
                    "headline": "2. BURACO NEGRO ESTELAR (10 SÓIS)",
                    "stats": {"label": "FORÇA DE MARÉ", "value": "LETAL ANTES DA BORDA"},
                    "image_query": "cygnus x-1 black hole devouring star nasa"
                },
                {
                    "headline": "3. A ESPAGUETIFICAÇÃO ATÔMICA",
                    "stats": {"label": "EFEITO FÍSICO", "value": "ESTIRAMENTO EM FIO DE PLASMA"},
                    "image_query": "tidal disruption event star shredded by black hole"
                },
                {
                    "headline": "4. BURACO NEGRO SUPERMASSIVO",
                    "stats": {"label": "HORIZONTE SUAVE", "value": "CRUZA A BORDA INTACTO"},
                    "image_query": "sagittarius a star black hole event horizon telescope"
                },
                {
                    "headline": "5. A VISÃO DE QUEM ESTÁ FORA",
                    "stats": {"label": "ILUSÃO RELATIVÍSTICA", "value": "IMAGEM CONGELA NA BORDA"},
                    "image_query": "m87 supermassive black hole polarized light"
                },
                {
                    "headline": "6. RUMO À SINGULARIDADE CENTRAL",
                    "stats": {"label": "DESTINO INEVITÁVEL", "value": "O ESPAÇO E O TEMPO SE INVERTEM"},
                    "image_query": "deep space gravitational wave black hole merger"
                }
            ]
        }
    ]
}

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"completed_slots": [], "published_topics": []}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def produce_and_publish_slot(slot_name: str, prepare_only: bool = False):
    """Produz e publica um mini-documentário vertical de alta densidade científica no TikTok para o slot indicado."""
    print("=" * 60, flush=True)
    print(f"🎵 TIKTOK SLOTS MANAGER: Executando Slot {slot_name.upper()} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})", flush=True)
    print("=" * 60, flush=True)

    state = load_state()
    today_str = datetime.now().strftime("%Y-%m-%d")
    slot_key = f"{today_str}_{slot_name}"

    if slot_key in state["completed_slots"]:
        print(f"[TIKTOK SLOTS] ℹ️ O slot {slot_name} de hoje ({today_str}) já foi publicado anteriormente. Finalizando.", flush=True)
        return True

    # Para o slot das 09h, o daily_autopilot já faz a publicação unificada!
    if slot_name == "09h":
        print("[TIKTOK SLOTS] ℹ️ O slot das 09h é orquestrado pelo Daily Autopilot unificado (YouTube Longo, Shorts, Reels e TikTok).", flush=True)
        return True

    static_candidates = TIKTOK_EXCLUSIVE_SLOTS.get(slot_name, [])
    sys.path.append(os.path.join(PROJECT_DIR, "pipeline"))
    from trend_replenisher import load_generated_tiktok_queue, replenish_tiktok_slots_queue

    tt_queue = load_generated_tiktok_queue()
    candidates = list(static_candidates) + list(tt_queue.get(slot_name, []))
    if not candidates:
        print(f"[TIKTOK SLOTS] ⚠️ Nenhum tema configurado para o slot {slot_name}.", flush=True)
        return False

    published_set = set(state.get("published_topics", []))

    # Escolhe o primeiro tema ainda não publicado
    target = None
    for cand in candidates:
        cand_id = cand["id"]
        if cand_id not in published_set:
            target = cand
            break

    if not target:
        # Lista do slot esgotou: lê tendências ao vivo e reabastece 7 dias antes de recorrer à rotação
        print(f"[TIKTOK SLOTS] 📡 Lista do slot {slot_name} concluída! Lendo tendências para preencher mais 7 dias...", flush=True)
        tt_queue = replenish_tiktok_slots_queue(published_set, TIKTOK_EXCLUSIVE_SLOTS, days=7)
        candidates = list(static_candidates) + list(tt_queue.get(slot_name, []))
        for cand in candidates:
            if cand["id"] not in published_set:
                target = cand
                break

    if not target:
        # Fallback de rotação apenas se nenhum novo pôde ser gerado
        target = candidates[0]
        state["published_topics"] = []

    proj_id = f"tiktok-{slot_name}-{datetime.now().strftime('%Y%m%d')}"
    proj_dir = os.path.join(PROJECT_DIR, "projects", proj_id)
    assets_dir = os.path.join(proj_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    print(f"[TIKTOK SLOTS] 🎬 Produzindo Mini-Documentário TikTok: {target['title']}", flush=True)

    # 1. Obter 6 imagens de alta resolução da NASA para os 6 capítulos progressivos (com fallback procedural anti-404)
    sys.path.append(os.path.join(PROJECT_DIR, "pipeline"))
    from daily_autopilot import get_nasa_image_url, download_and_crop
    from media.fallback_visuals import is_valid_image, generate_cosmic_artwork

    chapters = target.get("chapters", [])
    used_urls = set()
    pan_directions = ["zoom-in", "pan-right", "hyper-zoom", "zoom-out", "pan-left", "dramatic-pulse"]
    scenes = []

    for idx, ch in enumerate(chapters):
        q = ch.get("image_query", "deep space galaxies hubble")
        img_name = f"scene_{idx + 1}.jpg"
        img_dest = os.path.join(assets_dir, img_name)
        if not is_valid_image(img_dest):
            downloaded = False
            img_url = get_nasa_image_url(q, used_urls)
            if img_url:
                try:
                    download_and_crop(img_url, img_dest)
                    downloaded = is_valid_image(img_dest)
                except Exception as dl_err:
                    print(f"[TIKTOK SLOTS] ⚠️ Erro ao baixar {img_name}: {dl_err}", flush=True)
            if not downloaded:
                generate_cosmic_artwork(img_dest, seed_key=f"{proj_id}_{img_name}_{q}")
                print(f"[TIKTOK SLOTS] 🎨 Arte cósmica procedural gerada como fallback: {img_name}", flush=True)
            else:
                print(f"[TIKTOK SLOTS] 🔭 Imagem {img_name} obtida para capítulo {idx + 1}: {q}", flush=True)

        scenes.append({
            "id": f"scene_{idx + 1}",
            "type": "hook" if idx == 0 else ("climax" if idx == len(chapters) - 2 else ("cta" if idx == len(chapters) - 1 else "investigation")),
            "visual_theme": q,
            "headline": ch.get("headline", target["headline"]),
            "stats": ch.get("stats"),
            "narration": target["narration"] if idx == 0 else "",
            "highlight_words": [
                "SCAPATICI", "TECNOLOGIA", "UNIVERSO", "FÍSICA", "QUÂNTICA",
                "EINSTEIN", "HAWKING", "WEBB", "HUBBLE", "LUZ", "BURACO", "NEGRO",
                "TRILHÕES", "BILHÕES", "TEMPO", "GRAVIDADE", "PARADOXO"
            ],
            "backgroundImage": f"assets/{proj_id}/{img_name}",
            "panDirection": pan_directions[idx % len(pan_directions)]
        })

    # 2. Gerar script.json adaptado para Remotion Shorts de longa duração (1m45s - 2m05s)
    script_data = {
        "id": proj_id,
        "title": target["title"],
        "topic": target["headline"],
        "channel": "Scapatici Tecnologia",
        "target_duration_seconds": 115,
        "fps": 30,
        "vinheta_duration_frames": 0,
        "bg_music_volume": 0.12,
        "seo": {
            "description": target.get("description", target["title"]),
            "tags": target["tags"]
        },
        "scenes": scenes
    }
    with open(os.path.join(proj_dir, "script.json"), "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2, ensure_ascii=False)

    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    # 3. Gerar TTS (se ainda não existir)
    if not os.path.exists(os.path.join(proj_dir, "audio.mp3")):
        print("[TIKTOK SLOTS] 🎙️ Sintetizando áudio neural completo com Edge-TTS...", flush=True)
        subprocess.run(f"node pipeline/orchestrator.js tts {proj_id}", shell=True, check=True, cwd=PROJECT_DIR, env=env)
    else:
        print("[TIKTOK SLOTS] 🎙️ Áudio neural já existente. Pulando TTS...", flush=True)

    # 4. Renderizar vídeo vertical Shorts (se ainda não existir)
    if not os.path.exists(os.path.join(proj_dir, "output_shorts.mp4")):
        print("[TIKTOK SLOTS] 📱 Renderizando mini-documentário vertical (9:16)...", flush=True)
        subprocess.run(f"node pipeline/orchestrator.js render {proj_id} shorts", shell=True, check=True, cwd=PROJECT_DIR, env=env)
    else:
        print("[TIKTOK SLOTS] 📱 Vídeo vertical já renderizado. Pulando renderização...", flush=True)

    if prepare_only:
        print(f"[TIKTOK SLOTS] ✅ Pre-render concluído para slot {slot_name} ({proj_id}). Pronto para o horário exato!", flush=True)
        return True

    # 5. Publicar no TikTok Creator Center
    print("[TIKTOK SLOTS] 🚀 Enviando para o TikTok...", flush=True)
    try:
        from tiktok_uploader import upload_video
        success = upload_video(proj_id)
    except Exception as e:
        print(f"[TIKTOK SLOTS] ⚠️ Erro no upload direto: {e}", flush=True)
        res = subprocess.run(f"python pipeline/publishing/tiktok_uploader.py --project {proj_id}", shell=True, cwd=PROJECT_DIR, env=env)
        success = (res.returncode == 0)

    # 6. Atualizar estado
    if success:
        state["completed_slots"].append(slot_key)
        state.setdefault("published_topics", []).append(target["id"])
        save_state(state)
        print("=" * 60, flush=True)
        print(f"🎉 TIKTOK SLOT {slot_name.upper()} CONCLUÍDO COM SUCESSO! ({today_str})", flush=True)
        print("=" * 60, flush=True)
    else:
        print(f"[TIKTOK SLOTS] ❌ O upload do slot {slot_name} não pôde ser confirmado.", flush=True)

    return success

def main():
    parser = argparse.ArgumentParser(description="TikTok Slots Manager (3x ao dia: 09h, 16h, 20h)")
    parser.add_argument("--slot", choices=["09h", "16h", "20h", "auto"], default="auto", help="Slot a executar")
    parser.add_argument("--prepare-only", action="store_true", help="Apenas renderiza o slot sem publicar ainda")
    args = parser.parse_args()

    slot = args.slot
    if slot == "auto":
        hour = datetime.now().hour
        if hour < 13:
            slot = "09h"
        elif hour < 18:
            slot = "16h"
        else:
            slot = "20h"

    produce_and_publish_slot(slot, prepare_only=args.prepare_only)

if __name__ == "__main__":
    main()
