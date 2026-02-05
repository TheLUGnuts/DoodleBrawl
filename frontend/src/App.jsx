import { useState, useEffect } from 'react';

import { socket } from './socket';
import './App.css'
import DoodleCanvas from './components/DoodleCanvas';
import ArenaView from './components/ArenaView';
import RosterView from './components/RosterView';

function App() {
  const [connectionStatus, setConnectionStatus] = useState("Never Connected");
  const [openLeaderboard, setOpenLeaderboard] = useState(false);
  const [activeTab, setActiveTab] = useState("doodle"); //default to the drawing canvas

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
      <div class='header'>
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
        {activeTab === 'doodle' && (
          <div class='drawing'>
            <h2>Draw your fighter!</h2>
            <DoodleCanvas />
            <hr/>
          </div>
        )}

        {activeTab === 'battleground' && (
        <div class='battleground'>
          <ArenaView />
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

      <div class='tutorial'>
        <h2>How to Play</h2>
        <p>
          Doodle a combatant then hit "Submit For Battle!".<br></br>
          You drawing will be given a name and secret stats, then enter the fray.
        </p>
        <hr/>
      </div>

      <div class='status'>
        <p>Server Status: { connectionStatus }</p>
        <p>Made with love by <a class='status-link' href='https://www.linkedin.com/in/connor-fair36/'>Connor Fair</a>, <a class='status-link' href='https://www.linkedin.com/in/jonathanrutan/'>Jon Rutan</a>, and <a class='status-link' href='https://www.linkedin.com/in/trevorcorc/'>Trevor Corcoran</a> for VCU's 2026 Hackathon</p>
        <a class='status-link' href='https://github.com/TheLUGnuts/DoodleBrawl'>View on GitHub</a>
      </div>
    </>
  )
}

export default App
