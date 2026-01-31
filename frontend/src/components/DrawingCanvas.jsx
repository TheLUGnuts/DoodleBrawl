import React, { useRef, useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { socket } from '../socket.js';
import './DrawingCanvas.css';

const DrawingCanvas = () => {
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [strokeColor, setStrokeColor] = useState('#000000');
  const [strokeWidth, setStrokeWidth] = useState(4);
  const [eraseMode, setEraseMode] = useState(false);
  const [history, setHistory] = useState([]);
  const [historyStep, setHistoryStep] = useState(-1);

  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    
    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    // Set initial background
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Save initial state
    saveToHistory();
  }, []);

  const saveToHistory = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const imageData = canvas.toDataURL();
    const newHistory = history.slice(0, historyStep + 1);
    newHistory.push(imageData);
    setHistory(newHistory);
    setHistoryStep(newHistory.length - 1);
  };

  const getCoordinates = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    
    const x = (e.clientX || e.touches?.[0]?.clientX) - rect.left;
    const y = (e.clientY || e.touches?.[0]?.clientY) - rect.top;
    
    return { x, y };
  };

  const startDrawing = (e) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const { x, y } = getCoordinates(e);

    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = strokeWidth;
    ctx.strokeStyle = eraseMode ? 'white' : strokeColor;

    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    e.preventDefault();

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const { x, y } = getCoordinates(e);

    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (isDrawing) {
      setIsDrawing(false);
      saveToHistory();
    }
  };

  const handleClear = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    saveToHistory();
  };

  const handleUndo = () => {
    if (historyStep > 0) {
      const newStep = historyStep - 1;
      setHistoryStep(newStep);
      restoreFromHistory(history[newStep]);
    }
  };

  const handleRedo = () => {
    if (historyStep < history.length - 1) {
      const newStep = historyStep + 1;
      setHistoryStep(newStep);
      restoreFromHistory(history[newStep]);
    }
  };

  const restoreFromHistory = (imageData) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
    };
    img.src = imageData;
  };

  const handleDownloadPNG = () => {
    // Downloads directly to user's computer
    const canvas = canvasRef.current;
    const image = canvas.toDataURL('image/png');
    
    const link = document.createElement('a');
    link.href = image;
    link.download = `drawing-${Date.now()}.png`;
    link.click();
  };

  const getImageBase64 = () => {
    // Returns a base64 string of the canvas image
    // This is used for sending the image over the sockets.
    const canvas = canvasRef.current;
    const dataURL = canvas.toDataURL('image/png'); // "data:image/png;base64,..."
    
    // Remove the "data:image/png;base64," prefix to get just the Base64 string
    const base64String = dataURL.split(',')[1];
    
    return base64String; // Send this via socket
  }

  const sendImageOverSocket = () => {
    // Sends current Canvas image to server
    socket.emit('submit_character', {
      id: uuidv4(),
      imageBase: getImageBase64()}
    );
  }

  const colors = ['#000000', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF'];

  return (
    <div className="drawable-canvas-container">
      {/* Toolbar */}
      <div className="toolbar">
        {/* Color Palette */}
        <div className="color-palette">
          <span className="color-palette-label">Color:</span>
          {colors.map(color => (
            <button
              key={color}
              onClick={() => {
                setStrokeColor(color);
                setEraseMode(false);
              }}
              className={`color-button ${strokeColor === color && !eraseMode ? 'active' : ''}`}
              style={{ backgroundColor: color }}
            />
          ))}
        </div>

        {/* Stroke Width */}
        <div className="stroke-width-control">
          <label className="stroke-width-label">Size:</label>
          <input
            type="range"
            min="1"
            max="20"
            value={strokeWidth}
            onChange={(e) => setStrokeWidth(Number(e.target.value))}
            className="stroke-width-slider"
          />
          <span className="stroke-width-value">{strokeWidth}px</span>
        </div>

        {/* Tools */}
        <div className="tools">
          <button
            onClick={() => setEraseMode(!eraseMode)}
            className={`tool-button eraser ${eraseMode ? 'active' : ''}`}
          >
            {eraseMode ? 'Eraser' : 'Eraser'}
          </button>
          <button 
            onClick={handleUndo} 
            disabled={historyStep <= 0}
            className="tool-button"
          >
            Undo
          </button>
          <button 
            onClick={handleRedo} 
            disabled={historyStep >= history.length - 1}
            className="tool-button"
          >
            Redo
          </button>
          <button onClick={handleClear} className="tool-button clear">Clear</button>
          <button onClick={handleDownloadPNG} className="tool-button export">Export PNG</button>
          <button onClick={sendImageOverSocket} className="tool-button submit">Submit to Server</button>
        </div>
      </div>

      {/* Canvas */}
      <div className="canvas-wrapper">
        <canvas
          ref={canvasRef}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
          className="drawing-canvas"
        />
      </div>
    </div>
  );
};

export default DrawingCanvas;
