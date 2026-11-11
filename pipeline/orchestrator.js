const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PROJECT_DIR = path.resolve(__dirname, '..');
const PROJECTS_BASE = path.join(PROJECT_DIR, 'projects');
const PUBLIC_DIR = path.join(PROJECT_DIR, 'public');

function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

async function runCommand(cmd) {
  console.log(`\n> Executando: ${cmd}`);
  execSync(cmd, { stdio: 'inherit', cwd: PROJECT_DIR });
}

async function handleTTS(projectId) {
  const projectPath = path.join(PROJECTS_BASE, projectId);
  const scriptPath = path.join(projectPath, 'script.json');
  const audioPath = path.join(projectPath, 'audio.mp3');
  const subPath = path.join(projectPath, 'subtitles.json');

  if (!fs.existsSync(scriptPath)) {
    console.error(`[ERRO] Roteiro não encontrado em: ${scriptPath}`);
    process.exit(1);
  }

  console.log(`[1/2] Gerando voz neural e timings para "${projectId}"...`);
  const ttsCmd = `python pipeline/audio/tts_engine.py --file "${scriptPath}" --out-audio "${audioPath}" --out-sub "${subPath}" --voice pt-BR-AntonioNeural --rate="+0%" --pitch="+0Hz"`;
  runCommand(ttsCmd);
}

