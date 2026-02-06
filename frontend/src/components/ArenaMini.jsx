import { useState, useEffect, useRef } from 'react';
import { socket, API_URL } from '../socket.js';
import './ArenaMini.css';
import '../text_decor.css';

export default function ArenaView() {
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
    ],
  }
  const [battleState, setBattleState] = useState(defaultBattleState);
  const [lastWinner, setLastWinner] = useState("")
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timer, setTimer] = useState(null);
  const timeouts = useRef([]);
  
  function ImageViewer({ base64, isWinner, isLoser }) {
    let className = '';
    if (isWinner) className = 'winner-img';
    if (isLoser) className = 'loser-img';
    return (
      <img
        className="thumbnail-img"
        src={`data:image/png;base64,${base64}`}
        alt="Fighter Image"
      />
    );
  }

  function processFightData(data) {
    // Processes fighting data
    console.log(data);
    // Fighter images
    setBattleState(data);
  }

  const handleSchedule = (data) => {
    console.log("SCHEDULE ------");
    timeouts.current.forEach(clearTimeout);
    timeouts.current = [];

    setLogState([{description: "The match will begin soon!"}]);
    setLastWinner("");
    setSummaryState("");
    processFightData(data);
  }

  const handleTimerUpdate = (data) => {
    console.log("TIMER UPDATE ------")
    if (data.time_left > 0) {
      setTimer(data.time_left);
    } 
    else if (data.time_left == 0) {
      setTimer("Battle commencing!")
    }
    else {
      setTimer("Bookie is working on the next match...")
    }
    console.log(data);
  }

  // Listen for and load battles from backend
  useEffect(() => {
    // Register listeners
    socket.on('match_scheduled', handleSchedule);
    socket.on('timer_update', handleTimerUpdate);

    // Get initial fighter info from scheduled battle
    fetch(`${API_URL}/api/card`)
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(json => {
        console.log("Got Fresh Fighter Data");
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
      socket.off('timer_update', handleTimerUpdate);
    }
  }, []);


  if (loading) return <div class='net-loading'>Loading...</div>;
  if (error) return <div class='net-error'>Error: {error}</div>;
  if (!battleState || !battleState.fighters || battleState.fighters.length < 2) { return (
        <div className='root waiting-screen'>
            <h1>Waiting for Next Match...</h1>
            {timer && <h2>Next Match in: {timer}s</h2>}
        </div>
      );
    }

  return (
    <div class='root'>
      <div class='row'>
        <div class='column'>
          <p class='fighter-name fighter-1'>{battleState.fighters[0].name}</p>
          <div class='fighter-img'>
            {battleState && 
            <ImageViewer base64={battleState.fighters[0].image_file} 
              isWinner={lastWinner && lastWinner === battleState.fighters[0].name}
              isLoser={lastWinner && lastWinner !== battleState.fighters[0].name}
            />} 
          </div>
        </div>

        <div class="column">
            <p class="versus">VS</p>
            <p>IN: {timer}</p>
        </div>

        <div class='column'>
          <p class='fighter-name fighter-2'>{battleState.fighters[1].name}</p>
          <div class='fighter-img'>
            {battleState && 
            <ImageViewer base64={battleState.fighters[1].image_file} 
              isWinner={lastWinner && lastWinner === battleState.fighters[1].name}
              isLoser={lastWinner && lastWinner !== battleState.fighters[1].name}
            />} 
          </div>
        </div>
      </div>
    </div>
  );
}
