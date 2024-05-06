
const firebaseConfig = {
   
};
// Initialize Firebase
firebase.initializeApp(firebaseConfig);


firebase.auth().onAuthStateChanged(function(user) {
    if (user) {
        firebase.database().ref('users').once('value').then((snapshot) => {
            snapshot.forEach((childSnapshot) => {
                const user = snapshot.val()
                // console.log(user);
            });
        });
        // User is signed in
        console.log("User is logged in");
        // Fetch user details from Firebase Realtime Database
        firebase.database().ref('users/' + user.uid).once('value').then((snapshot) => {
            let username = snapshot.val().username; // Assuming the user object has a username property
            let admincheck = snapshot.val().isAdmin; // Assuming the user object has a username property

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
        // console.log("User is not logged in");
        document.getElementById("user-info").style.display = "none";
        document.getElementById("login-signup-buttons").style.display = "block";
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

var TxtType = function(el, toRotate, period) {
    this.toRotate = toRotate;
    this.el = el;
    this.loopNum = 0;
    this.period = parseInt(period, 10) || 2000;
    this.txt = '';
    this.tick();
    this.isDeleting = false;
};

TxtType.prototype.tick = function() {
    var i = this.loopNum % this.toRotate.length;
    var fullTxt = this.toRotate[i];

    if (this.isDeleting) {
    this.txt = fullTxt.substring(0, this.txt.length - 1);
    } else {
    this.txt = fullTxt.substring(0, this.txt.length + 1);
    }

    this.el.innerHTML = '<span class="wrap">'+this.txt+'</span>';

    var that = this;
    var delta = 200 - Math.random() * 100;

    if (this.isDeleting) { delta /= 2; }

    if (!this.isDeleting && this.txt === fullTxt) {
    delta = this.period;
    this.isDeleting = true;
    } else if (this.isDeleting && this.txt === '') {
    this.isDeleting = false;
    this.loopNum++;
    delta = 500;
    }

    setTimeout(function() {
    that.tick();
    }, delta);
};

window.onload = function() {
    var elements = document.getElementsByClassName('typewrite');
    for (var i=0; i<elements.length; i++) {
        var toRotate = elements[i].getAttribute('data-type');
        var period = elements[i].getAttribute('data-period');
        if (toRotate) {
          new TxtType(elements[i], JSON.parse(toRotate), period);
        }
    }
    // INJECT CSS FOR TYPEWRITE
    var css = document.createElement("style");
    css.type = "text/css";
    css.innerHTML = ".typewrite > .wrap { border-right: 0.08em solid #fff}";
    document.body.appendChild(css);
};

// ScrollReveal configurations
ScrollReveal().reveal('.headline', { delay: 500 });
ScrollReveal().reveal('.tagline', { delay: 500 });
ScrollReveal().reveal('.punchline', { delay: 500 });

// Rest of your JavaScript code
// ...

// ScrollReveal configurations
document.addEventListener('DOMContentLoaded', function() {
    const sr = ScrollReveal({
        origin: 'top',
        distance: '60px',
        duration: 2000,
        delay: 200,
        // reset: true
    });

    // Customizing what elements ScrollReveal will animate
    sr.reveal('.headline', { delay: 500 });
    sr.reveal('.tagline', { interval: 200 });
    sr.reveal('.punchline', { delay: 500 });
    sr.reveal('.pclear', { delay: 200 });
    sr.reveal('.price-table', { delay: 400 });
    sr.reveal('#contact', { delay: 600 });
    sr.reveal('.footer', { delay: 800 });
    sr.reveal('.service-item', { interval: 200 });
    sr.reveal('.carousel-slides', { delay: 1000 });
    
});

// Navigation logic for changing active class based on scroll position
document.addEventListener('DOMContentLoaded', (event) => {
    const sections = document.querySelectorAll('.section, .footer, .banner');
    const navItems = document.querySelectorAll('.menu-items a');

    function getDistanceFromTop(element) {
        return element.getBoundingClientRect().top;
    }

    function deactivateAllNavItems() {
        navItems.forEach((navItem) => {
            navItem.classList.remove('active-section');
        });
    }

    function setActiveSection() {
        let scrollPosition = window.pageYOffset;
        let windowHeight = window.innerHeight;
        let totalHeight = document.body.scrollHeight;
    
        // Assume no section is active
        deactivateAllNavItems();
    
        // Check each section to see if it's in view
        sections.forEach((section, index) => {
            let sectionTop = section.offsetTop;
            let sectionHeight = section.offsetHeight;
            let sectionBottom = sectionTop + sectionHeight;
    
            // Check if section is at the bottom of the page
            let isBottomSection = (totalHeight - sectionBottom) <= windowHeight;
    
            // Determine if the section is in the viewport or is the bottom section in view
            if ((scrollPosition + windowHeight >= sectionTop && scrollPosition < sectionBottom) || (isBottomSection && scrollPosition + windowHeight >= totalHeight)) {
                navItems[index].classList.add('active-section');
            }
        });
    }
    
    // Setup scroll event listener
    window.addEventListener('scroll', setActiveSection);
});

// Loop to check for the active section
function loop() {
    var sections = [
        document.getElementById('banner'),
        document.getElementById('salle'),
        document.getElementById('service'),
        document.getElementById('system'),
        document.getElementById('contact')
    ];

    function getClosestSection() {
        var closest = null;
        var closestDistance = Infinity;

        sections.forEach(function(section) {
            var rect = section.getBoundingClientRect();
            var distance = rect.top;
            
            if (distance >= 0 && distance < closestDistance) {
                closest = section;
                closestDistance = distance;
            }
        });

        return closest;
    }

    var activeSection = getClosestSection();

    sections.forEach(function(section, index) {
        if (section === activeSection) {
            document.querySelector('.menu-items li:nth-child(' + (index + 1) + ')').classList.add('active');
        } else {
            document.querySelector('.menu-items li:nth-child(' + (index + 1) + ')').classList.remove('active');
        }
    });

    window.requestAnimationFrame(loop);
}





(function() {
    emailjs.init("cccUPxjQA9UYTasH_"); // Replace with your actual EmailJS user ID
  })();
  
  document.getElementById('contact-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission
  
    // Manually collect the form data
    var from_name = document.getElementById('name').value;
    var from_email = document.getElementById('email').value;
    var message_html = document.getElementById('message').value;
  
    // Construct the parameters object with a predefined message
    var templateParams = {
      from_name: from_name,
      from_email: from_email,
      message: message_html, // User's message
      message_html: message_html, // This assumes your template has a parameter for the user's message as well
      // Add any other params your template needs
    };
  
    // Send the email
    emailjs.send('service_genguard', 'template_e2d7e2c', templateParams)
      .then(function(response) {
         console.log('SUCCESS!', response.status, response.text);
         Swal.fire({
           title: 'Success!',
           text: 'Your message has been sent successfully!',
           icon: 'success',
           confirmButtonText: 'Ok'
         });
      }, function(error) {
         console.log('FAILED...', error);
         Swal.fire({
           title: 'Error!',
           text: 'Failed to send your message, please try again.',
           icon: 'error',
           confirmButtonText: 'Ok'
         });
      });
  });
  
  
  
// Start the loop function
loop();



