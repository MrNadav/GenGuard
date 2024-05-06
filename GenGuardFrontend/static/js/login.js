// Your Firebase configuration object
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
  return password.length >= 6; // Simple validation for example
}



var submitbtn = document.getElementById("submit-btn");
var divProgress= document.getElementById("login-progress");
// Add event listener to the login form
document.getElementById("login-form").addEventListener("submit", function (event) {
  event.preventDefault();  // Prevent the form from submitting normally
  clearErrorStyles()
  // Get form values
  let email = document.getElementById("email").value.trim(); // Trim to remove whitespace
  let password = document.getElementById("password").value;
  if (!isValidEmail(email)) {
      displayError("Invalid email format");
      return;
  }

  if (password.length === 0) {
      displayError("Password cannot be empty");
      return;
  }
  submitbtn.disabled = true
  divProgress.innerHTML = 'Verifiying details....'
  // Firebase login
  firebase.auth().signInWithEmailAndPassword(email, password)
      .then((userCredential) => {
          // Signed in
          var user = userCredential.user;
          console.log("User logged in successfully!");
          divProgress.innerHTML = 'Success!'

          // Get reference to the user in the database
          var userId = user.uid;
          var userRef = firebase.database().ref('users/' + userId);
          Swal.fire({
            title: 'Success!',
            text: 'Logged in successfully.',
            icon: 'success',
            confirmButtonText: 'Ok'
          }).then((result) => {
          // Check if the user is an admin
          userRef.once('value').then(function(snapshot) {
            var isAdmin = (snapshot.val() && snapshot.val().isAdmin) || false; 
            
            // Navigate to the appropriate page based on isAdmin value
            if(isAdmin) {
              // console.log("Navigating to admin.html");
              window.location.href = "dashboard.html";
            } else {
              // console.log("Navigating to home.html");
              window.location.href = "profile.html";
            }
          });
        });
      })
      .catch((error) => {
          // Error occurred during login
          displayError(error.message);
          divProgress.innerHTML = ''
          submitbtn.disabled = false

      });

});

function displayError(errorMessage) {
    var errorMessageElement = document.getElementById("error-message");
    errorMessageElement.textContent = errorMessage;
    errorMessageElement.style.fontSize = "14px";  // Adjust as needed
    errorMessageElement.style.color = "red";
    document.getElementById("email").style.border = "1px solid red";
    document.getElementById("password").style.border = "1px solid red";
}
function clearErrorStyles() {
  var errorMessageElement = document.getElementById("error-message");
  errorMessageElement.textContent = "";  // Clear any previous error messages
  errorMessageElement.style.fontSize = "initial";  // Reset font size
  errorMessageElement.style.color = "initial";  // Reset color
  
  // Reset border styles for input fields
  document.getElementById("email").style.border = "initial";
  document.getElementById("password").style.border = "initial";
}
