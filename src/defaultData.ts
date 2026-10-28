import { VideoScript, SubtitlesData } from './types';

export const defaultScript: VideoScript = {
  title: 'O Mistério do Sinal WOW!: A Resposta que a Ciência Escondeu por 50 Anos',
  topic: 'Sinal WOW! e o Paradoxo de Fermi',
  target_duration_seconds: 45,
  fps: 30,
  seo: {
    tags: [
      'sinal wow',
      'paradoxo de fermi',
      'vida extraterrestre',
      'curiosidades cientificas',
      'misterios do universo',
    ],
    description:
      'Em 15 de agosto de 1977, um radiotelescópio captou o sinal mais intrigante da história espacial. Seria a prova definitiva de outra civilização? Confira a verdade científica.',
  },
  scenes: [
    {
      id: 'scene_1',
      type: 'hook',
      visual_theme: 'cyber_glitch',
      headline: 'A TRANSMISSÃO DESCONHECIDA',
      narration:
        'Em 15 de agosto de 1977, um radiotelescópio captou uma anomalia que desafia a ciência há quase cinquenta anos.',
      highlight_words: ['1977', 'ANOMALIA', '72 SEGUNDOS'],
      stats: { label: 'Duração do Sinal', value: '72s' },
      durationInFrames: 300,
    },
    {
      id: 'scene_2',
      type: 'investigation',
      visual_theme: 'deep_space',
      headline: 'FREQUÊNCIA PROIBIDA',
      narration:
        'O sinal ocorreu na linha do hidrogênio, a frequência exata que qualquer civilização avançada usaria para se comunicar pelo cosmos.',
      highlight_words: ['1420 MHz', 'HIDROGÊNIO', 'CÓDIGO 6EQUJ5'],
      stats: { label: 'Frequência do Hidrogênio', value: '1420 MHz' },
      durationInFrames: 350,
    },
    {
      id: 'scene_3',
      type: 'revelation',
      visual_theme: 'quantum_glow',
      headline: 'POR QUE ELE NUNCA MAIS SE REPETIU?',
      narration:
        'Centenas de buscas foram feitas na mesma coordenada da constelação de Sagitário. Silêncio absoluto. Até que uma nova hipótese emergiu.',
      highlight_words: ['SAGITÁRIO', 'HIPÓTESE', 'NUVEM DE GÁS'],
      stats: { label: 'Tentativas de Re-detecção', value: '100+' },
      durationInFrames: 350,
    },
    {
      id: 'scene_4',
      type: 'climax',
      visual_theme: 'cyber_alert',
      headline: 'A TEORIA FINAL',
      narration:
        'Estudos de 2024 sugerem um raro laser cósmico natural alimentado por uma estrela de nêutrons. Mas uma dúvida persiste: e se foi apenas um eco?',
      highlight_words: ['LASER CÓSMICO', 'ESTRELA DE NÊUTRONS', 'RESPOSTA'],
      durationInFrames: 350,
    },
  ],
};

export const defaultSubtitles: SubtitlesData = {
  voice: 'pt-BR-AntonioNeural',
  rate: '+5%',
  pitch: '-2Hz',
  total_words: 18,
  timeline: [
    { word: 'Em', start: 0.1, end: 0.3, duration: 0.2 },
    { word: '15', start: 0.3, end: 0.6, duration: 0.3 },
    { word: 'de', start: 0.6, end: 0.8, duration: 0.2 },
    { word: 'agosto', start: 0.8, end: 1.2, duration: 0.4 },
    { word: 'de', start: 1.2, end: 1.3, duration: 0.1 },
    { word: '1977', start: 1.3, end: 1.9, duration: 0.6 },
    { word: 'um', start: 2.0, end: 2.2, duration: 0.2 },
    { word: 'radiotelescópio', start: 2.2, end: 3.1, duration: 0.9 },
    { word: 'captou', start: 3.2, end: 3.6, duration: 0.4 },
    { word: 'uma', start: 3.6, end: 3.8, duration: 0.2 },
    { word: 'anomalia', start: 3.8, end: 4.5, duration: 0.7 },
    { word: 'que', start: 4.6, end: 4.8, duration: 0.2 },
    { word: 'desafia', start: 4.8, end: 5.3, duration: 0.5 },
    { word: 'a', start: 5.3, end: 5.4, duration: 0.1 },
    { word: 'ciência', start: 5.4, end: 5.9, duration: 0.5 },
    { word: 'há', start: 6.0, end: 6.2, duration: 0.2 },
    { word: 'cinquenta', start: 6.2, end: 6.7, duration: 0.5 },
    { word: 'anos.', start: 6.7, end: 7.2, duration: 0.5 },
  ],
};
