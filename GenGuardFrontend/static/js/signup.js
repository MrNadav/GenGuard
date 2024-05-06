const firebaseConfig = {
  
};
// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Utility functions for validation
function isValidEmail(email) {
    const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    return emailRegex.test(email);
}

function isValidPassword(password) {
    return password.length >= 6;
}

function isValidName(name) {
    return /^[A-Za-z]+$/.test(name) && name.length >= 2; //regex
}

// Real-time validation for the email field
document.getElementById("email").addEventListener("input", function(event) {
    if (isValidEmail(event.target.value)) {
        event.target.classList.add('input-valid');
        event.target.classList.remove('input-invalid');
    } else {
        event.target.classList.add('input-invalid');
        event.target.classList.remove('input-valid');
    }
});

// Real-time validation for the password field
document.getElementById("password").addEventListener("input", function(event) {
    if (isValidPassword(event.target.value)) {
        event.target.classList.add('input-valid');
        event.target.classList.remove('input-invalid');
    } else {
        event.target.classList.add('input-invalid');
        event.target.classList.remove('input-valid');
    }
});

// Real-time validation for the first name field
document.getElementById("first-name").addEventListener("input", function(event) {
    if (isValidName(event.target.value)) {
        event.target.classList.add('input-valid');
        event.target.classList.remove('input-invalid');
    } else {
        event.target.classList.add('input-invalid');
        event.target.classList.remove('input-valid');
    }
});

// Real-time validation for the last name field
document.getElementById("last-name").addEventListener("input", function(event) {
    if (isValidName(event.target.value)) {
        event.target.classList.add('input-valid');
        event.target.classList.remove('input-invalid');
    } else {
        event.target.classList.add('input-invalid');
        event.target.classList.remove('input-valid');
    }
});


// Function to handle face verifications
function verifyFace(photoFile) {
    const formData = new FormData();
    formData.append('file', photoFile);

    return fetch('https://genguard.site/api/verify-face', {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (!response.ok) {
            // If the response is an HTTP error status
            return response.json().then(error => {
                // Expecting error to have a 'detail' field as sent by FastAPI
                throw new Error(error.detail || 'Unknown error');
            });
        }
        return response.json();  // If no error, proceed as normal
    });
}

// Function to create user and upload data
// function createUserAndUploadData(email, password, firstname, lastname, username, photoFile) {
//     divProgress.innerHTML = "COMPLETE, Uploading Details..."
//     // console.log("CREATING AND UPLOADING")
//     firebase.auth().createUserWithEmailAndPassword(email, password)
//         .then((userCredential) => {
//             clearErrorStyles();
//             let user = userCredential.user;
//             let storage = firebase.storage();
//             let storageRef = storage.ref();
//             // console.log("BEFORE RESIZE BLOB")

//             resizeImage(photoFile, 400, 600, (resizedBlob) => {  // maxWidth and maxHeight as needed
//                 // console.log("AFTER RESIZE BLOB")

//                 let photoRef = storageRef.child('user_photos/' + user.uid + '.png');
//                 // console.log("BEFORE UPLOADING BLOB")

//             photoRef.put(photoFile).then((snapshot) => {
//                 // console.log('Uploaded a blob or file!');

//                 // Generate QR Code for user
//                 fetch('https://genguard.site/api/generate-qr', {
//                     method: 'POST',
//                     headers: {
//                         'Content-Type': 'application/json'
//                     },
//                     body: JSON.stringify({
//                         user_id: user.uid
//                     })
//                 })
//                 .then(response => response.json())
//                 .then(data => {
//                     if (data.success) {
//                         // console.log('QR Code generated and uploaded successfully!');
                        
