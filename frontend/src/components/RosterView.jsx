/* This component shows the top few fighters, including their stats and images. */

import { useState, useEffect } from 'react';
import { API_URL, decompressBase64Image } from '../socket.js';
import './RosterView.css'

export default function RosterView() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rosterData, setRosterData] = useState({});
  const [charPerPage, setCharPerPage] = useState(10);
  const [page, setPage] = useState(1); // Page number for fetch

  function ImageViewer({ compressedBase64, titles }) {
    const base64 = decompressBase64Image(compressedBase64);
    return (
      <div className="roster-image-wrapper">
        <img
          className="roster-fighter-img"
          src={`data:image/webp;base64,${base64}`}
          alt="Fighter Image"
        />
        {/* Map through all titles to stack overlapping belts */}
        {titles && titles.map((title, index) => (
          <img 
            key={index}
            className="roster-champ-badge" 
            src="./champ.png" 
            alt="Champion Badge" 
            title={title}
            style={{
              top: `${6 + (index * 10)}px`,
              left: `${-15 + (index * 10)}px`,
              zIndex: 10 - index 
            }}
          />
        ))}
      </div>
    );
  }

  const getAlignmentClass = (alignment) => {
      if (!alignment) return 'alignment-neutral-roster';
      const lower = alignment.toLowerCase();
      if (lower === 'good') return 'alignment-good-roster';
      if (lower === 'evil') return 'alignment-evil-roster';
      return 'alignment-neutral-roster';
    };
  
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
                <p className="place-number">#{(index + 1) + ((page-1))*charPerPage}</p> 
                <div className="stats">
                  <b className={getAlignmentClass(item.alignment)}>{item.name}</b>
                  <b className="roster-titles">{item.titles.join(", ")}</b>
                  <b className="fighter-status">{item.status}</b>
                  <p className="description"><span dangerouslySetInnerHTML={{ __html: item.description }} /></p>
                  <p>Wins: {item.wins}</p>
                  <p>Losses: {item.losses}</p>
                  <p>W/L Ratio: {(item.wins / item.losses) ? (item.wins / item.losses) : "None"}</p>
                  <br/><br/>
                  <p>Created by: {(item.creator_id) ? (item.creator_id) : "???" }</p>
                </div>
              </div>
              {rosterData && <ImageViewer compressedBase64={item.image_file} titles={item.titles} />}
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
