import StarField from './StarField.jsx';
import Ship from './Ship.jsx';
import AndromedaGalaxy from './AndromedaGalaxy.jsx';
import './JourneyScene.css';

export default function JourneyScene({ isRunning, reducedMotion, phaseName, progress, arrived, phaseDuration }) {
  return (
    <div className="journey-scene" style={{ '--phase-duration': `${phaseDuration}s` }}>
      <StarField isRunning={isRunning} reducedMotion={reducedMotion} />
      <AndromedaGalaxy progress={progress} arrived={arrived} />
      <div className="journey-scene__track" style={{ '--progress': progress }}>
        <Ship phaseName={phaseName} />
      </div>
    </div>
  );
}
