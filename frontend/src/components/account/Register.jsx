// registration screen with username input and portrait.
import { useState } from 'react';
import { API_URL, isProfane } from '../../socket';
import DoodleCanvas from '../DoodleCanvas';

export default function Register({ onBack }) {
  const [username, setUsername] = useState("");
  const [portraitData, setPortraitData] = useState(null); 
  const [generatedID, setGeneratedID] = useState(null);
  const [error, setError] = useState("");

  const submitRegister = async () => {
    if (!username || !portraitData) {
      setError("Please draw a portrait and enter a username!");
      return;
    }
    if (isProfane(username)) {
      setError("Please choose a more appropriate username!");
      return;
    }
    try {
      const response = await fetch(`${API_URL}/api/account/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, portrait: portraitData })
      });

      const data = await response.json();

      if (data.status === 'success') {
        setGeneratedID(data.account_id);
        setError("");
      } else {
        setError(data.error || "Registration failed");
      }
    } catch (err) {
      setError("Network error. Is the server running?");
    }
  };

  //succesfull account generation view
  if (generatedID) {
    return (
      <div className="account-container success-view">
        <h1 className="success-header">Account Created!</h1>
        <p>Welcome, <strong>{username}</strong>.</p>
        
        <div className="id-card">
            <h3>Your Login ID</h3>
            <h1 className="id-number">{generatedID}</h1>
            <p className="id-warning">SAVE THIS NUMBER! You will use this to log in!</p>
        </div>
        
        <button className="return-button" onClick={() => window.location.reload()}>Return to Menu</button>
      </div>
    );
  }

  //user account creation form
  return (
    <div className="account-container">
      <h2>Create New Account</h2>
      {error && <p className="error-message">{error}</p>}

      <div className="portrait-section">
        <p>Draw your Portrait:</p>
        <DoodleCanvas 
            isAccount={true} 
            canvWidth={200} 
            canvHeight={200} 
            onCanvasChange={setPortraitData} 
        />
      </div>

      <div className="form-group">
        <input 
          type="text" 
          value={username} 
          onChange={(e) => setUsername(e.target.value.replace(/[^a-zA-Z0-9]/g, ''))} 
          placeholder="Enter username..."
          maxLength={32}
        />
      </div>

      <button className="generate-button" onClick={submitRegister}>Generate ID</button>
      <p className="back-link" onClick={onBack}>Back</p>
    </div>
  );
}