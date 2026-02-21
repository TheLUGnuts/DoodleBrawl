// users dashboard they see while logged in
import { useState } from 'react';
import { decompressBase64Image, API_URL, isProfane } from '../../socket';
import './Dashboard.css';
import { useAlert } from '../Alert';

export default function Dashboard({ user, onLogin, onLogout }) {
  const [expandedFighter, setExpandedFighter] = useState(null);
  const [targetTeamName, setTargetTeamName] = useState("");
  const [selectedTeamDropdown, setSelectedTeamDropdown] = useState({});
  const showAlert = useAlert();

  const createNewTeam = async() => {
    try {
      const res = await fetch(`${API_URL}/api/account/create_team`, {method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_id: user.id })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showAlert("Team Created!");
        onLogin(user); //refresh the login to show new team
      }
    } catch (e) { showAlert("Network Error"); }
  };

  //Dragging handlers
  const handleDragStart = (e, fighterId, currentTeamId) => {
    e.dataTransfer.setData("fighterId", fighterId);
    e.dataTransfer.setData("currentTeamId", currentTeamId || "");
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e, targetTeamId) => {
    e.preventDefault();
    const fighterId = e.dataTransfer.getData("fighterId");
    const currentTeam = e.dataTransfer.getData("currentTeam");
    if (currentTeam === targetTeamName) return; 
    executeManagementAction(fighterId, 'team', targetTeamId);
  };

  const executeTeamManagementAction = async() => {
    console.log("Team Management Action Clicked")
  }

  const executeManagementAction = async (fighterId, actionType, team_id = "") => {
    if (actionType === 'retire' && !window.confirm("WARNING: Retiring a fighter is permanent! They will never fight again. Are you sure?")) return;
    if (actionType === 'release' && !window.confirm("WARNING: Releasing a fighter will give up your managerial rights to them! Are you sure?")) return;
    try {
      const res = await fetch(`${API_URL}/api/account/manage_fighter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_id: user.id, fighter_id: fighterId, action: actionType, team_id: team_id })
      });
      const data = await res.json();
      if (data.status === 'success') {
         showAlert("Done!", "success");
         onLogin(user);
      } else { showAlert(data.error, "error"); }
    } catch (e) { showAlert("Network Error", "error"); }
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
          <button className="ctrl-btn push" onClick={() => createNewTeam()}>Create Team</button>
        </div>
      </div>

      <div className="dashboard-lists">
        {/* MANAGED FIGHTERS */}
        <div className="list-section">
          <h3>Managed Fighters</h3>
          <p className="hint-text">Click a fighter to view stats, or drag them to a Team!</p>
          <div className="managed-roster-grid">
            {user.managed_characters && user.managed_characters.length > 0 ? (
              user.managed_characters.map(fighter => (fighter.is_approved ? (
                <div 
                  key={fighter.id} 
                  className={`managed-card ${expandedFighter === fighter.id ? 'expanded' : ''}`}
                  onClick={() => setExpandedFighter(expandedFighter === fighter.id ? null : fighter.id)}
                  draggable 
                  onDragStart={(e) => handleDragStart(e, fighter.id, fighter.team_id)}>
                   <img src={`data:image/webp;base64,${decompressBase64Image(fighter.image_file)}`} alt={fighter.name} draggable="false" />
                   <div className="managed-info">
                     <h4>{fighter.name}</h4>
                     <p className={`status-badge ${fighter.status}`}>{fighter.status}</p>
                     {fighter.team_name && <p className="team-badge">Team: {fighter.team_name}</p>}
                   </div>
                   
                   {expandedFighter === fighter.id &&  (
                     <div className="secret-stats">
                      {expandedFighter === fighter.id && fighter.stats && (
                        <div className="secret-stats">
                          <p><strong>HP:</strong> {fighter.stats.hp || "???"}</p>
                          <p><strong>Power:</strong> {fighter.stats.power || "???"}</p>
                          <p><strong>Agility:</strong> {fighter.stats.agility || "???"}</p>
                          <p><strong>Popularity:</strong> {fighter.popularity}</p>
                          <p><strong>Alignment:</strong> {fighter.alignment}</p>
                        </div>
                        )}
                        <div className="management-panel" onClick={(e) => e.stopPropagation()}>
                           <h5>Management Controls</h5>
                           {fighter.status !== 'retired' && user.teams && user.teams.length > 0 && (
                             <div className="team-assigner">
                               <select 
                                 value={selectedTeamDropdown[fighter.id] || ""}
                                 onChange={(e) => setSelectedTeamDropdown({...selectedTeamDropdown, [fighter.id]: e.target.value})}>
                                 <option value="" disabled>Select Team...</option>
                                 {user.teams.map(t => (
                                     <option key={t.id} value={t.name || t.id}>{t.name || `Team ${t.id}`}</option>
                                 ))}
                               </select>
                               <button 
                                 disabled={!selectedTeamDropdown[fighter.id]}
                                 onClick={() => executeManagementAction(fighter.id, 'team', selectedTeamDropdown[fighter.id])}>
                                 Assign
                               </button>
                             </div>
                           )}
                           {fighter.team_id && (
                               <button className="ctrl-btn release" style={{marginBottom: '5px'}} onClick={() => executeManagementAction(fighter.id, 'team', '')}>Remove from Team</button>
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
            ) : ( <p>You aren't managing any fighters yet!</p> )}
          </div>
        </div>

        {/* TEAMS */}
        <div className="list-section">
          <h3>Teams</h3>
          <div className="list-entries">
            {user.teams.length > 0 ? (user.teams.map((item, index) => (
              <div 
                key={item.id || index} 
                className="team-list-entry dropzone"
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, item.id)}>
                <div className="stats">
                  <b className="character-list-name">{item.name || `Team ${item.id}`}</b>
                  <p>Popularity: {item.popularity}</p>
                  <p>Wins: {item.wins}</p>
                  <p>Losses: {item.losses}</p>
                </div>
                <div className="team-thumbnails">
                  {console.log(item.members)}
                  {item.members && item.members.map((memberId) => {
                     const memberObj = user.managed_characters.find(c => c.id === memberId);
                     if (!memberObj) {
                      return null;
                     } 
                     return (
                         <img key={memberObj.id} src={`data:image/webp;base64,${decompressBase64Image(memberObj.image_file)}`} alt="Member Thumbnail" className="team-member-thumbnail" draggable="false"/>
                     )
                  })}
                </div>
              </div>
            ))) : (<p>No teams found.</p>)}
          </div>
        </div>

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
      </div>

      <button className="logout-button" onClick={onLogout}>Log Out</button>
    </div>
  );
}