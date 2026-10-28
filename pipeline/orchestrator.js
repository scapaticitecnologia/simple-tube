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
  // Copia o áudio principal para public com id único
  const publicAudioFilename = `${projectId}_audio.mp3`;
  fs.copyFileSync(audioPath, path.join(PUBLIC_DIR, publicAudioFilename));

  // Verifica se existem áudios divididos (Introdução e Restante)
  const audioIntroPath = path.join(projectPath, 'audio_intro.mp3');
  const audioRestPath = path.join(projectPath, 'audio_rest.mp3');
  let publicAudioIntro = null;
  let publicAudioRest = null;

  if (fs.existsSync(audioIntroPath) && fs.existsSync(audioRestPath)) {
    publicAudioIntro = `${projectId}_audio_intro.mp3`;
    publicAudioRest = `${projectId}_audio_rest.mp3`;
    fs.copyFileSync(audioIntroPath, path.join(PUBLIC_DIR, publicAudioIntro));
    fs.copyFileSync(audioRestPath, path.join(PUBLIC_DIR, publicAudioRest));
  }

  const script = JSON.parse(fs.readFileSync(scriptPath, 'utf8'));
  const subtitles = JSON.parse(fs.readFileSync(subPath, 'utf8'));

  // Copia imagens das cenas para public se forem caminhos relativos locais
  const projectAssetsDir = path.join(projectPath, 'assets');
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
    const introSec = subtitles.intro_duration_sec || (subtitles.total_duration_sec ? Math.min(subtitles.total_duration_sec, 65) : 60);
    totalFrames = Math.ceil((introSec + 3.5) * fps);
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
    bgMusicPath,
    bgMusicVolume: script.bg_music_volume ?? 0.12,
  };

  const propsFile = path.join(projectPath, 'render_props.json');
  fs.writeFileSync(propsFile, JSON.stringify(renderProps, null, 2), 'utf8');

  console.log(`\n[2/2] Renderizando vídeo em 1080p (${totalFrames} frames @ ${fps}fps)...`);
  const renderCmd = `npx remotion render src/index.ts ${compositionId} "${outputPath}" --props="${propsFile}"`;
  
  try {
    runCommand(renderCmd);
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
          break;
        } catch (e) {
          const sleep = (ms) => { const end = Date.now() + ms; while (Date.now() < end) {} };
          sleep(1500);
        }
      }
    } else {
      throw err;
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
