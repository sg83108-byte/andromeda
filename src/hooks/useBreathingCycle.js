import { useEffect, useRef, useState } from 'react';

export function useBreathingCycle(pace, isRunning) {
  const [phaseIndex, setPhaseIndex] = useState(0);
  const [cycleCount, setCycleCount] = useState(0);
  const timerRef = useRef(null);
  const activePhases = pace.phases.filter((p) => p.duration > 0);

  useEffect(() => {
    setPhaseIndex(0);
  }, [pace]);

  useEffect(() => {
    if (!isRunning) {
      clearTimeout(timerRef.current);
      return;
    }

    const currentPhase = activePhases[phaseIndex];
    timerRef.current = setTimeout(() => {
      setPhaseIndex((prevIndex) => {
        const nextIndex = (prevIndex + 1) % activePhases.length;
        if (nextIndex === 0) {
          setCycleCount((count) => count + 1);
        }
        return nextIndex;
      });
    }, currentPhase.duration * 1000);

    return () => clearTimeout(timerRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isRunning, phaseIndex, pace]);

  function reset() {
    clearTimeout(timerRef.current);
    setPhaseIndex(0);
    setCycleCount(0);
  }

  return {
    phase: activePhases[phaseIndex],
    cycleCount,
    reset,
  };
}
