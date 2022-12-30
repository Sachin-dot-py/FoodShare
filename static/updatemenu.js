const modal = document.querySelector(".modal");
const overlay = document.querySelector(".overlay");
const addFoodItemBtn = document.querySelector(".addfooditem");
const editFoodItemBtn = document.querySelector(".editfooditem");
const closeModalBtn = document.querySelector(".btn-close");
const modalForm = document.getElementById("modalform");
const snackbar = document.getElementById("snackbar");

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

function notify(notification) {
  snackbar.innerHTML = notification;
  snackbar.className = "show";
  setTimeout(function(){ snackbar.className = snackbar.className.replace("show", ""); }, 3000);
}



//// Open the Modal on Edit Food Item button click
//openModalBtn.addEventListener("click", openModal);
