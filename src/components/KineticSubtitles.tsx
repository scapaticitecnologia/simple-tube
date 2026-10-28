import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { WordTimeline } from '../types';

interface Props {
  timeline: WordTimeline[];
}

export const KineticSubtitles: React.FC<Props> = ({ timeline }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTimeSec = frame / fps;

  if (!timeline || timeline.length === 0) {
    return null;
  }

  // Encontrar o índice da palavra atual
  const activeWordIndex = timeline.findIndex(
    (item) => currentTimeSec >= item.start && currentTimeSec <= item.end
  );

  // Se estiver entre palavras, pega a última palavra próxima
  const effectiveIndex =
    activeWordIndex !== -1
      ? activeWordIndex
      : timeline.findIndex((item) => item.start > currentTimeSec) - 1;

  if (effectiveIndex < 0 || effectiveIndex >= timeline.length) {
    return null;
  }

  // Agrupar palavras em blocos de 3 a 5 palavras para não poluir a tela
  const CHUNK_SIZE = 4;
  const chunkStart = Math.floor(effectiveIndex / CHUNK_SIZE) * CHUNK_SIZE;
  const currentChunk = timeline.slice(chunkStart, chunkStart + CHUNK_SIZE);

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '12%',
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '0 40px',
        zIndex: 50,
      }}
    >
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          gap: '14px',
          backgroundColor: 'rgba(5, 8, 15, 0.75)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(0, 242, 254, 0.25)',
          borderRadius: '16px',
          padding: '16px 28px',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.6), 0 0 20px rgba(0, 242, 254, 0.1)',
        }}
      >
        {currentChunk.map((item, idx) => {
          const isCurrent = chunkStart + idx === effectiveIndex;
          const scale = isCurrent ? 1.15 : 1.0;
          const color = isCurrent ? '#00f2fe' : '#f8fafc';
          const textShadow = isCurrent ? '0 0 15px rgba(0, 242, 254, 0.8)' : 'none';

          return (
            <span
              key={`${item.word}-${idx}`}
              style={{
                fontSize: '38px',
                fontWeight: 800,
                letterSpacing: '1px',
                textTransform: 'uppercase',
                fontFamily: 'system-ui, -apple-system, sans-serif',
                color,
                textShadow,
                transform: `scale(${scale})`,
                transition: 'transform 0.05s ease-out, color 0.05s ease-out',
                display: 'inline-block',
              }}
            >
              {item.word}
            </span>
          );
        })}
      </div>
    </div>
  );
};
