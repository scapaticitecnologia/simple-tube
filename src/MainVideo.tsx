import React from 'react';
import { Audio, Sequence, staticFile, useVideoConfig } from 'remotion';
import { MainVideoProps, Scene } from './types';
import { DynamicBackground } from './components/DynamicBackground';
import { KineticSubtitles } from './components/KineticSubtitles';
import { SceneCard } from './components/SceneCard';
import { KenBurnsImage } from './components/KenBurnsImage';
import { ChannelIntro } from './components/ChannelIntro';

export const MainVideo: React.FC<MainVideoProps> = ({
  script,
  subtitles,
  audioPath,
  audioIntroPath,
  audioRestPath,
  bgMusicPath,
  bgMusicVolume,
}) => {
  const { fps, durationInFrames } = useVideoConfig();

  // Duração da vinheta oficial em frames (padrão: 3 segundos = 90 frames a 30fps)
  const vinhetaDurationInFrames = script.vinheta_duration_frames ?? Math.round(3.0 * fps);

  // Identificar cenas da Introdução e Restante
  const scenes = script.scenes || [];
  const introScene: Scene | undefined = scenes[0];
  const restScenes: Scene[] = scenes.slice(1);

  // Calcular frames da Introdução
  // Se vier especificado em durationInFrames ou subtitles.intro_duration_sec, usa com precisão
  const introDurationInFrames = introScene?.durationInFrames
    ? introScene.durationInFrames
    : subtitles?.intro_duration_sec
    ? Math.round(subtitles.intro_duration_sec * fps)
    : Math.floor((durationInFrames - vinhetaDurationInFrames) / Math.max(scenes.length, 1));

  // Restante dos frames do vídeo para distribuir entre as cenas restantes
  const restStartFrame = introDurationInFrames + vinhetaDurationInFrames;
  const remainingTotalFrames = Math.max(durationInFrames - restStartFrame, 300);
  const defaultRestSceneFrames = Math.floor(remainingTotalFrames / Math.max(restScenes.length, 1));

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        backgroundColor: '#04060a',
      }}
    >
      {/* 🌌 Fundo Dinâmico Procedural Base */}
      <DynamicBackground />

      {/* ============================================================== */}
      {/* 🎯 1. BLOCO INTRODUÇÃO (HOOK DE ALTA RETENÇÃO)                 */}
      {/* ============================================================== */}
      {introScene && (
        <Sequence
          key="intro_block"
          from={0}
          durationInFrames={introDurationInFrames}
        >
          {(introScene.backgroundImage || introScene.backgroundVideo) && (
            <KenBurnsImage
              imageSrc={introScene.backgroundImage}
              videoSrc={introScene.backgroundVideo}
              panDirection={introScene.panDirection || 'zoom-in'}
              isClimax={introScene.type === 'climax'}
            />
          )}
          <SceneCard scene={introScene} />

          {/* Áudio específico da Introdução se disponível */}
          {audioIntroPath && <Audio src={staticFile(audioIntroPath)} />}
        </Sequence>
      )}

      {/* ============================================================== */}
      {/* ⚡ 2. BLOCO VINHETA OFICIAL DO CANAL (3 SEGUNDOS)               */}
      {/* ============================================================== */}
      <Sequence
        key="vinheta_block"
        from={introDurationInFrames}
        durationInFrames={vinhetaDurationInFrames}
      >
        <ChannelIntro tagline="CIÊNCIA • COSMOS • TECNOLOGIA" />
      </Sequence>

      {/* ============================================================== */}
      {/* 🚀 3. BLOCO RESTANTE DO VÍDEO (CENAS 2 EM DIANTE)              */}
      {/* ============================================================== */}
      {restScenes.map((scene, index) => {
        // Cálculo do frame inicial acumulado para o restante das cenas
        const fromFrame = restStartFrame + (
          scene.durationInFrames
            ? restScenes
                .slice(0, index)
                .reduce((acc, s) => acc + (s.durationInFrames || defaultRestSceneFrames), 0)
            : index * defaultRestSceneFrames
        );

        const duration = scene.durationInFrames || defaultRestSceneFrames;

        return (
          <Sequence
            key={scene.id || `rest_${index}`}
            from={fromFrame}
            durationInFrames={duration}
          >
            {(scene.backgroundImage || scene.backgroundVideo) && (
              <KenBurnsImage
                imageSrc={scene.backgroundImage}
                videoSrc={scene.backgroundVideo}
                panDirection={
                  scene.panDirection ||
                  (scene.type === 'climax'
                    ? 'dramatic-pulse'
                    : index % 2 === 0
                    ? 'pan-left'
                    : 'pan-right')
                }
                isClimax={scene.type === 'climax'}
              />
            )}
            <SceneCard scene={scene} />
          </Sequence>
        );
      })}

      {/* Áudio do restante do vídeo iniciado após a vinheta */}
      {audioRestPath && (
        <Sequence from={restStartFrame}>
          <Audio src={staticFile(audioRestPath)} />
        </Sequence>
      )}

      {/* Fallback de áudio único contínuo para compatibilidade com vídeos anteriores */}
      {!audioIntroPath && !audioRestPath && audioPath && (
        <Audio src={staticFile(audioPath)} />
      )}

      {/* ============================================================== */}
      {/* 💬 LEGENDAS CINÉTICAS SINCRONIZADAS                             */}
      {/* ============================================================== */}
      {subtitles && subtitles.timeline && (
        <KineticSubtitles timeline={subtitles.timeline} />
      )}

      {/* ============================================================== */}
      {/* 🎵 TRILHA SONORA AMBIENTE DE FUNDO (SCI-FI DARK AMBIENT)       */}
      {/* ============================================================== */}
      {bgMusicPath && (
        <Audio
          src={staticFile(bgMusicPath)}
          volume={bgMusicVolume ?? 0.12}
          loop
        />
      )}
    </div>
  );
};

