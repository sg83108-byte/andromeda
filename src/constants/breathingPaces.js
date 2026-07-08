export const PACE_PRESETS = [
  {
    id: 'box',
    label: 'Box Breathing (4-4-4-4)',
    phases: [
      { name: 'inhale', duration: 4, text: 'Breathe In' },
      { name: 'hold1', duration: 4, text: 'Hold' },
      { name: 'exhale', duration: 4, text: 'Breathe Out' },
      { name: 'hold2', duration: 4, text: 'Hold' },
    ],
  },
  {
    id: '478',
    label: 'Relaxing Breath (4-7-8)',
    phases: [
      { name: 'inhale', duration: 4, text: 'Breathe In' },
      { name: 'hold1', duration: 7, text: 'Hold' },
      { name: 'exhale', duration: 8, text: 'Breathe Out' },
      { name: 'hold2', duration: 0, text: 'Hold' },
    ],
  },
];

export const TARGET_CYCLES = 18;
