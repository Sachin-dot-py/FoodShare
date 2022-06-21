function containsSpecialChars(string){
    const specialChars = "~`!@#$%^&*()_-+={[}]|\\:;\"'<,>.?/";
    for (let i = 0; i < string.length; i++){
        if (specialChars.indexOf(string.charAt(i)) !== -1){
            return true;
        }
    }
    return false;
}

function containsNumbers(string){
    const numbers = "1234567890";
    for (let i = 0; i < string.length; i++){
        if (numbers.indexOf(string.toLowerCase().charAt(i)) !== -1){
            return true;
        }
    }
    return false;
}

function containsLetters(string){
    const numbers = "abcdefghijklmnopqrstuvwxyz";
    for (let i = 0; i < string.length; i++){
        if (numbers.indexOf(string.toLowerCase().charAt(i)) !== -1){
            return true;
        }
    }
    return false;
}

function setEmoji(child) {
     if (child.className === "valid"){
        child.children[0].innerHTML = "✅️";
     }
     else if (child.className === "invalid"){ // Used else if because first <tr> must not have an emoji
        child.children[0].innerHTML = "❌";
     }
}

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

    if (!containsLetters(password)){
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
function validateForm(){
    if (checkMatchingPasswords() && validatePassword()){
        return true;
    }
    else{
        document.alert("Please correct the errors in the entered fields before submitting the form.")
        return false;
    }
}
