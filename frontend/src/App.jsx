import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import DrawingCanvas from './components/DrawingCanvas'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <h1>Doodle Brawl!</h1>
      <div>
        <p>lol</p>
        <DrawingCanvas />
      </div>
    </>
  )
}

export default App
