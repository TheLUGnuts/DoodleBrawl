// users dashboard they see while logged in
import { useState } from 'react';
import { decompressBase64Image, API_URL, isProfane } from '../../socket';
import './Dashboard.css';
import { useAlert } from '../Alert';

export default function Dashboard({ user, onLogin, onLogout }) {
  const [expandedFighter, setExpandedFighter] = useState(null);
  const [teamInput, setTeamInput] = useState("");
  const showAlert = useAlert();

  const executeManagementAction = async (fighterId, actionType, teamName = "") => {
    if (actionType === 'retire' && !window.confirm("WARNING: Retiring a fighter is permanent! They will never fight again. Are you sure?")) return;
    if (actionType === 'release' && !window.confirm("WARNING: Releasing a fighter will give up your managerial rights to them! Are you sure?")) return;

    if (actionType === 'team' && isProfane(teamName)) {
        showAlert("Please choose a more appropriate team name.");
        return;
    }

    try {
      const res = await fetch(`${API_URL}/api/account/manage_fighter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_id: user.id, fighter_id: fighterId, action: actionType, team_name: teamName })
      });
      const data = await res.json();
      if (data.status === 'success') {
         showAlert("Done!");
         onLogin(user); //force App.jsx to refresh
         setTeamInput("");
      } else { showAlert(data.error); }
    } catch (e) { showAlert("Network Error"); }
  };

  const joinDate = new Date(user.creation_time * 1000).toLocaleDateString();
  const portraitSrc = user.portrait ? `data:image/webp;base64,${decompressBase64Image(user.portrait)}` : null;

  return (
    <div className="account-container dashboard">
      <div className="profile-header">
        <div className="profile-pic-container">
           {portraitSrc && <img src={portraitSrc} alt="Profile" className="profile-pic" />}
        </div>
        <div className="profile-info">
          <h1>{user.username}</h1>
          <p>Joined: {joinDate}</p>
          <p className="money">Funds: ${user.money}</p>
          <details className="small-id">
            <summary>ID</summary>
            <p className="small-id">{user.id}</p>
          </details>
        </div>
      </div>

      <div className="dashboard-lists">
        {/* CREATED FIGHTERS */}
        <div className="list-section">
          <h3>Created Fighters</h3>
          <div className="list-entries">
            {user.created_characters.map((item, index) => (
              <div key={item.id || index} className="character-list-entry">
                <div className="info">
                  <div className="stats">
                    <b className="character-list-name">{item.name}</b>
                  </div>
                </div>
                {item.is_approved ? (
                  <img src={`data:image/webp;base64,${decompressBase64Image(item.image_file)}`} alt="Fighter" className="character-list-image"/>
                ) : (
                  <p className="unapproved">Not yet approved</p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* MANAGED FIGHTERS */}
        <div className="list-section">
          <h3>Managed Fighters</h3>
          <p className="hint-text">Click a fighter to view their secret combat stats!</p>
          <div className="managed-roster-grid">
            {user.managed_characters && user.managed_characters.length > 0 ? (
              user.managed_characters.map(fighter => (fighter.is_approved ? (
                <div 
                  key={fighter.id} 
                  className={`managed-card ${expandedFighter === fighter.id ? 'expanded' : ''}`}
                  onClick={() => setExpandedFighter(expandedFighter === fighter.id ? null : fighter.id)}
                >
                   <img src={`data:image/webp;base64,${decompressBase64Image(fighter.image_file)}`} alt={fighter.name} />
                   <div className="managed-info">
                     <h4>{fighter.name}</h4>
                     <p className={`status-badge ${fighter.status}`}>{fighter.status}</p>
                     {fighter.team_name && <p className="team-badge">Team: {fighter.team_name}</p>}
                   </div>
                   
                   {expandedFighter === fighter.id &&  (
                     <div className="secret-stats">
                        <div className="stat-grid">
                            <p><strong>HP:</strong> {fighter.stats?.hp || "???"}</p>
                            <p><strong>Power:</strong> {fighter.stats?.power || "???"}</p>
                            <p><strong>Agility:</strong> {fighter.stats?.agility || "???"}</p>
                            <p><strong>Popularity:</strong> {fighter.popularity}</p>
                            <p><strong>Alignment:</strong> {fighter.alignment}</p>
                        </div>
                        
                        <div className="management-panel" onClick={(e) => e.stopPropagation()}>
                           <h5>Management Controls</h5>
                           {fighter.status !== 'retired' && (
                             <div className="team-assigner">
                               <input type="text" placeholder="Tag Team Name..." value={teamInput} onChange={(e) => setTeamInput(e.target.value)} maxLength={32} />
                               <button onClick={() => executeManagementAction(fighter.id, 'team', teamInput)}>Set Team</button>
                             </div>
                           )}
                           <div className="control-buttons">
                             {fighter.status === 'active' && <button className="ctrl-btn pull" onClick={() => executeManagementAction(fighter.id, 'pull')}>Pull from Roster (Inactive)</button>}
                             {fighter.status === 'inactive' && <button className="ctrl-btn push" onClick={() => executeManagementAction(fighter.id, 'activate')}>Return to Roster (Active)</button>}
                             {fighter.status !== 'retired' && <button className="ctrl-btn release" onClick={() => executeManagementAction(fighter.id, 'release')}>Release to Free Agency</button>}
                             {fighter.status !== 'retired' && <button className="ctrl-btn retire" onClick={() => executeManagementAction(fighter.id, 'retire')}>Force Retirement</button>}
                           </div>
                        </div>
                     </div>
                   )}
                </div>) : ("")
                ))
            ) : (
              <p>You aren't managing any fighters yet!</p>
            )}
          </div>
        </div>
      </div>

      <button className="logout-button" onClick={onLogout}>Log Out</button>
    </div>
  );
}