//                         let db = firebase.database();
//                         db.ref('users/' + user.uid).set({
//                             firstName: firstname,
//                             lastName: lastname,
//                             username: username,
//                             email: email,
//                             isAdmin: false, // Be cautious with this
//                             isPermit: false, // Be cautious with this
//                             photoURL: 'user_photos/' + user.uid + '.png',
//                             qrCodeURL: 'qrcodes/' + user.uid + '.png', // Assuming the QR Code URL is returned in the response
//                         }).then(() => {
//                             //console.log("User information stored successfully!");
//                             window.location.href = "login.html";
//                         }).catch((error) => {
//                             //console.error("Error storing user information: ", error);
//                         });
//                     } else {
//                         //console.error('Error generating and uploading QR Code: ', data.error);
//                     }
//                 })
//                 .catch(error => {
//                     //console.error('Error during QR Code generation and upload: ', error.message);
//                 });
//             });
//         });
//         })
//         .catch((error) => {
//             //console.error("Error signing up: ", error);
//             let inputId;
//             switch (error.code) {
//                 case 'auth/email-already-in-use':
//                     inputId = 'email';
//                     break;
//                 case 'auth/invalid-email':
//                     inputId = 'email';
//                     break;
//                 case 'auth/weak-password':
//                     inputId = 'password';
//                     break;
//                 case 'auth/operation-not-allowed':
//                     inputId = 'email'; // or another appropriate field
//                     break;
//                 default:
//                     inputId = 'email'; // or another appropriate field
//             }
//             setError(inputId, error.message);
//         });
// }


function createUserAndUploadData(email, password, firstname, lastname, username, photoFile) {
    // Start the SweetAlert loading indicator
    Swal.fire({
        title: 'Uploading your details...',
        text: 'Please wait...',
        allowEscapeKey: false,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    firebase.auth().createUserWithEmailAndPassword(email, password)
        .then((userCredential) => {
            clearErrorStyles();
            const user = userCredential.user;
            const storageRef = firebase.storage().ref('user_photos/' + user.uid + '.png');

            // Note: Assuming resizeImage returns a Promise. If not, you need to adjust it to do so.
            resizeImage(photoFile, 400, 600, (resizedBlob) => {
                storageRef.put(resizedBlob).then(() => {
                    fetch('https://genguard.site/api/generate-qr', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            user_id: user.uid
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            let db = firebase.database();
                            db.ref('users/' + user.uid).set({
                                firstName: firstname,
                                lastName: lastname,
                                username: username,
                                email: email,
                                isAdmin: false,
                                isPermit: false,
                                photoURL: 'user_photos/' + user.uid + '.png',
                                qrCodeURL: 'qrcodes/' + user.uid + '.png'
                            }).then(() => {
                                Swal.fire({
                                    title: 'Success!',
                                    text: 'Your details have been uploaded successfully!',
                                    icon: 'success',
                                    confirmButtonText: 'OK'
                                }).then(() => {
                                    window.location.href = "login.html";
                                });
                            }).catch((error) => {
                                Swal.fire('Error!', 'An error occurred while storing user information.', 'error');
                            });
                        } else {
                            Swal.fire('Error!', 'Error generating and uploading QR Code.', 'error');
                        }
                    })
                    .catch(error => {
                        Swal.fire('Error!', 'Error during QR Code generation and upload: ' + error.message, 'error');
                    });
                });
            });
        })
        .catch((error) => {
            // Determine the appropriate input field based on the error and set the error message
            let inputId = 'email'; // Default to 'email' for simplicity in this example
            switch (error.code) {
                case 'auth/email-already-in-use':
                case 'auth/invalid-email':
                case 'auth/operation-not-allowed':
                    inputId = 'email';
                    break;
                case 'auth/weak-password':
                    inputId = 'password';
                    break;
                // Add more cases as needed
            }
            setError(inputId, error.message);
            Swal.fire('Error!', error.message, 'error');
        });
}

var firstnameInput = document.getElementById("first-name");
var lastnameInput = document.getElementById("last-name");
var usernameInput = document.getElementById("username");
var emailInput = document.getElementById("email");
var passwordInput = document.getElementById("password");
var photoInput = document.getElementById("photo");
var btn = document.getElementById("signup-button");

