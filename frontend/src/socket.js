// Initializes socket connection

import { io } from 'socket.io-client';

export const socket = io(undefined, {
    transports: ['websocket', 'polling']
});
