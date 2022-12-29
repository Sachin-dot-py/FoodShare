addToCart = function (itemid, restid) {
    $.ajax({
        url: '/cart/add',
        type: 'POST',
        data: {'itemid': itemid,
               'restid': restid},
        success: function (data) {
        notify("Item successfully added to cart.");
            // do something
        }
    });
}
function notify(notification) {
  snackbar.innerHTML = notification;
  snackbar.className = "show";
  setTimeout(function(){ snackbar.className = snackbar.className.replace("show", ""); }, 3000);
}
