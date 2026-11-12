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
  const sidebar = document.querySelector('.sidebar');
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener('click', () => {
      sidebar.classList.toggle('hidden');
      sidebar.classList.toggle('md:block');
    });
  }
});
