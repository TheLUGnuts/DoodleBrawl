import { useState, useEffect } from 'react';
import './Debug.css'
import { API_URL } from '../socket.js';

export default function Debug() {
  const [isLocal, setIsLocal] = useState(false);

  useEffect(() => {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      setIsLocal(true);
    }
  }, []);

  const handleFreeze = async () => {
    try {
      await fetch(`${API_URL}/api/debug/freeze`, { method: 'POST' });
    } catch (e) {
      console.error("Debug Freeze Failed:", e);
    }
  };

  const handleSkip = async () => {
    try {
      await fetch(`${API_URL}/api/debug/skip`, { method: 'POST' });
    } catch (e) {
      console.error("Debug Skip Failed:", e);
    }
  };

  const handleRematch = async () => {
    try {
      await fetch(`${API_URL}/api/debug/rematch`, { method: 'POST' });
    } catch (e) {
      console.error("Debug Rematch Failed:", e);
    }
  };

  if (!isLocal) return null;

  return (
    <div className="debug-modal">
      <h4 className='debug-h4'>DEBUG:</h4>
      <button onClick={handleSkip} className="debug-button">
        Skip Timer
      </button>
      <button onClick={handleFreeze} className="debug-button">
        Freeze Timer
      </button>
      <button onClick={handleRematch} className="debug-button">
        New Matchup
      </button>
    </div>
  );
}