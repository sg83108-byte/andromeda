import './Ship.css';

export default function Ship({ phaseName }) {
  return (
    <div className={`ship phase-${phaseName}`}>
      <div className="ship__glow" aria-hidden="true" />
      <svg
        className="ship__body"
        viewBox="0 0 64 32"
        role="img"
        aria-label="Space vehicle traveling toward Andromeda"
      >
        <g transform="translate(0 16)">
          <path
            d="M4 0 C 20 -9, 44 -9, 60 0 C 44 9, 20 9, 4 0 Z"
            fill="#dfe3ff"
          />
          <circle cx="44" cy="0" r="4" fill="#7cc9ff" opacity="0.9" />
          <path d="M18 -8 L28 -2 L18 -2 Z" fill="#a9b3ff" />
          <path d="M18 8 L28 2 L18 2 Z" fill="#a9b3ff" />
        </g>
      </svg>
    </div>
  );
}
