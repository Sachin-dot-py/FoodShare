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
