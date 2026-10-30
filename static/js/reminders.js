/**
 * MediCare Hub – Medicine Reminders System
 * Daily and Weekly view toggles, family member filters, and browser reminder triggers
 */

document.addEventListener('DOMContentLoaded', () => {
  initScheduleTabs();
  initMemberFilter();
  initRemindersActions();
});

function initScheduleTabs() {
  const dailyTab = document.getElementById('tabDailySchedule');
  const weeklyTab = document.getElementById('tabWeeklySchedule');
  const dailyView = document.getElementById('dailyScheduleView');
  const weeklyView = document.getElementById('weeklyScheduleView');

  if (dailyTab && weeklyTab) {
    dailyTab.addEventListener('click', () => {
      dailyTab.classList.add('active', 'btn-primary');
      dailyTab.classList.remove('btn-secondary');
      weeklyTab.classList.remove('active', 'btn-primary');
      weeklyTab.classList.add('btn-secondary');

      if (dailyView) dailyView.style.display = 'block';
      if (weeklyView) weeklyView.style.display = 'none';
    });

    weeklyTab.addEventListener('click', () => {
      weeklyTab.classList.add('active', 'btn-primary');
      weeklyTab.classList.remove('btn-secondary');
      dailyTab.classList.remove('active', 'btn-primary');
      dailyTab.classList.add('btn-secondary');

      if (dailyView) dailyView.style.display = 'none';
      if (weeklyView) weeklyView.style.display = 'block';
    });
  }
}

function initMemberFilter() {
  const memberSelect = document.getElementById('filterScheduleMember');
  if (!memberSelect) return;

  memberSelect.addEventListener('change', () => {
    const selectedMember = memberSelect.value;
    const items = document.querySelectorAll('.schedule-dose-card');

    items.forEach(card => {
      const cardMember = card.getAttribute('data-member-id');
      if (!selectedMember || cardMember === selectedMember) {
        card.style.display = '';
      } else {
        card.style.display = 'none';
      }
    });
  });
}

function initRemindersActions() {
  document.querySelectorAll('.btn-rem-action').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const button = e.currentTarget;
      const prescriptionId = button.getAttribute('data-prescription-id');
      const slot = button.getAttribute('data-slot');
      const action = button.getAttribute('data-action');
      const card = button.closest('.schedule-dose-card');

      button.disabled = true;
      button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

      fetch('/api/doses/record', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prescription_id: prescriptionId,
          scheduled_time: slot,
          status: action,
          scheduled_date: new Date().toISOString().split('T')[0]
        })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          const actionWrap = card.querySelector('.schedule-action-wrap');
          if (action === 'taken') {
            actionWrap.innerHTML = `<span class="dose-status-tag status-taken"><i class="fas fa-check-circle"></i> Taken</span>`;
            showToast('success', 'Dose Recorded', `${data.medicine_name} marked as Taken. Remaining: ${data.remaining_stock} units.`);
          } else {
            actionWrap.innerHTML = `<span class="dose-status-tag status-missed"><i class="fas fa-times-circle"></i> Missed</span>`;
            showToast('info', 'Dose Logged', `${data.medicine_name} marked as Missed.`);
          }

          if (data.refill_alert_created) {
            showToast('warning', 'Low Stock Alert', `${data.medicine_name} stock is low! Please check Refill Alerts.`);
          }
        } else {
          showToast('danger', 'Error', data.message || 'Could not record dose.');
          button.disabled = false;
          button.innerHTML = action === 'taken' ? 'Taken' : 'Missed';
        }
      })
      .catch(err => {
        console.error(err);
        showToast('danger', 'Error', 'Server connection failure.');
        button.disabled = false;
        button.innerHTML = action === 'taken' ? 'Taken' : 'Missed';
      });
    });
  });
}