async function handleRender(projectId, format = '16x9') {
  const projectPath = path.join(PROJECTS_BASE, projectId);
  const scriptPath = path.join(projectPath, 'script.json');
  const audioPath = path.join(projectPath, 'audio.mp3');
  const subPath = path.join(projectPath, 'subtitles.json');
  const outputPath = path.join(projectPath, `output_${format}.mp4`);

  if (!fs.existsSync(scriptPath) || !fs.existsSync(audioPath) || !fs.existsSync(subPath)) {
    console.log(`Assets não encontrados para "${projectId}". Gerando TTS primeiro...`);
    await handleTTS(projectId);
  }

  ensureDir(PUBLIC_DIR);

  // Limpa áudios e pastas de projetos antigos no diretório public para evitar copiar +150MB a cada bundle
  try {
    const pubEntries = fs.readdirSync(PUBLIC_DIR);
    for (const entry of pubEntries) {
      if ((entry.startsWith('video-') || entry.startsWith('tiktok-')) && !entry.startsWith(projectId) && entry.endsWith('.mp3')) {
        fs.unlinkSync(path.join(PUBLIC_DIR, entry));
      }
    }
    const pubAssetsRoot = path.join(PUBLIC_DIR, 'assets');
    if (fs.existsSync(pubAssetsRoot)) {
      const assetFolders = fs.readdirSync(pubAssetsRoot);
      for (const folder of assetFolders) {
        if ((folder.startsWith('video-') || folder.startsWith('tiktok-')) && folder !== projectId) {
          fs.rmSync(path.join(pubAssetsRoot, folder), { recursive: true, force: true });
        }
      }
    }
  } catch (cleanErr) {
    console.warn('[CLEANUP] Aviso ao limpar assets antigos do public:', cleanErr.message);
  }

  // Copia o áudio principal para public com id único
  const publicAudioFilename = `${projectId}_audio.mp3`;
  fs.copyFileSync(audioPath, path.join(PUBLIC_DIR, publicAudioFilename));

  // Verifica se existem áudios divididos (Introdução, Restante e Vertical Denso)
  const audioIntroPath = path.join(projectPath, 'audio_intro.mp3');
  const audioRestPath = path.join(projectPath, 'audio_rest.mp3');
  const audioShortsPath = path.join(projectPath, 'audio_shorts.mp3');
  let publicAudioIntro = null;
  let publicAudioRest = null;
  let publicAudioShorts = null;

  if (fs.existsSync(audioIntroPath) && fs.existsSync(audioRestPath)) {
    publicAudioIntro = `${projectId}_audio_intro.mp3`;
    publicAudioRest = `${projectId}_audio_rest.mp3`;
    fs.copyFileSync(audioIntroPath, path.join(PUBLIC_DIR, publicAudioIntro));
    fs.copyFileSync(audioRestPath, path.join(PUBLIC_DIR, publicAudioRest));
  }
  if (fs.existsSync(audioShortsPath)) {
    publicAudioShorts = `${projectId}_audio_shorts.mp3`;
    fs.copyFileSync(audioShortsPath, path.join(PUBLIC_DIR, publicAudioShorts));
  }

  const script = JSON.parse(fs.readFileSync(scriptPath, 'utf8'));
  const subtitles = JSON.parse(fs.readFileSync(subPath, 'utf8'));

  // Garante integridade absoluta dos assets visuais antes do bundle (evita 404 no Remotion)
  const projectAssetsDir = path.join(projectPath, 'assets');
  ensureDir(projectAssetsDir);
  script.scenes.forEach((scene, idx) => {
    if (scene.backgroundImage && !scene.backgroundImage.startsWith('http') && !/\.(mp4|webm|mov|m4v)$/i.test(scene.backgroundImage)) {
      const filename = path.basename(scene.backgroundImage);
      const localAssetPath = path.join(projectAssetsDir, filename);
      const needsFallback = !fs.existsSync(localAssetPath) || fs.statSync(localAssetPath).size < 4096;
      if (needsFallback) {
        const seed = `${projectId}_${scene.id || idx}_${scene.visual_theme || scene.headline || 'cosmos'}`;
        console.warn(`[GUARD VISUAL] ⚠️ Asset ausente/inválido (${filename}). Gerando arte cósmica procedural...`);
        execSync(`python pipeline/media/fallback_visuals.py --out "${localAssetPath}" --seed "${seed.replace(/"/g, '')}"`, { stdio: 'inherit', cwd: PROJECT_DIR });
      }
    }
  });

  // Copia imagens das cenas para public se forem caminhos relativos locais
  if (fs.existsSync(projectAssetsDir)) {
    const publicProjectAssets = path.join(PUBLIC_DIR, 'assets', projectId);
    ensureDir(publicProjectAssets);
    const files = fs.readdirSync(projectAssetsDir);
    files.forEach((file) => {
      fs.copyFileSync(path.join(projectAssetsDir, file), path.join(publicProjectAssets, file));
    });
  }

  // Ajustar caminhos de backgroundImage e backgroundVideo para apontar para o public
  script.scenes.forEach((scene) => {
    // Se for vídeo ou se a imagem tiver extensão de vídeo
    if (scene.backgroundVideo && !scene.backgroundVideo.startsWith('http')) {
      const filename = path.basename(scene.backgroundVideo);
      scene.backgroundVideo = `assets/${projectId}/${filename}`;
    }
    if (scene.backgroundImage && !scene.backgroundImage.startsWith('http')) {
      const filename = path.basename(scene.backgroundImage);
      if (/\.(mp4|webm|mov|m4v)$/i.test(filename)) {
        scene.backgroundVideo = `assets/${projectId}/${filename}`;
      } else {
        scene.backgroundImage = `assets/${projectId}/${filename}`;
      }
    }
  });

  // Validação da Matriz Obrigatória de Encerramento (Canal Scapatici Tecnologia)
  const lastScene = script.scenes[script.scenes.length - 1];
  const lastNarration = (lastScene?.narration || '').toLowerCase();
  const hasFarewell =
    lastNarration.includes('scapatici tecnologia') &&
    (lastNarration.includes('inscreva-se') || lastNarration.includes('inscreva') || lastNarration.includes('próximo vídeo'));

  if (!hasFarewell) {
    console.warn(`\n[AVISO DO DIRETOR]: O roteiro de "${projectId}" NÃO contém a matriz clássica de despedida do canal na última cena!`);
    console.warn(`Lembre-se sempre de incluir o fechamento padrão: "... inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"\n`);
  } else {
    console.log(`[DIRETOR] ✅ Matriz de despedida Scapatici Tecnologia confirmada no encerramento.`);
  }

  const isShorts = format === 'shorts';
  const compositionId = isShorts ? 'SimpleTubeVideo-Shorts' : 'SimpleTubeVideo-16x9';

  // Calcular número exato de frames
  const fps = script.fps || 30;
  let totalFrames;
  if (isShorts) {
    const shortsSec = subtitles.shorts_duration_sec || subtitles.intro_duration_sec || subtitles.total_duration_sec || 90;
    totalFrames = Math.ceil((shortsSec + 3.5) * fps);
  } else {
    const audioDurationSec = subtitles.total_duration_sec || 30;
    totalFrames = Math.ceil((audioDurationSec + 1.2) * fps);
  }

  // Vinheta oficial de 3 segundos
  const vinhetaFrames = Math.round((subtitles.vinheta_duration_sec || 3.0) * fps);
  script.vinheta_duration_frames = vinhetaFrames;

  // Distribuir frames respeitando Introdução -> Vinheta -> Restante
  if (subtitles.intro_duration_sec && script.scenes.length > 1) {
    const introFrames = Math.ceil(subtitles.intro_duration_sec * fps);
    script.scenes[0].durationInFrames = introFrames;

    const restScenes = script.scenes.slice(1);
    const restFrames = Math.max(totalFrames - introFrames - vinhetaFrames, 300);
    const framesPerRestScene = Math.floor(restFrames / restScenes.length);

    restScenes.forEach((s) => {
      s.durationInFrames = framesPerRestScene;
    });
  } else {
    // Fallback proporcional padrão
    const framesPerScene = Math.floor(totalFrames / Math.max(script.scenes.length, 1));
    script.scenes.forEach((s) => {
      s.durationInFrames = framesPerScene;
    });
  }

  // Trilha sonora ambiente de fundo
  let bgMusicPath = 'audio/ambient_space_drone.wav';
  const projectBgMusic = path.join(projectPath, 'bg_music.mp3');
  if (fs.existsSync(projectBgMusic)) {
    const publicBgName = `${projectId}_bg.mp3`;
    fs.copyFileSync(projectBgMusic, path.join(PUBLIC_DIR, publicBgName));
    bgMusicPath = publicBgName;
  }

  const renderProps = {
    script,
    subtitles,
    audioPath: publicAudioFilename,
    audioIntroPath: publicAudioIntro,
    audioRestPath: publicAudioRest,
    audioShortsPath: publicAudioShorts,
    bgMusicPath,
    bgMusicVolume: script.bg_music_volume ?? 0.12,
  };

  const propsFile = path.join(projectPath, 'render_props.json');
  fs.writeFileSync(propsFile, JSON.stringify(renderProps, null, 2), 'utf8');

  console.log(`\n[2/2] Renderizando vídeo em 1080p (${totalFrames} frames @ ${fps}fps)...`);
  const renderCmd = `npx remotion render src/index.ts ${compositionId} "${outputPath}" --props="${propsFile}" --concurrency=2 --gl=angle`;
  
  let renderSuccess = false;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      if (attempt > 1) {
        console.log(`\n[RETRY RENDER] Tentativa ${attempt}/3 para "${projectId}"...`);
      }
      runCommand(renderCmd);
      renderSuccess = true;
      break;
    } catch (err) {
      // Tratamento de lock temporário do Windows/OneDrive no arquivo .remotion-in-progress
      const files = fs.readdirSync(projectPath);
      const inProgressFile = files.find((f) => f.startsWith(`output_${format}.mp4`) && f.endsWith('.remotion-in-progress'));
      if (inProgressFile) {
        console.log(`[RETRY] Finalizando renomeação pós-render para: ${outputPath}...`);
        const src = path.join(projectPath, inProgressFile);
        for (let i = 0; i < 5; i++) {
          try {
            if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
            fs.renameSync(src, outputPath);
            console.log(`[RETRY] Renomeação concluída com sucesso!`);
            renderSuccess = true;
            break;
          } catch (e) {
            const sleep = (ms) => { const end = Date.now() + ms; while (Date.now() < end) {} };
            sleep(1500);
          }
        }
        if (renderSuccess) break;
      }
      console.warn(`[AVISO RENDER] Falha na tentativa ${attempt}/3: ${err.message}`);
      if (attempt === 3) {
        throw err;
      }
    }
  }

  console.log(`\n[SUCESSO] Vídeo gerado com sucesso em: ${outputPath}`);
}

