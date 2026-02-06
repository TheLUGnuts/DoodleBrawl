import { useState, useEffect, useRef } from 'react';
import './ArenaMini.css';
import '../text_decor.css';

export default function ArenaMini({ battleState, timer }) {
  //const [battleState, setBattleState] = useState(defaultBattleState);
  const [lastWinner, setLastWinner] = useState("")
  const [error, setError] = useState(null);
  //const [timer, setTimer] = useState(null);
  const timeouts = useRef([]);
  
  function ImageViewer({ base64, isWinner, isLoser }) {
    let className = '';
    if (isWinner) className = 'winner-img';
    if (isLoser) className = 'loser-img';
    return (
      <img
        className="thumbnail-img"
        src={`data:image/png;base64,${base64}`}
        alt="Fighter Image"
      />
    );
  }

  if (error) return <div class='net-error'>Error: {error}</div>;
  if (!battleState || !battleState.fighters || battleState.fighters.length < 2) { return (
        <div className='root waiting-screen'>
            <h1>Waiting for Next Match...</h1>
            {timer && <h2>Next Match in: {timer}s</h2>}
        </div>
      );
    }

  return (
    <div className='root-mini'>
      <div className='row-mini'>
        <div className='column-mini'>
          <p className='fighter-name-mini fighter-1'>{battleState.fighters[0].name}</p>
          <div className='fighter-img'>
            {battleState && 
            <ImageViewer base64={battleState.fighters[0].image_file} 
              isWinner={lastWinner && lastWinner === battleState.fighters[0].name}
              isLoser={lastWinner && lastWinner !== battleState.fighters[0].name}
            />} 
          </div>
        </div>

        <div className="column-mini">
            <p className="versus">VS</p>
            <p>IN: {timer}</p>
        </div>

        <div className='column-mini'>
          <p className='fighter-name-mini fighter-2'>{battleState.fighters[1].name}</p>
          <div className='fighter-img'>
            {battleState && 
            <ImageViewer base64={battleState.fighters[1].image_file} 
              isWinner={lastWinner && lastWinner === battleState.fighters[1].name}
              isLoser={lastWinner && lastWinner !== battleState.fighters[1].name}
            />} 
          </div>
        </div>
      </div>
    </div>
  );
}
