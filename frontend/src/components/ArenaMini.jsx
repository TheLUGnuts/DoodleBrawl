import { useState, useRef } from 'react';
import './ArenaMini.css';
import '../text_decor.css';
import { decompressBase64Image } from '../socket';

export default function ArenaMini({ battleState, timer, lastWinner}) {
  //const [battleState, setBattleState] = useState(defaultBattleState);
  const [error, setError] = useState(null);
  //const [timer, setTimer] = useState(null);
  const timeouts = useRef([]);
  
  function ImageViewer({ compressedBase64, isWinner, isLoser }) {
    let className = '';
    const base64 = decompressBase64Image(compressedBase64);

    if (isWinner) className = 'winner-img-mini';
    if (isLoser) className = 'loser-img-mini';
    return (
      <img
        className="thumbnail-img"
        src={`data:image/webp;base64,${base64}`}
        alt="Fighter Image"
      />
    );
  }

  if (error) return <div class='net-error'>Error: {error}</div>;
  if (!battleState || !battleState.fighters || battleState.fighters.length < 2) { return (
        <div>
            <img className="throbber-mini" src="./RatJohnson.gif"></img>
            <p>Waiting for Next Match...</p>
            {timer && <h2>Next Match in: {timer}s</h2>}
        </div>
      );
    }

  return (
    <div className='root-mini'>
      <div className='row-mini'>
        <div className='column-mini'>
          <p className='fighter-name-mini-left fighter-1'>{battleState.fighters[0].name}</p>
          <div className='fighter-img-mini'>
            {battleState && 
            <ImageViewer compressedBase64={battleState.fighters[0].image_file} 
              isWinner={lastWinner && lastWinner === battleState.fighters[0].name}
              isLoser={lastWinner && lastWinner !== battleState.fighters[0].name}
            />} 
          </div>
        </div>

        <div className="column-mini">
            <p className="versus-mini"><u>VS</u></p>
            <p>{timer}</p>
        </div>

        <div className='column-mini'>
          <p className='fighter-name-mini-right fighter-2'>{battleState.fighters[1].name}</p>
          <div className='fighter-img-mini'>
            {battleState && 
            <ImageViewer compressedBase64={battleState.fighters[1].image_file} 
              isWinner={lastWinner && lastWinner === battleState.fighters[1].name}
              isLoser={lastWinner && lastWinner !== battleState.fighters[1].name}
            />} 
          </div>
        </div>
      </div>
    </div>
  );
}
