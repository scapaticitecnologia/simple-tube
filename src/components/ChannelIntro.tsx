import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';

interface Props {
  tagline?: string;
}

export const ChannelIntro: React.FC<Props> = ({
  tagline = 'CIÊNCIA • COSMOS • TECNOLOGIA',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Animação de entrada explosiva com spring
  const scale = spring({
    frame,
    fps,
    config: {
      damping: 12,
      stiffness: 120,
      mass: 0.8,
    },
  });

  // Linha de laser varrendo a tela
  const laserWidth = interpolate(frame, [5, 30], [0, 100], {
    extrapolateRight: 'clamp',
  });

  // Revelação de opacidade
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Fade out suave no final dos 3 segundos
  const fadeOut = interpolate(frame, [70, 90], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Pulso de brilho ciano
  const glow = Math.sin(frame / 6) * 15 + 25;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#04060a',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        opacity: opacity * fadeOut,
        zIndex: 100,
        overflow: 'hidden',
      }}
    >
      {/* Grade Quântica de Fundo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            radial-gradient(circle at center, rgba(0, 242, 254, 0.15) 0%, transparent 60%),
            linear-gradient(to right, rgba(0, 242, 254, 0.05) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(0, 242, 254, 0.05) 1px, transparent 1px)
          `,
          backgroundSize: '100% 100%, 60px 60px, 60px 60px',
        }}
      />

      {/* Ícone Tecnológico Central */}
      <div
        style={{
          width: '70px',
          height: '70px',
          borderRadius: '20px',
          border: '2px solid #00f2fe',
          boxShadow: `0 0 ${glow}px #00f2fe, inset 0 0 15px rgba(0, 242, 254, 0.5)`,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          marginBottom: '24px',
          transform: `scale(${scale}) rotate(${frame * 0.8}deg)`,
          backgroundColor: 'rgba(5, 10, 25, 0.8)',
        }}
      >
        <div
          style={{
            width: '28px',
            height: '28px',
            backgroundColor: '#00f2fe',
            borderRadius: '6px',
            boxShadow: '0 0 20px #00f2fe',
          }}
        />
      </div>

      {/* Título Principal Scapatici Tecnologia */}
      <h1
        style={{
          fontSize: '52px',
          fontWeight: 900,
          color: '#ffffff',
          letterSpacing: '6px',
          textTransform: 'uppercase',
          margin: 0,
          fontFamily: 'system-ui, -apple-system, sans-serif',
          textShadow: `0 0 30px rgba(0, 242, 254, 0.6), 0 4px 15px rgba(0,0,0,0.9)`,
          transform: `scale(${scale})`,
        }}
      >
        SCAPATICI <span style={{ color: '#00f2fe' }}>TECNOLOGIA</span>
      </h1>

      {/* Linha de Laser Varredura */}
      <div
        style={{
          width: `${laserWidth}%`,
          maxWidth: '550px',
          height: '2px',
          backgroundColor: '#00f2fe',
          boxShadow: '0 0 12px #00f2fe',
          margin: '18px 0',
        }}
      />

      {/* Tagline / Subtítulo */}
      <p
        style={{
          fontSize: '16px',
          fontWeight: 700,
          color: '#94a3b8',
          letterSpacing: '8px',
          textTransform: 'uppercase',
          margin: 0,
          fontFamily: 'system-ui, -apple-system, sans-serif',
          opacity: interpolate(frame, [15, 35], [0, 1]),
        }}
      >
        {tagline}
      </p>
    </div>
  );
};
