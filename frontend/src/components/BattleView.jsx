import { useState, useEffect, useRef } from 'react';
import { socket, useLocalhost } from '../socket.js';
import './BattleView.css';
import '../text_decor.css';

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
    ],
  }
  const [battleState, setBattleState] = useState(defaultBattleState);
  const [lastWinner, setLastWinner] = useState("")
  const [logState, setLogState] = useState([{description: "The match will begin soon!"}]);
  const [summaryState, setSummaryState] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timer, setTimer] = useState(null);
  const timeouts = useRef([]);
  
  function ImageViewer({ base64, isWinner }) {
    return (
      <img
        className={isWinner ? 'winner-img' : ''}
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

  function processFightLogs(data) {
    // Processes only the logs
    setLogState([]);
    const LOG_DELAY = 1500 // 1.5 seconds between message
    data.log.forEach((log, index) => {
      const t = setTimeout(() => {
        setLogState(prev => [...prev, log]);
        const logContainer = document.querySelector('.logs');
        if (logContainer) logContainer.scrollTop = logContainer.scrollHeight;
      }, (index + 1) * LOG_DELAY);
      timeouts.current.push(t);
    });
    //totalTime is how long to wait before the winner text and summary is displayed. Calculated by the amount of logs times the log delay
    const totalTime = (data.log.length + 1) * LOG_DELAY;
    const tWinner = setTimeout(() => {
      setLastWinner(data.winner);
      setSummaryState(data.summary);
      setBattleState(data);
    }, totalTime);
    timeouts.current.push(tWinner);
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

  const handleResult = (data) => {
    // Takes data from a fight and places it in the correct places
    console.log("RESULT ------")
    processFightLogs(data);
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
    socket.on('match_result', handleResult);
    socket.on('timer_update', handleTimerUpdate);

    // Get initial fighter info from scheduled battle
    fetch(useLocalhost ? 'http://localhost:5000/api/card' : 'api/card')
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
      socket.off('match_result', handleResult);
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
      <h2>Next match in: {timer}</h2>
      <div class='row'>

        <div class='column'>
          <p class='fighter-name fighter-1'>{battleState.fighters[0].name}</p>
          <div class='fighter-img'>
            {battleState && <ImageViewer base64={battleState.fighters[0].image_file} isWinner={lastWinner && lastWinner === battleState.fighters[0].name}/>} 
          </div>
          <div class='stats'>
            <p>Fighter Description: {battleState.fighters[0].description}</p>
            <p>Wins: {battleState.fighters[0].wins}</p>
            <p>Loses: {battleState.fighters[0].losses}</p>
          </div>
        </div>

        <div class='column'>
          <p class='fighter-name fighter-2'>{battleState.fighters[1].name}</p>
          <div class='fighter-img'>
            {battleState && <ImageViewer base64={battleState.fighters[1].image_file} isWinner={lastWinner && lastWinner === battleState.fighters[1].name}/>} 
          </div>
          <div class='stats'>
            <p>Fighter Description: {battleState.fighters[1].description}</p>
            <p>Wins: {battleState.fighters[1].wins}</p>
            <p>Loses: {battleState.fighters[1].losses}</p>
          </div>
        </div>

      </div>
        <div class='logs'>
          <ul>
            {logState.map((log, index) => (
              <li class='one-log' key={index}>
                <span class='log-name'>
                  {log.actor}
                </span>
                  <div dangerouslySetInnerHTML={{ __html: log.description }} />
              </li>
            ))}
          </ul>
          {lastWinner && (
            <h2><span class="action-green">WINNER</span>: {lastWinner}</h2>
          )}
          <p class='summary'>{summaryState}</p>
        </div>
    </div>
  );
}