//progresss for the user
var divProgress= document.getElementById("signup-progress");
document.getElementById("signup-form").addEventListener("submit", function(event) {

    event.preventDefault(); // Prevent the form from submitting normally
    clearErrorStyles();
    divProgress.innerHTML = "Validaiting Info..."
    // Disabling all input fields
    firstnameInput.disabled = true;
    lastnameInput.disabled = true;
    usernameInput.disabled = true;
    emailInput.disabled = true;
    passwordInput.disabled = true;
    photoInput.disabled = true;
    btn.disabled = true;
    // Get form values
    let firstname = document.getElementById("first-name").value;
    let lastname = document.getElementById("last-name").value;
    let username = document.getElementById("username").value;
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;

    // Validate form inputs
    if (!isValidEmail(email)) {
        setError("email", "Invalid email format");
        return;
    }
    if (!isValidPassword(password)) {
        setError("password", "Password does not meet criteria");
        return;
    }
    if (!isValidName(firstname)) {
        setError("first-name", "Invalid first name");
        return;
    }
    if (!isValidName(lastname)) {
        setError("last-name", "Invalid last name");
        return;
    }
    divProgress.innerHTML = "Validaiting Picture..."
    if (photoInput.files.length > 0) {
        let photoFile = photoInput.files[0];

        verifyFace(photoFile)
            .then(data => {
                if (data.success) {
                    createUserAndUploadData(email, password, firstname, lastname, username, photoFile);
                } else {
                    setError("photo", 'Face verification failed: ' + data.error);
                    firstnameInput.disabled = false;
                    lastnameInput.disabled = false;
                    usernameInput.disabled = false;
                    emailInput.disabled = false;
                    passwordInput.disabled = false;
                    photoInput.disabled = false;
                    btn.disabled = false;
                }
            })
            .catch(error => {
                setError("photo", 'Error during face verification: ' + error.message);
                firstnameInput.disabled = false;
                lastnameInput.disabled = false;
                usernameInput.disabled = false;
                emailInput.disabled = false;
                passwordInput.disabled = false;
                photoInput.disabled = false;
                btn.disabled = false;
            });
    } else {
        setError("photo", "No photo uploaded!");
        firstnameInput.disabled = false;
        lastnameInput.disabled = false;
        usernameInput.disabled = false;
        emailInput.disabled = false;
        passwordInput.disabled = false;
        photoInput.disabled = false;
        btn.disabled = false;
    }


});

function setError(inputId, message) {
    firstnameInput.disabled = false;
    lastnameInput.disabled = false;
    usernameInput.disabled = false;
    emailInput.disabled = false;
    passwordInput.disabled = false;
    photoInput.disabled = false;
    btn.disabled = false;
    let element = document.getElementById(inputId);
    if (element) {
        element.classList.add('input-invalid');
        let errorElement = document.getElementById(inputId + "-error");
        if (errorElement) {
            errorElement.textContent = message;
        }
    }
    divProgress.innerHTML = " "
}

function clearErrorStyles() {
    ["email", "password", "first-name", "last-name", "username", "photo"].forEach(id => {
        let element = document.getElementById(id);
        if (element) {
            element.classList.remove('input-invalid');
        }
        let errorElement = document.getElementById(id + "-error");
        if (errorElement) {
            errorElement.textContent = "";
        }
    });
}

function resizeImage(file, maxWidth, maxHeight, callback) {
    const reader = new FileReader();
    reader.onload = (event) => {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            let width = img.width;
            let height = img.height;

            if (width > height) {
                if (width > maxWidth) {
                    height *= maxWidth / width;
                    width = maxWidth;
                }
            } else {
                if (height > maxHeight) {
                    width *= maxHeight / height;
                    height = maxHeight;
                }
            }
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);

            // Convert canvas to Blob
            canvas.toBlob(callback, 'image/png', 0.7); // Adjust quality as needed
        };
        img.src = event.target.result;
    };
    reader.readAsDataURL(file);
}
