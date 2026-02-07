

document.addEventListener('DOMContentLoaded', function () {

    /* =========================
       Search Button
    ========================= */
    const searchButton = document.getElementById('search-button');
    if (searchButton) {
        searchButton.addEventListener('click', function () {
            console.log('Search clicked');
        });
    }

    /* =========================
       Cart Button
    ========================= */
    const cartButton = document.getElementById('cart-button');
    if (cartButton) {
        cartButton.addEventListener('click', function () {
            console.log('Cart clicked');
        });
    }

});

/* =========================
   ADD TO CART
========================= */
function addToCart(event, productId) {
    event.stopPropagation();

    fetch(`/cart/add/${productId}/`, {
        method: "GET",
        credentials: "same-origin"
    })
    .then(response => {
        if (response.status === 401) {
            showAuthPopup();
            return;
        }
        return response.json();
    })
    .then(data => {
        if (!data) return;

        if (data.status === "success") {
            showToast(`${data.product_name} added to cart`);
            animateCartIcon();
        }
    })
    .catch(err => console.error("Cart Error:", err));
}

/* ===== SHOW AUTH POPUP ===== */
function showAuthPopup() {
    const popup = document.getElementById("auth-popup");
    popup.classList.add("show");
    document.body.style.overflow = "hidden";
}

/* =========================
   TOAST MESSAGE
========================= */
function showToast(message) {
    const toast = document.getElementById("cart-toast");

    if (!toast) {
        console.error("❌ cart-toast not found");
        return;
    }

    toast.textContent = message;
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 2000);
}

/* =========================
   CART ICON ANIMATION
========================= */
function animateCartIcon() {
    const cartBtn = document.getElementById("cart-button");
    if (!cartBtn) return;

    cartBtn.classList.add("cart-bounce");

    setTimeout(() => {
        cartBtn.classList.remove("cart-bounce");
    }, 400);
}

function removeFromCart(productId) {
    fetch(`/cart/remove/${productId}/`, {
        method: "GET",
        credentials: "same-origin"
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            location.reload(); // refresh cart page
        }
    })
    .catch(error => console.error("Remove Error:", error));
}


function increaseQty(productId) {
    fetch(`/cart/increase/${productId}/`, {
        method: "GET",
        credentials: "same-origin"
    })
    .then(() => location.reload())
    .catch(err => console.error(err));
}

function decreaseQty(productId) {
    fetch(`/cart/decrease/${productId}/`, {
        method: "GET",
        credentials: "same-origin"
    })
    .then(() => location.reload())
    .catch(err => console.error(err));
}

