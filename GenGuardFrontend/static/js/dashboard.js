

const firebaseConfig = {
    
};
// Initialize Firebase
firebase.initializeApp(firebaseConfig);
var storage = firebase.storage();
var storageRef = storage.ref();
var alarmRef = firebase.database().ref('Alarm')
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
            fetchUserCount()
            
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
    loadImages()

 


    
    // Event listener for the "Start Alarm" button
    document.getElementById('start-alarm-button').addEventListener('click', function() {
        alarmRef.update({ alarmState: true });
        alarmRef.update({ alarmZone: 999 });
    });

    // Event listener for the "Stop Alarm" button
    document.getElementById('stop-alarm-button').addEventListener('click', function() {
        alarmRef.update({ alarmState: false });
        alarmRef.update({ alarmZone: -1 });

    });

    firebase.database().ref('Alarm/alarmZone').on('value', function(snapshot) {
        const alarmZone = snapshot.val();
        // Update the text of the element that shows the alarm zone
        document.getElementById('text-zone').textContent =  alarmZone;
    });

    firebase.database().ref('Alarm/alarmState').on('value', function(snapshot) {
        const alarmState = snapshot.val();
        // Update the text of the element that shows the alarm zone
        document.getElementById('text-bin').textContent =  alarmState;
        console.log(alarmState);
        if(alarmState == "true" || alarmState == true || alarmState =="True")
        {
            document.getElementById('control-grid').style.display = 'none';
        }
        else
        {
            document.getElementById('control-grid').style.display = 'block';
        }
    });
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

function fetchUserCount() {
    firebase.database().ref('users').on('value', (snapshot) => {
        let adminCount = 0;
        let permittedCount = 0;
        let totalCount = 0;

        snapshot.forEach((childSnapshot) => {
            const user = childSnapshot.val();
            if (user.isAdmin) {
                adminCount++;
            }
            if (user.isPermit) {
                permittedCount++;
            }
            totalCount++;
        });

        console.log("Total users: ", totalCount);
        console.log("Admin users: ", adminCount);
        console.log("Permitted users: ", permittedCount);

        document.querySelector('.card-text').textContent = `Total users: ${totalCount}`;
        document.querySelector('.permittedCount').textContent = `Permitted users: ${permittedCount}`;

        diagram(adminCount, permittedCount, totalCount); // This will now be called anytime there's an update
    }, (error) => {
        console.error("Error fetching user count: ", error);
    });
}



function diagram(adminCount, permittedCount, totalCount) {
    // Define the variables for regular and not permitted user counts
    let regularUserCount = totalCount - adminCount;
    let notPermittedCount = totalCount - permittedCount;

    // Safely destroy existing charts if they exist and are indeed Chart.js instances
    if (window.adminVsRegularChart && typeof window.adminVsRegularChart.destroy === 'function') {
        window.adminVsRegularChart.destroy();
    }
    if (window.permittedVsNotChart && typeof window.permittedVsNotChart.destroy === 'function') {
        window.permittedVsNotChart.destroy();
    }

    // Create the charts again with the updated data
    // Admin vs Regular Users Pie Chart
    const ctxAdminVsRegular = document.getElementById('adminVsRegularChart').getContext('2d');
    window.adminVsRegularChart = new Chart(ctxAdminVsRegular, {
        type: 'pie',
        data: {
            labels: ['Admins', 'Regular Users'],
            datasets: [{
                data: [adminCount, regularUserCount],
                backgroundColor: ['rgba(245, 34, 203, 1)', 'rgba(34, 118, 245, 1)'],
                borderColor: ['rgba(245, 34, 203, 1)', 'rgba(34, 118, 245, 1)'],
                borderWidth: 1
            }]
        }
    });

    // Permitted vs Not Permitted Users Pie Chart
    const ctxPermittedVsNot = document.getElementById('permittedVsNotChart').getContext('2d');
    window.permittedVsNotChart = new Chart(ctxPermittedVsNot, {
        type: 'pie',
        data: {
            labels: ['Permitted', 'Not Permitted'],
            datasets: [{
                data: [permittedCount, notPermittedCount],
                backgroundColor: ['rgba(66, 245, 120, 1)', 'rgba(245, 34, 45, 1)'],
                borderColor: ['rgba(66, 245, 130, 1)', 'rgba(245, 34, 45, 1)'],
                borderWidth: 1
            }]
        }
    });
}



function loadImages() {
    var imagesRef = storageRef.child('logs'); // Adjust 'logs' to your folder path

    imagesRef.listAll()
        .then(function(result) {
            if (result.items.length > 0) {
                var lastImageRef = result.items[result.items.length - 1];
                lastImageRef.getDownloadURL().then(function(url) {
                    displayLastLoginImage(url);
                
                    var filename = lastImageRef.name;
                    var filenameParts = filename.split('_'); // Splitting by underscore
                    if (filenameParts.length > 2) {
                        var timestampPart = filenameParts[2].split('.')[0]; // Assuming timestamp is the third part
                        var timestamp = parseInt(timestampPart); // Converting to integer
                    
                        console.log("Extracted timestamp:", timestamp); // For debugging
                    
                        if (!isNaN(timestamp)) {
                            var date = new Date(timestamp * 1000); // Convert Unix timestamp to milliseconds
                            var formattedDate = date.toLocaleString();
                            var detailsDiv = document.getElementById('lastLoginDetails');
                            detailsDiv.innerText = `Uploaded: ${formattedDate}`;
                        } else {
                            console.log("Invalid timestamp extracted from filename");
                        }
                    } else {
                        console.log("Filename format not as expected");
                    }
                    
                }).catch(function(error) {
                    console.log("Error getting download URL: ", error);
                });
                
            }
        })
        .catch(function(error) {
            console.log("Error listing images: ", error);
        });
}


function displayLastLoginImage(url) {
    var imageContainer = document.getElementById('lastLoginImageContainer'); // Make sure this element exists in your HTML
    var imgElement = document.createElement('img');
    imgElement.src = url;
    imgElement.className = 'img-fluid';
    imageContainer.innerHTML = ''; // Clear any previous content
    imageContainer.appendChild(imgElement);
}

