import React from 'react';
import { Audio, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { MainVideoProps, Scene } from './types';
import { DynamicBackground } from './components/DynamicBackground';
import { KenBurnsImage } from './components/KenBurnsImage';

export const ShortsVideo: React.FC<MainVideoProps> = ({
  script,
  subtitles,
  audioPath,
  audioIntroPath,
  audioShortsPath,
  bgMusicPath,
  bgMusicVolume,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const scenes = script.scenes || [];
  const introScene = scenes[0];

  // Duração do mini-documentário vertical em segundos e frames (~95s a 125s)
  const introSec =
    subtitles?.shorts_duration_sec ||
    subtitles?.intro_duration_sec ||
    subtitles?.total_duration_sec ||
    90;
  const introDurationInFrames = Math.round(introSec * fps);
  const ctaDurationInFrames = Math.max(durationInFrames - introDurationInFrames, Math.round(3.5 * fps));

  // Filtrar palavras das legendas pertencentes ao mini-documentário vertical
  const rawShortsTimeline =
    subtitles?.shorts_timeline && subtitles.shorts_timeline.length > 0
      ? subtitles.shorts_timeline
      : subtitles?.timeline || [];
  const introTimeline = rawShortsTimeline.filter(
    (item) => item.start <= introSec + 0.5
  );

  const currentTimeSec = frame / fps;

  // Encontrar palavra ativa no timeline
  const activeWordIndex = introTimeline.findIndex(
    (item) => currentTimeSec >= item.start && currentTimeSec <= item.end
  );

  const effectiveIndex =
    activeWordIndex !== -1
      ? activeWordIndex
      : introTimeline.findIndex((item) => item.start > currentTimeSec) - 1;

  // Agrupar em pequenos blocos de 2 a 3 palavras para leitura relâmpago no mobile
  const CHUNK_SIZE = 3;
  const chunkStart = Math.max(0, Math.floor(effectiveIndex / CHUNK_SIZE) * CHUNK_SIZE);
  const currentChunk = introTimeline.slice(chunkStart, chunkStart + CHUNK_SIZE);

  // Barra de progresso contínua para retenção psicológica (topo da safe zone)
  const progressRatio = Math.min(frame / Math.max(durationInFrames, 1), 1);

  // Dinamismo Visual Cinematográfico Multicena:
  // Alternância visual a cada ~4.5 segundos (ritmo de retenção ouro do TikTok/Reels)
  const sceneCutIntervalFrames = Math.round(4.5 * fps);
  const activeSceneIndex =
    scenes.length > 1
      ? Math.floor(frame / sceneCutIntervalFrames) % scenes.length
      : 0;
  const currentDisplayScene: Scene = scenes[activeSceneIndex] || introScene;

  // Capítulo narrativo progressivo ao longo da duração do vídeo (Ato 1 -> Ato N)
  const chapterIndex =
    scenes.length > 1
      ? Math.min(
          Math.floor((frame / Math.max(introDurationInFrames, 1)) * scenes.length),
          scenes.length - 1
        )
      : 0;
  const currentChapterScene: Scene = scenes[chapterIndex] || introScene;
  const isExclusiveTikTok = Boolean(script.id && script.id.startsWith('tiktok-'));

  // Animação de entrada do cabeçalho superior (permanece ativo guiando os capítulos)
  const headerOpacity = interpolate(
    frame,
    [0, 15, Math.max(introDurationInFrames - 15, 30), Math.max(introDurationInFrames, 45)],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );
  const headerTranslateY = interpolate(
    frame,
    [0, 15],
    [-20, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Transição de flash cósmico sutil a cada troca de cena
  const frameInCurrentCut = frame % sceneCutIntervalFrames;
  const cutFlashOpacity = interpolate(
    frameInCurrentCut,
    [0, 3, 10],
    [0.35, 0.45, 0],
    { extrapolateRight: 'clamp' }
  );

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        backgroundColor: '#04060a',
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
      }}
    >
      {/* 🌌 Fundo Dinâmico Base */}
      <DynamicBackground />

      {/* ============================================================== */}
      {/* 🎯 1. BLOCO DO HOOK / INTRODUÇÃO VERTICAL (9:16)               */}
      {/* ============================================================== */}
      {introScene && (
        <Sequence from={0} durationInFrames={introDurationInFrames}>
          {/* Mídia Visual com Enquadramento Inteligente Ambient Canvas (SEM CORTES) */}
          {(currentDisplayScene.backgroundImage || currentDisplayScene.backgroundVideo) && (
            <KenBurnsImage
              imageSrc={currentDisplayScene.backgroundImage}
              videoSrc={currentDisplayScene.backgroundVideo}
              panDirection={
                activeSceneIndex % 2 === 0 ? 'zoom-in' : 'pan-right'
              }
              isClimax={currentDisplayScene.type === 'climax'}
            />
          )}

          {/* Flash Cinematográfico de Transição Cósmica entre Cenas */}
          {cutFlashOpacity > 0 && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                backgroundColor: '#00f2fe',
                opacity: cutFlashOpacity,
                mixBlendMode: 'screen',
                zIndex: 8,
                pointerEvents: 'none',
              }}
            />
          )}

          {/* Gradientes de Safe Zone para Legibilidade Extrema */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '320px',
              background: 'linear-gradient(to bottom, rgba(4,6,12,0.96) 0%, rgba(4,6,12,0.7) 60%, transparent 100%)',
              zIndex: 10,
              pointerEvents: 'none',
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: '650px',
              background: 'linear-gradient(to top, rgba(4,6,12,0.98) 0%, rgba(4,6,12,0.85) 50%, transparent 100%)',
              zIndex: 10,
              pointerEvents: 'none',
            }}
          />

          {/* ⚡ Barra de Progresso Laser no Topo (Estimula conclusão do vídeo) */}
          <div
            style={{
              position: 'absolute',
              top: '95px',
              left: '60px',
              right: '60px',
              height: '5px',
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
              borderRadius: '4px',
              overflow: 'hidden',
              zIndex: 35,
            }}
          >
            <div
              style={{
                width: `${progressRatio * 100}%`,
                height: '100%',
                backgroundColor: '#00f2fe',
                boxShadow: '0 0 12px #00f2fe',
                transition: 'width 0.1s linear',
              }}
            />
          </div>

          {/* Header Superior - Perfeitamente alinhado com a Safe Zone do Instagram/YouTube */}
          <div
            style={{
              position: 'absolute',
              top: '125px',
              left: '60px',
              right: '100px', // Margem extra na direita para não colidir com botões de redes
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-start',
              textAlign: 'left',
              zIndex: 30,
              opacity: headerOpacity,
              transform: `translateY(${headerTranslateY}px)`,
              pointerEvents: 'none',
              transition: 'opacity 0.2s ease',
            }}
          >
            {/* Badge de Destaque Oficial */}
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '10px',
                padding: '8px 20px',
                borderRadius: '30px',
                backgroundColor: 'rgba(0, 242, 254, 0.16)',
                border: '1.5px solid rgba(0, 242, 254, 0.6)',
                color: '#00f2fe',
                fontSize: '18px',
                fontWeight: 900,
                letterSpacing: '2.5px',
                textTransform: 'uppercase',
                marginBottom: '14px',
                boxShadow: '0 0 20px rgba(0, 242, 254, 0.35)',
              }}
            >
              <span>⚛️</span> SCAPATICI TECNOLOGIA{scenes.length > 1 ? ` • ATO ${chapterIndex + 1}/${scenes.length}` : ''}
            </div>

            {/* Headline com Tipografia Pesada e Contraste Máximo */}
            <h1
              style={{
                color: '#ffffff',
                fontSize: '36px',
                fontWeight: 900,
                lineHeight: 1.2,
                margin: 0,
                textShadow: '0 3px 18px rgba(0,0,0,0.95), 0 0 25px rgba(0,242,254,0.35)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                maxWidth: '850px',
              }}
            >
              {currentChapterScene.headline || introScene.headline}
            </h1>

            {/* HUD de Dado Científico do Capítulo (quando disponível) */}
            {currentChapterScene.stats && (
              <div
                style={{
                  marginTop: '14px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '8px 18px',
                  borderRadius: '14px',
                  backgroundColor: 'rgba(5, 10, 22, 0.85)',
                  border: '1.5px solid rgba(255, 210, 0, 0.65)',
                  boxShadow: '0 6px 20px rgba(0,0,0,0.75)',
                }}
              >
                <span
                  style={{
                    color: '#cbd5e1',
                    fontSize: '16px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                  }}
                >
                  📊 {currentChapterScene.stats.label}:
                </span>
                <span
                  style={{
                    color: '#ffd200',
                    fontSize: '18px',
                    fontWeight: 900,
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                  }}
                >
                  {currentChapterScene.stats.value}
                </span>
              </div>
            )}
          </div>

          {/* Legendas Cinéticas Verticais - Na Safe Zone Ideal (Acima da UI das redes sociais) */}
          {currentChunk.length > 0 && (
            <div
              style={{
                position: 'absolute',
                top: '1220px', // Posição calculada segura contra sobreposição de UI
                left: '60px',
                right: '110px', // Evita o botão curtir/comentar do Reels na direita
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                zIndex: 40,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  justifyContent: 'center',
                  gap: '14px',
                  padding: '16px 26px',
                  backgroundColor: 'rgba(5, 8, 16, 0.88)',
                  backdropFilter: 'blur(16px)',
                  borderRadius: '24px',
                  border: '1.5px solid rgba(0, 242, 254, 0.4)',
                  boxShadow: '0 12px 35px rgba(0, 0, 0, 0.85), 0 0 30px rgba(0, 242, 254, 0.25)',
                }}
              >
                {currentChunk.map((wordItem, idx) => {
                  const isActive =
                    currentTimeSec >= wordItem.start && currentTimeSec <= wordItem.end;
                  const activeHighlights = [
                    ...(currentChapterScene.highlight_words || []),
                    ...(introScene.highlight_words || []),
                  ];
                  const isHighlighted = activeHighlights.some((h) =>
                    wordItem.word.toLowerCase().includes(h.toLowerCase())
                  );

                  return (
                    <span
                      key={`${wordItem.word}_${idx}_${wordItem.start}`}
                      style={{
                        fontSize: isActive ? '46px' : '40px',
                        fontWeight: 900,
                        color: isActive
                          ? '#00f2fe'
                          : isHighlighted
                          ? '#ffd200'
                          : '#ffffff',
                        textTransform: 'uppercase',
                        letterSpacing: '1px',
                        textShadow: isActive
                          ? '0 0 25px #00f2fe, 0 0 45px rgba(0,242,254,0.9)'
                          : isHighlighted
                          ? '0 0 25px #ffd200'
                          : '0 2px 10px rgba(0,0,0,0.9)',
                        transform: isActive ? 'scale(1.15)' : 'scale(1)',
                        transition: 'transform 0.08s ease, color 0.08s ease',
                      }}
                    >
                      {wordItem.word}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {/* Áudio do Mini-Documentário Vertical */}
          {(audioShortsPath || audioIntroPath || audioPath) && (
            <Audio src={staticFile(audioShortsPath || audioIntroPath || audioPath || '')} />
          )}
        </Sequence>
      )}

      {/* ============================================================== */}
      {/* ⚡ 2. BLOCO CTA FINAL (CHAMADA HIPNÓTICA PARA O VÍDEO COMPLETO) */}
      {/* ============================================================== */}
      <Sequence from={introDurationInFrames} durationInFrames={ctaDurationInFrames}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: '#05070d',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '50px 60px',
            textAlign: 'center',
            zIndex: 60,
          }}
        >
          {/* Card Central Glassmorphism com Brilho Pulsante */}
          <div
            style={{
              padding: '50px 35px',
              borderRadius: '32px',
              backgroundColor: 'rgba(8, 12, 24, 0.94)',
              border: '2px solid rgba(0, 242, 254, 0.85)',
              boxShadow: '0 0 60px rgba(0, 242, 254, 0.45), inset 0 0 30px rgba(0, 242, 254, 0.25)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
              maxWidth: '850px',
            }}
          >
            <div
              style={{
                fontSize: '70px',
                marginBottom: '15px',
                filter: 'drop-shadow(0 0 20px #00f2fe)',
              }}
            >
              🛸
            </div>

            <div
              style={{
                fontSize: '26px',
                fontWeight: 900,
                color: '#ffd200',
                letterSpacing: '4px',
                textTransform: 'uppercase',
                marginBottom: '12px',
                textShadow: '0 0 25px rgba(255, 210, 0, 0.6)',
              }}
            >
              {isExclusiveTikTok ? 'CIÊNCIA PROFUNDA TODOS OS DIAS' : 'INVESTIGAÇÃO COMPLETA'}
            </div>

            <h2
              style={{
                fontSize: '42px',
                fontWeight: 900,
                color: '#ffffff',
                lineHeight: 1.25,
                margin: '0 0 26px 0',
                textTransform: 'uppercase',
                textShadow: '0 0 30px rgba(0, 242, 254, 0.6)',
              }}
            >
              {isExclusiveTikTok
                ? 'SIGA O PERFIL E INSCREVA-SE NO YOUTUBE'
                : 'ASSISTA AO DOCUMENTÁRIO COMPLETO'}
            </h2>

            <div
              style={{
                padding: '16px 36px',
                borderRadius: '50px',
                backgroundColor: '#00f2fe',
                color: '#04060a',
                fontSize: '24px',
                fontWeight: 900,
                letterSpacing: '2px',
                textTransform: 'uppercase',
                marginBottom: '26px',
                boxShadow: '0 0 40px rgba(0, 242, 254, 0.8)',
              }}
            >
              SCAPATICI TECNOLOGIA
            </div>

            <p
              style={{
                fontSize: '24px',
                fontWeight: 700,
                color: '#cbd5e1',
                margin: '0 0 22px 0',
                lineHeight: 1.4,
              }}
            >
              {isExclusiveTikTok
                ? '🔔 Novos episódios diários às 09h, 16h e 20h!'
                : '🔗 Link completo fixado no primeiro comentário!'}
            </p>

            {/* Barra Visual de Conversão para Atrair Seguidores e Engajamento */}
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '16px',
                padding: '10px 24px',
                borderRadius: '16px',
                backgroundColor: 'rgba(255, 210, 0, 0.12)',
                border: '1px solid rgba(255, 210, 0, 0.5)',
                color: '#ffd200',
                fontSize: '18px',
                fontWeight: 900,
                letterSpacing: '1.5px',
                textTransform: 'uppercase',
              }}
            >
              👍 CURTA • 💬 COMENTE • 🔔 SIGA O PERFIL
            </div>
          </div>
        </div>
      </Sequence>

      {/* ============================================================== */}
      {/* 🎵 Trilha Sonora de Mistério e Suspense (Sempre Presente)      */}
      {/* ============================================================== */}
      {bgMusicPath && (
        <Audio
          src={staticFile(bgMusicPath)}
          volume={bgMusicVolume ? bgMusicVolume * 1.15 : 0.14}
          loop
        />
      )}
    </div>
  );
};
