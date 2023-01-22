/* Form validation for sign up, change password, reset password: */

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

/* Autocompleting Address */

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

/* Snackbar Notifications */
snackbar = document.getElementById("snackbar");
function notify(notification) {
  snackbar.innerHTML = notification;
  snackbar.className = "show";
  setTimeout(function(){ snackbar.className = snackbar.className.replace("show", ""); }, 3000);
}

/* For buyer_orders.html, seller_dashboard.html and restaurant.html */
updateCart = function (itemid, action) {
    let qtyField = document.getElementById(itemid.toString());
    if (qtyField.value == 0 && action == "decrement") {
                notify("Invalid action.");
                return; // Prevent decrement beyond 0
    }
    $.ajax({
        url: '/cart/update',
        type: 'POST',
        data: {'itemid': itemid,
               'action': action},
        success: function (data) {
        qtyField = document.getElementById(itemid.toString());
        if (action == 'increment') {
            if (qtyField.value == 0) {
                notify("Item added to cart!");
            }
            else{
                notify("Item quantity updated!");
            }
            qtyField.value++;
        }
        else if (action == 'decrement') {
            if (qtyField.value == 1) {
                notify("Item removed from cart!");
            }
            else{
                notify("Item quantity updated!");
            }
            qtyField.value--;
        }
    },
    error: function (data) {
        notify("Error updating cart. Please clear your cart of items from other restaurants before proceeding.");
    }
    }
   );
}

function cancelOrder(orderid) {
    $.ajax({
        url: '/orders/cancel',
        type: 'POST',
        data: {'orderid': orderid},
        success: function (data) {
            notify("Order successfully cancelled!");
            let order = document.getElementById(orderid.toString());
            order.outerHTML = ""; // Clear this order from the page
        },
        error: function (data) {
            notify("Error while cancelling order.");
        }
    });
}

function markOrderReady(orderid) {
    $.ajax({
        url: '/orders/markready',
        type: 'POST',
        data: {'orderid': orderid},
        success: function (data) {
            notify("Order marked as ready!");
            // Change button to "Mark as Collected"
            let order = document.getElementById(orderid.toString() + "button");
            order.innerHTML = '<button class="button tablebutton" style="vertical-align:middle" type="button" onclick="markOrderCollected('+orderid.toString()+');"><span>Mark as Collected</span></button>';
        },
        error: function (data) {
            notify("Error while marking order as ready.");
        }
    });
}

function markOrderCollected(orderid) {
    $.ajax({
        url: '/orders/markcollected',
        type: 'POST',
        data: {'orderid': orderid},
        success: function (data) {
            notify("Order marked as collected!");
            document.querySelectorAll('.onlyforpending'+orderid.toString()).forEach(e => e.remove()); // Remove the cells which are only applicable for pending orders.

            let order = document.getElementById(orderid.toString());
            let fulfilledtable = document.getElementById("fulfilledorders");
            fulfilledtable.innerHTML += order.outerHTML;  // Add this order to the fulfilled orders table
            order.outerHTML = ""; // Clear this order from the pending orders table
        },
        error: function (data) {
            notify("Error while marking order as collected.");
        }
    });
}

function toggleNewOrders() {
    $.ajax({
        url: '/orders/toggle',
        type: 'POST',
        data: {'toggle': document.getElementById("acceptorders").checked},
        success: function (data) {
            notify("Order status updated!");
        },
        error: function (data) {
            notify("Error updating order status.");
    }});
}

const modal = document.querySelector(".modal");
const overlay = document.querySelector(".overlay");
const addFoodItemBtn = document.querySelector(".addfooditem");
const editFoodItemBtn = document.querySelector(".editfooditem");
const closeModalBtn = document.querySelector(".btn-close");
const modalForm = document.getElementById("modalform");

// Close the Modal
const closeModal = function () {
  modal.classList.add("hidden");
  overlay.classList.add("hidden");
};

// Close the modal when the close button or the overlay is clicked
closeModalBtn.addEventListener("click", closeModal);
overlay.addEventListener("click", closeModal);

