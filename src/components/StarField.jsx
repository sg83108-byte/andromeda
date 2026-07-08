import { useEffect, useRef } from 'react';
import './StarField.css';

const LAYERS = [
  { count: 60, speed: 0.15, radius: [0.4, 1], alpha: 0.5 },
  { count: 45, speed: 0.35, radius: [0.6, 1.5], alpha: 0.75 },
  { count: 30, speed: 0.6, radius: [1, 2], alpha: 1 },
];

export default function StarField({ isRunning, reducedMotion }) {
  const canvasRef = useRef(null);
  const starsRef = useRef([]);
  const frameRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    function resize() {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    starsRef.current = LAYERS.flatMap((layer) =>
      Array.from({ length: layer.count }, () => ({
        x: Math.random() * canvas.clientWidth,
        y: Math.random() * canvas.clientHeight,
        radius: layer.radius[0] + Math.random() * (layer.radius[1] - layer.radius[0]),
        speed: layer.speed,
        alpha: layer.alpha,
        twinklePhase: Math.random() * Math.PI * 2,
      }))
    );

    let twinkleTime = 0;

    function draw() {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      context.clearRect(0, 0, width, height);

      twinkleTime += 0.02;
      for (const star of starsRef.current) {
        if (isRunning && !reducedMotion) {
          star.x -= star.speed;
          if (star.x < 0) star.x = width;
        }
        const twinkle = reducedMotion
          ? star.alpha
          : star.alpha * (0.7 + 0.3 * Math.sin(twinkleTime + star.twinklePhase));
        context.beginPath();
        context.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
        context.fillStyle = `rgba(232, 232, 255, ${twinkle})`;
        context.fill();
      }

      frameRef.current = requestAnimationFrame(draw);
    }

    frameRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(frameRef.current);
      window.removeEventListener('resize', resize);
    };
  }, [isRunning, reducedMotion]);

  return <canvas className="star-field" ref={canvasRef} aria-hidden="true" />;
}
