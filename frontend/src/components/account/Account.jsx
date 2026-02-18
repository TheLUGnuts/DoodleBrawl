//Account tab, handles login, registration, and user dashboard.
import { useState } from 'react';
import Dashboard from './Dashboard';
import Login from './Login';
import Register from './Register';
import './Account.css';

export default function Account({ user, onLogin, onLogout }) {
  const [view, setView] = useState("select");

  //if logged in, load the dashboard
  if (user) {
    return <Dashboard user={user} onLogin={onLogin} onLogout={onLogout} />;
  }

  //clicked 'login'
  if (view === 'login') {
    return <Login onLogin={onLogin} onBack={() => setView('select')} />;
  }

  //clicked 'register'
  if (view === 'register') {
    return <Register onBack={() => setView('select')} />;
  }

  //the selection screen.
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