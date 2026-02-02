import React, { useState, useEffect } from 'react';
import { IconButton } from "@chakra-ui/react"
import { MdLeaderboard } from "react-icons/md";

import { socket } from './socket';
import './App.css'
import DrawingCanvas from './components/DrawingCanvas';
import BattleView from './components/BattleView';
import LeaderboardModal from './components/LeaderboardModal';

function App() {
  const [connectionStatus, setConnectionStatus] = useState("Never Connected");
  const [openLeaderboard, setOpenLeaderboard] = useState(false);

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
        <p>Server Status: { connectionStatus }</p>
        <p>Made with love by <a class='status-link' href='https://www.linkedin.com/in/connor-fair36/'>Connor Fair</a>, <a class='status-link' href='https://www.linkedin.com/in/jonathanrutan/'>Jon Rutan</a>, and <a class='status-link' href='https://www.linkedin.com/in/trevorcorc/'>Trevor Corcoran</a> for VCU's 2026 Hackathon</p>
        <a class='status-link' href='https://github.com/TheLUGnuts/DoodleBrawl'>View on GitHub</a>
      </div>

      <IconButton variant="outline" rounded="full" colorScheme="blue"
        onClick={() => setOpenLeaderboard(true)}
        icon={<MdLeaderboard />}
        position="fixed" bottom="20px" right="20px"
        shadow="lg"
        zIndex="1000"
        aria-label="Leaderboard" />
      <LeaderboardModal isOpen={openLeaderboard} setIsOpen={setOpenLeaderboard} />

    </>
  )
}

export default App
