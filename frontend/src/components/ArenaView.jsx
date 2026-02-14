import { useState, useEffect } from 'react';
import './ArenaView.css';
import '../text_decor.css';
import { socket, decompressBase64Image } from '../socket';

export default function ArenaView({ battleState, timer, logState, lastWinner, summaryState, introState, user, setUser, currentPool, matchOdds}) {
  //jim scribble is speaking
  const [isTalking, setIsTalking] = useState(false);
  //betting stuff
  const [betAmount, setBetAmount] = useState(10);
  const [isBetting, setIsBetting] = useState(false);

  useEffect(() => {
    if (logState && logState.length > 0) {
      setIsTalking(true);
      const timerId = setTimeout(() => setIsTalking(false), 400); // Stop shaking after 400ms
      return () => clearTimeout(timerId);
    }
  }, [logState]);

  const handleBet = (fighterId) => {
    if (!user) {
      alert("You must be logged in to place a bet!");
      return;
    }
    if (betAmount > user.money) {
      alert("You don't have enough money for that bet!");
      return;
    }
    setIsBetting(true);
    socket.emit('place_bet', {
      user_id: user.id,
      fighter_id: fighterId,
      amount: Number(betAmount)
    }, (response) => {
      setIsBetting(false);
      if (response.status === 'success') {
        setUser(prev => ({...prev, money: response.new_balance}));
      } else {
        console.log(response.message);
        alert(response.message);
      }
    });
  };

  const getAlignmentClass = (alignment) => {
    if (!alignment) return 'alignment-neutral';
    const lower = alignment.toLowerCase();
    if (lower === 'good') return 'alignment-good';
    if (lower === 'evil') return 'alignment-evil';
    return 'alignment-neutral';
  };

  if (!battleState || !battleState.fighters || battleState.fighters.length === 0) { return (
      <div className='root waiting-screen'>
          <img className="throbber" src="./RatJohnson.gif"></img>
          <h1>Waiting for Next Match...</h1>
          {timer && <h2>Next Match in: {timer}</h2>}
      </div>
    );
  }

  const hasTitles = (fighter) => fighter.titles && fighter.titles.length > 0;

  const isTitleFight = (
    (hasTitles(battleState.fighters[0])) || 
    (hasTitles(battleState.fighters[1]))
  );

  const shouldShowBelt = (fighter) => {
    if (lastWinner && isTitleFight) {
      return lastWinner === fighter.name;
    }
    return hasTitles(fighter);
  };

  function ImageViewer({ compressedBase64, isWinner, isLoser, isChampion }) {
    let className = '';
    const base64 = decompressBase64Image(compressedBase64);

    if (isWinner) className = 'winner-img';
    if (isLoser) className = 'loser-img';

    return (
      <div className="image-wrapper">
        <img
          className={className}
          src={`data:image/webp;base64,${base64}`}
          alt="Fighter Image"
        />
        {isChampion && 
          <img 
            className="champ-badge" 
            src="./champ.png" 
            alt="Champion Badge" 
          />
        }
      </div>
    );
  }

  return (
    <div class='root'>
      <h2>Next match in: {timer}</h2>
      {logState.length === 0 && battleState.fighters.length === 2 && (
        <div className="betting-module">
          <div className="pool-display">
            <h3>Match Prize Pool: <span className="gold-text">${currentPool}</span></h3>
          </div>
          
          {user ? (
            <div className="betting-controls">
              <div className="bet-input-row">
                <label>Your Wager:</label>
                <input 
                  type="number" 
                  min="1" 
                  max={user.money} 
                  value={betAmount} 
                  onChange={(e) => setBetAmount(e.target.value)} 
                />
                <span className="wallet">Wallet: ${user.money}</span>
              </div>
              
              <div className="bet-buttons">
                <button 
                  disabled={isBetting || betAmount > user.money || betAmount < 1}
                  onClick={() => handleBet(battleState.fighters[0].id)}
                  className="bet-btn p1-bet"
                >
                  Bet on {battleState.fighters[0].name} <br/>
                  <small>Pays {matchOdds[battleState.fighters[0].id]}x</small>
                </button>
                
                <button 
                  disabled={isBetting || betAmount > user.money || betAmount < 1}
                  onClick={() => handleBet(battleState.fighters[1].id)}
                  className="bet-btn p2-bet"
                >
                  Bet on {battleState.fighters[1].name} <br/>
                  <small>Pays {matchOdds[battleState.fighters[1].id]}x</small>
                </button>
              </div>
            </div>
          ) : (
             <p className="login-prompt">Log in from the Account tab to place bets!</p>
          )}
        </div>
      )}
      <div class='row'>

        {/* FIGHTER 1*/}
        <div class='column'>
          <p class='fighter-name fighter-1'>{battleState.fighters[0].name}</p>
          <p className={getAlignmentClass(battleState.fighters[0].alignment)}>
            {hasTitles(battleState.fighters[0]) 
              ? battleState.fighters[0].titles.join(", ") 
              : battleState.fighters[0].alignment}
          </p>
          <div class='fighter-img'>
            {battleState && 
            <ImageViewer compressedBase64={battleState.fighters[0].image_file} 
              isWinner={lastWinner && lastWinner === battleState.fighters[0].name}
              isLoser={lastWinner && lastWinner !== battleState.fighters[0].name}
              isChampion={shouldShowBelt(battleState.fighters[0])}
            />} 
          </div>
          <div class='stats'>
            <p>Fighter Profile: <span dangerouslySetInnerHTML={{ __html: battleState.fighters[0].description }} /></p>
            <p>Wins: {battleState.fighters[0].wins}</p>
            <p>Losses: {battleState.fighters[0].losses}</p>
          </div>
        </div>

        {/* FIGHTER 2*/}
        <div class='column'>
          <p class='fighter-name fighter-2'>{battleState.fighters[1].name}</p>
          <p className={getAlignmentClass(battleState.fighters[1].alignment)}>
            {hasTitles(battleState.fighters[1]) 
              ? battleState.fighters[1].titles.join(", ") 
              : battleState.fighters[1].alignment}
          </p>
          <div class='fighter-img'>
            {battleState && 
            <ImageViewer compressedBase64={battleState.fighters[1].image_file} 
              isWinner={lastWinner && lastWinner === battleState.fighters[1].name}
              isLoser={lastWinner && lastWinner !== battleState.fighters[1].name}
              isChampion={shouldShowBelt(battleState.fighters[1])}
            />} 
          </div>
          <div class='stats'>
            <p>Fighter Profile: <span dangerouslySetInnerHTML={{ __html: battleState.fighters[1].description }} /></p>
            <p>Wins: {battleState.fighters[1].wins}</p>
            <p>Losses: {battleState.fighters[1].losses}</p>
          </div>
        </div>

      </div>
      <div className="commentator-container">
        <img 
          src="./js.png" 
          alt="Jim Scribble" 
          className={`commentator-img ${isTalking ? 'talking' : ''}`} 
        />
      </div>
        <p class='introduction' dangerouslySetInnerHTML={{ __html: introState }} />
        <div class='logs'>
          <ul>
            {logState.map((log, index) => (
              <li class='one-log' key={index}>
                <span class='log-name'>
                  {log.actor}
                </span>
                  <div dangerouslySetInnerHTML={{ __html: log.description }} />
              </li>
            ))}
          </ul>
          {lastWinner && (
            <h2><span class="action-green">WINNER</span>: {lastWinner}</h2>
          )}
          <p class='summary' dangerouslySetInnerHTML={{ __html: summaryState }} />
        </div>
    </div>
  );
}
