/**
 * MediCare Hub – Dashboard Scripts
 * Live dose logging, automatic stock update feedback, and Chart.js adherence graphs
 */

document.addEventListener('DOMContentLoaded', () => {
  initDoseActionButtons();
  initDashboardAnalytics();
});

function initDoseActionButtons() {
  document.querySelectorAll('.btn-dose-action').forEach(btn => {
    btn.addEventListener('click', handleDoseAction);
  });
}

function handleDoseAction(e) {
  const btn = e.currentTarget;
  const prescriptionId = btn.getAttribute('data-prescription-id');
  const slot = btn.getAttribute('data-slot');
  const action = btn.getAttribute('data-action'); // 'taken' or 'missed'
  const parentContainer = btn.closest('.dose-item');

  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

  fetch('/api/doses/record', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
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
      // Replace buttons with permanent status badge
      const actionsWrap = parentContainer.querySelector('.dose-actions');
      if (action === 'taken') {
        actionsWrap.innerHTML = `<span class="dose-status-tag status-taken"><i class="fas fa-check"></i> Taken</span>`;
        parentContainer.classList.add('taken');
        showToast('success', 'Dose Recorded', `${data.medicine_name} marked as Taken. Remaining stock: ${data.remaining_stock} units.`);

        if (data.refill_alert_created) {
          showToast('warning', 'Low Stock Warning', `${data.medicine_name} is running low! (${data.estimated_days} days remaining).`);
        }
      } else {
        actionsWrap.innerHTML = `<span class="dose-status-tag status-missed"><i class="fas fa-times"></i> Missed</span>`;
        parentContainer.classList.add('missed');
        showToast('info', 'Dose Logged', `${data.medicine_name} marked as Missed. Stock was not deducted.`);
      }

      // Update stat cards dynamically if present
      const dosesStatEl = document.getElementById('statTodayDosesTaken');
      if (dosesStatEl && data.today_taken_count !== undefined) {
        dosesStatEl.textContent = data.today_taken_count;
      }

      const pendingRefillsEl = document.getElementById('statPendingRefills');
      if (pendingRefillsEl && data.active_refill_count !== undefined) {
        pendingRefillsEl.textContent = data.active_refill_count;
      }
    } else {
      showToast('danger', 'Error', data.message || 'Could not record dose.');
      btn.disabled = false;
      btn.innerHTML = action === 'taken' ? '<i class="fas fa-check"></i> Taken' : '<i class="fas fa-times"></i> Missed';
    }
  })
  .catch(err => {
    console.error(err);
    showToast('danger', 'Network Error', 'Failed to communicate with server.');
    btn.disabled = false;
    btn.innerHTML = action === 'taken' ? '<i class="fas fa-check"></i> Taken' : '<i class="fas fa-times"></i> Missed';
  });
}

function initDashboardAnalytics() {
  fetch('/api/analytics/dashboard')
    .then(res => res.json())
    .then(data => {
      // 1. Weekly Adherence Line Chart
      const lineCanvas = document.getElementById('adherenceChart');
      if (lineCanvas && data.weekly) {
        new Chart(lineCanvas.getContext('2d'), {
          type: 'line',
          data: {
            labels: data.weekly.labels,
            datasets: [
              {
                label: 'Doses Taken',
                data: data.weekly.taken,
                borderColor: '#20B486',
                backgroundColor: 'rgba(32, 180, 134, 0.1)',
                tension: 0.35,
                fill: true,
                borderWidth: 2.5,
                pointBackgroundColor: '#20B486',
                pointRadius: 4
              },
              {
                label: 'Doses Missed',
                data: data.weekly.missed,
                borderColor: '#EF5350',
                backgroundColor: 'rgba(239, 83, 80, 0.05)',
                tension: 0.35,
                fill: true,
                borderWidth: 2,
                pointBackgroundColor: '#EF5350',
                pointRadius: 4
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'top',
                labels: { boxWidth: 12, font: { family: "'Inter', sans-serif", size: 12, weight: 600 } }
              }
            },
            scales: {
              y: { beginAtZero: true, ticks: { stepSize: 1, color: '#627D98' }, grid: { color: '#F1F5F9' } },
              x: { ticks: { color: '#627D98' }, grid: { display: false } }
            }
          }
        });
      }

      // 2. Taken vs Missed Donut Chart
      const donutCanvas = document.getElementById('dashboardDonutChart');
      if (donutCanvas && data.totals) {
        new Chart(donutCanvas.getContext('2d'), {
          type: 'doughnut',
          data: {
            labels: ['Taken Doses', 'Missed Doses'],
            datasets: [{
              data: [data.totals.taken, data.totals.missed],
              backgroundColor: ['#20B486', '#EF5350'],
              borderWidth: 0,
              hoverOffset: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: 'bottom', labels: { boxWidth: 12, font: { family: "'Inter', sans-serif", weight: 600 } } }
            },
            cutout: '70%'
          }
        });
      }

      // 3. Medicine Stock Overview Horizontal Bar Chart
      const stockCanvas = document.getElementById('dashboardStockChart');
      if (stockCanvas && data.stock) {
        new Chart(stockCanvas.getContext('2d'), {
          type: 'bar',
          data: {
            labels: data.stock.labels.slice(0, 6),
            datasets: [
              {
                label: 'Available Stock',
                data: data.stock.available.slice(0, 6),
                backgroundColor: '#1769E0',
                borderRadius: 4
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: {
              x: { beginAtZero: true, grid: { color: '#F1F5F9' } },
              y: { grid: { display: false }, ticks: { font: { size: 11 } } }
            }
          }
        });
      }

      // 4. Monthly Medicine Consumption Bar Chart
      const consCanvas = document.getElementById('dashboardConsumptionChart');
      if (consCanvas && data.consumption) {
        new Chart(consCanvas.getContext('2d'), {
          type: 'bar',
          data: {
            labels: data.consumption.labels,
            datasets: [{
              label: 'Doses Taken',
              data: data.consumption.values,
              backgroundColor: '#20B486',
              borderRadius: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, grid: { color: '#F1F5F9' } },
              x: { grid: { display: false } }
            }
          }
        });
      }

    })
    .catch(err => {
      console.warn('Dashboard analytics loading error:', err);
    });
}
