document.addEventListener('DOMContentLoaded', () => {
    const cartLink = document.querySelector('.cart-link');
    const cartCount = document.querySelector('.cart-count');
    const addToCartButtons = document.querySelectorAll('.add-to-cart');

    let cart = [];

    // Add to Cart Functionality
    addToCartButtons.forEach(button => {
        button.addEventListener('click', () => {
            const productCard = button.closest('.product-card');
            const productName = productCard.querySelector('h3').textContent;
            const productPrice = productCard.querySelector('.price').textContent;

            const product = {
                name: productName,
                price: productPrice,
                quantity: 1
            };

            // Check if product already in cart
            const existingProduct = cart.find(item => item.name === productName);
            if (existingProduct) {
                existingProduct.quantity += 1;
            } else {
                cart.push(product);
            }

            updateCartCount();
            showCartNotification(product);
        });
    });

    function updateCartCount() {
        const totalItems = cart.reduce((total, item) => total + item.quantity, 0);
        cartCount.textContent = totalItems;
    }

    function showCartNotification(product) {
        const notification = document.createElement('div');
        notification.classList.add('cart-notification');
        notification.innerHTML = `
        <p>✔ ${product.name} ajouté au panier</p>
      `;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Cart Link (placeholder for future implementation)
    cartLink.addEventListener('click', () => {
        // Future: Open cart modal/sidebar
        alert('Fonctionnalité panier à venir !');
    });
});