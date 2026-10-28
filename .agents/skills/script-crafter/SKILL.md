---
name: script-crafter
description: Cria roteiros hipnóticos de alta retenção no formato estruturado para o pipeline Remotion do Simple-Tube, seguindo as diretrizes cinematográficas e de social media sênior do Canal Scapatici Tecnologia.
---

# Script Crafter & Cinematographic Master Skill
**Canal Oficial:** Scapatici Tecnologia  
**Padrão de Qualidade:** Direção Cinematográfica (USD $50k/mês) & Social Media de Alta Performance (R$ 100k/mês)

Esta skill define as regras invioláveis de roteirização, ritmo de edição, cinematografia e desdobramento para YouTube Shorts e Instagram Reels consumidos pelo pipeline Remotion e Edge-TTS do Simple-Tube.

---

## 🎯 1. REGRAS INVIOLÁVEIS DO CANAL SCAPATICI TECNOLOGIA

### Regra de Ouro da Despedida (Matriz Obrigatória de Encerramento)
> [!IMPORTANT]
> **Nenhum vídeo longo pode terminar sem a matriz clássica de despedida e convite à comunidade.**
> Nos últimos vídeos, se essa frase for omitida, a retenção comunitária e a conversão de inscritos despencam.

A última cena (`scenes[scenes.length - 1]`) deve ser OBRIGATORIAMENTE do tipo `"cta"` e conter a narração de fechamento seguindo esta matriz:
```json
{
  "id": "scene_final_cta",
  "type": "cta",
  "visual_theme": "future_network_community",
  "headline": "O FUTURO DA DESCOBERTA CÓSMICA",
  "narration": "E você, o que acha dessa revelação? Deixe sua teoria aqui nos comentários, compartilhe este vídeo com quem é fascinado pelos mistérios do universo, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras da ciência e da tecnologia, e até o próximo vídeo!",
  "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SEU COMENTÁRIO", "INSCREVA-SE", "PRÓXIMO VÍDEO"],
  "stats": { "label": "Canal Oficial", "value": "Scapatici Tech" },
  "backgroundImage": "assets/<projectId>/scene_cta.jpg",
  "panDirection": "zoom-out"
}
```

---

## 🎬 2. DIRETRIZES DE DIREÇÃO CINEMATOGRÁFICA (USD $50.000/mês)

1. **Movimentos de Câmera Variados (Evitar Monotonia Visual):**
   - Use uma alternância inteligente de `panDirection` ao longo dos capítulos:
     - `'zoom-in'`: Para hooks, apresentações de anomalias e momentos de aproximação dramática.
     - `'zoom-out'`: Para conclusões, revelações da imensidão cósmica e encerramentos.
     - `'pan-left'` e `'pan-right'`: Para investigações, dados técnicos e transições laterais.
     - `'dramatic-pulse'`: Para momentos de clímax, paradoxos e dilemas aterrorizantes.
     - `'floating-drift'`: Para temas de gravidade zero, poeira interestelar e tempo profundo.
     - `'hyper-zoom'`: Para impactos, singularidades e saltos tecnológicos exponenciais.
     - `'tilt-down'`: Para revelar estruturas de mega-escala ou profundidade cósmica.

2. **Imagens e Vídeos Dinâmicos de Fundo (Movies):**
   - O pipeline suporta tanto imagens de altíssima definição quanto vídeos curtos/animações em loop (`.mp4`, `.webm`) através de `backgroundImage` ou `backgroundVideo`.
   - Em cenas de clímax, buracos negros, naves espaciais ou explosões cósmicas, priorize mídias animadas ou de dinamismo extremo.

3. **Trilha Sonora de Mistério e Suspense (Sempre Presente):**
   - Toda renderização deve ter trilha de dark sci-fi ambient / space drone (`bg_music_volume: 0.12` a `0.14`).
   - A trilha deve criar uma atmosfera imersiva sem conflitar com as frequências vocais da narração.

---

## 📱 3. DIRETRIZES DE SHORTS & REELS (R$ 100.000/mês - Social Media Master)

Todo vídeo longo produzido gera automaticamente uma versão vertical (9:16 - 1080x1920) otimizada para o algoritmo do YouTube Shorts e do Instagram Reels:

1. **Enquadramento Inteligente "Ambient Canvas" (Zero Imagens Cortadas):**
   - As redes sociais verticais frequentemente cortam 70% das imagens horizontais. No Simple-Tube, o componente `ShortsVideo` e `KenBurnsImage` utilizam a técnica de **Ambient Blur 9:16 + Hero Window 16:9 Central com Glow Neon**, garantindo que nenhum gráfico, planeta ou rosto seja cortado.
