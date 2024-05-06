# GenGuardFrontend
Welcome

const imageUrl = 'http://127.0.0.1:5500/static/test/person.jpg';

fetch(imageUrl).then(response => response.blob()).then(blob => {
    const formData = new FormData();
    
    formData.append('file', blob, 'your_image_file.extension'); 
    
    fetch('http://127.0.0.1:5569/verify-face', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => console.log('Response from server:', data))
        .catch(error => console.error('Error during fetch:', error));
});


fetch
**©GenGuard**