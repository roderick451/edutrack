document.addEventListener('DOMContentLoaded', () => {
  const flashMessages = document.querySelectorAll('.flash-message');
  flashMessages.forEach((message, index) => {
    setTimeout(() => {
      message.style.opacity = '0';
      message.style.transform = 'translateY(-8px)';
      message.style.transition = 'all 0.25s ease';
      setTimeout(() => message.remove(), 250);
    }, 3000 + index * 200);
  });

  const mobileToggle = document.querySelector('.mobile-toggle');
  const sidebarNav = document.querySelector('.sidebar-nav');
  if (mobileToggle && sidebarNav) {
    mobileToggle.addEventListener('click', () => {
      const isVisible = sidebarNav.style.display === 'flex';
      sidebarNav.style.display = isVisible ? 'none' : 'flex';
    });
  }

  const passwordButtons = document.querySelectorAll('[data-password-toggle]');
  passwordButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const field = button.closest('.password-shell')?.querySelector('input');
      if (!field) return;

      const showPassword = field.type === 'password';
      field.type = showPassword ? 'text' : 'password';
      button.textContent = showPassword ? 'Hide' : 'Show';
      button.setAttribute('aria-label', showPassword ? 'Hide password' : 'Show password');
    });
  });
});
