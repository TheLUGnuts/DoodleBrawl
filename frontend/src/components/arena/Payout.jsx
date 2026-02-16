// the payout effect of money confetti. 1 dollar per 10 won.
import "./Payout.css"
export default function Payout({ payoutWon }) {

    return (
        <div className="confetti-container">
           <h1 className="payout-text">${payoutWon}</h1>
           {[...Array(Math.floor(payoutWon/10))].map((_, i) => (
              <img key={i} src="./cash.png" className="cash-confetti" alt="cash" style={{ left: `${Math.random() * 100}vw`, animationDelay: `${Math.random() * 1.2}s`, width: `${40 + Math.random() * 30}px` }} />
           ))}
        </div>
    );
}
