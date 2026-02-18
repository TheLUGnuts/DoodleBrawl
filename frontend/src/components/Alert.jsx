import { createContext, useState, useContext } from 'react';
import './Alert.css';
const AlertContext = createContext();

export const useAlert = () => useContext(AlertContext);

export const AlertProvider = ({ children }) => {
  const [alertState, setAlertState] = useState({ isOpen: false, message: '', type: 'info' });

  // type can be 'success', 'error', or 'info'
  const showAlert = (message, type = 'info') => {
    setAlertState({ isOpen: true, message, type });
    
    // close the alert after 6 seconds
    setTimeout(() => {
      setAlertState(prev => ({ ...prev, isOpen: false }));
    }, 6000);
  };

  const closeAlert = () => {
    setAlertState(prev => ({ ...prev, isOpen: false }));
  };

  return (
    <AlertContext.Provider value={showAlert}>
      {children}
      
      {/* UI OVERLAY*/}
      {alertState.isOpen && (
        <div className="custom-alert-overlay" onClick={closeAlert}>
          <div className={`custom-alert-card slide-down ${alertState.type}`} onClick={(e) => e.stopPropagation()}>
            <div className="custom-alert-content">
              <span className="custom-alert-icon">
                {alertState.type === 'error' ? 'ERROR' : alertState.type === 'success' ? 'SUCCESS' : ''}
              </span>
              <p>{alertState.message}</p>
            </div>
            <button className="custom-alert-close" onClick={closeAlert}>✖</button>
          </div>
        </div>
      )}
    </AlertContext.Provider>
  );
};