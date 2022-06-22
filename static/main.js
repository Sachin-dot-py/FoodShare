/* Password validation and sign up, reset password form validation: */

// Checks if a given strings contains special characters
function containsSpecialChars(string){
    const specialChars = "~`!@#$%^&*()_-+={[}]|\\:;\"'<,>.?/";
    for (let i = 0; i < string.length; i++){
        if (specialChars.indexOf(string.charAt(i)) !== -1){
            return true;
        }
    }
    return false;
}

// Checks if a given strings contains numerical characters
function containsNumbers(string){
    const numbers = "1234567890";
    for (let i = 0; i < string.length; i++){
        if (numbers.indexOf(string.toLowerCase().charAt(i)) !== -1){
            return true;
        }
    }
    return false;
}

// Checks if a given strings contains uppercase letters
function containsUppercase(string){
    const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    for (let i = 0; i < string.length; i++){
        if (letters.indexOf(string.charAt(i)) !== -1){
            return true;
        }
    }
    return false;
}

// Sets the tick or cross emoji in the validation for a secure password
function setEmoji(child) {
     if (child.className === "valid"){
        child.children[0].innerHTML = "✅️";
     }
     else if (child.className === "invalid"){ // Used else if because first <tr> must not have an emoji
        child.children[0].innerHTML = "❌";
     }
}

// Checks if a password matches the requirements for a strong password in the sign-up and reset password form
function validatePassword(){
    const password = document.getElementsByName("password")[0].value;
    const passvalidation = document.getElementById('passvalidation');
    const valtable = passvalidation.getElementsByTagName('table')[0].children[0]; // .children[0] fetches tbody
    let valid = true;

    if (!containsSpecialChars(password)){
        valid = false;
        valtable.children[1].className = "invalid";
    }
    else{
        valtable.children[1].className = "valid";
    }

    if (!containsNumbers(password)){
        valid = false;
        valtable.children[2].className = "invalid";
    }
    else{
        valtable.children[2].className = "valid";
    }

    if (!containsUppercase(password)){
        valid = false;
        valtable.children[3].className = "invalid";
    }
    else{
        valtable.children[3].className = "valid";
    }

    if (password.length < 8){
        valid = false;
        valtable.children[4].className = "invalid";
    }
    else{
        valtable.children[4].className = "valid";
    }

    Array.from(valtable.children).forEach(setEmoji)

    if (valid){
        passvalidation.hidden = true;
    }
    else{
        passvalidation.hidden = false;
    }
    return valid;
}

// Checks if both password fields in the sign-up form and reset-password form match
function checkMatchingPasswords(){
    const span = document.getElementById('passmatchvalidate');
    if (document.getElementsByName('password')[0].value === document.getElementsByName('repassword')[0].value){
        span.innerHTML = "Passwords match ✅";
        span.style.color = "green";
        return true;
    }
    else{
        span.innerHTML = "Passwords do not match ❌";
        span.style.color = "red";
        return false;
    }
}

// Validate Reset Password form and Sign Up form
function validateForm(){
    if (checkMatchingPasswords() && validatePassword()){
        return true;
    }
    else{
        document.alert("Please correct the errors in the entered fields before submitting the form.");
        return false;
    }
}

// Toggle visibility of password in password field
function toggleShowPassword(){
    pwdbox = document.getElementsByName("password")[0];
    if (pwdbox.type === "password"){
        pwdbox.type = "text";  // Password visible
    }
    else{
        pwdbox.type = "password"; // Password not visible
    }
}

// Autocompleting address


async function getSuggestions(text){
    base_url = window.location.origin
    url = base_url + "/autocomplete/address?address=" + text;
    const result = await fetch(url).then(function(response) {
        return response.json();
      }).then(function(data) {
        return data;
      }).catch(function() {
        console.log("Error.");
      });

      const suggestions = Object.keys(result); // We only want the addresses, not the coordinates
      return suggestions
}

function setAddress(text){
    const address_field = document.getElementsByName("address")[0];
    address_field.value = text;
}

// Adds an autocomplete suggestion to the autocomplete box
function addSuggestion(suggestion){
    const autocomplete_box = document.getElementById('address_autocomplete');
    const ul = autocomplete_box.getElementsByTagName('ul')[0];
    const li = document.createElement('li');
    li.onclick = function() {
    setAddress(this.innerHTML); // When the suggestion is clicked, set the address field as the suggestion
    ul.innerHTML = "" // Remove suggestions from screen
    };
    li.innerHTML = suggestion;
    ul.appendChild(li);
}

// Called whenever user inputs text in the address field to give suggestions
async function autocompleteAddress(text){
    // Only if there is text and once every 4 characters (to reduce load on the server)
    if (text.length > 0 && text.length % 4 === 0){
        const suggestions = await getSuggestions(text);
        const autocomplete_box = document.getElementById('address_autocomplete');
        const ul = autocomplete_box.getElementsByTagName('ul')[0];
        ul.innerHTML = ""; // Clears previous autocomplete output
        if (!suggestions.includes(text)){ // If user has not already chosen a suggestion
            suggestions.forEach(addSuggestion);
        }
    }
}
