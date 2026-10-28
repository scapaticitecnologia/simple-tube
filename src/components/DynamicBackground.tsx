import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

interface Props {
  theme?: string;
}

export const DynamicBackground: React.FC<Props> = ({ theme = 'deep_space' }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Movimento orgânico lento do centro de luz
  const xOffset = interpolate(Math.sin(frame / 60), [-1, 1], [40, 60]);
  const yOffset = interpolate(Math.cos(frame / 75), [-1, 1], [35, 65]);
  const gridShift = (frame * 1.5) % 100;

  return (
    <div
      style={{
        position: 'absolute',
        width: '100%',
        height: '100%',
        backgroundColor: '#07090e',
        overflow: 'hidden',
        zIndex: 0,
      }}
    >
      {/* Nebulosa Quântica / Glow Principal */}
      <div
        style={{
          position: 'absolute',
          width: '140%',
          height: '140%',
          top: '-20%',
          left: '-20%',
          background: `radial-gradient(circle at ${xOffset}% ${yOffset}%, rgba(0, 242, 254, 0.16) 0%, rgba(79, 172, 254, 0.08) 35%, rgba(6, 11, 25, 0) 70%)`,
          filter: 'blur(40px)',
        }}
      />

      {/* Segundo foco de luz (Mistério / Neon Violet) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          background: `radial-gradient(circle at ${100 - xOffset}% ${100 - yOffset}%, rgba(139, 92, 246, 0.12) 0%, transparent 60%)`,
        }}
      />

      {/* Grid Tecnológico Sci-Fi em Perspectiva */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(to right, rgba(0, 242, 254, 0.04) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(0, 242, 254, 0.04) 1px, transparent 1px)
          `,
          backgroundSize: '80px 80px',
          backgroundPosition: `0px ${gridShift}px`,
          opacity: 0.7,
        }}
      />

      {/* Vinheta escura nas bordas para focar a atenção no centro */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(circle at center, transparent 40%, rgba(3, 5, 10, 0.85) 100%)',
          pointerEvents: 'none',
        }}
      />
    </div>
  );
};
