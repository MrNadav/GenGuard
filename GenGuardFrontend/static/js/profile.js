// Your web app's Firebase configuration
const firebaseConfig = {
   
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

firebase.auth().onAuthStateChanged(function(user) {
    if (user) {
        // User is signed in
        console.log("User is logged in");
        //fetch the image
        let storage = firebase.storage();
        let storageRef = storage.ref();
        let photoRef = storageRef.child('user_photos/' + user.uid + ".png");
        let qrRef = storageRef.child('qrcodes/' + user.uid + ".png");
        let barcodeRef = storageRef.child('barcodes/' + user.uid + ".png");
        photoRef.getDownloadURL().then(function(url) {
          // `url` is the download URL for the uploaded user's photo
          // Set the src attribute of the profile picture img element to the download URL
          document.getElementById('profile-picture').src = url;
        }).catch(function(error) {
        //   console.error("Error getting download URL:", error);
        });
        qrRef.getDownloadURL().then(function(url) {
            // `url` is the download URL for the uploaded user's photo
            // Set the src attribute of the profile picture img element to the download URL
            document.getElementById('user-qr').src = url;
          }).catch(function(error) {
            // console.error("Error getting download URL:", error);
          }).catch(function(error) {
            // console.error("Error getting download URL:", error);
          });;
        // Fetch user details from Firebase Realtime Database
        firebase.database().ref('users/' + user.uid).once('value').then((snapshot) => {
            let username = snapshot.val().username; // Assuming the user object has a username property
            // console.log("Fetched username: ", username);
            //user credintials
            document.getElementById('username').textContent += username;
            document.getElementById('first-name').textContent += snapshot.val().firstName;
            document.getElementById('last-name').textContent += snapshot.val().lastName;
            document.getElementById('email').textContent += snapshot.val().email;

            let admincheck = snapshot.val().isAdmin; // Assuming the user object has a username property
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
        });

        
    } else {
        // No user is signed in
        // console.log("User is not logged in");
        document.getElementById("user-info").style.display = "none";
        document.getElementById("login-signup-buttons").style.display = "block";
        alert("you must login to see your profile")
        window.location.href = "login.html";
    }
    
    
});

// Function to log out user
function logout() {
    firebase.auth().signOut().then(() => {
        window.location.href = "login.html";
    }).catch((error) => {
        // console.error("Error during sign out: ", error);
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


