import { useState, memo } from 'react';
import { decompressBase64Image } from '../../socket';
import Betting from './Betting';
import Commentator from './Commentator';
import Payout from './Payout';
import Logs from './Logs';
import './ArenaView.css';
import '../../text_decor.css';

//grabs a creators portrait
const CreatorPortrait = memo(function CreatorPortrait({ fighter, align, onProfileClick }) {
  console.log(fighter.creator_name);
  //unknown has no portrait
  if (!fighter.creator_name || fighter.creator_name === "Unknown" || !fighter.creator_portrait) return null;

  return (
    <div 
      className={`creator-portrait-container ${align}`} 
      onClick={() => onProfileClick && onProfileClick(fighter.creator_name)}
    >
      <div className="creator-label">
        <span>Manager</span>
        <strong>{fighter.creator_name}</strong>
      </div>
      <img 
        src={`data:image/webp;base64,${decompressBase64Image(fighter.creator_portrait)}`} 
        alt={`${fighter.creator_name}'s portrait`} 
        className="creator-portrait-img"
      />
    </div>
  );
});

const ImageViewer = memo(function ImageViewer({ compressedBase64, titles }) {
  const base64 = decompressBase64Image(compressedBase64);
  return (
    <div className="image-wrapper">
      <img className="fighter-wrap" src={`data:image/webp;base64,${base64}`} alt="Fighter Image" />
      {titles && titles.map((title, index) => (
        <img key={index} className="champ-badge" src="./champ.png" alt="Champion Badge" title={title} style={{ top: `${3 + (index * 8)}px`, left: `${-18 + (index * 5)}px`, zIndex: 2 - index }} />
      ))}
    </div>
  );
});

export default function ArenaView({ battleState, timer, logState, lastWinner, summaryState, introState, user, setUser, matchOdds, currentPool, myBet, setMyBet, payoutWon, onProfileClick}) {
  //controls the collapsable logs
  const [showAllLogs, setShowAllLogs] = useState(false);

  //Match timer display
  if (!battleState || !battleState.fighters || battleState.fighters.length === 0) { return (
      <div className='root waiting-screen'>
          <img className="throbber" src="./RatJohnson.gif"></img>
          <h1>Waiting for Next Match...</h1>
          {timer && <h2>Next Match in: {timer}</h2>}
      </div>
    );
  }

  // Determine who is currently acting for animations
  const latestLog = logState.length > 0 ? logState[logState.length - 1] : null;
  const p0Acting = latestLog && latestLog.actor === battleState.fighters[0].name;
  const p1Acting = latestLog && latestLog.actor === battleState.fighters[1].name;

  //what action are they taking?
  const getActionClass = (isActing) => {
    if (lastWinner) return ''; 
    if (!isActing || !latestLog || !latestLog.action) return '';
    
    switch (latestLog.action.toUpperCase()) {
      case 'ATTACK': return 'action-attack';
      case 'DODGE': return 'action-dodge';
      case 'POWER': return 'action-power';
      case 'RECOVER': return 'action-recover';
      case 'AGILITY': return 'action-agility';
      case 'ACROBATIC': return 'action-agility';
      case 'ULTIMATE': return 'action-ultimate';
      default: return 'action-attack'; 
    }
  };

  //applies winner or loser css
  const getMatchStatusClass = (fighterName) => {
    if (!lastWinner) return '';
    return lastWinner === fighterName ? 'winner-img' : 'loser-img';
  };

  return (
    <div className='root'>
      <h2 className="next-match">Next match in: {timer}</h2>
      <div className='arena-floor'>
        <div className='row'>
          {/* FIGHTER 1 (LEFT) */}
          <div className='column'>
            <CreatorPortrait fighter={battleState.fighters[0]} align="left" onProfileClick={onProfileClick} />
            <div className='stats-header'>
              <p className='fighter-name fighter-1'>{battleState.fighters[0].name}</p>
              <p className={(battleState.fighters[0].alignment.toLowerCase())}>
                {battleState.fighters[0].titles.length !== 0 ? battleState.fighters[0].titles.join(", ") : battleState.fighters[0].alignment}
              </p>
            </div>

            <div 
              className={`fighter-img ${getActionClass(p0Acting)} ${getMatchStatusClass(battleState.fighters[0].name)}`} 
              key={p0Acting && !lastWinner ? latestLog.description : 'idle-1'}
              style={{ position: 'relative' }}
            >
              {battleState && <ImageViewer compressedBase64={battleState.fighters[0].image_file} titles={battleState.fighters[0].titles} />} 
            </div>

            <div className='stats-footer'>
              <p>Wins: {battleState.fighters[0].wins} | Losses: {battleState.fighters[0].losses}</p>
            </div>
          </div>

          {/* FIGHTER 2 (RIGHT) */}
          <div className='column'>
            <CreatorPortrait fighter={battleState.fighters[1]} align="right" onProfileClick={onProfileClick} />
            <div className='stats-header'>
              <p className='fighter-name fighter-2'>{battleState.fighters[1].name}</p>
              <p className={(battleState.fighters[1].alignment.toLowerCase())}>
                {battleState.fighters[1].titles.length !== 0 ? battleState.fighters[1].titles.join(", ") : battleState.fighters[1].alignment}
              </p>
            </div>

            <div 
              className={`fighter-img ${getActionClass(p1Acting)} ${getMatchStatusClass(battleState.fighters[1].name)}`} 
              key={p1Acting && !lastWinner ? latestLog.description : 'idle-2'}
              style={{ position: 'relative' }}
            >
              {battleState && <ImageViewer compressedBase64={battleState.fighters[1].image_file} titles={battleState.fighters[1].titles} />} 
            </div>

            <div className='stats-footer'>
              <p>Wins: {battleState.fighters[1].wins} | Losses: {battleState.fighters[1].losses}</p>
            </div>
          </div>
        </div>
      </div>

      {/* NONMATCH AREA BETTING/COMMENTATOR */}
      <div className="pre-match-area">
        {typeof timer == 'number' ? (
          <Betting 
            user={user} 
            setUser={setUser} 
            matchOdds={matchOdds} 
            currentPool={currentPool} 
            myBet={myBet} 
            setMyBet={setMyBet} 
            battleState={battleState} 
          />
        ) : (
          <Commentator logState={logState} />
        )}
      </div>

      {/* ANIMATED DIALOGUE BOX BANNER */}
      <div className="">
        {lastWinner ? (
          <div key="winner-screen" className="winner-reveal">
            <h2><span className="action-green">WINNER</span>: {lastWinner}</h2>
            <div dangerouslySetInnerHTML={{ __html: summaryState }} />
          </div>
        ) : latestLog ? (
          <div key={latestLog.description} className="current-action dialogue-pop">
            <span className="log-name">{latestLog.actor}</span>
            <div dangerouslySetInnerHTML={{ __html: latestLog.description }} />
          </div>
        ) : (
          <p key="intro-text" className='introduction dialogue-pop' dangerouslySetInnerHTML={{ __html: introState }} />
        )}
      </div>

      {/* BATTLE LOGS */}
      {lastWinner && (<Logs showAllLogs={showAllLogs} setShowAllLogs={setShowAllLogs} logState={logState}/>)}
      {/* PAYOUT EFFECT */}
      {payoutWon > 0 && (<Payout payoutWon={payoutWon}/>)}
      </div>
  );
}