// src/components/arena/Commentator.jsx
import { useState, useEffect } from 'react';
import './Commentator.css';

export default function Commentator({ logState }) {
  const [isTalking, setIsTalking] = useState(false);
  const [commentatorSrc, setCommentatorSrc] = useState('./js.png');

  // Trigger Jim Scribble speaking animation when a log appears
  useEffect(() => {
    if (logState && logState.length > 0) {
      setIsTalking(true);
      
      // Pick a random talking frame for this log
      const frames = ['./js1.png', './js2.png', './js3.png'];
      const randomFrame = frames[Math.floor(Math.random() * frames.length)];
      setCommentatorSrc(randomFrame);

      const timerId = setTimeout(() => {
        setIsTalking(false);
        setCommentatorSrc('./js.png'); // Revert to resting face
      }, 500);
      
      return () => clearTimeout(timerId);
    }
  }, [logState]);

  return (
    <div key="jim-scribble" className="commentator-container slide-up-fade">
      <img 
        src={commentatorSrc} 
        alt="Jim Scribble" 
        className={`commentator-img ${isTalking ? 'talking' : ''}`} 
      />
    </div>
  );
}