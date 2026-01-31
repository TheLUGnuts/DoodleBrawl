import React, { useState, useEffect } from 'react';
import { socket } from './socket';
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import DrawingCanvas from './components/DrawingCanvas';
import BattleView from './components/BattleView';

function App() {
  const [connectionStatus, setConnectionStatus] = useState("Never Connected");

  useEffect(() => {
    function onConnect() {
      setConnectionStatus("Connected!");
      console.log("Connected to socket.");
    }

    function onDisconnect() {
      setConnectionStatus("Disconnected...");
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
        <hr/>
      </div>
      
      <div class='battle'>
        <h2>Battle Grounds</h2>
        <BattleView />
        <hr/>
      </div>

      <div class='drawing'>
        <h2>Draw your fighter!</h2>
        <DrawingCanvas />
        <hr/>
      </div>

      <div class='tutorial'>
        <h2>How to Play</h2>
        <p>
          At the bottom, draw a character to be entered into the pool of fighters. Draw anything!
          When ready, hit the "Submit for Battle!" button to enter your fighter into the fray.
          AI will evaluate your character and give it hidden fighting characteristics.
        </p>
        <p>
          In the battle grounds, two characters will be selected from the pool of fighters.
          AI will take the character statistics and simulate a battle between them.
          The match will play out in front of your eyes, and you will see who wins!
        </p>
        <hr/>
      </div>

      <div class='status'>
        <p>Connection Status: { connectionStatus }</p>
        <p>Made with love by Connor Fair, Jon Rutan, and Trevor Corcoran for VCU's 2026 Hackathon</p>
      </div>
    </>
  )
}

export default App
