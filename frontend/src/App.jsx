import { useState, useEffect, useRef } from 'react';
import { socket, API_URL } from './socket.js';
import './App.css'
import DoodleCanvas from './components/DoodleCanvas';
import ArenaView from './components/ArenaView';
import RosterView from './components/RosterView';
import ArenaMini from './components/ArenaMini';
import Account from './components/Account';
import Debug from './components/Debug';

function App() {
  const [timer, setTimer] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState("Never Connected");
  const [activeTab, setActiveTab] = useState("battleground"); //default to the drawing canvas
  const [battleState, setBattleState] = useState(null);
  const timeouts = useRef([]);
  const [logState, setLogState] = useState([]);
  const [lastWinner, setLastWinner] = useState("");
  const [summaryState, setSummaryState] = useState("");
  const [introState, setIntroState] = useState("");
  const [user, setUser] = useState(null);
  const [log, setLoading] = useState(true);
  const [matchOdds, setMatchOdds] = useState({});
  const [currentPool, setCurrentPool] = useState(0);
  const [myBet, setMyBet] = useState(null);
  const [payoutWon, setPayoutWon] = useState(0);

  const handleResult = (data) => {
    // Takes data from a fight and places it in the correct places
    setIntroState(data.introduction);
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
          losses: oldFighter ? oldFighter.losses : newFighter.losses,
          titles: oldFighter ? oldFighter.titles : newFighter.titles,
          alignment: oldFighter ? oldFighter.alignment : newFighter.alignment
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
      setMyBet(currentBet => {
          if (currentBet && data.winner === currentBet.fighterName) {
              setPayoutWon(currentBet.payout);
          } else {
            setPayoutWon(-1);
          }
          return currentBet; 
      });
      const savedID = localStorage.getItem("doodle_brawl_id"); //this refreshed the users login to update their money once the fight logs are done processing.
      if (savedID) verifyLogin(savedID);
    }, totalTime);
    timeouts.current.push(tWinner);
  }

  function processFightData(data) {
    // Processes fighting data
    if (data.odds) setMatchOdds(data.odds);
    if (data.pool) setCurrentPool(data.pool);
    setBattleState(data);
  }

  //see if a user has a locally saved login ID
  useEffect(() => {
    const savedID = localStorage.getItem("doodle_brawl_id");
    if (savedID) {
      console.log("Found saved ID, verifying...", savedID);
      verifyLogin(savedID);
    }
  }, []);

  //verify a login status if they have a local ID
  const verifyLogin = async (id) => {
    try {
      const response = await fetch(`${API_URL}/api/account/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_id: id })
      });
      const data = await response.json();
      if (data.status === 'success') {
        setUser(data);
        console.log("Logged in as", data.username);
      } else {
        console.log("Saved ID invalid, clearing.");
        localStorage.removeItem("doodle_brawl_id");
      }
    } catch (e) {
      console.error("Login verification failed:", e);
    }
  };

  const handleAuthSuccess = (userData) => {
    localStorage.setItem("doodle_brawl_id", userData.id || userData.account_id);
    // If it was a registration, we might need to fetch the full profile?
    verifyLogin(userData.id || userData.account_id);
  };

  const handleLogout = () => {
    localStorage.removeItem("doodle_brawl_id");
    setUser(null);
  }

  const handleCharacterAdded = (data) => {
      if (data.status === 'success') {
        alert(`Success! ${data.character.name} has been added to the approval queue!`);
        console.log("New character verified by server:", data.character);

        setUser(prevUser => {
          if (!prevUser) return prevUser;
          
          return {
            ...prevUser,
            created_characters: [...prevUser.created_characters, data.character]
          };
        });
      }
    };

  // Listen for and load battles from backend
  useEffect(() => {
    // Register listeners
    socket.on('match_scheduled', handleSchedule);
    socket.on('timer_update', handleTimerUpdate);
    socket.on('match_result', handleResult);
    socket.on('character_added', handleCharacterAdded);
    socket.on('pool_update', (data) => {setCurrentPool(data.pool)});

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
      socket.off('match_result', handleResult);
      socket.off('character_added', handleCharacterAdded);
      socket.off('pool_update');
    }
  }, []);

  const handleSchedule = (data) => {
    console.log("SCHEDULE ------");
    timeouts.current.forEach(clearTimeout);
    timeouts.current = [];

    setLogState([{description: "The match will begin soon!"}]);
    setLastWinner("");
    setSummaryState("");
    setIntroState("");
    processFightData(data);
    setMyBet(null);
    if (data.odds) setMatchOdds(data.odds);
    if (data.pool) setCurrentPool(data.pool);
    setPayoutWon(0);
  }

  const handleTimerUpdate = (data) => {
    //console.log("TIMER UPDATE ------")
    if (data.time_left > 0) {
      setTimer(data.time_left);
    } 
    else if (data.time_left == 0) {
      setTimer(<img className="throbber" src="./RatJohnson.gif"></img>);
    }
    else {
      setTimer("Scheduling...")
    }
    //console.log(data);
  }

  // Enables connected/disconnected status events
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

  //check if the logged in user is a registered admin
  const adminIds = (import.meta.env.VITE_ADMIN_IDS || "").split(',');
  const isAdmin = user && adminIds.includes(user.id);

  return (
    <>
      <div className='header'>
        <h1>Doodle Brawl!</h1>
          <button className = {`tab-button ${activeTab === 'doodle' ? 'active' : ''}`} onClick={() => setActiveTab('doodle')}>
              Doodle
            </button>
          <button className = {`tab-button ${activeTab === 'battleground' ? 'active' : ''}`} onClick={() => setActiveTab('battleground')}>
            Arena
          </button>
          <button className = {`tab-button ${activeTab === 'leaderboard' ? 'active' : ''}`} onClick={() => setActiveTab('leaderboard')}>
            Roster
          </button>
          <button className = {`tab-button ${activeTab === 'account' ? 'active' : ''}`} onClick={() => setActiveTab('account')}>
            Account
          </button>
          {/* ONLY RENDERS IF ADMIN */}
          {isAdmin && (
            <button className={`tab-button ${activeTab === 'debug' ? 'active' : ''}`} onClick={() => setActiveTab('debug')}>
              Debug
            </button>
          )}
        <hr/>
      </div>


      {/* These are all of our tabs at the top of the website */}
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
            {/*MAGIC NUMBER ALERT! This was our original size of the canvas before being made modifiable with props*/}
            <DoodleCanvas canvWidth={754} canvHeight={400} userID={user ? user.id : null}/>
            <hr/>
          </div>
        )}

        {activeTab === 'battleground' && (
        <div class='battleground'>
          <ArenaView battleState={battleState} timer={timer} logState={logState} lastWinner={lastWinner} summaryState={summaryState} introState={introState} user={user} setUser={setUser} matchOdds={matchOdds} currentPool={currentPool} myBet={myBet} setMyBet={setMyBet} payoutWon={payoutWon}/>
          <hr/>
        </div>
        )}

        {activeTab === 'leaderboard' && (
        <div class='leaderboard'>
          <RosterView />
          <hr/>
        </div>
        )}

        {activeTab === 'account' && (
        <div class='account'>
          <Account user={user} onLogin={handleAuthSuccess} onLogout={handleLogout}/>
          <hr/>
        </div>
        )}

        {/* ONLY RENDERS IF ADMIN AND TAB IS ACTIVE */}
        {activeTab === 'debug' && isAdmin && (
          <div className='debug-tab-container'>
            <Debug user={user} /> 
            <hr/>
          </div>
        )}
      </div>

      <div className='tutorial'>
        <h2>How to Play</h2>
        <p>
          Doodle a combatant then hit "Submit For Battle!".<br></br>
          Your drawing will be given a name and secret stats, then enter the fray.
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
