/* This component shows the top few fighters, including their stats and images. */

import { useState, useEffect, useRef } from 'react';
import { socket, API_URL } from '../socket.js';
import './RosterView.css'

export default function RosterView() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rosterData, setRosterData] = useState({});
  const [page, setPage] = useState(1); // Page number for fetch

  const checkIsChampion = (status) => {
    return status && status.includes("Champion");
  };

  function ImageViewer({ base64, fighterPlacement, isChampion }) {
    // Decodes base64 image from server
    // Fighter placement (eg 1, 2, 3, etc.) is the fighter's placement in the lineup. 1st, 2nd, 3rd get special css
    return (
      <img
        className="{'fighter-' + fighterPlacement} roster-fighter-img"
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
      if (data.length == 0) {
        console.log("No fighters to display.")
        return false;
      } 
      processRosterData(data);
      setPage(pageNum);
      return true;

    } catch (error) {  // Catch error
      console.error('Error fetching items:', error);
      setError(error.message);

    } finally {  // Unset loading variable
      setLoading(false);
    }
  };

  const getNextPage = () => {
    const pageNum = page + 1;
    fetchRoster(pageNum);
  }

  const getPrevPage = () => {
    if (page === 1) return;
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
      <div className="page-button-container">
        <button className="page-button" onClick={getPrevPage}>Previous</button>
        <button className="page-button" onClick={getNextPage}>Next</button>
      </div>

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
                <p className="place-number">#{(index + 1) + ((page-1))*5}</p> 
                <div className="stats">
                  <b className="fighter-name">{item.name}</b>
                  <b className="fighter-status">{item.status}</b>
                  <p className="description"><span dangerouslySetInnerHTML={{ __html: item.description }} /></p>
                  <p>Wins: {item.wins}</p>
                  <p>Losses: {item.losses}</p>
                  <p>W/L Ratio: {item.wins / item.losses}</p>
                </div>
              </div>
              {rosterData && <ImageViewer base64={item.image_file} fighterPlacement='{1}' isChampion={checkIsChampion(item.status)} />}
            </div>
            {index < rosterData.length - 1 && <hr />}
          </>
        ))}
      </div>
      )}

      {rosterData.length > 0 && (
        <div className="page-button-container">
          <button className="page-button" onClick={getPrevPage}>Previous</button>
          <button className="page-button" onClick={getNextPage}>Next</button>
        </div>
      )}
    </>
  )
};
