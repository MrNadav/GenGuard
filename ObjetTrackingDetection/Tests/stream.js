const express = require('express');
const app = express();
const PORT = 3001;

// Use dynamic import for node-fetch
let fetch;
const cors = require('cors');
app.use(cors()); // This enables CORS for all routes

import('node-fetch').then(({default: nodeFetch}) => {
    fetch = nodeFetch;
});

// Proxy endpoint
app.get('/stream', async (req, res) => {
    if (!fetch) {
        res.status(500).send('Fetch is not initialized yet.');
        return;
    }
    const espCamStreamUrl = 'http://192.168.238.194/stream';

    try {
        const response = await fetch(espCamStreamUrl);
        // Set the content type to match the ESPCam stream's content type
        const contentType = response.headers.get('Content-Type');
        if (contentType) {
            res.setHeader('Content-Type', contentType);
        }
        response.body.pipe(res);
    } catch (error) {
        console.error(error);
        res.status(500).send('Failed to fetch the ESPCam stream.');
    }
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
