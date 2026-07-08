import { useState } from 'react';
import JourneyScene from './components/JourneyScene.jsx';
import BreathingGuide from './components/BreathingGuide.jsx';
import ProgressReadout from './components/ProgressReadout.jsx';
import Controls from './components/Controls.jsx';
import ArrivalBanner from './components/ArrivalBanner.jsx';
import { useBreathingCycle } from './hooks/useBreathingCycle.js';
import { useReducedMotion } from './hooks/useReducedMotion.js';
import { PACE_PRESETS, TARGET_CYCLES } from './constants/breathingPaces.js';
import './App.css';

export default function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [paceId, setPaceId] = useState(PACE_PRESETS[0].id);
  const pace = PACE_PRESETS.find((preset) => preset.id === paceId);
  const reducedMotion = useReducedMotion();
  const { phase, cycleCount, reset } = useBreathingCycle(pace, isRunning);

  const progress = Math.min(cycleCount / TARGET_CYCLES, 1);
  const arrived = progress >= 1;

  function handleToggleRunning() {
    setIsRunning((running) => !running);
  }

  function handleReset() {
    reset();
  }

  return (
    <div className="app">
      <h1>Voyage to Andromeda</h1>
      <p className="app__subtitle">
        A guided breath moves your ship across 2.5 million light-years. Breathe with the thrusters.
      </p>

      <JourneyScene
        isRunning={isRunning}
        reducedMotion={reducedMotion}
        phaseName={isRunning ? phase.name : 'hold2'}
        phaseDuration={phase.duration}
        progress={progress}
        arrived={arrived}
      />

      <BreathingGuide phase={phase} isRunning={isRunning} />
      <ProgressReadout progress={progress} />
      {arrived && <ArrivalBanner />}

      <Controls
        isRunning={isRunning}
        onToggleRunning={handleToggleRunning}
        paceId={paceId}
        onPaceChange={setPaceId}
        onReset={handleReset}
      />
    </div>
  );
}
