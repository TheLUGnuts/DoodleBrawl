import { useState, useEffect } from 'react';
import './ArenaView.css';
import '../text_decor.css';
import { decompressBase64Image, socket, API_URL } from '../socket';

export default function ArenaView({ battleState, timer, logState, lastWinner, summaryState, introState, user, setUser, matchOdds, currentPool, myBet, setMyBet, payoutWon}) {
  const [isTalking, setIsTalking] = useState(false);
  const [betAmount, setBetAmount] = useState(10);
  const [isBetting, setIsBetting] = useState(false);
  const [crowd, setCrowd] = useState([]);
  const [showAllLogs, setShowAllLogs] = useState(false);

  //jim scribble is speaking
  useEffect(() => {
    if (logState && logState.length > 0) {
      setIsTalking(true);
      const timerId = setTimeout(() => setIsTalking(false), 400);
      return () => clearTimeout(timerId);
    }
  }, [logState]);

  //make a new crowd to populate the bleachers
  useEffect(() => {
    if (battleState && battleState.fighters && battleState.fighters.length === 2) {
      setShowAllLogs(false);
      
      fetch(`${API_URL}/api/crowd`)
        .then(res => res.json())
        .then(data => setCrowd(data))
        .catch(e => console.error("Failed to fetch crowd:", e));
    }
  }, [battleState?.fighters?.[0]?.id]);

  //divide the crowd array in half for the two bleachers
  const leftCrowd = crowd.slice(0, 6);
  const rightCrowd = crowd.slice(6, 12);

  const seatPositions = [
    { top: '15%', left: '10%' },
    { top: '25%', left: '40%' },
    { top: '35%', left: '75%' },
    { top: '55%', left: '15%' },
    { top: '65%', left: '50%' },
    { top: '75%', left: '85%' }
  ];

  const handleBet = (fighterId, fighterName) => {
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
            const odds = matchOdds[fighterId] || 1.1; 
            
            setMyBet({
              fighterId: fighterId,
              fighterName: fighterName,
              payout: Math.floor(betAmount * odds)
            });
        } else {
            alert(response.message);
        }
    });
  };

  if (!battleState || !battleState.fighters || battleState.fighters.length === 0) { return (
      <div className='root waiting-screen'>
          <img className="throbber" src="./RatJohnson.gif"></img>
          <h1>Waiting for Next Match...</h1>
          {timer && <h2>Next Match in: {timer}</h2>}
      </div>
    );
  }

  function ImageViewer({ compressedBase64, isWinner, isLoser, titles }) {
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
        {titles && titles.map((title, index) => (
          <img 
            key={index}
            className="champ-badge" 
            src="./champ.png" 
            alt="Champion Badge" 
            title={title}
            style={{
              top: `${6 + (index * 20)}px`,
              left: `${-15 + (index * 15)}px`,
              zIndex: 10 - index
            }}
          />
        ))}
      </div>
    );
  }

  //latest log for immediate display
  const latestLog = logState.length > 0 ? logState[logState.length - 1] : null;

  return (
    <div className='root'>
      <h2>Next match in: {timer}</h2>
      <div className="active-log-banner">
        {lastWinner ? (
          <h2><span className="action-green">WINNER</span>: {lastWinner}</h2>
        ) : latestLog ? (
          <div className="current-action">
            <span className="log-name">{latestLog.actor}</span>
            <div dangerouslySetInnerHTML={{ __html: latestLog.description }} />
          </div>
        ) : (
          <p className='introduction' dangerouslySetInnerHTML={{ __html: introState }} />
        )}
      </div>

      {/* --- NEW: EXPANDABLE LOGS (Only visible after match ends) --- */}
      {lastWinner && (
        <div className="logs-dropdown-section">
          <button className="toggle-logs-btn" onClick={() => setShowAllLogs(!showAllLogs)}>
            {showAllLogs ? "▲ Hide Full Battle Logs ▲" : "▼ Show Full Battle Logs ▼"}
          </button>
          
          {showAllLogs && (
            <div className='logs expanded-logs'>
              <ul>
                {logState.map((log, index) => (
                  <li className='one-log' key={index}>
                    <span className='log-name'>{log.actor}</span>
                    <div dangerouslySetInnerHTML={{ __html: log.description }} />
                  </li>
                ))}
              </ul>
              <p className='summary' dangerouslySetInnerHTML={{ __html: summaryState }} />
            </div>
          )}
        </div>
      )}

      {/* --- ARENA FLOOR (Anchors fighters and bleachers to the bottom) --- */}
      <div className='arena-floor'>
        <div className='row'>
          
          {/* FIGHTER 1 (LEFT) */}
          <div className='column'>
            <div className='stats-header'>
              <p className='fighter-name fighter-1'>{battleState.fighters[0].name}</p>
              <p>{battleState.fighters[0].titles.length === 0 ? battleState.fighters[0].alignment : ""}</p>
            </div>
            
            <div className='fighter-img' style={{ position: 'relative' }}>
              <div className="bleachers-container left">
                 <img src="./bleacher.png" className="bleacher-bg" alt="bleachers" />
                 {leftCrowd.map((portrait, i) => seatPositions[i] && (
                    <img key={i} className="crowd-portrait" src={`data:image/webp;base64,${decompressBase64Image(portrait)}`} style={{ ...seatPositions[i], '--random': Math.random() }} alt="crowd member" />
                 ))}
              </div>
              
              {battleState && <ImageViewer compressedBase64={battleState.fighters[0].image_file} isWinner={lastWinner && lastWinner === battleState.fighters[0].name} isLoser={lastWinner && lastWinner !== battleState.fighters[0].name} titles={battleState.fighters[0].titles} />} 
            </div>
            
            <div className='stats-footer'>
              <p>Wins: {battleState.fighters[0].wins} | Losses: {battleState.fighters[0].losses}</p>
            </div>
          </div>

          {/* FIGHTER 2 (RIGHT) */}
          <div className='column'>
            <div className='stats-header'>
              <p className='fighter-name fighter-2'>{battleState.fighters[1].name}</p>
              <p>{battleState.fighters[1].titles.length === 0 ? battleState.fighters[1].alignment : ""}</p>
            </div>
            
            <div className='fighter-img' style={{ position: 'relative' }}>
               <div className="bleachers-container right">
                 <img src="./bleacher.png" className="bleacher-bg flipped" alt="bleachers" />
                 {rightCrowd.map((portrait, i) => seatPositions[i] && (
                    <img key={i} className="crowd-portrait" src={`data:image/webp;base64,${decompressBase64Image(portrait)}`} style={{ top: seatPositions[i].top, right: seatPositions[i].left, '--random': Math.random() }} alt="crowd member" />
                 ))}
              </div>
              
              {battleState && <ImageViewer compressedBase64={battleState.fighters[1].image_file} isWinner={lastWinner && lastWinner === battleState.fighters[1].name} isLoser={lastWinner && lastWinner !== battleState.fighters[1].name} titles={battleState.fighters[1].titles} />} 
            </div>
            
            <div className='stats-footer'>
              <p>Wins: {battleState.fighters[1].wins} | Losses: {battleState.fighters[1].losses}</p>
            </div>
          </div>

        </div>
      </div>
      
      {typeof timer == 'number' && (
        <div className="betting-module">
          <div className="pool-display">
            <h3>Match Prize Pool: <span className="gold-text">${currentPool}</span></h3>
          </div>
          
          {user ? (
            <div className="betting-controls">
              <div className="bet-input-row">
                <label>Wager:</label>
                <input 
                  type="number" 
                  min="1" 
                  max={user.money} 
                  value={betAmount} 
                  onChange={(e) => setBetAmount(e.target.value)} 
                  disabled={myBet !== null}
                /><br/>
              </div>
              <div className="wallet">You have ${user.money}</div>
              <div className="bet-buttons">
                <button 
                  disabled={isBetting || betAmount > user.money || betAmount < 1 || myBet !== null}
                  onClick={() => handleBet(battleState.fighters[0].id, battleState.fighters[0].name)}
                  className="bet-btn p1-bet"
                >
                  {myBet?.fighterId === battleState.fighters[0].id ? "Bet Placed!" : `Bet on ${battleState.fighters[0].name}`} <br/>
                  <small>Pays {matchOdds[battleState.fighters[0].id]}x</small>
                </button>
                
                <button 
                  disabled={isBetting || betAmount > user.money || betAmount < 1 || myBet !== null}
                  onClick={() => handleBet(battleState.fighters[1].id, battleState.fighters[1].name)}
                  className="bet-btn p2-bet"
                >
                  {myBet?.fighterId === battleState.fighters[1].id ? "Bet Placed!" : `Bet on ${battleState.fighters[1].name}`} <br/>
                  <small>Pays {matchOdds[battleState.fighters[1].id]}x</small>
                </button>
              </div>
            </div>
          ) : (
             <p className="login-prompt">Log in from the Account tab to place bets!</p>
          )}
        </div>
      )}

      {/* Jim Scribble Commentator */}
      <div className="commentator-container">
        <img 
          src="./js.png" 
          alt="Jim Scribble" 
          className={`commentator-img ${isTalking ? 'talking' : ''}`} 
        />
      </div>

      {payoutWon > 0 && (
        <div className="confetti-container">
           <h1 className="payout-text">${payoutWon}</h1>
           {[...Array(Math.floor(payoutWon/10))].map((_, i) => (
              <img
                 key={i}
                 src="./cash.png"
                 className="cash-confetti"
                 alt="cash"
                 style={{
                    left: `${Math.random() * 100}vw`,
                    animationDelay: `${Math.random() * 1.2}s`,
                    width: `${40 + Math.random() * 30}px`
                 }}
              />
           ))}
        </div>
      )}
    </div>
  );
}