2. **Safe Zones Absolutas:**
   - **Topo:** Margem livre de 130px (evita barra de status e abas).
   - **Laterais:** Margem livre de 60px à esquerda e 110px à direita (evita botões de Like, Comentário e Compartilhamento do Reels).
   - **Inferior:** Margem livre abaixo de 1480px (evita nome de usuário, descrição e tag de áudio).
3. **Legendas Cinéticas Hormozi / MrBeast:**
   - Posição segura centralizada (Y = 1220px).
   - Blocos de 2 a 3 palavras para leitura relâmpago.
   - Destaque palavra-a-palavra com escala pop (1.15x), ciano elétrico `#00F2FE` e dourado `#FFD200`.
4. **Retenção Psicológica & Pacing:**
   - Barra de progresso contínua no topo para motivar o espectador a ver até o último segundo.
   - Troca visual ou corte de câmera a cada ~7 segundos para resetar o nível de atenção do espectador.
5. **CTA Final do Shorts (3.5 segundos):**
   - Card magnético orientando o espectador a clicar no link nos comentários/descrição para assistir ao documentário completo no YouTube.

---

## 🔬 4. VARREDURA DE TENDÊNCIAS E TEMAS EM ALTA

Para novos episódios, sempre priorize pautas que combinem:
- **Mistérios da Física & Astrofísica:** Paradoxo de Fermi, Teoria da Floresta Negra, Radiação Hawking, Matéria Escura, Telescópio James Webb, Buracos de Minhoca.
- **Tecnologias de Fronteira:** Computação Quântica Inviolável, Inteligência Artificial Geral, Singularidade Tecnológica, Engenharia Estelar (Esferas de Dyson).
- **Enigmas Histórico-Científicos:** Sinal WOW!, Projeto Arecibo, Paradoxo de Olbers, Teoria dos Jogos Cósmica.

---

## 📝 5. ESTRUTURA DO ARQUIVO `script.json`

```json
{
  "id": "video-xxx-slug-do-tema",
  "title": "Título Impactante com Mais de 80 Caracteres e Alta Curiosidade",
  "topic": "Tema Central, Física Aplicada e Curiosidades",
  "channel": "Scapatici Tecnologia",
  "target_duration_seconds": 320,
  "fps": 30,
  "vinheta_duration_frames": 90,
  "bg_music_volume": 0.12,
  "seo": {
    "title_options": [
      "Opção 1: Pergunta Intrigante",
      "Opção 2: Declaração Científica Provocativa",
      "Opção 3: O Mistério Revelado"
    ],
    "description": "Sinopse hipnótica detalhada com capítulos (timestamps), hashtags e link de inscrição...",
    "tags": [
      "scapatici tecnologia",
      "astronomia",
      "fisica",
      "ciencia",
      "misterios do universo"
    ]
  },
  "scenes": [
    {
      "id": "scene_1_hook",
      "type": "hook",
      "visual_theme": "deep_space_anomaly",
      "headline": "O SINAL QUE NÃO DEVERIA EXISTIR",
      "narration": "Texto do hook hipnótico de alta retenção nos primeiros 50 segundos...",
      "highlight_words": ["ANOMALIA", "RADIAÇÃO", "DESCONHECIDO"],
      "stats": { "label": "Detecção", "value": "Origem Desconhecida" },
      "backgroundImage": "assets/video-xxx/scene_1.jpg",
      "panDirection": "zoom-in"
    },
    {
      "id": "scene_final_cta",
      "type": "cta",
      "visual_theme": "cosmic_community",
      "headline": "QUEM SOMOS NÓS NO COSMOS?",
      "narration": "E você, o que acha dessa descoberta? Deixe sua teoria nos comentários, compartilhe este vídeo com quem ama ciência e tecnologia, inscreva-se no canal Scapatici Tecnologia para desvendar as maiores fronteiras do universo, e até o próximo vídeo!",
      "highlight_words": ["SCAPATICI TECNOLOGIA", "DEIXE SEU COMENTÁRIO", "INSCREVA-SE"],
      "stats": { "label": "Canal Oficial", "value": "Scapatici Tech" },
      "backgroundImage": "assets/video-xxx/scene_cta.jpg",
      "panDirection": "zoom-out"
    }
  ]
}
```
