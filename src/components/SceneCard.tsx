import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { Scene } from '../types';

interface Props {
  scene: Scene;
}

export const SceneCard: React.FC<Props> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Animação suave de entrada deslizando da esquerda para a direita
  const entrance = spring({
    frame,
    fps,
    config: {
      damping: 16,
      stiffness: 100,
    },
  });

  const opacity = interpolate(frame, [0, 12], [0, 1], {
    extrapolateRight: 'clamp',
  });

  const translateX = interpolate(entrance, [0, 1], [-25, 0]);

  // Obter texto do badge por tipo de cena
  const badgeLabel =
    scene.type === 'hook'
      ? 'ANOMALIA CIENTÍFICA'
      : scene.type === 'revelation'
      ? 'DESCOBERTA ASTROFÍSICA'
      : scene.type === 'climax'
      ? 'A TEORIA FINAL'
      : scene.type === 'cta'
      ? 'SCAPATICI TECNOLOGIA'
      : 'INVESTIGAÇÃO DE DADOS';

  return (
    <div
      style={{
        position: 'absolute',
        top: '55px',
        left: '65px',
        maxWidth: '680px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        textAlign: 'left',
        opacity,
        transform: `translateX(${translateX}px)`,
        zIndex: 25,
      }}
    >
      {/* Container Glassmorphism Discreto no Canto Superior Esquerdo */}
      <div
        style={{
          backgroundColor: 'rgba(5, 8, 16, 0.72)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          borderLeft: '4px solid #00f2fe',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          borderRight: '1px solid rgba(255, 255, 255, 0.05)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '0 16px 16px 0',
          padding: '16px 24px',
          boxShadow: '0 12px 35px rgba(0, 0, 0, 0.55), 0 0 20px rgba(0, 242, 254, 0.08)',
        }}
      >
        {/* Badge / Indicador de Capítulo */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '8px',
          }}
        >
          <span
            style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              backgroundColor: '#00f2fe',
              boxShadow: '0 0 8px #00f2fe',
              display: 'inline-block',
            }}
          />
          <span
            style={{
              color: '#00f2fe',
              fontSize: '13px',
              fontWeight: 800,
              letterSpacing: '2px',
              textTransform: 'uppercase',
              fontFamily: 'system-ui, -apple-system, sans-serif',
            }}
          >
            {badgeLabel}
          </span>
        </div>

        {/* Título Principal do Capítulo (Highlight Elegante) */}
        <h2
          style={{
            fontSize: '32px',
            fontWeight: 900,
            color: '#f8fafc',
            lineHeight: 1.18,
            textTransform: 'uppercase',
            letterSpacing: '0px',
            margin: '0 0 6px 0',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            textShadow: '0 2px 10px rgba(0, 0, 0, 0.8)',
          }}
        >
          {scene.headline}
        </h2>

        {/* Subtítulo / Métrica Chave em Linha Discreta */}
        {scene.stats && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginTop: '4px',
            }}
          >
            <span
              style={{
                fontSize: '18px',
                fontWeight: 800,
                color: '#38bdf8',
                letterSpacing: '0.5px',
              }}
            >
              {scene.stats.value}
            </span>
            <span
              style={{
                fontSize: '13px',
                color: '#94a3b8',
                textTransform: 'uppercase',
                letterSpacing: '1px',
                fontWeight: 600,
              }}
            >
              • {scene.stats.label}
            </span>
          </div>
        )}

        {/* Palavras-chave / Tags Sutis */}
        {scene.highlight_words && scene.highlight_words.length > 0 && (
          <div
            style={{
              display: 'flex',
              gap: '8px',
              marginTop: '10px',
            }}
          >
            {scene.highlight_words.slice(0, 3).map((hw, i) => (
              <span
                key={i}
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.06)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  color: '#cbd5e1',
                  padding: '3px 10px',
                  borderRadius: '6px',
                  fontSize: '11px',
                  fontWeight: 600,
                  letterSpacing: '0.5px',
                }}
              >
                #{hw}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
