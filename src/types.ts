export interface WordTimeline {
  word: string;
  start: number; // segundos
  end: number;   // segundos
  duration: number;
}

export interface SubtitlesData {
  voice: string;
  rate: string;
  pitch: string;
  total_words: number;
  total_duration_sec?: number;
  timeline: WordTimeline[];
  intro_duration_sec?: number;
  vinheta_duration_sec?: number;
  rest_duration_sec?: number;
}

export type PanDirection =
  | 'zoom-in'
  | 'zoom-out'
  | 'pan-left'
  | 'pan-right'
  | 'floating-drift'
  | 'dramatic-pulse'
  | 'hyper-zoom'
  | 'tilt-down';

export interface Scene {
  id: string;
  type: 'hook' | 'investigation' | 'revelation' | 'climax' | 'cta';
  visual_theme: string;
  narration: string;
  headline: string;
  subheadline?: string;
  highlight_words?: string[];
  stats?: { label: string; value: string };
  durationInFrames?: number;
  backgroundImage?: string;
  backgroundVideo?: string;
  panDirection?: PanDirection;
  videoSpeed?: number;
  overlayEffect?: 'particles' | 'scanlines' | 'anamorphic_flare' | 'vignette' | 'none';
}

export interface VideoScript {
  id?: string;
  title: string;
  topic: string;
  target_duration_seconds?: number;
  fps?: number;
  vinheta_duration_frames?: number;
  seo?: {
    tags: string[];
    description: string;
    title_options?: string[];
  };
  scenes: Scene[];
}

export interface MainVideoProps {
  script: VideoScript;
  subtitles?: SubtitlesData;
  audioPath?: string;
  audioIntroPath?: string;
  audioRestPath?: string;
  bgMusicPath?: string;
  bgMusicVolume?: number;
}

