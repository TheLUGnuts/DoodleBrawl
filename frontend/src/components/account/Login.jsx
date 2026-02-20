// logging in functionality
import { useState } from 'react';
import { API_URL } from '../../socket';
import { useAlert } from '../Alert';

export default function Login({ onLogin, onBack }) {
  const [inputID, setInputID] = useState("");
  const [error, setError] = useState("");

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
        if (data.bonus_awarded) useAlert("Daily Login Bonus! You received $200!");
        onLogin(data); 
      } else {
        setError(data.error || "Login Failed");
      }
    } catch (e) {
      setError("Server connection error.");
    }
  };

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
      <p className="back-link" onClick={onBack}>Back</p>
    </div>
  );
}