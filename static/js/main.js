/**
 * MediCare Hub – Core Global JavaScript
 * Toast notifications, modals, dropdowns, and browser notification integration
 */

document.addEventListener('DOMContentLoaded', () => {
  initDropdowns();
  initModals();
  initMobileNav();
  initNotificationsSystem();
  initGlobalSearch();
});

// ==========================================
// Toast Notifications
// ==========================================
function showToast(type = 'info', title = 'Notification', message = '') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  let iconClass = 'fa-info-circle';
  if (type === 'success') iconClass = 'fa-check-circle';
  if (type === 'danger') iconClass = 'fa-exclamation-circle';
  if (type === 'warning') iconClass = 'fa-exclamation-triangle';

  toast.innerHTML = `
    <div class="toast-icon">
      <i class="fas ${iconClass}"></i>
    </div>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      ${message ? `<div class="toast-message">${message}</div>` : ''}
    </div>
    <button type="button" class="modal-close-btn" style="font-size: 0.9rem;" onclick="this.parentElement.remove()">
      <i class="fas fa-times"></i>
    </button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// ==========================================
// Modal Handlers
// ==========================================
function initModals() {
  // Close modals when clicking backdrop
  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal(modal.id);
      }
    });
  });

  // Close with Esc key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const activeModal = document.querySelector('.modal-overlay.active');
      if (activeModal) closeModal(activeModal.id);
    }
  });
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// ==========================================
// Dropdowns & Mobile Navigation
// ==========================================
function initDropdowns() {
  const notifBtn = document.getElementById('notifBellBtn');
  const notifMenu = document.getElementById('notifDropdown');
  const profileBtn = document.getElementById('profileDropdownBtn');
  const profileMenu = document.getElementById('profileDropdownMenu');

  if (notifBtn && notifMenu) {
    notifBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      notifMenu.classList.toggle('show');
      if (profileMenu) profileMenu.classList.remove('show');
    });
  }

  if (profileBtn && profileMenu) {
    profileBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      profileMenu.classList.toggle('show');
      if (notifMenu) notifMenu.classList.remove('show');
    });
  }

  document.addEventListener('click', () => {
    if (notifMenu) notifMenu.classList.remove('show');
    if (profileMenu) profileMenu.classList.remove('show');
  });
}

function initMobileNav() {
  const toggleBtn = document.getElementById('mobileNavToggle');
  const sidebar = document.getElementById('appSidebar');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggleBtn) {
        sidebar.classList.remove('open');
      }
    });
  }
}

// ==========================================
// Global Search (Live Page Navigation)
// ==========================================
function initGlobalSearch() {
  const searchInput = document.getElementById('globalSearchInput');
  if (!searchInput) return;

  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const q = searchInput.value.trim();
      if (q) {
        // Redirect to Prescriptions or Pharmacy finder depending on query
        window.location.href = `/prescriptions?search=${encodeURIComponent(q)}`;
      }
    }
  });
}

// ==========================================
// Browser Notification API
// ==========================================
function initNotificationsSystem() {
  // Check permission status
  if ('Notification' in window) {
    if (Notification.permission === 'default') {
      // Prompt user gently after login
      console.log('Browser notifications are supported and available to request.');
    }
  }

  // Poll for upcoming dose reminders every 45s while active
  setInterval(checkUpcomingReminders, 45000);
}

function requestNotificationPermission() {
  if (!('Notification' in window)) {
    showToast('warning', 'Notifications', 'This browser does not support desktop notifications.');
    return;
  }

  Notification.requestPermission().then(permission => {
    if (permission === 'granted') {
      showToast('success', 'Permission Granted', 'MediCare Hub will now notify you of scheduled medicine doses.');
      new Notification('MediCare Hub Reminders Active', {
        body: "Your family's medicine reminders are now active on this device.",
        icon: '/static/images/logo-icon.svg'
      });
    } else {
      showToast('warning', 'Permission Denied', 'Desktop notifications are blocked in your browser settings.');
    }
  });
}

function checkUpcomingReminders() {
  fetch('/api/reminders/check-due')
    .then(res => res.json())
    .then(data => {
      if (data && data.due_reminders && data.due_reminders.length > 0) {
        data.due_reminders.forEach(rem => {
          // Trigger in-app toast
          showToast('info', `Medicine Reminder: ${rem.slot_name}`, `${rem.patient_name} - ${rem.medicine_name} (${rem.dosage})`);

          // Trigger browser notification if permitted
          if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(`MediCare Hub: Time for ${rem.medicine_name}`, {
              body: `${rem.patient_name} is scheduled to take ${rem.dosage} now (${rem.slot_name}).`,
              icon: '/static/images/logo-icon.svg'
            });
          }
        });
      }
    })
    .catch(err => console.debug('Reminder check:', err));
}

