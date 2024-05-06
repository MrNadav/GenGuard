const firebaseConfig = {
   
};

firebase.initializeApp(firebaseConfig);
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
                populateUserTable();

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

function logout() {
    firebase.auth().signOut().then(() => {
        window.location.href = "login.html";
    }).catch((error) => {
        // console.error("Error during sign out: ", error);
    });
}
function populateUserTable() {
    console.log('Populating user table...');
    const userTable = document.getElementById('user-table');
    userTable.innerHTML = ''; // Clear existing content
    const headerRow = userTable.insertRow(-1); // Use -1 for appending at the end
    const headers = ['First Name', 'Last Name', 'Email', 'Status', 'Actions'];
    headers.forEach(headerText => {
        const headerCell = document.createElement('th');
        headerCell.textContent = headerText;
        headerRow.appendChild(headerCell);
    });

    // Listen for real-time updates
    firebase.database().ref('users').on('value', snapshot => {
        snapshot.forEach(childSnapshot => {
            const uid = childSnapshot.key;
            const user = childSnapshot.val();

            // Update or insert new row
            let row = userTable.querySelector(`#user-${uid}`);
            if (!row) {
                row = userTable.insertRow(-1);
                row.id = `user-${uid}`; // Unique ID for the row
            } else {
                row.innerHTML = ''; // Clear row for update
            }

            // Insert cells
            const firstNameCell = row.insertCell(0);
            const lastNameCell = row.insertCell(1);
            const emailCell = row.insertCell(2);
            const statusCell = row.insertCell(3);
            const actionsCell = row.insertCell(4);

            // Set cell values
            firstNameCell.textContent = user.firstName || 'N/A';
            lastNameCell.textContent = user.lastName || 'N/A';
            emailCell.textContent = user.email || 'N/A';

             // Inserting text before dots
             const adminLabelText = document.createTextNode("Admin: ");
             const adminDot = document.createElement('span');
             adminDot.className = `dot ${user.isAdmin ? 'green' : 'red'}`;
             adminDot.title = "Toggle Admin Status";
             adminDot.onclick = () => toggleStatus(uid, 'isAdmin');
 
             const permitLabelText = document.createTextNode(" Permit: ");
             const permitDot = document.createElement('span');
             permitDot.className = `dot ${user.isPermit ? 'green' : 'red'}`;
             permitDot.title = "Toggle Permit Status";
             permitDot.onclick = () => toggleStatus(uid, 'isPermit');
 
             // Append text and dots to the status cell
             statusCell.appendChild(adminLabelText);
             statusCell.appendChild(adminDot);
             statusCell.appendChild(permitLabelText);
             statusCell.appendChild(permitDot);

            const editButton = document.createElement('button');
            editButton.innerHTML = 'Edit';
            editButton.addEventListener('click', () => {
                editUser(user, uid);
                console.log("populate uid: "+uid);
            });
            actionsCell.appendChild(editButton);

            const deleteButton = document.createElement('button');
            deleteButton.style.backgroundColor = "red";
            deleteButton.style.marginLeft = "3px";
            deleteButton.innerHTML = 'Delete';
            deleteButton.addEventListener('click', () => {
                deleteUser(childSnapshot.key); // Corrected reference to the user ID
            });
            actionsCell.appendChild(deleteButton);
        });
    });
}

