// Wait for the DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
  // Get the login form element
  var loginForm = document.querySelector('.login-form');

  // Add an event listener for form submission
  loginForm.addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    // Get the entered username and password values
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;

    // Perform login validation
    if (username === 'admin' && password === 'password') {
      // Successful login
      alert('Login successful!');
      // Redirect to the employer dashboard or perform other actions
    } else {
      // Invalid credentials
      alert('Invalid username or password. Please try again.');
    }
  });
});