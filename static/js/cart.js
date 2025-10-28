// Centralized Cart Management System
// Provides consistent cart operations across the application

const CART_STORAGE_KEY = 'akkaui_cart_v1';
const OLD_CART_KEY = 'akka_cart';

class CartManager {
  constructor() {
    this.migrateOldCart();
  }

  // Migrate old cart data to new storage key
  migrateOldCart() {
    try {
      const oldCart = localStorage.getItem(OLD_CART_KEY);
      const newCart = localStorage.getItem(CART_STORAGE_KEY);
      
      if (oldCart && !newCart) {
        localStorage.setItem(CART_STORAGE_KEY, oldCart);
        localStorage.removeItem(OLD_CART_KEY);
        console.log('Cart migrated to new storage key');
      }
    } catch (error) {
      console.error('Failed to migrate cart:', error);
    }
  }

  // Get cart from localStorage
  getCart() {
    try {
      const cart = localStorage.getItem(CART_STORAGE_KEY);
      return cart ? JSON.parse(cart) : [];
    } catch (error) {
      console.error('Failed to get cart:', error);
      return [];
    }
  }

  // Save cart to localStorage
  saveCart(cart) {
    try {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
      this.updateCartCount();
      this.dispatchCartUpdateEvent();
      return true;
    } catch (error) {
      console.error('Failed to save cart:', error);
      if (typeof showToast === 'function') {
        showToast('Erro ao salvar carrinho', 'error');
      }
      return false;
    }
  }

  // Add item to cart
  addToCart(item) {
    console.log('[CartManager] addToCart recebeu:', item);
    
    if (!item || !item.id) {
      console.error('[CartManager] Invalid item:', item);
      return false;
    }

    const cart = this.getCart();
    console.log('[CartManager] Carrinho atual:', cart);
    
    const existingItem = cart.find(i => i.id === item.id);

    if (existingItem) {
      // Não permitir mais de 1 do mesmo SVG
      console.log('[CartManager] Item já existe no carrinho, não adicionando novamente');
      if (typeof showToast === 'function') {
        showToast('Este item já está no seu carrinho', 'info');
      }
      return false;
    } else {
      console.log('[CartManager] Adicionando novo item');
      cart.push({
        id: item.id,
        name: item.name || 'Item sem nome',
        price: parseFloat(item.price) || 0,
        quantity: 1,
        type: item.type || 'svg',
        thumbnail: item.thumbnail || null
      });
    }

    console.log('[CartManager] Carrinho após adição:', cart);
    const saved = this.saveCart(cart);
    console.log('[CartManager] Salvo com sucesso:', saved);
    
    if (saved && typeof showToast === 'function') {
      showToast('Item adicionado ao carrinho!', 'success');
    }
    
    return saved;
  }

  // Remove item from cart
  removeFromCart(itemId) {
    if (!itemId) {
      console.error('Invalid itemId');
      return false;
    }

    const cart = this.getCart();
    const newCart = cart.filter(item => item.id !== itemId);
    
    if (newCart.length === cart.length) {
      console.warn('Item not found in cart:', itemId);
      return false;
    }

    const saved = this.saveCart(newCart);
    
    if (saved && typeof showToast === 'function') {
      showToast('Item removido do carrinho', 'info');
    }
    
    return saved;
  }

  // Update item quantity
  updateQuantity(itemId, delta) {
    if (!itemId || typeof delta !== 'number') {
      console.error('Invalid parameters:', { itemId, delta });
      return false;
    }

    const cart = this.getCart();
    const item = cart.find(i => i.id === itemId);

    if (!item) {
      console.warn('Item not found in cart:', itemId);
      return false;
    }

    item.quantity = Math.max(1, (item.quantity || 1) + delta);
    return this.saveCart(cart);
  }

  // Set item quantity directly
  setQuantity(itemId, quantity) {
    if (!itemId || typeof quantity !== 'number' || quantity < 1) {
      console.error('Invalid parameters:', { itemId, quantity });
      return false;
    }

    const cart = this.getCart();
    const item = cart.find(i => i.id === itemId);

    if (!item) {
      console.warn('Item not found in cart:', itemId);
      return false;
    }

    item.quantity = Math.max(1, Math.floor(quantity));
    return this.saveCart(cart);
  }

  // Calculate cart totals
  calculateTotals() {
    const cart = this.getCart();
    
    const subtotal = cart.reduce((sum, item) => {
      return sum + (parseFloat(item.price) || 0) * (item.quantity || 1);
    }, 0);

    const itemCount = cart.reduce((sum, item) => {
      return sum + (item.quantity || 1);
    }, 0);

    return {
      subtotal: parseFloat(subtotal.toFixed(2)),
      itemCount,
      items: cart.length
    };
  }

  // Update cart badge count
  updateCartCount() {
    const totals = this.calculateTotals();
    const badges = document.querySelectorAll('.cart-badge, #cart-badge');
    
    badges.forEach(badge => {
      badge.textContent = totals.itemCount;
      badge.style.display = totals.itemCount > 0 ? 'flex' : 'none';
    });

    return totals.itemCount;
  }

  // Clear entire cart
  clearCart() {
    try {
      localStorage.removeItem(CART_STORAGE_KEY);
      this.updateCartCount();
      this.dispatchCartUpdateEvent();
      
      if (typeof showToast === 'function') {
        showToast('Carrinho limpo', 'info');
      }
      
      return true;
    } catch (error) {
      console.error('Failed to clear cart:', error);
      return false;
    }
  }

  // Dispatch custom event for cart updates
  dispatchCartUpdateEvent() {
    const event = new CustomEvent('cartUpdated', {
      detail: {
        cart: this.getCart(),
        totals: this.calculateTotals()
      }
    });
    window.dispatchEvent(event);
  }

  // Get item by ID
  getItem(itemId) {
    const cart = this.getCart();
    return cart.find(item => item.id === itemId) || null;
  }

  // Check if item is in cart
  isInCart(itemId) {
    return this.getItem(itemId) !== null;
  }
}

// Global instance
const cartManager = new CartManager();

// Global convenience functions
function getCart() {
  return cartManager.getCart();
}

function saveCart(cart) {
  return cartManager.saveCart(cart);
}

function addToCart(id, name, price, type = 'svg') {
  console.log('[Cart Debug] addToCart chamado com:', { id, name, price, type });
  const result = cartManager.addToCart({ id, name, price, type });
  console.log('[Cart Debug] addToCart resultado:', result);
  return result;
}

function removeFromCart(itemId) {
  return cartManager.removeFromCart(itemId);
}

function updateQuantity(itemId, delta) {
  return cartManager.updateQuantity(itemId, delta);
}

function calculateTotals() {
  return cartManager.calculateTotals();
}

function updateCartCount() {
  return cartManager.updateCartCount();
}

function clearCart() {
  return cartManager.clearCart();
}

// Initialize cart count on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    cartManager.updateCartCount();
  });
} else {
  cartManager.updateCartCount();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { CartManager, cartManager };
}
