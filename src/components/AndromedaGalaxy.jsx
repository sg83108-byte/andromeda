import './AndromedaGalaxy.css';

export default function AndromedaGalaxy({ progress, arrived }) {
  const scale = 0.4 + progress * 1.2;
  const brightness = 0.5 + progress * 0.7;

  return (
    <div
      className={`andromeda-galaxy${arrived ? ' andromeda-galaxy--arrived' : ''}`}
      style={{ '--galaxy-scale': scale, '--galaxy-brightness': brightness }}
      aria-hidden="true"
    />
  );
}
