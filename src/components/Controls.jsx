import { PACE_PRESETS } from '../constants/breathingPaces.js';
import './Controls.css';

export default function Controls({ isRunning, onToggleRunning, paceId, onPaceChange, onReset }) {
  return (
    <div className="controls">
      <button
        type="button"
        className="controls__button controls__button--primary"
        onClick={onToggleRunning}
        aria-pressed={isRunning}
      >
        {isRunning ? 'Pause' : 'Begin'}
      </button>

      <div className="controls__field">
        <label htmlFor="pace-select">Breathing pace</label>
        <select
          id="pace-select"
          value={paceId}
          disabled={isRunning}
          onChange={(event) => onPaceChange(event.target.value)}
        >
          {PACE_PRESETS.map((preset) => (
            <option key={preset.id} value={preset.id}>
              {preset.label}
            </option>
          ))}
        </select>
      </div>

      <button type="button" className="controls__button" onClick={onReset}>
        Restart Journey
      </button>
    </div>
  );
}
