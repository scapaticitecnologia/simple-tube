import React, { useMemo } from 'react';
import { Img, interpolate, staticFile, useCurrentFrame, useVideoConfig, Video } from 'remotion';
import { PanDirection } from '../types';

interface Props {
  imageSrc?: string;
  videoSrc?: string;
  panDirection?: PanDirection;
  isClimax?: boolean;
  forceFit?: 'cover' | 'contain' | 'cinematic_ambient';
}

export const KenBurnsImage: React.FC<Props> = ({
  imageSrc,
  videoSrc,
  panDirection = 'zoom-in',
  isClimax = false,
  forceFit,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();

  // Detecção de formato vertical (Shorts / Reels: 9:16)
  const isVertical = width < height;

  // Identificar mídia principal (se videoSrc foi passado ou se imageSrc for extensão de vídeo)
  const rawSrc = videoSrc || imageSrc;
  if (!rawSrc) return null;

  const isVideo =
    Boolean(videoSrc) ||
    /\.(mp4|webm|mov|m4v)$/i.test(rawSrc);

  const resolvedSrc =
    rawSrc.startsWith('http') || rawSrc.startsWith('/')
      ? rawSrc
      : staticFile(rawSrc);

  // Partículas flutuantes procedurais geradas de forma determinística
  const particles = useMemo(() => {
    return Array.from({ length: 32 }).map((_, i) => ({
      x: (i * 37) % 100,
      y: (i * 43) % 100,
      size: 2 + (i % 4) * 2.5,
      speed: 0.15 + (i % 5) * 0.12,
      delay: (i * 12) % 60,
      opacity: 0.2 + (i % 4) * 0.18,
    }));
  }, []);

  // 1. Cálculos de Transformação Dinâmica de Câmera (Direção Cinematográfica)
  let scale = 1.0;
  let translateX = 0;
  let translateY = 0;
  let rotate = 0;

  switch (panDirection) {
    case 'zoom-in':
      scale = interpolate(frame, [0, durationInFrames], [1.02, 1.24], {
        extrapolateRight: 'clamp',
      });
      translateY = interpolate(frame, [0, durationInFrames], [0, -25], {
        extrapolateRight: 'clamp',
      });
      break;

    case 'zoom-out':
      scale = interpolate(frame, [0, durationInFrames], [1.25, 1.03], {
        extrapolateRight: 'clamp',
      });
      translateY = interpolate(frame, [0, durationInFrames], [-25, 0], {
        extrapolateRight: 'clamp',
      });
      break;

    case 'pan-left':
      scale = interpolate(frame, [0, durationInFrames], [1.14, 1.22], {
        extrapolateRight: 'clamp',
      });
      translateX = interpolate(frame, [0, durationInFrames], [50, -50], {
        extrapolateRight: 'clamp',
      });
      break;

    case 'pan-right':
      scale = interpolate(frame, [0, durationInFrames], [1.14, 1.22], {
        extrapolateRight: 'clamp',
      });
      translateX = interpolate(frame, [0, durationInFrames], [-50, 50], {
        extrapolateRight: 'clamp',
      });
      break;

    case 'dramatic-pulse':
      scale = interpolate(
        Math.sin((frame / Math.max(durationInFrames, 1)) * Math.PI * 2),
        [-1, 1],
        [1.06, 1.28]
      );
      translateY = interpolate(frame, [0, durationInFrames], [0, -30], {
        extrapolateRight: 'clamp',
      });
      break;

    case 'hyper-zoom':
      // Aceleração cinematográfica dramática para revelações e ameaças cósmicas
      scale = interpolate(frame, [0, durationInFrames], [1.0, 1.38], {
        extrapolateRight: 'clamp',
        easing: (t) => t * t * (3 - 2 * t),
      });
      translateY = interpolate(frame, [0, durationInFrames], [10, -35], {
        extrapolateRight: 'clamp',
      });
      break;

    case 'tilt-down':
      scale = interpolate(frame, [0, durationInFrames], [1.05, 1.20], {
        extrapolateRight: 'clamp',
      });
      translateY = interpolate(frame, [0, durationInFrames], [-40, 20], {
        extrapolateRight: 'clamp',
      });
      break;

    case 'floating-drift':
    default:
      // Movimento contínuo e orgânico de câmera flutuante (gravidade zero)
      scale = 1.1 + Math.sin(frame / 45) * 0.05;
      translateX = Math.sin(frame / 60) * 22;
      translateY = Math.cos(frame / 50) * 18;
      rotate = Math.sin(frame / 85) * 0.6;
      break;
  }

  // Micro-tremor de tensão para momentos de clímax e perigo
  if (isClimax) {
    const jitterX = Math.sin(frame * 2.2) * 2.0;
    const jitterY = Math.cos(frame * 1.8) * 1.6;
    translateX += jitterX;
    translateY += jitterY;
  }

  // Anamorphic Light Flare varrendo sutilmente da esquerda para a direita
  const flarePositionX = interpolate(
    frame,
    [0, durationInFrames],
    [-20, 120],
    { extrapolateRight: 'clamp' }
  );

  // Renderizar o elemento visual (Vídeo ou Imagem)
  const renderVisualElement = (isBackgroundBlur = false) => {
    const style: React.CSSProperties = isBackgroundBlur
      ? {
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          filter: 'blur(35px) brightness(0.42) saturate(1.4)',
          transform: 'scale(1.25)',
        }
      : {
          width: '100%',
          height: '100%',
          objectFit: isVertical ? 'contain' : 'cover',
          transform: `scale(${scale}) translate(${translateX}px, ${translateY}px) rotate(${rotate}deg)`,
          filter: isClimax
            ? 'brightness(0.72) contrast(1.25) saturate(1.15)'
            : 'brightness(0.70) contrast(1.18)',
          willChange: 'transform',
        };

    if (isVideo) {
      return (
        <Video
          src={resolvedSrc}
          loop
          muted
          style={style}
        />
      );
    }

    return (
      <Img
        src={resolvedSrc}
        style={style}
      />
    );
  };

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        zIndex: 1,
        backgroundColor: '#04060a',
      }}
    >
      {/* SE FOR SHORTS / VERTICAL: TÉCNICA AMBIENT CANVAS (NENHUMA IMAGEM É CORTADA) */}
      {isVertical ? (
        <>
          {/* 1. Camada de Fundo com Blur Imersivo cobrindo os 1080x1920 */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              overflow: 'hidden',
              zIndex: 1,
            }}
          >
            {renderVisualElement(true)}
          </div>

          {/* 2. Janela Central Hero (Aspect Ratio Preservado com Borda Tecnológica e Sombra 3D) */}
          <div
            style={{
              position: 'absolute',
              top: '200px',
              bottom: '500px',
              left: '30px',
              right: '30px',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              zIndex: 3,
            }}
          >
            <div
              style={{
                position: 'relative',
                width: '100%',
                maxHeight: '100%',
                aspectRatio: '16 / 9',
                borderRadius: '24px',
                overflow: 'hidden',
                border: '1.5px solid rgba(0, 242, 254, 0.45)',
                boxShadow: '0 25px 65px rgba(0, 0, 0, 0.85), 0 0 35px rgba(0, 242, 254, 0.25)',
                backgroundColor: '#050811',
              }}
            >
              {renderVisualElement(false)}

              {/* Vinheta interna suave na janela */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  background: 'radial-gradient(circle at center, transparent 55%, rgba(4, 6, 12, 0.6) 100%)',
                  pointerEvents: 'none',
                }}
              />
            </div>
          </div>
        </>
      ) : (
        /* FORMATO 16:9 PADRÃO YOUTUBE: TELA CHEIA CINEMATOGRÁFICA */
        renderVisualElement(false)
      )}

      {/* Camada de Partículas Cósmicas / Poeira em Paralaxe */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          zIndex: 4,
        }}
      >
        {particles.map((p, idx) => {
          const currentY = (p.y - frame * p.speed) % 100;
          const currentX = (p.x + Math.sin((frame + p.delay) / 30) * 4) % 100;
          const pulseOpacity = p.opacity + Math.sin((frame + p.delay) / 15) * 0.15;

          return (
            <div
              key={idx}
              style={{
                position: 'absolute',
                top: `${(currentY + 100) % 100}%`,
                left: `${(currentX + 100) % 100}%`,
                width: `${p.size}px`,
                height: `${p.size}px`,
                borderRadius: '50%',
                backgroundColor: idx % 3 === 0 ? '#00f2fe' : '#ffffff',
                boxShadow: `0 0 ${p.size * 3}px ${idx % 3 === 0 ? '#00f2fe' : '#ffffff'}`,
                opacity: Math.max(0.1, pulseOpacity),
              }}
            />
          );
        })}
      </div>

      {/* Feixe de Luz Anamórfico Cinematográfico */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          bottom: 0,
          left: `${flarePositionX}%`,
          width: isVertical ? '150px' : '260px',
          background: 'linear-gradient(90deg, transparent 0%, rgba(0, 242, 254, 0.08) 50%, transparent 100%)',
          transform: 'skewX(-25deg)',
          pointerEvents: 'none',
          zIndex: 5,
          filter: 'blur(12px)',
        }}
      />

      {/* Gradiente Atmosférico de Profundidade */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: isVertical
            ? `
              linear-gradient(to bottom, rgba(4, 6, 12, 0.92) 0%, rgba(4, 6, 12, 0.4) 18%, transparent 35%),
              linear-gradient(to top, rgba(4, 6, 12, 0.95) 0%, rgba(4, 6, 12, 0.6) 28%, transparent 45%)
            `
            : `
              radial-gradient(circle at center, rgba(5, 8, 16, 0.3) 0%, rgba(4, 6, 12, 0.92) 100%),
              linear-gradient(to top, rgba(4, 6, 12, 0.96) 0%, transparent 35%),
              linear-gradient(to bottom, rgba(4, 6, 12, 0.85) 0%, transparent 28%)
            `,
          pointerEvents: 'none',
          zIndex: 6,
        }}
      />
    </div>
  );
};
