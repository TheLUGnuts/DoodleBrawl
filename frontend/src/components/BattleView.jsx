import { useState, useEffect } from 'react';
import { socket } from '../socket.js';
import './BattleView.css';

export default function BattleView() {
  
  function ImageViewer({ base64 }) {
    const src = `data:image/png;base64,${base64}`;
    return <img src={src} alt="From socket" />;
  }

  const handleSchedule = (data) => {
    console.log("SCHEDULE ------")
    console.log(data);
  }

  const handleResult = (data) => {
    console.log("RESULT ------")
    console.log(data);
  }

  const handleTimerUpdate = (data) => {
    console.log("TIMER UPDATE ------")
    console.log(data);
  }

  // Listen for and load battles from backend
  useEffect(() => {
    // Register listeners
    socket.on('match_scheduled', handleSchedule);
    socket.on('match_result', handleResult);
    socket.on('timer_update', handleTimerUpdate);

    // De-register listeners for cleanup
    return () => {
      socket.off('match_scheduled', handleSchedule);
      socket.off('match_result', handleResult);
      socket.off('timer_update', handleTimerUpdate);
    }
  }, []);

  return (
    <div class='root'>
      <p>hehe</p>
    </div>
  );
}