// Close the modal when the Esc key is pressed
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape" && !modal.classList.contains("hidden")) {
    closeModal();
  }
});

// Open the Modal
const openModal = function () {
  modal.classList.remove("hidden");
  overlay.classList.remove("hidden");
};


const modalDeleteFoodItem = function () {
    let modalitemid = document.getElementById("modalitemid");
    if(modalitemid.value=="") {
    // For add food item
        closeModal();
    }
    else{
    // for edit/delete food item
        modalForm.action = "/fooditem/delete";
        modalForm.submit();
    }
}

const addEditFoodItem = function (itemid=null, name=null, description=null, price=null, restrictions=null) {
   if(itemid) {
      let modalitemid = document.getElementById("modalitemid");
      modalitemid.value = itemid;

      modalheader = document.querySelector(".modal-header");
      modalheader.innerHTML = "Edit Food Item";

      modalForm.action = "/fooditem/edit";
      document.getElementById("modalname").value = name;
        document.getElementById("modaldesc").value = description;
        document.getElementById("modalprice").value = price;

      if(restrictions.includes("dairy")){
        document.getElementById("dietarydairy").checked = true;
      }
      else{
        document.getElementById("dietarydairy").checked = false;
      }

      if(restrictions.includes("meat")){
        document.getElementById("dietarymeat").checked = true;
      }
        else{
        document.getElementById("dietarymeat").checked = false;
      }

      if(restrictions.includes("seafood")){
        document.getElementById("dietaryseafood").checked = true;
      }
        else{
        document.getElementById("dietaryseafood").checked = false;
        }

      if(restrictions.includes("eggs")){
        document.getElementById("dietaryeggs").checked = true;
      }
        else{
        document.getElementById("dietaryeggs").checked = false;
        }

      if(restrictions.includes("nuts")){
        document.getElementById("dietarynuts").checked = true;
      }
        else{
        document.getElementById("dietarynuts").checked = false;
        }
   } else{
        // Reset modal form
        modalheader = document.querySelector(".modal-header");
        modalheader.innerHTML = "Add Food Item";
        modalForm.action = "/fooditem/add";
        document.getElementById("modalname").value = "";
        document.getElementById("modaldesc").value = "";
        document.getElementById("modalprice").value = "";
        document.getElementById("dietarydairy").checked = false;
        document.getElementById("dietarymeat").checked = false;
        document.getElementById("dietaryseafood").checked = false;
        document.getElementById("dietaryeggs").checked = false;
        document.getElementById("dietarynuts").checked = false;
   }
    openModal();
};

const openAddReviewModal = function (orderid) {
    document.getElementById("modalitemid").value = orderid;
    modalitemid.value = orderid;
    openModal();
}

const modalSetStars = function (stars) {
    document.getElementById("modalstars").value = stars;
    // Change the visible stars to reflect the rating
    for(let i=stars+1; i<=5; i++) {
        document.getElementById("modalstar"+i.toString()).classList.remove("checked");
    }
    for(let i=1; i<=stars; i++) {
        document.getElementById("modalstar"+i.toString()).classList.add("checked");
    }
}

$("#modaladdreviewform").submit(function(e) {
    e.preventDefault();
    $.ajax({
        url: '/reviews/add',
        type: 'POST',
        data: $('#modaladdreviewform').serialize(),
        success: function(data){
            notify("Review added successfully!");
            closeModal();

            // Replace the "Add Review" button with the user's review
            stars = document.getElementById("modalstars").value
            modalitemid = document.getElementById("modalitemid")
            reviewbtn = document.getElementById(modalitemid.value+"reviewbtn");
            reviewbtn.innerHTML = '<span class="fa fa-star checked"></span>&nbsp;'.repeat(stars) + '<span class="fa fa-star"></span>&nbsp;'.repeat(5-stars);

            // Clear the user inputs from the modal
            for(let i=1; i<=5; i++) {
                document.getElementById("modalstar"+i.toString()).classList.remove("checked");
            }
            document.getElementById("modalstars").value = 0;
            document.getElementById("modaltitle").value = "";
            document.getElementById("modaldesc").value = "";
            modalitemid.value = "";
        }
    });
});
