document.addEventListener('DOMContentLoaded', () => {
  const greeting = document.querySelector('[data-greeting]');
  if (greeting) {
    const hour = new Date().getHours();
    greeting.textContent = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  }

  const dateLabel = document.querySelector('[data-current-date]');
  if (dateLabel) {
    dateLabel.textContent = new Intl.DateTimeFormat(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(new Date());
  }

  const themeToggle = document.querySelector('.theme-toggle');
  const savedTheme = localStorage.getItem('edutrack-theme');
  if (savedTheme === 'dark') {
    document.body.dataset.theme = 'dark';
  }

  const updateThemeButton = () => {
    if (!themeToggle) return;
    const isDark = document.body.dataset.theme === 'dark';
    themeToggle.innerHTML = `<i data-lucide="${isDark ? 'sun' : 'moon'}"></i>`;
    themeToggle.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
    if (window.lucide) window.lucide.createIcons();
  };

  updateThemeButton();
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const isDark = document.body.dataset.theme !== 'dark';
      document.body.dataset.theme = isDark ? 'dark' : 'light';
      localStorage.setItem('edutrack-theme', isDark ? 'dark' : 'light');
      updateThemeButton();
    });
  }

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
      const isVisible = sidebarNav.classList.toggle('is-open');
      mobileToggle.setAttribute('aria-expanded', String(isVisible));
    });
  }

  document.querySelectorAll('[data-modal-open]').forEach((button) => {
    button.addEventListener('click', () => {
      const dialog = document.getElementById(button.dataset.modalOpen);
      if (!(dialog instanceof HTMLDialogElement) || dialog.open) return;

      const currentDialog = button.closest('dialog[open]');
      if (currentDialog instanceof HTMLDialogElement) {
        currentDialog.addEventListener('close', () => dialog.showModal(), { once: true });
        currentDialog.close();
        return;
      }

      dialog.showModal();
    });
  });

  document.querySelectorAll('[data-modal-close]').forEach((button) => {
    button.addEventListener('click', () => button.closest('dialog')?.close());
  });

  document.querySelectorAll('dialog[data-open-on-load="true"]').forEach((dialog) => {
    if (dialog instanceof HTMLDialogElement && !dialog.open) dialog.showModal();
  });

  document.querySelectorAll('dialog.record-modal').forEach((dialog) => {
    dialog.addEventListener('click', (event) => {
      if (event.target === dialog) dialog.close();
    });
  });

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
