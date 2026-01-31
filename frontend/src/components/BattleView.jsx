import { useState, useEffect } from 'react';
import { socket } from '../socket.js';
import './BattleView.css';

export default function BattleView() {
  const defaultBattleState = {
    fighters: [
      {
        name: "",
        description: "",
        wins: 0,
        losses: 0,
      },
      {
        name: "",
        description: "",
        wins: 0,
        losses: 0,
      }
    ]
  }
  const [battleState, setBattleState] = useState(defaultBattleState);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  function ImageViewer({ base64 }) {
    return (
      <img
        src={`data:image/png;base64,${base64}`}
        alt="Fighter Image"
      />
    );
  }

  function processFightData(data) {
    // Processes fighting data

    // Fighter images
    setBattleState(data);
  }

  const handleSchedule = (data) => {
    console.log("SCHEDULE ------")
    console.log(data);

    processFightData(data);
  }

  const handleResult = (data) => {
    // Takes data from a fight and places it in the correct places
    console.log("RESULT ------")
    console.log(data);

    processFightData(data);
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

    // Get initial fighter info from scheduled battle
    fetch('http://localhost:5000/card')
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(json => {
        console.log("Got data-----------------")
        processFightData(json);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });


    // De-register listeners for cleanup
    return () => {
      socket.off('match_scheduled', handleSchedule);
      socket.off('match_result', handleResult);
      socket.off('timer_update', handleTimerUpdate);
    }
  }, []);


  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!battleState) return null;

  return (
    <div class='root'>
      <div class='row'>

        <div class='column'>
          <p class='fighter-name fighter-1'>{battleState.fighters[0].name}</p>
          <div class='fighter-img'>
            {battleState && <ImageViewer base64={battleState.fighters[0].image_file} />} 
          </div>
          <div class='stats'>
            <p>Wins: {battleState.fighters[0].wins}</p>
            <p>Loses: {battleState.fighters[0].wins}</p>
          </div>
        </div>

        <div class='column'>
          <p class='fighter-name fighter-2'>Fighter 2</p>
          {battleState && <ImageViewer base64={battleState.fighters[1].image_file} />} 
        </div>
      </div>
    </div>
  );
}
