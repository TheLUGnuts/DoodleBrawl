/* This component shows the top few fighters, including their stats and images. */

import { useState, useEffect, useRef } from 'react';
import { socket, API_URL } from '../socket.js';
import { Button, CloseButton, Dialog, Portal, Text } from "@chakra-ui/react"
import './RosterView.css'

export default function RosterView() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [leaderboardData, setLeaderboardData] = useState({})

  function ImageViewer({ base64, fighterPlacement }) {
    // Decodes base64 image from server
    // Fighter placement (eg 1, 2, 3, etc.) is the fighter's placement in the lineup. 1st, 2nd, 3rd get special css
    return (
      <img
        className={'fighter-' + fighterPlacement}
        src={`data:image/png;base64,${base64}`}
        alt="Fighter Image"
      />
    );
  }

  function processLeaderboardData(json) {
    console.log(json)
    setLeaderboardData(json)
  }

  useEffect(() => {
    console.log("Fetching leaderboard")

    setLoading(true);
    setError(null);
    
    fetch(`${API_URL}/api/card`)
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(json => {
        console.log("Got Fresh Fighter Data");
        processLeaderboardData(json);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Show loading/error states inside the dialog
  return (
    <>
      {loading ? (
        <div class='net-loading'>Loading...</div>
      ) : error ? (
        <div class='net-error'>Error: {error}</div>
      ) : (
        <div class='leaderboard-display'>
        {leaderboardData.map((item, index) => (
          <div key={item.id || index} class="leaderboard-entry">
            <h2>#{index + 1}</h2>
            <b>{item.name}</b>
            <p>{item.description}</p>
            <p>Wins: {item.wins}</p>
            {leaderboardData && <ImageViewer base64={item.image_file} fighterPlacement='{1}' />}
            <hr/>
          </div>
        ))}
      </div>
      )}
    </>
  )
};
