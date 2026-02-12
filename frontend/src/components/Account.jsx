// Account.jsx
import { useState, useRef } from 'react';
import DoodleCanvas from '../components/DoodleCanvas';
import { API_URL } from '../socket';

export default function Account() {
  const [username, setUsername] = useState("");
  const [generatedID, setGeneratedID] = useState(null);
  const [portraitData, setPortraitData] = useState(null); // Stores base64
  const [error, setError] = useState("");

  const handleCapture = (base64Image) => {
    setPortraitData(base64Image);
  };

  const handleSubmit = async () => {
    console.log(username);
    console.log(portraitData);
    if (!username || !portraitData) {
      setError("Please draw a portrait and enter a username!");
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/account/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username,
          portrait: portraitData
        })
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
      console.error(err);
    }
  };

  if (generatedID) {
    return (
      <div className="account-container" style={{textAlign: 'center', padding: '20px'}}>
        <h1 style={{color: '#4CAF50'}}>Account Created!</h1>
        <p>Welcome, <strong>{username}</strong>.</p>
        
        <div className="id-card" style={{
            border: '2px dashed gold', 
            padding: '20px', 
            margin: '20px auto',
            maxWidth: '400px',
            background: '#333'
        }}>
            <h3>Your Login ID</h3>
            <h1 style={{fontFamily: 'monospace', letterSpacing: '2px', color: 'white'}}>
                {generatedID}
            </h1>
            <p style={{color: '#aaa', fontSize: '0.9em'}}>
                SAVE THIS NUMBER. It is the only way to log in.
            </p>
        </div>
        
        <button onClick={() => window.location.reload()}>Return to Menu</button>
      </div>
    );
  }

  // REGISTRATION FORM
  return (
    <div className="account-container">
      <h2>Create New Account</h2>
      {error && <p className="error" style={{color: 'red'}}>{error}</p>}
      
      <div className="form-group">
        <label>Username:</label>
        <input 
          type="text" 
          value={username} 
          onChange={(e) => setUsername(e.target.value)} 
          placeholder="Create a username"
          maxLength="16"
        />
      </div>

      <div className="portrait-section" style={{marginTop: '20px'}}>
        <p>Draw your Trainer ID Portrait:</p>
        <DoodleCanvas onCanvasChange={handleCapture} width={200} height={200}/>
      </div>

      <button 
        onClick={handleSubmit}
        style={{marginTop: '20px', padding: '10px 20px', fontSize: '1.2em', cursor: 'pointer'}}
      >
        Generate ID
      </button>
    </div>
  );
}