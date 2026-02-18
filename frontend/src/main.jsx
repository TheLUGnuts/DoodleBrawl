import { ChakraProvider, defaultSystem } from "@chakra-ui/react"
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AlertProvider } from './components/Alert.jsx'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ChakraProvider value={defaultSystem}>
      <AlertProvider>
        <App />
      </AlertProvider>
    </ChakraProvider>
  </StrictMode>,
)
