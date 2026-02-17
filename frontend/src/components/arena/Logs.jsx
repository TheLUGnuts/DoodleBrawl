import './Logs.css'
export default function Logs ({showAllLogs, setShowAllLogs, logState}) {
    return (
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
            </div>
          )}
        </div>
    );
}