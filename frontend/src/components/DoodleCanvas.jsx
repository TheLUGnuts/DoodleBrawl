import React, { useRef, useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { socket, encodeImageURL } from '../socket.js';
import './DoodleCanvas.css';

const DoodleCanvas = () => {
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [strokeColor, setStrokeColor] = useState('#000000');
  const [strokeWidth, setStrokeWidth] = useState(4);
  const [activeTool, setActiveTool] = useState("brush") //this will replace "eraseMode" and "fillMode" with just an active tool const
  const [history, setHistory] = useState([]);
  const [historyStep, setHistoryStep] = useState(-1);
  const [drawingName, setDrawingName] = useState("");

  // localStorage item names
  // This is just to avoid any unfortunate index mismatches between the set/get methods
  const storageCanvas = "storageCanvas";

  function saveToStorage() {
    // Saves canvas information to the browser's local storage
    const canvasImageData = canvasRef.current.toDataURL();
    localStorage.setItem(storageCanvas, canvasImageData);
  }

  function loadFromStorage() {
    // Loads canvas information from the browser's local storage
    const savedImageData = localStorage.getItem(storageCanvas);
    
    if (!savedImageData) return; // No saved data
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
      saveToHistory(); // Save loaded state to history
    };
    
    img.src = savedImageData;
  }

  const saveToHistory = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const imageData = canvas.toDataURL();
    const newHistory = history.slice(0, historyStep + 1);
    newHistory.push(imageData);
    setHistory(newHistory);
    setHistoryStep(newHistory.length - 1);
  };


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
    
    //handle bucket tool selection
    if (activeTool === 'bucket') {
      paintFill(Math.floor(x), Math.floor(y), strokeColor);
      return;
    }

    if (activeTool === 'picker') {
      pickColor(Math.floor(x), Math.floor(y));
      return;
    }

    //handle brush and eraser
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = strokeWidth;
    //eraser is just a white brush? clever.
    ctx.strokeStyle = activeTool === 'eraser' ? 'white' : strokeColor;
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
    const image = canvas.toDataURL('image/webp');
    
    const link = document.createElement('a');
    link.href = image;
    link.download = `drawing-${Date.now()}.webp`;
    link.click();
  };

  const getImageBase64 = () => {
    // Returns a base64 string of the canvas image
    // This is used for sending the image over the sockets.
    const canvas = canvasRef.current;
    const dataURL = canvas.toDataURL('image/webp'); // "data:image/png;base64,..."
    
    const encodedBase64String = encodeImageURL(dataURL);
    
    return encodedBase64String; // Send this via socket
  }

  //change hex decimals to RGB
  //ai :]
  const hexToRgb = (hex) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16),
      a: 255
    } : null;
  };

  const rgbToHex = (r, g, b) => {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
  };

  const pickColor = (startX, startY) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const imageData = ctx.getImageData(0, 0, width, height);
    const data = imageData.data;
    const getPixelPos = (x, y) => (y * width + x) * 4;
    const startPos = getPixelPos(startX, startY);
    const startR = data[startPos];
    const startG = data[startPos + 1];
    const startB = data[startPos + 2];
    setStrokeColor(rgbToHex(startR, startG, startB));
    setActiveTool("brush");
  }

  // paint bucket logic
  const paintFill = (startX, startY, fillColorHex) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const imageData = ctx.getImageData(0, 0, width, height);
    const data = imageData.data;
    const getPixelPos = (x, y) => (y * width + x) * 4;
    const startPos = getPixelPos(startX, startY);
    const startR = data[startPos];
    const startG = data[startPos + 1];
    const startB = data[startPos + 2];
    const startA = data[startPos + 3];
    const fillRgb = hexToRgb(fillColorHex);
    if (!fillRgb) return;

    //if trying to fill a color with the same color, do nothing
    if (startR === fillRgb.r && startG === fillRgb.g && startB === fillRgb.b && startA === fillRgb.a) return;

    //use a stack to go over all nearby pixels in omnidirection from the starting pixel
    const stack = [[startX, startY]];
    while (stack.length) {
      const [x, y] = stack.pop();
      const pos = getPixelPos(x, y);
      //if the pixel matches the first selected pixel:
      if (x >= 0 && x < width && y >= 0 && y < height &&
          data[pos] === startR && data[pos + 1] === startG && 
          data[pos + 2] === startB && data[pos + 3] === startA) {
        //change it's color
        data[pos] = fillRgb.r;
        data[pos + 1] = fillRgb.g;
        data[pos + 2] = fillRgb.b;
        data[pos + 3] = 255; //full alpha

        //adds the pixels neighbors to the stack to be checked
        stack.push([x + 1, y]);
        stack.push([x - 1, y]);
        stack.push([x, y + 1]);
        stack.push([x, y - 1]);
      }
    }
    //push data and save it to edit history
    ctx.putImageData(imageData, 0, 0);
    saveToHistory();
  };

  const sendImageOverSocket = () => {
    if (drawingName === "") {
      setDrawingName("Joe Mystery");
    }
    // Sends current Canvas image to server
    socket.emit('submit_character', {
      id: uuidv4(),
      imageBase: getImageBase64(),
      name: drawingName}
    );

    // Clear drawing
    setDrawingName("");
    history.length = 0;
    setHistoryStep(-1);
    handleClear();
  }


  const colors = ['#000000', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF'];

  return (
    <div className="drawable-canvas-container">
      {/* Toolbar */}
      <div className="toolbar">
        {/* Color Palette */}
        <div className="color-palette">
          <span className="color-palette-label">Color:</span>
          {/* custom color picker for the pallette*/}
          <input className="custom-color"
            type="color" 
            value={strokeColor} 
            onChange={(e) => {
                setStrokeColor(e.target.value);
            }}
            title="Custom Color"
          />
          {colors.map(color => (
            <button
              key={color}
              onClick={() => {
                setStrokeColor(color);
              }}
              className={`color-button ${strokeColor === color && activeTool !== 'eraser' ? 'active' : ''}`}
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
            onClick={() => setActiveTool('brush')}
            className={`tool-button brush ${activeTool === 'brush' ? 'active' : ''}`}
          >
            Brush
          </button>
          <button
            onClick={() => setActiveTool('bucket')}
            className={`tool-button bucket ${activeTool === 'bucket' ? 'active' : ''}`}
          >
            Bucket
          </button>
          <button
            onClick={() => setActiveTool('picker')}
            className={`tool-button picker ${activeTool === 'picker' ? 'active' : ''}`}
          >
            Color Pick
          </button>
          <button
            onClick={() => setActiveTool('eraser')}
            className={`tool-button eraser ${activeTool === 'eraser' ? 'active' : ''}`}
          >
            Eraser
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
          <button onClick={handleDownloadPNG} className="tool-button export">Download</button>
          <button onClick={sendImageOverSocket} className="tool-button submit">Submit for Battle!</button>
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

export default DoodleCanvas;
