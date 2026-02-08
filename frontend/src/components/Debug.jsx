import { useState, useEffect } from 'react';
import { API_URL } from '../socket.js';

export default function Debug() {
  const [isLocal, setIsLocal] = useState(false);

  useEffect(() => {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      setIsLocal(true);
    }
  }, []);

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
    <div style={{ 
      position: 'fixed', 
      bottom: '10px', 
      right: '10px', 
      backgroundColor: 'rgba(0, 0, 0, 0.8)', 
      padding: '10px', 
      borderRadius: '8px',
      border: '1px solid #444', 
      zIndex: 9999,
      display: 'flex',
      gap: '10px'
    }}>
      <h4 style={{ margin: '0', color: '#fff', alignSelf: 'center', marginRight: '5px' }}>DEBUG:</h4>
      <button onClick={handleSkip} style={{ cursor: 'pointer', padding: '5px 10px' }}>
        Skip Timer
      </button>
      <button onClick={handleRematch} style={{ cursor: 'pointer', padding: '5px 10px' }}>
        New Matchup
      </button>
    </div>
  );
}