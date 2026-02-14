import { useState, useEffect } from 'react';
import './Debug.css'
import { API_URL } from '../socket.js';
import { decompressBase64Image } from '../socket';

export default function Debug() {
  const [editorTab, setEditorTab] = useState('characters');
  const [isLocal, setIsLocal] = useState(false);
  const [characters, setCharacters] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [formData, setFormData] = useState(null);
  const [message, setMessage] = useState("");
  const [showPreview, setShowPreview] = useState("");

  useEffect(() => {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      setIsLocal(true);
    }
    if (editorTab === 'characters') fetchCharacters();
    if (editorTab === 'users') fetchUsers();
  }, [editorTab]);

  const fetchCharacters = async () => {
    try {
      const res = await fetch(`${API_URL}/api/debug/characters`);
      const data = await res.json();
      setCharacters(data);
    } catch (e) {
      console.log(e);
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_URL}/api/debug/users`);
      const data = await res.json();
      setUsers(data);
    } catch (e) {
      console.error("Failed to fetch debug users", e);
    }
  };

  const handleSelect = (item) => {
    setSelectedItem(item);
    setShowPreview(false);
    
    if (editorTab === 'characters') {
      setFormData({
        ...item,
        stats: JSON.stringify(item.stats, null, 2),
        titles: JSON.stringify(item.titles, null, 2)
      });
    } else {
      setFormData({ ...item });
    }
    setMessage("");
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSave = async () => {
    setMessage("Saving character.");
    const payload = { ...formData };
    try {
      payload.stats = JSON.parse(formData.stats);
      payload.titles = JSON.parse(formData.titles);
    } catch (e) {
      setMessage("Error: Invalid JSON format.");
      console.log(e);
      return;
    }
    const endpoint = editorTab === 'characters' 
        ? `${API_URL}/api/debug/character/${selectedItem.id}` 
        : `${API_URL}/api/debug/user/${selectedItem.id}`;

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.status === 'success'){
        setMessage("Database updated.");
        editorTab === 'characters' ? fetchCharacters() : fetchUsers();
      } else {
        setMessage(`Error: ${data.error}`);
      }
    } catch (e) {
      setMessage("Error upating database");
      console.log(e);
    }
  };

  const triggerAction = async (endpoint) => {
    await fetch(`${API_URL}/api/debug/${endpoint}`, {method:'POST'});
  }

  //show the image in the DB editor window
  //FIXME - refer to the `app.py` /api/debug/characters route for more info
  const getPreviewSource = (base64Str) => {
    //console.log(base64Str);
    if (!base64Str) return null;
    try {
      return `data:image/webp;base64,${decompressBase64Image(base64Str)}`;
    } catch (e) {
      return null;
    }
  };

  if (!isLocal) return null;

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
          </ul>
          <button onClick={editorTab === 'characters' ? fetchCharacters : fetchUsers} className="refresh-btn">Refresh List</button>
        </div>

        {/* EDITING WINDOW */}
        <div className="debug-form-pane">
          {!selectedItem ? (
            <p className="placeholder-text">Select an entry from the list to edit its database row.</p>
          ) : (
            <div className="debug-form">
              <div className="form-header">
                <h4>Editing: {editorTab === 'characters' ? selectedItem.name : selectedItem.username}</h4>
                <p className="id-subtext">ID: {selectedItem.id}</p>
                
                <button className="preview-toggle-btn" onClick={() => setShowPreview(!showPreview)}>
                  {showPreview ? "Hide Image Preview" : "Show Image Preview"}
                </button>
                {showPreview && (
                  <div className="preview-box">
                    <img 
                       src={getPreviewSource(editorTab === 'characters' ? formData.image_file : formData.portrait)} 
                       alt="Preview" 
                       onError={(e) => {e.target.style.display='none'; setMessage("Error rendering image. Corrupt Base64.");}}
                    />
                  </div>
                )}
              </div>

              {message && <div className="debug-message">{message}</div>}

              {/* EDITOR FORMS*/}
              {/* CHARACTER FORM*/}
              {editorTab === 'characters' ? (
                <>
                  <div className="form-grid">
                    <label>Name: <input type="text" name="name" value={formData.name || ""} onChange={handleChange} /></label>
                    <label>Alignment: <input type="text" name="alignment" value={formData.alignment || ""} onChange={handleChange} /></label>
                    <label>Popularity: <input type="number" name="popularity" value={formData.popularity || 0} onChange={handleChange} /></label>
                    <label>Personality: <input type="text" name="personality" value={formData.personality || ""} onChange={handleChange} /></label>
                    <label>Wins: <input type="number" name="wins" value={formData.wins || 0} onChange={handleChange} /></label>
                    <label>Losses: <input type="number" name="losses" value={formData.losses || 0} onChange={handleChange} /></label>
                    <label>Creator ID: <input type="text" name="creator_id" value={formData.creator_id || ""} onChange={handleChange} /></label>
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
              ) : (
                <>
                  {/* USER FORM */}
                  <div className="form-grid">
                    <label>Username: <input type="text" name="username" value={formData.username || ""} onChange={handleChange} /></label>
                    <label>Money: <input type="number" name="money" value={formData.money || 0} onChange={handleChange} /></label>
                    <label>Creation Time (Unix): <input type="number" step="0.01" name="creation_time" value={formData.creation_time || 0} onChange={handleChange} /></label>
                    <label>Last Submission (Unix): <input type="number" step="0.01" name="last_submission" value={formData.last_submission || 0} onChange={handleChange} /></label>
                  </div>
                </>
              )}

              <button className="save-btn" onClick={handleSave}>Save Changes to DB</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}