function toggleStatus(uid, field) {
    const userRef = firebase.database().ref('users/' + uid);
    userRef.once('value').then(snapshot => {
        const user = snapshot.val();
        userRef.update({ [field]: !user[field] }); // Toggle the status
    });
}
function editUser(user, uid) {
    const editModal = document.getElementById('edit-modal');
    const firstNameInput = document.getElementById('edit-first-name');
    const lastNameInput = document.getElementById('edit-last-name');
    const emailInput = document.getElementById('edit-email');
    const usernameInput = document.getElementById('edit-username');
    //const passwordInput = document.getElementById('edit-password');
    const isAdminInput = document.getElementById('edit-is-admin');
    const isPermitInput = document.getElementById('edit-is-permit');
    const saveButton = document.getElementById('edit-save-button');
    const cancelButton = document.getElementById('edit-cancel-button');
    const deleteButton = document.getElementById('edit-delete-button');
    //saveButton.setAttribute('data-uid', uid);
    saveButton.setAttribute('data-uid', uid); // This line is missing in your current code
    saveButton.setAttribute('data-user', JSON.stringify(user)); // This is correct

    // Attach event listener
    saveButton.removeEventListener('click', saveUser);
    saveButton.addEventListener('click', saveUser);

    // Define saveUser within editUser
    function saveUser(event) {
        const button = event.target;
        const uid = button.getAttribute('data-uid');
        const userStr = button.getAttribute('data-user');
        //const user = button.getAttribute('data-user'); // Ensure this is correctly serialized    
        const user = JSON.parse(userStr || '{}'); 

        console.log("saveuser uid = "+uid);
        console.log("Saving data for user:", user);
        if (firstNameInput.value.trim() === '') {
            alert('Please enter a first name.');
            return;
        }
        if (lastNameInput.value.trim() === '') {
            alert('Please enter a last name.');
            return;
        }
        if (emailInput.value.trim() === '') {
            alert('Please enter an email.');
            return;
        }
        // if (passwordInput.value.trim() === '') {
        //     alert('Please enter a password.');
        //     return;
        // }
        // if (!uid) {
        //     console.error("User UID is undefined. Cannot save data.");
        //     return; // Exit the function to prevent further execution
        // }

        firebase.database().ref('users/' + uid).update({
            firstName: firstNameInput.value,
            lastName: lastNameInput.value,
            email: emailInput.value,
            isAdmin: isAdminInput.checked,
            isPermit: isPermitInput.checked,
            username: usernameInput.value
        }, function(error) {
            if (error) {
                // Handle the error case
                console.error("Data could not be saved." + error);
            } else {
                // Data saved successfully!
                console.log("Data saved successfully.");
                //location.reload();
            }
        });

        const row = document.getElementById(uid);
        if (row) {
            row.cells[0].innerHTML = firstNameInput.value;
            row.cells[1].innerHTML = lastNameInput.value;
            row.cells[2].innerHTML = emailInput.value;
            // Update other cells if necessary
        } else {
            console.error("No element found with ID:", uid);
        }
        editModal.style.display = 'none';
    }

    function closeModal() {
        editModal.style.display = 'none';
    }
    
 
    firstNameInput.value = user.firstName;
    lastNameInput.value = user.lastName;
    emailInput.value = user.email;
    usernameInput.value = user.username;
    isAdminInput.checked = user.isAdmin || false;
    isPermitInput.checked = user.isPermit || false;

    let closebtn = document.getElementById("x");

    closebtn.addEventListener('click', closeModal);
    saveButton.addEventListener('click', saveUser);
    //cancelButton.addEventListener('click', closeModal);
    deleteButton.addEventListener('click', () => {
        deleteUser(user.username);
        closeModal();
    });

    editModal.style.display = 'block';
}

function deleteUser(uid) {
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
            // User confirmed the deletion, show a loading message
            Swal.fire({
                title: 'Please wait...',
                html: 'Deleting user...',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                },
            });

            // Proceed with your fetch request to delete the user
            fetch('https://genguard.site/api/deleteUser', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ uid })
            })
            .then(response => {
                if (response.ok) {
                    // If deletion is successful, show a success message
                    Swal.fire({
                        icon: 'success',
                        title: 'Deleted!',
                        text: 'User has been deleted.',
                    });
                    // Then remove the user from the table as before
                    const row = document.getElementById(uid);
                    if (row) {
                        row.remove();
                    }
                } else {
                    // If the request failed, show an error message
                    Swal.fire({
                        icon: 'error',
                        title: 'Oops...',
                        text: 'Failed to delete user.',
                    });
                }
            })
            .catch(error => {
                // Handle any errors that occur during the fetch
                Swal.fire({
                    icon: 'error',
                    title: 'Oops...',
                    text: 'An error occurred!',
                });
                console.error('Error removing user:', error);
            });
        }
    });
}

