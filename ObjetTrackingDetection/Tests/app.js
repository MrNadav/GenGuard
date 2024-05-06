let model;

// Load the COCO-SSD model
async function loadModel() {
    model = await cocoSsd.load();
    console.log('Model loaded');
    // Start processing once the model is loaded
    setInterval(processImage, 1000); // Adjust the interval as needed
}

// Function to process the image
async function processImage() {
    const webcamElement = document.getElementById('webcam');
    if (!model || !webcamElement) {
        console.log('Model not loaded or webcam element not found');
        return;
    }

    try {
        const predictions = await model.detect(webcamElement);
        console.log(predictions);
        drawPredictions(predictions);
    } catch (error) {
        console.error(error);
    }
}

// Function to draw the predictions on the canvas
// Assuming a simplistic approach where the object's size in pixels inversely correlates with distance
function calculateDistance(width, height) {
    // Placeholder for a simple distance calculation
    // The larger the object appears, the closer it is
    // This calculation needs to be calibrated for your use case
    const knownWidth = 20; // The known width of the object in some unit (e.g., cm)
    const focalLength = 500; // Example focal length - this should be calibrated
    const perceivedWidth = width; // The width of the object in pixels in the image

    // Using a simplistic formula for demonstration
    // distance = (knownWidth * focalLength) / perceivedWidth
    // This formula assumes you have calibrated your camera to find the focal length
    // and you know the actual width of the object
    const distance = (knownWidth * focalLength) / perceivedWidth;

    return distance;
}

// Modify the drawPredictions function to include distance calculation and display
function drawPredictions(predictions) {
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    predictions.forEach(prediction => {
        // Draw the bounding box
        ctx.strokeStyle = '#00FFFF';
        ctx.lineWidth = 4;
        ctx.strokeRect(...prediction.bbox);

        // Calculate and display distance
        const distance = calculateDistance(prediction.bbox[2], prediction.bbox[3]); // Width and Height
        const distanceText = `Distance: ${distance.toFixed(2)} units`;

        // Draw the label background
        ctx.fillStyle = '#00FFFF';
        const x = prediction.bbox[0];
        const y = prediction.bbox[1];
        const width = ctx.measureText(prediction.class + distanceText).width;
        const height = parseInt(ctx.font, 10);
        ctx.fillRect(x, y - height * 2 - 10, width + 10, height * 2 + 10); // Adjust the box size

        // Draw the label text
        ctx.fillStyle = '#000000';
        ctx.fillText(prediction.class, x, y - 5); // Slightly adjust position for visibility
        ctx.fillText(distanceText, x, y + height - 5); // Display distance below the class label
    });
}

// Load the model and start processing
loadModel().catch(console.error);
