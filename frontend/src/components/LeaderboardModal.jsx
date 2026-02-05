/* This component shows the top few fighters, including their stats and images. */

import { useState, useEffect, useRef, memo } from 'react';
import { socket, useLocalhost } from '../socket.js';
import { Button, CloseButton, Dialog, Portal, Text } from "@chakra-ui/react"
import './LeaderboardModal.css'

export default memo(function LeaderboardModal({ isOpen, setIsOpen }) {
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

  // Fetch data only when modal opens
  useEffect(() => {
    if (!isOpen) return; // Don't fetch if modal is closed
    console.log("Fetching leaderboard")

    setLoading(true);
    setError(null);
    
    fetch(useLocalhost ? 'http://localhost:5000/api/leaderboard' : 'api/leaderboard')
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
  }, [isOpen]); // Re-run when isOpen changes
  
  // Show loading/error states inside the dialog
  return (
    <Dialog.Root
      role="alertdialog"
      open={isOpen}
      size="lg"
      onOpenChange={(e) => setIsOpen(e.open)}
    >
      <Portal>
        <Dialog.Backdrop bg="gray.700/50" />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.CloseTrigger asChild>
              <CloseButton variant="subtle" />
            </Dialog.CloseTrigger>
            <Dialog.Header>
              <Dialog.Title>Leaderboard</Dialog.Title>
            </Dialog.Header>
            <Dialog.Body>
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
            </Dialog.Body>
            <Dialog.Footer>
              {/* Empty, could be filled later */}
            </Dialog.Footer>
          </Dialog.Content>
        </Dialog.Positioner>
      </Portal>
    </Dialog.Root>
  )
});
