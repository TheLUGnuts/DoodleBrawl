import { useState, useEffect } from 'react';
import './Debug.css'
import { API_URL, decompressBase64Image } from '../socket';

export default function Debug({user}) {
  const [editorTab, setEditorTab] = useState('characters');
  const [characters, setCharacters] = useState([]);
  const [users, setUsers] = useState([]);
  const [matches, setMatches] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [formData, setFormData] = useState(null);
  const [message, setMessage] = useState("");
  const [showPreview, setShowPreview] = useState("");

  const typeMap = { characters: 'character', users: 'user', matches: 'match' };

  useEffect(() => {
    if (editorTab === 'characters') fetchCharacters();
    if (editorTab === 'users') fetchUsers();
    if (editorTab === 'matches') fetchMatches();
  }, [editorTab]);

  const fetchCharacters = async () => { 
    const res = await fetch(`${API_URL}/api/debug/characters`, { headers: { 'X-User-ID': user?.id || '' } });
    setCharacters(await res.json());
  };
  const fetchUsers = async () => {  
    const res = await fetch(`${API_URL}/api/debug/users`, { headers: { 'X-User-ID': user?.id || '' } });
    setUsers(await res.json());
  };
  
  //fetch match history
  const fetchMatches = async () => {
    try {
      const res = await fetch(`${API_URL}/api/debug/matches`, { headers: { 'X-User-ID': user?.id || '' } });
      setMatches(await res.json());
    } catch (e) { console.error(e); }
  };

  const handleSelect = (item) => {
    setSelectedItem(item);
    setShowPreview(false);
    
    if (editorTab === 'characters') {
      setFormData({ ...item, stats: JSON.stringify(item.stats, null, 2), titles: JSON.stringify(item.titles, null, 2) });
    } else if (editorTab === 'matches') {
      setFormData({ ...item, match_data: JSON.stringify(item.match_data, null, 2) });
    } else {
      setFormData({ ...item });
    }
    setMessage("");
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSave = async () => {
    setMessage("Saving to DB...");
    const payload = { ...formData };
    
    try {
        if (editorTab === 'characters') {
          payload.stats = JSON.parse(formData.stats);
          payload.titles = JSON.parse(formData.titles);
        }
        if (editorTab === 'matches') {
          payload.match_data = JSON.parse(formData.match_data);
        }
    } catch (e) {
        setMessage("Error: Invalid JSON format."); return;
    }
    const endpoint = `${API_URL}/api/debug/${typeMap[editorTab]}/${selectedItem.id}`;
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-ID': user?.id || '' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.status === 'success'){
        setMessage("Database updated.");
        if (editorTab === 'characters') fetchCharacters();
        if (editorTab === 'users') fetchUsers();
        if (editorTab === 'matches') fetchMatches();
      } else { setMessage(`Error: ${data.error}`); }
    } catch (e) { setMessage("Error updating database"); }
  };

  //handle deletions from the DB
  const handleDelete = async () => {
    if(!window.confirm("WARNING: Are you sure you want to permanently delete this row? This cannot be undone!")) return;
    
    setMessage("Deleting row...");
    const endpoint = `${API_URL}/api/debug/${typeMap[editorTab]}/${selectedItem.id}`;
    try {
      const res = await fetch(endpoint, {
        method: 'DELETE',
        headers: { 'X-User-ID': user?.id || '' }
      });
      const data = await res.json();
      if (data.status === 'success'){
        setMessage("Row deleted.");
        setSelectedItem(null);
        if (editorTab === 'characters') fetchCharacters();
        if (editorTab === 'users') fetchUsers();
        if (editorTab === 'matches') fetchMatches();
      } else { setMessage(`Error: ${data.error}`); }
    } catch (e) { setMessage("Error deleting row."); }
  };

  const triggerAction = async (endpoint) => {
    await fetch(`${API_URL}/api/debug/${endpoint}`, { method: 'POST', headers: { 'X-User-ID': user?.id || '' }});
  };

  const getPreviewSource = (base64Str) => {
    if (!base64Str) return null;
    try { return `data:image/webp;base64,${decompressBase64Image(base64Str)}`; } catch (e) { return null; }
  };

  return (
    <div className="debug-container">
      <h2>Developer Debug Tools</h2>
      
      {/* SERVER CONTROLS */}
      <div className="debug-server-controls">
        <h3>Server Actions</h3>
        <div className="button-group">
            <button onClick={() => triggerAction('skip')}>Skip Timer to 5s</button>
            <button onClick={() => triggerAction('rematch')}>New Matchup</button>
            <button onClick={() => triggerAction('freeze')}>Toggle Timer Freeze</button>
            <button onClick={() => triggerAction('randomize_alignments')}>Randomize Alignments</button>
            <button onClick={() => triggerAction('test_actions')}>Mock UI Animations</button>
        </div>
      </div>

      <hr />

      {/* DB EDITOR */}
      <h3>Database Editor</h3>
      <div className="debug-editor-layout">
        
        {/* ITEM LISTS */}
        <div className="debug-roster-list">
          <div className="editor-tabs">
            <button className={editorTab === 'characters' ? 'active' : ''} onClick={() => {setEditorTab('characters'); setSelectedItem(null);}}>Characters</button>
            <button className={editorTab === 'users' ? 'active' : ''} onClick={() => {setEditorTab('users'); setSelectedItem(null);}}>Users</button>
            <button className={editorTab === 'matches' ? 'active' : ''} onClick={() => {setEditorTab('matches'); setSelectedItem(null);}}>Matches</button>
          </div>
          <ul>
            {editorTab === 'characters' && characters.map(char => (
              <li key={char.id} className={selectedItem?.id === char.id ? 'selected' : ''} onClick={() => handleSelect(char)}>
                {char.name} {!char.is_approved && "(Unapproved)"}
              </li>
            ))}
            {editorTab === 'users' && users.map(u => (
              <li key={u.id} className={selectedItem?.id === u.id ? 'selected' : ''} onClick={() => handleSelect(u)}>
                {u.username}
              </li>
            ))}
            {editorTab === 'matches' && matches.map(m => (
              <li key={m.id} className={selectedItem?.id === m.id ? 'selected' : ''} onClick={() => handleSelect(m)}>
                Match #{m.id} ({m.winner_name} wins)
              </li>
            ))}
          </ul>
          <button onClick={() => { if(editorTab==='characters') fetchCharacters(); if(editorTab==='users') fetchUsers(); if(editorTab==='matches') fetchMatches(); }} className="refresh-btn">Refresh List</button>
        </div>

        {/* EDITING WINDOW */}
        <div className="debug-form-pane">
          {!selectedItem ? (
            <p className="placeholder-text">Select an entry from the list to edit its database row.</p>
          ) : (
            <div className="debug-form">
              <div className="form-header">
                <h4>Editing: {editorTab === 'characters' ? selectedItem.name : editorTab === 'users' ? selectedItem.username : `Match #${selectedItem.id}`}</h4>
                <p className="id-subtext">ID: {selectedItem.id}</p>
                
                {editorTab !== 'matches' && (
                  <button className="preview-toggle-btn" onClick={() => setShowPreview(!showPreview)}>
                    {showPreview ? "Hide Image Preview" : "Show Image Preview"}
                  </button>
                )}
                {showPreview && editorTab !== 'matches' && (
                  <div className="preview-box">
                    <img src={getPreviewSource(editorTab === 'characters' ? formData.image_file : formData.portrait)} alt="Preview" onError={(e) => {e.target.style.display='none'; setMessage("Error rendering image. Corrupt Base64.");}} />
                  </div>
                )}
              </div>

              {message && <div className="debug-message">{message}</div>}

              {/* EDITOR FORMS*/}
              {editorTab === 'characters' ? (
                <>
                  <div className="form-grid">
                    <label>Name: <input type="text" name="name" value={formData.name || ""} onChange={handleChange} /></label>
                    <label>Alignment: <input type="text" name="alignment" value={formData.alignment || ""} onChange={handleChange} /></label>
                    <label>Popularity: <input type="number" name="popularity" value={formData.popularity || 0} onChange={handleChange} /></label>
                    <label>Personality: <input type="text" name="personality" value={formData.personality || ""} onChange={handleChange} /></label>
                    <label>Wins: <input type="number" name="wins" value={formData.wins || 0} onChange={handleChange} /></label>
                    <label>Losses: <input type="number" name="losses" value={formData.losses || 0} onChange={handleChange} /></label>
                    <label>Status: <input type="text" name="status" value={formData.status || ""} onChange={handleChange} /></label>
                    <label>Team: <input type="text" name="status" value={formData.team_name || ""} onChange={handleChange} /></label>
                    <label>Creator ID: <input type="text" name="creator_id" value={formData.creator_id || ""} onChange={handleChange} /></label>
                    <label>Manager ID: <input type="text" name="manager_id" value={formData.manager_id || ""} onChange={handleChange} /></label>
                    <label>Creation Time (Unix): <input type="number" step="0.01" name="creation_time" value={formData.creation_time || 0} onChange={handleChange} /></label>
                  </div>
                  
                  <label className="checkbox-label">
                    <input type="checkbox" name="is_approved" checked={formData.is_approved} onChange={handleChange} />
                    Approved for Battle
                  </label>

                  <label className="full-width">
                    Description:
                    <textarea name="description" value={formData.description} onChange={handleChange} rows="3" />
                  </label>

                  <div className="json-editors">
                    <label>Stats (JSON):<textarea name="stats" value={formData.stats} onChange={handleChange} rows="6" className="code-font" /></label>
                    <label>Titles (JSON Array):<textarea name="titles" value={formData.titles} onChange={handleChange} rows="4" className="code-font" /></label>
                  </div>
                </>
              ) : editorTab === 'users' ? (
                <>
                  {/* USER FORM */}
                  <div className="form-grid">
                    <label>Username: <input type="text" name="username" value={formData.username || ""} onChange={handleChange} /></label>
                    <label>Money: <input type="number" name="money" value={formData.money || 0} onChange={handleChange} /></label>
                    <label>Creation Time (Unix): <input type="number" step="0.01" name="creation_time" value={formData.creation_time || 0} onChange={handleChange} /></label>
                    <label>Last Bonus (Unix): <input type="number" step="0.01" name="last_login_bonus" value={formData.last_login_bonus || 0} onChange={handleChange} /></label>
                    <label>Last Submission (Unix): <input type="number" step="0.01" name="last_submission" value={formData.last_submission || 0} onChange={handleChange} /></label>
                  </div>
                </>
              ) : (
                <>
                  {/* MATCH FORM */}
                  <div className="form-grid">
                    <label>Match Type: <input type="text" name="match_type" value={formData.match_type || ""} onChange={handleChange} /></label>
                    <label>Winner Name: <input type="text" name="winner_name" value={formData.winner_name || ""} onChange={handleChange} /></label>
                    <label>Winner ID: <input type="text" name="winner_id" value={formData.winner_id || ""} onChange={handleChange} /></label>
                    <label>Title Exchanged: <input type="text" name="title_exchanged" value={formData.title_exchanged || ""} onChange={handleChange} /></label>
                  </div>
                  
                  <label className="checkbox-label">
                    <input type="checkbox" name="is_title_bout" checked={formData.is_title_bout || false} onChange={handleChange} />
                    Is Title Bout
                  </label>
          
                  <label className="full-width">
                    Summary:
                    <textarea name="summary" value={formData.summary || ""} onChange={handleChange} rows="3" />
                  </label>
          
                  <div className="json-editors">
                    <label>Match Data (JSON):<textarea name="match_data" value={formData.match_data || "{}"} onChange={handleChange} rows="6" className="code-font" /></label>
                  </div>
                </>
              )}

              {/* ACTION BUTTONS */}
              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button className="save-btn" onClick={handleSave}>Save Changes to DB</button>
                <button className="delete-btn" onClick={handleDelete}>Delete Row</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}