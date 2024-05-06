
const firebaseConfig = {

};
// Initialize Firebase
firebase.initializeApp(firebaseConfig);
var storage = firebase.storage();
var storageRef = storage.ref();


firebase.auth().onAuthStateChanged(function(user) {
    if (user) {
        firebase.database().ref('users').once('value').then((snapshot) => {
            snapshot.forEach((childSnapshot) => {
                const user = snapshot.val()
                console.log(user);
            });
        });
        // User is signed in
        console.log("User is logged in");
        // Fetch user details from Firebase Realtime Database
        firebase.database().ref('users/' + user.uid).once('value').then((snapshot) => {
            let username = snapshot.val().username; // Assuming the user object has a username property
            let admincheck = snapshot.val().isAdmin; // Assuming the user object has a username property
            if(admincheck)
            {
                document.getElementById("admin-button").style.display = "block";
                document.getElementById("logs-button").style.display = "block";

            } else {
                alert('You do not have permission to access this page.');
                window.location.href = 'login.html';
            }
            console.log("Fetched username: ", username);

            // Update UI elements
            document.getElementById("user-info").style.display = "flex";
            document.getElementById("login-signup-buttons").style.display = "none";
            document.getElementById("user-name").textContent = username;
            if(admincheck)
            {
                document.getElementById("admin-button").style.display = "block";
                document.getElementById("logs-button").style.display = "block";

            }
        }).catch((error) => {
            console.error("Error fetching user data: ", error);
            window.alert("Unexpected error please contact admin");
            window.location.href = 'login.html';
            //logout();
        });
    } else {
        // No user is signed in
        console.log("User is not logged in");
        window.location.href = 'login.html';
    }  
});

// Function to log out user
function logout() {
    firebase.auth().signOut().then(() => {
        window.location.href = "login.html";
    }).catch((error) => {
        console.error("Error during sign out: ", error);
    });
}

function getCookie(name) {
    let nameEQ = name + "=";
    let ca = document.cookie.split(';');
    for(let i=0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}


function loadImages() {
    var imagesRef = storageRef.child('logs'); // Adjust 'logs' to your folder path

    var imageDetails = []; // Array to store image details

    imagesRef.listAll()
        .then(function(result) {
            result.items.forEach(function(imageRef) {
                // Get the image download URL
                imageRef.getDownloadURL().then(function(url) {
                    // Extract the timestamp from the filename
                    var filename = imageRef.name;
                    var timestamp = filename.split('_')[2].split('.')[0]; // Adjust this according to your filename format
                    var date = new Date(parseInt(timestamp) * 1000); // Convert to milliseconds

                    // Add image details to the array
                    imageDetails.push({
                        url: url,
                        timestamp: date.getTime(), // Get timestamp in milliseconds
                        imageRef: imageRef // Store the image reference
                    });

                    // Check if all images have been processed
                    if (imageDetails.length === result.items.length) {
                        // Sort the image details array by timestamp in descending order
                        imageDetails.sort(function(a, b) {
                            return b.timestamp - a.timestamp;
                        });

                        // Display the sorted images
                        displayImages(imageDetails);
                    }
                }).catch(function(error) {
                    console.log("Error getting download URL: ", error);
                });
            });
        })
        .catch(function(error) {
            console.log("Error listing images: ", error);
        });
}

function displayImages(imageDetails) {
    var imagesRow = document.getElementById('imagesRow');

    // Iterate through the sorted array and display the images
    imageDetails.forEach(function(imageDetail) {
        var url = imageDetail.url;
        var timestamp = imageDetail.timestamp;
        var imageRef = imageDetail.imageRef; // Retrieve the image reference

        var date = new Date(timestamp);
        var formattedDate = date.toLocaleString();

        var imgWrap = document.createElement('div');
        imgWrap.className = 'col-lg-4 col-md-6 mb-4 position-relative';

        var imgElement = document.createElement('img');
        imgElement.src = url;
        imgElement.className = 'img-fluid';

        var deleteBtn = document.createElement('button');
        deleteBtn.innerText = 'Delete';
        deleteBtn.className = 'btn btn-danger btn-sm position-absolute';
        deleteBtn.style.bottom = '10px';
        deleteBtn.style.right = '10px';
        deleteBtn.style.display = 'none';

        // Listen for deletion
        deleteBtn.onclick = function() { deleteImage(imageRef, imgWrap); };

        var detailsDiv = document.createElement('div');
        detailsDiv.className = 'image-details position-absolute';
        detailsDiv.innerText = `Uploaded: ${formattedDate}`;
        detailsDiv.style.display = 'none';

        imgWrap.appendChild(imgElement);
        imgWrap.appendChild(detailsDiv);
        imgWrap.appendChild(deleteBtn);
        imagesRow.appendChild(imgWrap);

        // Add hover behavior
        imgWrap.addEventListener('mouseenter', function() {
            detailsDiv.style.display = 'block';
            deleteBtn.style.display = 'block';
        });

        imgWrap.addEventListener('mouseleave', function() {
            detailsDiv.style.display = 'none';
            deleteBtn.style.display = 'none';
        });
    });
}

function deleteImage(imageRef, imgWrap) {
    // Show a SweetAlert confirmation dialog
    Swal.fire({
        title: 'Are you sure?',
        text: "You won't be able to revert this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
    }).then((result) => {
        if (result.isConfirmed) {
            // Proceed with deleting the image
            imageRef.delete().then(function() {
                // Remove the image element after successful deletion
                imgWrap.remove();
                // Show a success message
                Swal.fire(
                    'Deleted!',
                    'Your file has been deleted.',
                    'success'
                );
            }).catch(function(error) {
                // Handle any errors that occur during deletion
                console.log("Error deleting file: ", error);
                Swal.fire(
                    'Failed!',
                    'There was an error deleting your file.',
                    'error'
                );
            });
        }
    });
}
// Load images when the script loads
loadImages();
