import React from 'react';
import { Composition } from 'remotion';
import { MainVideo } from './MainVideo';
import { ShortsVideo } from './ShortsVideo';
import { ChannelIntro } from './components/ChannelIntro';
import { defaultScript, defaultSubtitles } from './defaultData';
import { MainVideoProps } from './types';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Vinheta Oficial do Canal Scapatici Tecnologia (3 segundos @ 30fps) */}
      <Composition
        id="Scapatici-Vinheta-16x9"
        component={ChannelIntro}
        durationInFrames={90}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          tagline: 'CIÊNCIA • COSMOS • TECNOLOGIA',
        }}
      />

      {/* Formato Clássico YouTube (16:9 - 1920x1080) */}
      <Composition<any, any>
        id="SimpleTubeVideo-16x9"
        component={MainVideo}
        durationInFrames={1350}
        fps={30}
        width={1920}
        height={1080}
        calculateMetadata={async (args: any) => {
          const props = args.props as MainVideoProps;
          const fps = props.script?.fps || 30;
          const audioSec = props.subtitles?.total_duration_sec;
          const totalFrames = audioSec
            ? Math.ceil((audioSec + 1.5) * fps)
            : props.script?.scenes?.reduce(
                (acc: number, s: any) => acc + (s.durationInFrames || 300),
                0
              ) || 300;

          return {
            durationInFrames: Math.max(totalFrames, 300),
          };
        }}
        defaultProps={{
          script: defaultScript,
          subtitles: defaultSubtitles,
        }}
      />

      {/* Formato YouTube Shorts / TikTok (9:16 - 1080x1920) */}
      <Composition<any, any>
        id="SimpleTubeVideo-Shorts"
        component={ShortsVideo}
        durationInFrames={2100}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={async (args: any) => {
          const props = args.props as MainVideoProps;
          const fps = props.script?.fps || 30;
          const introSec =
            props.subtitles?.intro_duration_sec ||
            (props.subtitles?.total_duration_sec
              ? Math.min(props.subtitles.total_duration_sec, 65)
              : 60);
          const totalFrames = Math.ceil((introSec + 3.5) * fps);

          return {
            durationInFrames: Math.max(totalFrames, 300),
          };
        }}
        defaultProps={{
          script: defaultScript,
          subtitles: defaultSubtitles,
        }}
      />
    </>
  );
};
