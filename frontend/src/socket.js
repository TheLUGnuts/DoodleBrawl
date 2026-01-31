// Initializes socket connection

import { io } from 'socket.io-client';

export const socket = io("http://localhost:5000")
//export const socket = io(undefined, {
//    transports: ['websocket', 'polling']
//});
