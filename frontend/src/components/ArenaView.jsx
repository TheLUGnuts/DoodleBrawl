import './ArenaView.css';
import '../text_decor.css';

export default function ArenaView({ battleState, timer, logState, lastWinner, summaryState, introState}) {

  const checkIsChampion = (status) => {
    return status && status.includes("Champion") && !status.includes("Former");
  };

  const isTitleFight = battleState && battleState.fighters && (
    checkIsChampion(battleState.fighters[0].status) || 
    checkIsChampion(battleState.fighters[1].status)
  );

  const shouldShowBelt = (fighter) => {
    if (lastWinner && isTitleFight) {
      return lastWinner === fighter.name;
    }
    return checkIsChampion(fighter.status);
  };

  function ImageViewer({ base64, isWinner, isLoser, isChampion }) {
    let className = '';
    if (isWinner) className = 'winner-img';
    if (isLoser) className = 'loser-img';
    return (
      <div className="image-wrapper">
        <img
          className={className}
          src={`data:image/png;base64,${base64}`}
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

  if (!battleState || !battleState.fighters || battleState.fighters.length === 0) { return (
        <div className='root waiting-screen'>
            <img className="throbber" src="./RatJohnson.gif"></img>
            <h1>Waiting for Next Match...</h1>
            {timer && <h2>Next Match in: {timer}</h2>}
        </div>
      );
    }

  return (
    <div class='root'>
      <h2>Next match in: {timer}</h2>
      <div class='row'>

        {/* FIGHTER 1*/}
        <div class='column'>
          <p class='fighter-name fighter-1'>{battleState.fighters[0].name}</p>
          <p>{battleState.fighters[0].status ? battleState.fighters[0].status : "Fighter"}</p>
          <div class='fighter-img'>
            {battleState && 
            <ImageViewer base64={battleState.fighters[0].image_file} 
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
          <p>{battleState.fighters[1].status ? battleState.fighters[1].status : "Fighter"}</p>
          <div class='fighter-img'>
            {battleState && 
            <ImageViewer base64={battleState.fighters[1].image_file} 
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
