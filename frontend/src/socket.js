// Initializes socket connection

import { io } from 'socket.io-client';
import { gzip, ungzip } from 'pako'; // gzip compression library
import { fromByteArray, toByteArray } from 'base64-js';

// EDIT THIS TO CHANGE BETWEEN SERVER DEPLOYMENT AND LOCAL DEV ENVIRONMENT
const API_URL = import.meta.env.VITE_SOCKET_URL || "http://localhost:5000";
// --------------------------------------------------------

const socket = io(
    API_URL,
    {
        transports: ['websocket', 'polling']
    }
);

function encodeImageURL(dataURL) {
    // Takes an image file URL as input, encodes it to base64, then compresses it.
    // Returns a stringified image ready to be sent to the backend

    // Remove the "data:image/png;base64," prefix to get just the Base64 string
    const base64String = dataURL.split(',')[1];

    const compressed = gzip(base64String);  // Run compression
    const result = fromByteArray(compressed); // Stringify for json transmission
    console.log(result);
    return result;
}

function decompressBase64Image(compressedBase64String) {
    // Takes a gzip-compressed base64 string (presumably from a json sent by the backend) and decompresses it.
    // Returns an uncompressed base64 string
    const compressed = toByteArray(compressedBase64String);
    const result = ungzip(compressed, { to: 'string' });
    console.log(result)
    return result;
}

export { socket, API_URL, encodeImageURL, decompressBase64Image };
