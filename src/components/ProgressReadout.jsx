import './ProgressReadout.css';

const TOTAL_LIGHT_YEARS = 2_500_000;

export default function ProgressReadout({ progress }) {
  const percent = Math.round(progress * 100);
  const lightYearsRemaining = Math.round((1 - progress) * TOTAL_LIGHT_YEARS);

  return (
    <div className="progress-readout">
      <div className="progress-readout__bar">
        <div className="progress-readout__fill" style={{ width: `${percent}%` }} />
      </div>
      <p className="progress-readout__text">
        {percent}% of the way to Andromeda &middot; {lightYearsRemaining.toLocaleString()} light-years remaining
      </p>
    </div>
  );
}
