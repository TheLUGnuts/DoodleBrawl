import { useState, useEffect, useRef } from 'react';
import { socket, API_URL } from '../socket.js';
import './ArenaView.css';
import '../text_decor.css';

export default function ArenaView({ battleState, timer, logState, lastWinner, summaryState}) {

  function ImageViewer({ base64, isWinner, isLoser }) {
    let className = '';
    if (isWinner) className = 'winner-img';
    if (isLoser) className = 'loser-img';
    return (
      <img
        className={className}
        src={`data:image/png;base64,${base64}`}
        alt="Fighter Image"
      />
    );
  }

  if (!battleState || !battleState.fighters || battleState.fighters.length < 2) { return (
        <div className='root waiting-screen'>
            <h1>Waiting for Next Match...</h1>
            {timer && <h2>Next Match in: {timer}s</h2>}
        </div>
      );
    }

  return (
    <div class='root'>
      <h2>Next match in: {timer}</h2>
      <div class='row'>

        <div class='column'>
          <p class='fighter-name fighter-1'>{battleState.fighters[0].name}</p>
          <div class='fighter-img'>
            {battleState && 
            <ImageViewer base64={battleState.fighters[0].image_file} 
              isWinner={lastWinner && lastWinner === battleState.fighters[0].name}
              isLoser={lastWinner && lastWinner !== battleState.fighters[0].name}
            />} 
          </div>
          <div class='stats'>
            <p>Fighter Profile: <span dangerouslySetInnerHTML={{ __html: battleState.fighters[0].description }} /></p>
            <p>Wins: {battleState.fighters[0].wins}</p>
            <p>Losses: {battleState.fighters[0].losses}</p>
          </div>
        </div>

        <div class='column'>
          <p class='fighter-name fighter-2'>{battleState.fighters[1].name}</p>
          <div class='fighter-img'>
            {battleState && 
            <ImageViewer base64={battleState.fighters[1].image_file} 
              isWinner={lastWinner && lastWinner === battleState.fighters[1].name}
              isLoser={lastWinner && lastWinner !== battleState.fighters[1].name}
            />} 
          </div>
          <div class='stats'>
            <p>Fighter Profile: <span dangerouslySetInnerHTML={{ __html: battleState.fighters[1].description }} /></p>
            <p>Wins: {battleState.fighters[1].wins}</p>
            <p>Losses: {battleState.fighters[1].losses}</p>
          </div>
        </div>

      </div>
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
