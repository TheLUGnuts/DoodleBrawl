/* This component shows the top few fighters, including their stats and images. */

import { useState, useEffect, useRef } from 'react';
import { socket, API_URL } from '../socket.js';
import './RosterView.css'

export default function RosterView() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rosterData, setRosterData] = useState({});
  const [page, setPage] = useState(1); // Page number for fetch

  function ImageViewer({ base64, fighterPlacement }) {
    // Decodes base64 image from server
    // Fighter placement (eg 1, 2, 3, etc.) is the fighter's placement in the lineup. 1st, 2nd, 3rd get special css
    return (
      <img
        className="{'fighter-' + fighterPlacement} fighter-img"
        src={`data:image/png;base64,${base64}`}
        alt="Fighter Image"
      />
    );
  }

  function processRosterData(json) {
    // Pass data around where necessary
    console.log(json)
    setRosterData(json)
  }

  const fetchRoster = async (pageNum) => {
    // Fetch data from server
    // pageNum specifies which page of data to return (1st, 2nd, 3rd, etc.)

    // Set fetch status
    setLoading(true);
    setError(null);

    // Attempt POST to server
    try {
      const response = await fetch(`${API_URL}/api/roster`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          page: pageNum,
        })
      });

      // Process data upon success
      const data = await response.json();
      console.log("Got Fresh Fighter Data");
      processRosterData(data);

    } catch (error) {  // Catch error
      console.error('Error fetching items:', error);
      setError(error.message);

    } finally {  // Unset loading variable
      setLoading(false);
    }
  };

  const getNextPage = () => {
    const pageNum = page + 1;
    setPage(pageNum);
    fetchRoster(pageNum);
  }

  const getPrevPage = () => {
    const pageNum = page - 1;
    setPage(pageNum);
    fetchRoster(pageNum);
  }

  // Fetch initial data
  useEffect(() => {
    console.log("Fetching initial roster data")
    fetchRoster(1);
  }, []);

  // Show loading/error states inside the dialog
  return (
    <>
      {loading ? (
        <div class='net-loading'>Loading...</div>
      ) : error ? (
        <div class='net-error'>Error: {error}</div>
      ) : (
        <div class='roster-container'>
        {rosterData.map((item, index) => (
          <>
            <div key={item.id || index} class="entry">
              <div className="info">
                <p className="place-number">#{index + 1}</p>
                <div className="stats">
                  <b className="fighter-name">{item.name}</b>
                  <p className="description">{item.description}</p>
                  <p>Wins: {item.wins}</p>
                  <p>Losses: {item.losses}</p>
                  <p>W/L Ratio: {item.wins / item.losses}</p>
                </div>
              </div>
              {rosterData && <ImageViewer base64={item.image_file} fighterPlacement='{1}' />}
            </div>
            <hr />
          </>
        ))}
      </div>
      )}

      <div className="page-button-container">
        <button className="page-button"onClick={getNextPage}>Next</button>
      </div>
    </>
  )
};
