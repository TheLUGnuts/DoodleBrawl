import { useState, useEffect, memo } from 'react';
import { API_URL, decompressBase64Image } from '../socket';
import './ProfileCard.css';

const ImageViewer = memo(function ImageViewer({ compressedBase64, titles }) {
  const base64 = decompressBase64Image(compressedBase64);
  return (
    <div className="image-wrapper-tiny">
      <img className="fighter-wrap-tiny" src={`data:image/webp;base64,${base64}`} alt="Fighter Image" />
      {titles && titles.map((title, index) => (
        <img key={index} className="champ-badge-tiny" src="./champ.png" alt="Champion Badge" title={title} style={{ top: `${-2 + (index * 8)}px`, left: `${-15 + (index * 5)}px`, zIndex: 2 - index }} />
      ))}
    </div>
  );
});

export default function ProfileCard({ username, onClose }) {
  const [profileData, setProfileData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/api/account/profile/${username}`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setProfileData(data);
        } else {
          setError(data.error || "Failed to load profile.");
        }
      })
      .catch(e => setError("Network error."));
  }, [username]);

  // Close the modal if the user clicks the dark background outside the card
  const handleOverlayClick = (e) => {
    if (e.target.className === 'profile-modal-overlay') onClose();
  };

  if (error) {
    return (
      <div className="profile-modal-overlay" onClick={handleOverlayClick}>
        <div className="profile-card error"><p>{error}</p><button onClick={onClose}>Close</button></div>
      </div>
    );
  }

  if (!profileData) {
    return (
      <div className="profile-modal-overlay">
        <div className="profile-card loading"><img className="throbber" src="./RatJohnson.gif" alt="loading"/></div>
      </div>
    );
  }

  return (
    <div className="profile-modal-overlay" onClick={handleOverlayClick}>
      <div className="profile-card pop-in">
        <button className="close-btn" onClick={onClose}>X</button>
        
        <div className="profile-header">
          {profileData.portrait ? (
             <img className="profile-portrait" src={`data:image/webp;base64,${decompressBase64Image(profileData.portrait)}`} alt="Portrait" />
          ) : (
             <div className="profile-portrait placeholder">?</div>
          )}
        </div>
          <div className="profile-info">
            <h2>{profileData.username}</h2>
            <p className="wallet">Wallet: ${profileData.money}</p>
            <p className="join-date">Joined: {new Date(profileData.creation_time * 1000).toLocaleDateString()}</p>
          </div>
        
        <h3>Managed Fighters ({profileData.characters.length})</h3>
        <div className="profile-roster">
          {profileData.characters.length > 0 ? (
            profileData.characters.map(c => (
              <div key={c.id} className="mini-fighter-card">
                 <ImageViewer compressedBase64={c.image_file} titles={c.titles}/>
                 <div className="mini-fighter-info">
                   <strong>{c.name}</strong>
                   <p className="mini-stats">W: {c.wins} | L: {c.losses}</p>
                 </div>
                 
              </div>
            ))
          ) : (
            <p className="no-fighters">This manager hasn't debuted any fighters yet!</p>
          )}
        </div>
      </div>
    </div>
  );
}