import { useState, useEffect, useRef } from 'react';
import { socket, API_URL } from './socket.js';
import './App.css'
import DoodleCanvas from './components/DoodleCanvas';
import ArenaView from './components/ArenaView';
import RosterView from './components/RosterView';
import ArenaMini from './components/ArenaMini';

function App() {
  const [timer, setTimer] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState("Never Connected");
  const [activeTab, setActiveTab] = useState("battleground"); //default to the drawing canvas
  const [battleState, setBattleState] = useState(null);
  const [lastFightResult, setLastFightResult] = useState(null);
  const timeouts = useRef([]);
  const [logState, setLogState] = useState([]);
  const [lastWinner, setLastWinner] = useState("");
  const [summaryState, setSummaryState] = useState("");
  

  const [loading, setLoading] = useState(true);

  const handleResult = (data) => {
    // Takes data from a fight and places it in the correct places
    console.log("RESULT ------")
    //in order to preview the new character name and description we used a mixed battle state
    //the mixed battle state retains all the information of the previous battle state but includes the new name and description
    //this is only used temporarily, until the complete battle state will overwrite this inside of processFightLogs
    setBattleState(prev => {
      const mixedState = {...data, fighters: [...data.fighters]};
      mixedState.fighters = data.fighters.map((newFighter, index) => {
        const oldFighter = prev.fighters[index];
        return {
          ...newFighter,
          wins: oldFighter ? oldFighter.wins : newFighter.wins,
          losses: oldFighter ? oldFighter.losses : newFighter.losses
        };
      });
      return mixedState;
    });
    processFightLogs(data);
  }

  function processFightLogs(data) {
    // Processes only the logs
    setLogState([]);
    setLastWinner("");
    setSummaryState("");
    timeouts.current.forEach(clearTimeout);
    timeouts.current = [];

    const LOG_DELAY = 1500 // 1.5 seconds between message
    data.log.forEach((log, index) => {
      const t = setTimeout(() => {
        setLogState(prev => [...prev, log]);
      }, (index + 1) * LOG_DELAY);
      timeouts.current.push(t);
    });
    //totalTime is how long to wait before the winner text and summary is displayed. Calculated by the amount of logs times the log delay
    const totalTime = (data.log.length + 1) * LOG_DELAY;
    const tWinner = setTimeout(() => {
      setLastWinner(data.winner);
      setSummaryState(data.summary);
      setBattleState(data); 
      console.log("Battle finished.");
    }, totalTime);
    timeouts.current.push(tWinner);
  }

  function processFightData(data) {
    // Processes fighting data
    console.log(data);

    // Fighter images
    setBattleState(data);
  }

  // Listen for and load battles from backend
  useEffect(() => {
    // Register listeners
    socket.on('match_scheduled', handleSchedule);
    socket.on('timer_update', handleTimerUpdate);
    socket.on('match_result', handleResult);

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
        console.log(err);
      });


    // De-register listeners for cleanup
    return () => {
      socket.off('match_scheduled', handleSchedule);
      socket.off('timer_update', handleTimerUpdate);
    }
  }, []);

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
      setTimer(<img className="throbber" src="./RatJohnson.gif"></img>);
    }
    else {
      setTimer("Scheduling...")
    }
    console.log(data);
  }

  useEffect(() => {
    function onConnect() {
      setConnectionStatus("Connected!");
      console.log("Connected to socket.");
    }

    function onDisconnect() {
      setConnectionStatus("Lost Connection...");
      console.log("Disconnected from socket.");
    }

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
    };
  }, []);

  return (
    <>
      <div className='header'>
        <h1>Doodle Brawl!</h1>
          <button className = {`tab-button ${activeTab === 'doodle' ? 'active' : ''}`} onClick={() => setActiveTab('doodle')}>
              Doodle!
            </button>
          <button className = {`tab-button ${activeTab === 'battleground' ? 'active' : ''}`} onClick={() => setActiveTab('battleground')}>
            Arena!
          </button>
          <button className = {`tab-button ${activeTab === 'leaderboard' ? 'active' : ''}`} onClick={() => setActiveTab('leaderboard')}>
            Roster!
          </button>
        <hr/>
      </div>


      <div className="main-content">
        {activeTab !== 'battleground' && (
          <div className='small-battleground'>
            <ArenaMini battleState={battleState} timer={timer} lastWinner={lastWinner}/>
            <hr/>
          </div>
        )}

        {activeTab === 'doodle' && (
          <div className='drawing'>
            <h2>Draw your fighter!</h2>
            <DoodleCanvas />
            <hr/>
          </div>
        )}

        {activeTab === 'battleground' && (
        <div class='battleground'>
          <ArenaView battleState={battleState} timer={timer} logState={logState} lastWinner={lastWinner} summaryState={summaryState}/>
          <hr/>
        </div>
        )}

        {activeTab === 'leaderboard' && (
        <div class='leaderboard'>
          <RosterView />
          <hr/>
        </div>
        )}
      </div>

      <div className='tutorial'>
        <h2>How to Play</h2>
        <p>
          Doodle a combatant then hit "Submit For Battle!".<br></br>
          You drawing will be given a name and secret stats, then enter the fray.
        </p>
        <hr/>
      </div>

      <div className='status'>
        <p>Server Status: { connectionStatus }</p>
        <p>Made with love by <a className='status-link' href='https://www.linkedin.com/in/connor-fair36/'>Connor Fair</a>, <a className='status-link' href='https://www.linkedin.com/in/jonathanrutan/'>Jon Rutan</a>, and <a className='status-link' href='https://www.linkedin.com/in/trevorcorc/'>Trevor Corcoran</a> for VCU's 2026 Hackathon</p>
        <a className='status-link' href='https://github.com/TheLUGnuts/DoodleBrawl'>View on GitHub</a>
      </div>
    </>
  )
}

export default App
