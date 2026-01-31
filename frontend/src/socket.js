// Initializes socket connection

import { io } from 'socket.io-client';

//FIXME
//this is hardcoded to work :)
const URL = 'https://doodle.jfelix.space:5000';

export const socket = io(URL);
