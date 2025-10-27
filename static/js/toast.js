// Toast Notification System
// Provides accessible toast notifications with animations

const ToastType = {
  SUCCESS: 'success',
  ERROR: 'error',
  INFO: 'info',
  WARNING: 'warning'
};

class ToastManager {
  constructor() {
    this.container = null;
    this.toasts = [];
    this.init();
  }

  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.className = 'toast-container';
      this.container.setAttribute('aria-live', 'polite');
      this.container.setAttribute('aria-atomic', 'true');
      document.body.appendChild(this.container);
    }
  }

  show({ message, type = ToastType.INFO, timeout = 3000 }) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    
    const icon = this.getIcon(type);
    
    toast.innerHTML = `
      <div class="toast-icon">${icon}</div>
      <div class="toast-message">${this.escapeHtml(message)}</div>
      <button class="toast-close" aria-label="Fechar notificação" type="button">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    `;

    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => this.remove(toast));

    this.container.appendChild(toast);
    this.toasts.push(toast);

    // Trigger animation
    requestAnimationFrame(() => {
      toast.classList.add('toast-show');
    });

    // Auto remove
    if (timeout > 0) {
      setTimeout(() => this.remove(toast), timeout);
    }

    return toast;
  }

  remove(toast) {
    if (!toast || !toast.parentNode) return;
    
    toast.classList.remove('toast-show');
    toast.classList.add('toast-hide');
    
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
      this.toasts = this.toasts.filter(t => t !== toast);
    }, 300);
  }

  getIcon(type) {
    switch (type) {
      case ToastType.SUCCESS:
        return `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="9" stroke="currentColor" stroke-width="2"/>
          <path d="M6 10L9 13L14 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>`;
      case ToastType.ERROR:
        return `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="9" stroke="currentColor" stroke-width="2"/>
          <path d="M10 6V11M10 14V14.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
      case ToastType.WARNING:
        return `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M10 2L2 17H18L10 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M10 8V12M10 15V15.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
      case ToastType.INFO:
      default:
        return `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="9" stroke="currentColor" stroke-width="2"/>
          <path d="M10 9V14M10 6V6.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
    }
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  clearAll() {
    this.toasts.forEach(toast => this.remove(toast));
  }
}

// Global instance
const toastManager = new ToastManager();

// Global function for easy use
function showToast(message, type = ToastType.INFO, timeout = 3000) {
  return toastManager.show({ message, type, timeout });
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ToastManager, ToastType, showToast };
}
