// Initializes socket connection

import { io } from 'socket.io-client'; // socket.io client package
import { gzip, ungzip } from 'pako';   // gzip compression package
import Filter from 'bad-words';        // bad word filter package
import { fromByteArray, toByteArray } from 'base64-js';


// EDIT THIS TO CHANGE BETWEEN SERVER DEPLOYMENT AND LOCAL DEV ENVIRONMENT
const API_URL = import.meta.env.VITE_SOCKET_URL || "http://localhost:5000";
const socket = io(
    API_URL,
    {
        transports: ['websocket', 'polling']
    }
);

//Profanity filter using the "bad-words" package
const profanityFilter = new Filter();
export const isProfane = (text) => {
  if (!text) return false;
  return profanityFilter.isProfane(text);
};

function encodeImageURL(dataURL) {
    // Takes an image file URL as input, encodes it to base64, compresses it, then converts that into base64 again.
    // Returns a stringified image ready to be sent to the backend
    //
    // NOTE: The data URL contains the actual base64 representation of the image used in display.
    // Using fromByteArray, the gzip'd image is converted into base64 again, this time so it can be transmitted easily over JSON.

    // Remove the "data:image/png;base64," prefix from the dataURL to get just the Base64 string
    const base64String = dataURL.split(',')[1];

    const compressed = gzip(base64String);  // Run compression
    const result = fromByteArray(compressed); // Stringify to base64 (again) for json transmission
    return result;
}

function decompressBase64Image(compressedBase64String) {
    // Takes a base64 encoded string of a gzip-compressed base64 image (presumably from a json sent by the backend) and decompresses it.
    // Returns an uncompressed base64 string
    // .
    // NOTE: This reverses encodeImageURL.
    const compressed = toByteArray(compressedBase64String);
    const result = ungzip(compressed, { to: 'string' });
    return result;
}

export { socket, API_URL, encodeImageURL, decompressBase64Image };
