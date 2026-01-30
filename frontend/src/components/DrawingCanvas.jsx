import React, { useRef, useState, useEffect } from 'react';

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

  const handleExportPNG = () => {
    const canvas = canvasRef.current;
    const image = canvas.toDataURL('image/png');
    
    const link = document.createElement('a');
    link.href = image;
    link.download = `drawing-${Date.now()}.png`;
    link.click();
  };

  const colors = ['#000000', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '1rem', maxWidth: '800px', margin: '0 auto' }}>
      {/* Toolbar */}
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', padding: '1rem', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        {/* Color Palette */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span style={{ fontSize: '14px', fontWeight: '500' }}>Color:</span>
          {colors.map(color => (
            <button
              key={color}
              onClick={() => {
                setStrokeColor(color);
                setEraseMode(false);
              }}
              style={{
                width: '32px',
                height: '32px',
                backgroundColor: color,
                border: strokeColor === color && !eraseMode ? '3px solid #333' : '1px solid #ccc',
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'transform 0.1s',
              }}
              onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.9)'}
              onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
            />
          ))}
        </div>

        {/* Stroke Width */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <label style={{ fontSize: '14px', fontWeight: '500' }}>Size:</label>
          <input
            type="range"
            min="1"
            max="20"
            value={strokeWidth}
            onChange={(e) => setStrokeWidth(Number(e.target.value))}
            style={{ width: '100px' }}
          />
          <span style={{ fontSize: '14px', width: '30px' }}>{strokeWidth}px</span>
        </div>

        {/* Tools */}
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => setEraseMode(!eraseMode)}
            style={{
              padding: '8px 16px',
              backgroundColor: eraseMode ? '#ff6b6b' : '#fff',
              border: '1px solid #ccc',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
            }}
          >
            {eraseMode ? '✓ Eraser' : 'Eraser'}
          </button>
          <button 
            onClick={handleUndo} 
            disabled={historyStep <= 0}
            style={{ ...buttonStyle, opacity: historyStep <= 0 ? 0.5 : 1 }}
          >
            Undo
          </button>
          <button 
            onClick={handleRedo} 
            disabled={historyStep >= history.length - 1}
            style={{ ...buttonStyle, opacity: historyStep >= history.length - 1 ? 0.5 : 1 }}
          >
            Redo
          </button>
          <button onClick={handleClear} style={{ ...buttonStyle, backgroundColor: '#ff6b6b', color: 'white', border: 'none' }}>Clear</button>
          <button onClick={handleExportPNG} style={{ ...buttonStyle, backgroundColor: '#4CAF50', color: 'white', border: 'none' }}>Export PNG</button>
        </div>
      </div>

      {/* Canvas */}
      <div style={{ border: '2px solid #ddd', borderRadius: '8px', overflow: 'hidden', backgroundColor: 'white' }}>
        <canvas
          ref={canvasRef}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
          style={{
            display: 'block',
            width: '100%',
            height: '600px',
            touchAction: 'none',
            cursor: eraseMode ? 'crosshair' : 'crosshair',
          }}
        />
      </div>
    </div>
  );
};

const buttonStyle = {
  padding: '8px 16px',
  backgroundColor: '#fff',
  border: '1px solid #ccc',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '14px',
  fontWeight: '500',
};

export default DrawingCanvas;
