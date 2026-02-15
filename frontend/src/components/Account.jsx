import { useState, useEffect } from 'react';
import DoodleCanvas from '../components/DoodleCanvas';
import { API_URL } from '../socket';
import { decompressBase64Image } from '../socket';
import './Account.css';

export default function Account({user, onLogin, onLogout}) {
  const [view, setView] = useState("select");
  const [username, setUsername] = useState("");
  const [inputID, setInputID] = useState("");
  const [generatedID, setGeneratedID] = useState(null);
  const [portraitData, setPortraitData] = useState(null); 
  const [error, setError] = useState("");

  function ImageViewer({compressedBase64}) {
    // Decodes base64 image from server
    const base64 = decompressBase64Image(compressedBase64);
    return (
      <img
        src={`data:image/webp;base64,${base64}`}
        alt="Fighter Image"
      />
    );
  }

  useEffect(() => {
      
    }, []);
  

  //dashboard view
  if (user) {
    const joinDate = new Date(user.creation_time * 1000).toLocaleDateString();
    
    //decompress the user portrait for display
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
          <div className="list-section">
            <h3>Created Fighters</h3>
            <div className="list-entries">
              {user.created_characters.map((item, index) => (
              <>
                <div key={item.id || index} class="character-list-entry">
                  <div className="info">
                    <div className="stats">
                      <b className="character-list-name">{item.name}</b>
                    </div>
                  </div>
                  {item.is_approved ? <img src={`data:image/webp;base64,${decompressBase64Image(item.image_file)}`} alt="Fighter picture" className="character-list-image"/> : <p className="unapproved">Not yet approved</p>}
                </div>
              </>
            ))}
            </div>
          </div>
          <div className="list-section">
            <h3>Managed Fighters</h3>
            {user.managed_characters && user.managed_characters.length > 0 ? (
              <ul>
                {user.managed_characters.map(char => (
                  <li key={char.id}>{char.name} ({char.wins}W - {char.losses}L)</li>
                ))}
              </ul>
            ) : <p>Coming Soon.</p>}
          </div>
        </div>

        <button className="logout-button" onClick={onLogout}>Log Out</button>
      </div>
    );
  }

  //auth handlers

  //grabs portrait image
  const handleCapture = (base64Image) => {
    setPortraitData(base64Image);
  };

  //logging in with a code.
  const submitLogin = async () => {
    if (!inputID || inputID.length < 16) {
      setError("Please enter a valid 16-digit ID.");
      return;
    }
    try {
      const response = await fetch(`${API_URL}/api/account/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_id: inputID })
      });
      const data = await response.json();
      if (data.status === 'success') {
        if (data.bonus_awarded) {
            alert("Daily Login Bonus! You received $200!");
        }
        onLogin(data); // Pass data up to App.jsx
      } else {
        setError(data.error || "Login Failed");
      }
    } catch (e) {
      console.log(e);
      setError("Server connection error.");
    }
  };

  //generate ID button clicked
  const submitRegister = async () => {
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

  //log in or register screen
  if (view === 'select') {
    return (
      <div className="account-container">
        <p>Log in to manage your fighters or create a new legacy.</p>
        <div className="auth-buttons">
          <button className="big-button login" onClick={() => setView('login')}>
            Log In with ID
          </button>
          <button className="big-button register" onClick={() => setView('register')}>
            Create New Account
          </button>
        </div>
      </div>
    );
  }

  //logging in screen.
  if (view === 'login') {
    return (
      <div className="account-container">
        <h2>Login</h2>
        {error && <p className="error-message">{error}</p>}
        <div className="form-group">
          <input 
            type="text" 
            value={inputID} 
            onChange={(e) => setInputID(e.target.value)} 
            placeholder="Enter your 16-digit ID"
            maxLength="16"
          />
        </div>
        <button className="generate-button" onClick={submitLogin}>Login</button>
        <p className="back-link" onClick={() => {setError(""); setView('select')}}>Back</p>
      </div>
    );
  }

  //if an account was created
  if (generatedID) {
    return (
      <div className="account-container success-view">
        <h1 className="success-header">Account Created!</h1>
        <p>Welcome, <strong>{username}</strong>.</p>
        
        <div className="id-card">
            <h3>Your Login ID</h3>
            <h1 className="id-number">
                {generatedID}
            </h1>
            <p className="id-warning">
                SAVE THIS NUMBER! You will use this to log in!
            </p>
        </div>
        
        <button className="return-button" onClick={() => window.location.reload()}>Return to Menu</button>
      </div>
    );
  }

  //creating an account
  return (
    <div className="account-container">
      <h2>Create New Account</h2>
      {error && <p className="error-message">{error}</p>}

      <div className="portrait-section">
        <p>Draw your Portrait:</p>
        
        {/* Pass isAccount, Dimensions, and the Callback */}
        <DoodleCanvas 
            isAccount={true} 
            canvWidth={200} 
            canvHeight={200} 
            onCanvasChange={handleCapture} 
        />
      </div>

      <div className="form-group">
        <input 
          type="text" 
          value={username} 
          onChange={(e) => setUsername(e.target.value)} 
          placeholder="Username"
          maxLength="16"
        />
      </div>

      <button className="generate-button" onClick={submitRegister}>
        Generate ID
      </button>
    </div>
  );
}