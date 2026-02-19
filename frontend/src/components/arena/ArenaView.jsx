import { useState, memo } from 'react';
import { decompressBase64Image } from '../../socket';
import Betting from './Betting';
import Commentator from './Commentator';
import Payout from './Payout';
import Logs from './Logs';
import './ArenaView.css';
import '../../text_decor.css';

//grabs a managers portrait
const ManagerPortrait = memo(function ManagerPortrait({ fighter, align, onProfileClick }) {
  console.log(fighter.manager_name);
  //unknown has no portrait
  if (!fighter.manager_name || fighter.manager_name === "Unknown" || !fighter.manager_portrait) {
    console.log("Null hit in manager portrait.");
    return null;
  } 

  return (
    <div 
      className={`manager-portrait-container ${align}`} 
      onClick={() => onProfileClick && onProfileClick(fighter.manager_name)}
    >
      <div className="manager-label">
        <span>Manager</span>
        <strong>{fighter.manager_name}</strong>
      </div>
      <img 
        src={`data:image/webp;base64,${decompressBase64Image(fighter.manager_portrait)}`} 
        alt={`${fighter.manager_name}'s portrait`} 
        className="manager-portrait-img"
      />
    </div>
  );
});

const ImageViewer = memo(function ImageViewer({ compressedBase64, titles }) {
  const base64 = decompressBase64Image(compressedBase64);
  console.log(base64);
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
  const [showAllLogs, setShowAllLogs] = useState(false);

  // Match timer display (Check for teams OR fighters)
  if (!battleState || (!battleState.fighters && !battleState.teams)) { return (
      <div className='root waiting-screen'>
          <img className="throbber" src="./RatJohnson.gif"></img>
          <h1>Waiting for Next Match...</h1>
          {timer && <h2>Next Match in: {timer}</h2>}
      </div>
    );
  }

  const latestLog = logState.length > 0 ? logState[logState.length - 1] : null;

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

  const getIsActing = (team) => {
      if (!latestLog || !latestLog.actor) return false;
      if (latestLog.actor.includes(team.name)) return true; // Team combo attack
      return team.members.some(m => latestLog.actor.includes(m.name)); // Individual attack
  };

  const getMatchStatusClass = (fighterName) => {
    if (!lastWinner) return '';
    return lastWinner === fighterName ? 'winner-img' : 'loser-img';
  };

  return (
    <div className='root'>
      <h2 className="next-match">Next match in: {timer}</h2>
      <div className='arena-floor'>
        <div className='row'>
          
          {/* DYNAMICALLY RENDER COLUMNS FOR TEAM 1 AND TEAM 2 */}
          {battleState.teams?.map((team, index) => {
              const isTeamActing = getIsActing(team);
              const isWinner = lastWinner === team.name;
              const isLoser = lastWinner && !isWinner;

              return (
                 <div className='column' key={team.id}>
                    
                    {/* Render Team Name for 2v2s */}
                    {battleState.match_type === '2v2' && <h2 className="team-display-name">{team.name}</h2>}
                    
                    <div className={battleState.match_type === '2v2' ? 'tag-team-container' : ''}>
                       {team.members.map((fighter) => {
                           // Ensure individual fighters animate if they are specifically called out in the log
                           const isFighterActing = latestLog?.actor?.includes(fighter.name) || isTeamActing;
                           
                           return (
                               <div className="fighter-card" key={fighter.id}>
                                   <ManagerPortrait fighter={fighter} align={index === 0 ? "left" : "right"} onProfileClick={onProfileClick} />
                                   
                                   <div className='stats-header'>
                                     <p className={`fighter-name fighter-${index+1}`}>{fighter.name}</p>
                                     <p className={(fighter.alignment.toLowerCase())}>
                                       {fighter.titles.length !== 0 ? fighter.titles.join(", ") : fighter.alignment}
                                     </p>
                                   </div>

                                   <div 
                                     className={`fighter-img ${getActionClass(isFighterActing)} ${isWinner ? 'winner-img' : isLoser ? 'loser-img' : ''}`} 
                                     key={isFighterActing && !lastWinner ? latestLog.description : `idle-${fighter.id}`}
                                     style={{ position: 'relative' }}
                                   >
                                     <ImageViewer compressedBase64={fighter.image_file} titles={fighter.titles} />
                                   </div>

                                   <div className='stats-footer'>
                                     <p>Wins: {fighter.wins} | Losses: {fighter.losses}</p>
                                   </div>
                               </div>
                           );
                       })}
                    </div>

                 </div>
              )
          })}

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