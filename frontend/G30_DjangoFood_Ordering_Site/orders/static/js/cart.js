// Add to cart
function addToCart(itemId, quantity = 1) {
    if (!itemId || quantity < 1) {
        showError('Invalid item or quantity');
        return;
    }

    console.log('Adding to cart:', { itemId, quantity });
    fetch('/cart/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            item_id: itemId,
            quantity: quantity
        })
    })
    .then(response => {
        console.log('Add to cart response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Add to cart response data:', data);
        if (data.error) {
            showError(data.error);
        } else {
            updateCartUI(data.cart);
            showSuccess('Item added to cart!');
        }
    })
    .catch(error => {
        console.error('Add to cart error:', error);
        showError('Error adding item to cart');
    });
}

// Update cart item quantity
function updateCartItem(itemId, quantity) {
    if (!itemId || quantity < 0) {
        showError('Invalid item or quantity');
        return;
    }

    console.log('Updating cart item:', { itemId, quantity });
    fetch('/cart/update/', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            item_id: itemId,
            quantity: quantity
        })
    })
    .then(response => {
        console.log('Update cart response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Update cart response data:', data);
        if (data.error) {
            showError(data.error);
        } else {
            updateCartUI(data.cart);
        }
    })
    .catch(error => {
        console.error('Update cart error:', error);
        showError('Error updating cart');
    });
}

// Remove item from cart
function removeFromCart(itemId) {
    if (!itemId) {
        showError('Invalid item');
        return;
    }

    console.log('Removing from cart:', { itemId });
    fetch('/cart/remove/', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            item_id: itemId
        })
    })
    .then(response => {
        console.log('Remove from cart response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Remove from cart response data:', data);
        if (data.error) {
            showError(data.error);
        } else {
            updateCartUI(data.cart);
            showSuccess('Item removed from cart!');
        }
    })
    .catch(error => {
        console.error('Remove from cart error:', error);
        showError('Error removing item from cart');
    });
}

// Update cart UI
function updateCartUI(cartData) {
    console.log('Updating cart UI with data:', cartData);
    const cartContainer = document.getElementById('cart-items');
    if (!cartContainer) return;

    let totalPrice = 0;
    let totalItems = 0;
    let cartHTML = '';

    if (!cartData || Object.keys(cartData).length === 0) {
        cartHTML = '<div class="text-center">Your cart is empty</div>';
    } else {
        for (const [itemId, item] of Object.entries(cartData)) {
            if (!item || !item.price || !item.quantity) continue;
            
            totalPrice += item.price * item.quantity;
            totalItems += item.quantity;

            cartHTML += `
                <div class="cart-item" data-item-id="${itemId}">
                    <div class="item-details">
                        <h4>${item.name || 'Unknown Item'}</h4>
                        <p>₹${item.price.toFixed(2)}</p>
                    </div>
                    <div class="quantity-controls">
                        <button onclick="updateCartItem(${itemId}, ${item.quantity - 1})" ${item.quantity <= 1 ? 'disabled' : ''}>-</button>
                        <span>${item.quantity}</span>
                        <button onclick="updateCartItem(${itemId}, ${item.quantity + 1})">+</button>
                    </div>
                    <button onclick="removeFromCart(${itemId})" class="remove-btn">Remove</button>
                </div>
            `;
        }
    }

    cartContainer.innerHTML = cartHTML;
    document.getElementById('total-price').textContent = `₹${totalPrice.toFixed(2)}`;
    document.getElementById('total-items').textContent = totalItems;
    
    // Show/hide checkout button based on cart contents
    const checkoutBtn = document.getElementById('checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.style.display = totalItems > 0 ? 'inline-block' : 'none';
    }
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show success message
function showSuccess(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success';
    alertDiv.textContent = message;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 3000);
}

// Show error message
function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger';
    alertDiv.textContent = message;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 3000);
} 