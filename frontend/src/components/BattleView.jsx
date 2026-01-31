import { useState, useEffect } from 'react';
import { socket } from '../socket.js';
import './BattleView.css';

export default function BattleView() {
  const [battleState, setBattleState] = useState({});
  const [fighterLImg, setFighterLImg] = useState(null);
  const [fighterRImg, setFighterRImg] = useState(null);
  
  function ImageViewer({ base64 }) {
    return (
      <img
        src={`data:image/png;base64,${base64}`}
        alt="Fighter Image"
      />
    );
  }


  const handleSchedule = (data) => {
    console.log("SCHEDULE ------")
    console.log(data);
  }

  const handleResult = (data) => {
    // Takes data from a fight and places it in the correct places
    console.log("RESULT ------")
    console.log(data);

    // Fighter images
    setFighterLImg(data.fighters[0].image_file);
    setFighterRImg(data.fighters[1].image_file);
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
      {fighterLImg && <ImageViewer base64={fighterLImg} />} 
      {fighterRImg && <ImageViewer base64={fighterRImg} />} 
    </div>
  );
}
