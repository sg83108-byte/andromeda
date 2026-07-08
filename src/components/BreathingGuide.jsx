import './BreathingGuide.css';

export default function BreathingGuide({ phase, isRunning }) {
  const phaseName = phase.name;
  const label = isRunning ? phase.text : 'Ready';

  return (
    <div className="breathing-guide">
      <div
        className={`breathing-guide__circle phase-${phaseName}`}
        style={{ '--phase-duration': `${phase.duration}s` }}
        aria-hidden="true"
      />
      <p className="breathing-guide__text" aria-live="polite" aria-atomic="true">
        {label}
      </p>
    </div>
  );
}
