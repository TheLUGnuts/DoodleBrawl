import { useState } from 'react';
import { socket } from '../../socket';
import { useAlert } from '../Alert';
import './Betting.css';

export default function Betting({ user, setUser, matchOdds, currentPool, myBet, setMyBet, battleState }) {
  const [betAmount, setBetAmount] = useState(10);
  const [isBetting, setIsBetting] = useState(false);

  const handleBet = (fighterId, fighterName) => {
    if (!user) { useAlert("You must be logged in to place a bet!"); return; }
    if (betAmount > user.money) { useAlert("You don't have enough money for that bet!"); return; }
    
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
              totalWagered: response.total_wagered,
              payout: Math.floor(response.total_wagered * odds) 
            });
        } else { useAlert(response.message); }
    });
  };

  return (
    <div key="betting" className="betting-module fade-in-down">
      <div className="pool-display">
        <h3>Match Prize Pool: <span className="gold-text">${currentPool}</span></h3>
      </div>
      {user ? (
        <div className="betting-controls">
          <div className="bet-input-row">
            <label>Wager:</label>
            <input type="number" min="1" max={user.money} value={betAmount} onChange={(e) => setBetAmount(e.target.value)}/><br/>
          </div>
          <div className="wallet">You have ${user.money}</div>
          <div className="bet-buttons">
            <button 
              disabled={isBetting || betAmount > user.money || betAmount < 1 || (myBet && myBet.fighterId !== battleState.fighters[0].id)}
              onClick={() => handleBet(battleState.fighters[0].id, battleState.fighters[0].name)}
              className="bet-btn p1-bet"
            >
              {myBet?.fighterId === battleState.fighters[0].id ? `Add to Bet ($${myBet.totalWagered} total)` : `Bet on ${battleState.fighters[0].name}`} <br/>
              <small>Pays {matchOdds[battleState.teams?.[0].id] || 1.0}x<br/>Prospective Wager Payout: {Math.round(betAmount * matchOdds[battleState.teams?.[0].id])}</small>
            </button>
            
            <button 
              disabled={isBetting || betAmount > user.money || betAmount < 1 || (myBet && myBet.fighterId !== battleState.fighters[1].id)}
              onClick={() => handleBet(battleState.fighters[1].id, battleState.fighters[1].name)}
              className="bet-btn p2-bet"
            >
              {myBet?.fighterId === battleState.fighters[1].id ? `Add to Bet ($${myBet.totalWagered} total)` : `Bet on ${battleState.fighters[1].name}`} <br/>
              <small>Pays {matchOdds[battleState.teams?.[1].id] || 1.0}x<br/>Prospective Wager Payout: {Math.round(betAmount * matchOdds[battleState.teams?.[1].id])}</small>
            </button>
          </div>
        </div>
      ) : ( <p className="login-prompt">Log in from the Account tab to place bets!</p> )}
    </div>
  );
}