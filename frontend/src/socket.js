// Initializes socket connection

import { io } from 'socket.io-client';

// EDIT THIS TO CHANGE BETWEEN SERVER DEPLOYMENT AND LOCAL DEV ENVIRONMENT
const useLocalhost = true;
// --------------------------------------------------------

const socket = io(
    useLocalhost ? 'http://localhost:5000' : undefined,
    {
        transports: ['websocket', 'polling']
    }
);

export { socket, useLocalhost };