async function handlePublish(projectId, privacy = 'private', format = '16x9') {
  console.log(`\nPublicando automaticamente no YouTube ("${projectId}" [formato: ${format.toUpperCase()}])...`);
  const validPrivacy = ['private', 'unlisted', 'public'].includes(privacy) ? privacy : 'private';
  const publishCmd = `python pipeline/publishing/youtube_uploader.py --project ${projectId} --privacy ${validPrivacy} --format ${format}`;
  await runCommand(publishCmd);
}

async function handleInstagram(projectId) {
  console.log(`\nPublicando automaticamente no Instagram Reels ("${projectId}")...`);
  const instaCmd = `python pipeline/publishing/instagram_uploader.py --project ${projectId}`;
  await runCommand(instaCmd);
}

async function handleTikTok(projectId) {
  console.log(`\nPublicando automaticamente no TikTok ("${projectId}")...`);
  const tiktokCmd = `python pipeline/publishing/tiktok_uploader.py --project ${projectId}`;
  await runCommand(tiktokCmd);
}

async function main() {
  const args = process.argv.slice(2);
  const action = args[0] || 'help';
  const projectId = args[1] || 'video-006-quantum-entanglement';
  const formatOrPrivacy = args[2] || '16x9';

  ensureDir(PUBLIC_DIR);
  ensureDir(PROJECTS_BASE);

  switch (action) {
    case 'tts':
      await handleTTS(projectId);
      break;
    case 'render':
      await handleRender(projectId, formatOrPrivacy);
      break;
    case 'publish':
      await handlePublish(projectId, formatOrPrivacy, '16x9');
      break;
    case 'publish-shorts':
      await handlePublish(projectId, formatOrPrivacy, 'shorts');
      break;
    case 'shorts':
      await handleRender(projectId, 'shorts');
      await handlePublish(projectId, formatOrPrivacy, 'shorts');
      break;
    case 'instagram':
      await handleInstagram(projectId);
      break;
    case 'tiktok':
      await handleTikTok(projectId);
      break;
    case 'full':
      await handleTTS(projectId);
      await handleRender(projectId, formatOrPrivacy);
      break;
    case 'pipeline':
      // 1. Gera voz e timings
      await handleTTS(projectId);
      // 2. Renderiza e publica o vídeo longo oficial (16:9)
      await handleRender(projectId, '16x9');
      await handlePublish(projectId, 'private', '16x9');
      // 3. Renderiza e publica a versão YouTube Shorts (9:16)
      await handleRender(projectId, 'shorts');
      await handlePublish(projectId, 'private', 'shorts');
      // 4. Se houver credenciais do Instagram configuradas, publica no Reels automaticamente
      const instaCreds = path.join(__dirname, 'publishing', 'instagram_credentials.json');
      if (fs.existsSync(instaCreds)) {
        await handleInstagram(projectId);
      }
      // 5. Se houver sessão do TikTok configurada, publica no TikTok Creator Center automaticamente
      const tiktokSession = path.join(__dirname, 'publishing', 'tiktok_session.json');
      if (fs.existsSync(tiktokSession)) {
        await handleTikTok(projectId);
      }
      break;
    default:
      console.log(`
Simple-Tube Orchestrator
Uso:
  node pipeline/orchestrator.js tts <projectId>
  node pipeline/orchestrator.js render <projectId> [16x9|shorts]
  node pipeline/orchestrator.js publish <projectId> [private|unlisted|public]
  node pipeline/orchestrator.js publish-shorts <projectId> [private|unlisted|public]
  node pipeline/orchestrator.js shorts <projectId> [private|unlisted|public]
  node pipeline/orchestrator.js instagram <projectId>
  node pipeline/orchestrator.js pipeline <projectId>
      `);
      break;
  }
}

main().catch((err) => {
  console.error('[ERRO NO PIPELINE]:', err);
  process.exit(1);
});
