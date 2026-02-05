// Initializes socket connection

import { io } from 'socket.io-client';

// EDIT THIS TO CHANGE BETWEEN SERVER DEPLOYMENT AND LOCAL DEV ENVIRONMENT
const API_URL = import.meta.env.VITE_SOCKET_URL || "http://localhost:5000";
// --------------------------------------------------------

const socket = io(
    API_URL,
    {
        transports: ['websocket', 'polling']
    }
);

export { socket, API_URL };
