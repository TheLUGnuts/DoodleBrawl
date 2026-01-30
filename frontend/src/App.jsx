import React, { useState, useEffect } from 'react';
import { socket } from './socket';
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import DrawingCanvas from './components/DrawingCanvas'

function App() {
  const [count, setCount] = useState(0)
  const [isConnected, setIsConnected] = useState(socket.connected);
  const [fooEvents, setFooEvents] = useState([]);

  useEffect(() => {
    function onConnect() {
      setIsConnected(true);
    }

    function onDisconnect() {
      setIsConnected(false);
    }

    function onFooEvent(value) {
      setFooEvents(previous => [...previous, value]);
    }

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    socket.on('foo', onFooEvent);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('foo', onFooEvent);
    };
  }, []);

  return (
    <>
      <h1>Doodle Brawl!</h1>
      <div>
        <p>Is Connected: { isConnected }</p>
        <DrawingCanvas />
      </div>
    </>
  )
}

export default App
