# 🛸 Simple-Tube (v1.0.0) — Pipeline Audiovisual Autônomo & Cinematográfico
**Canal Oficial:** Scapatici Tecnologia  
**Versão:** 1.0.0 (Release Oficial de Produção)

O **Simple-Tube** é uma esteira industrial de produção audiovisual e distribuição multicanal de alto nível, projetada sob rigorosa **Direção Cinematográfica (padrão USD $50.000/mês)** e **Social Media de Alta Performance (padrão R$ 100.000/mês)**, com automação ponta a ponta e integração nativa ao ecossistema do Windows.

---

## 💎 Pilares da Versão 1.0.0

1. **Direção Cinematográfica e Suporte a Filmes (*Movies*):**
   - Suporte dinâmico a imagens estáticas e vídeos curtos em loop (`.mp4`, `.webm`) através de `backgroundVideo` e `backgroundImage`.
   - Movimentos avançados de câmera com foco em astrofísica e suspense: `hyper-zoom`, `tilt-down`, `dramatic-pulse`, `floating-drift`, `pan-left`, `pan-right`, `zoom-in` e `zoom-out`.
   - Partículas cósmicas com paralaxe, anamorphic lens flare e profundidade atmosférica.
2. **Matriz Obrigatória de Encerramento (Canal Scapatici Tecnologia):**
   - Todo roteiro encerra rigorosamente com a matriz clássica do canal:
     > *"Deixe sua visão nos comentários, compartilhe este vídeo com quem ama ciência espacial e mistérios do cosmos, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras do universo, e até o próximo vídeo!"*
   - Validador pré-renderização no orquestrador garantindo integridade comunitária.
3. **Shorts & Reels de Alta Performance (*Ambient Canvas*):**
   - **Zero Imagens Cortadas:** Camada de fundo 9:16 com desfoque gaussiano de 35px + Janela Hero central em proporção preservada com borda ciano neon e sombra 3D profunda.
   - **Safe Zones Absolutas:** Margens calculadas para nunca colidir com a interface do YouTube Shorts e botões de curtir/comentar do Instagram Reels.
   - **Legendas Cinéticas Hormozi / MrBeast:** Animação pop-scale (1.15x) e contraste elétrico (`#00F2FE` e `#FFD200`).
   - **Trilha Sonora de Mistério Ativa:** Mixagem de dark space drone em harmonia com a narração vocal.
4. **Link Automático no Primeiro Comentário:**
   - No YouTube Shorts, o link do vídeo longo é adicionado no cabeçalho da descrição.
   - No Instagram Reels, o primeiro comentário é publicado automaticamente pelo bot com o link direto para o documentário completo no YouTube.
5. **Autopilot Diário 100% Autônomo às 09h:**
   - Agendamento duplo:
     - **Windows Task Scheduler:** Disparo pontual diário às 09:00 (`SimpleTube-Daily-09h`).
     - **Windows Startup:** Se a máquina estava desligada às 09h, executa automaticamente em segundo plano assim que o computador ligar.
     - **Proteção contra Duplicidade:** O script verifica a data atual e finaliza em 0.1s se o conteúdo do dia já foi postado.

---

## 🚀 Como Executar Manualmente

### 1. Pré-visualizar no Remotion Player
```bash
npm run preview
```

### 2. Sintetizar Voz Neural e Timings (Edge-TTS)
```bash
node pipeline/orchestrator.js tts <id-do-projeto>
```

### 3. Renderizar Vídeo (1080p)
```bash
# Formato Horizontal 16:9 (YouTube)
node pipeline/orchestrator.js render <id-do-projeto> 16x9

# Formato Vertical 9:16 (Shorts & Reels com Ambient Canvas)
node pipeline/orchestrator.js render <id-do-projeto> shorts
```

### 4. Publicar nas Plataformas
```bash
# Publica o vídeo longo 16:9 no YouTube
node pipeline/orchestrator.js publish <id-do-projeto> public

# Publica o Shorts no YouTube
node pipeline/orchestrator.js publish-shorts <id-do-projeto> public

# Publica no Instagram Reels (com primeiro comentário fixado com o link do YouTube)
node pipeline/orchestrator.js instagram <id-do-projeto>
```

### 5. Executar o Autopilot Diário Manualmente
```bash
python pipeline/daily_autopilot.py
```

---

## 📂 Arquitetura de Pastas de Cada Vídeo

Cada episódio vive isolado em `projects/<id-do-projeto>/`:
- `script.json`: Roteiro estruturado, cenas, ganchos, palavras-chave e matriz de CTA.
- `assets/`: 8 imagens/vídeos de alta definição (1920x1080) da NASA e arte conceitual.
- `audio.mp3`: Narração vocal completa (`pt-BR-AntonioNeural`).
- `audio_intro.mp3` e `audio_rest.mp3`: Áudios divididos para encaixe da vinheta de 3s.
- `subtitles.json`: Timeline de palavras e marcações fonéticas para as legendas cinéticas.
- `thumbnail.jpg`: Miniatura em alta conversão (1920x1080).
- `output_16x9.mp4`: Arquivo de vídeo longo final em 1080p.
- `output_shorts.mp4`: Arquivo vertical 9:16 final.
- `youtube_16x9_info.json` e `youtube_shorts_info.json`: Metadados e links das postagens ao vivo.

---

## 🏆 Catálogo de Episódios Produzidos (v1.0.0)
- **Vídeo 001:** O Mistério do Sinal WOW!
- **Vídeo 002:** O Paradoxo de Fermi
- **Vídeo 003:** A Hipótese da Simulação
- **Vídeo 004:** Matéria Escura e Energia Escura
- **Vídeo 005:** O Princípio Holográfico
- **Vídeo 006:** O Entrelaçamento Quântico
- **Vídeo 007:** A Hipótese da Floresta Negra
- **Vídeo 008:** A Teoria do Grande Filtro (Lançamento Oficial v1.0.0)
- **Vídeo 009:** O Vazio de Boötes (Agendado no Autopilot)
