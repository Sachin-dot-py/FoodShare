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
    failure: function (data) {
        notify("Error updating cart. Please clear your cart of items from other restaurants before proceeding.");
    }
    }
   );
}
function notify(notification) {
  snackbar.innerHTML = notification;
  snackbar.className = "show";
  setTimeout(function(){ snackbar.className = snackbar.className.replace("show", ""); }, 3000);
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
        failure: function (data) {
            notify("Error cancelling order.");
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
            order.innerHTML = '<button onclick="markOrderCollected('+orderid+');">Mark as Collected</button>';
        },
        failure: function (data) {
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
        failure: function (data) {
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
        failure: function (data) {
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
    modalForm.action = "/fooditem/delete";
    modalForm.submit();
}

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
