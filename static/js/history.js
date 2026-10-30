/**
 * MediCare Hub – Medicine History, Reports & Analytics
 * Comprehensive Chart.js visualizations and CSV data export
 */

document.addEventListener('DOMContentLoaded', () => {
  initHistoryFilters();
  initAnalyticsCharts();
  initCsvExport();
});

function initHistoryFilters() {
  const memberFilter = document.getElementById('histMemberFilter');
  const statusFilter = document.getElementById('histStatusFilter');
  const searchFilter = document.getElementById('histSearchInput');

  const applyFilters = () => {
    const memberVal = memberFilter ? memberFilter.value : '';
    const statusVal = statusFilter ? statusFilter.value : '';
    const searchVal = searchFilter ? searchFilter.value.toLowerCase().trim() : '';

    const rows = document.querySelectorAll('#historyTableBody tr');
    let visibleCount = 0;

    rows.forEach(row => {
      const rowMember = row.getAttribute('data-member') || '';
      const rowStatus = row.getAttribute('data-status') || '';
      const rowText = row.innerText.toLowerCase();

      const memberMatch = !memberVal || rowMember === memberVal;
      const statusMatch = !statusVal || rowStatus === statusVal;
      const searchMatch = !searchVal || rowText.includes(searchVal);

      if (memberMatch && statusMatch && searchMatch) {
        row.style.display = '';
        visibleCount++;
      } else {
        row.style.display = 'none';
      }
    });

    const countEl = document.getElementById('histCountDisplay');
    if (countEl) countEl.textContent = `Showing ${visibleCount} records`;
  };

  if (memberFilter) memberFilter.addEventListener('change', applyFilters);
  if (statusFilter) statusFilter.addEventListener('change', applyFilters);
  if (searchFilter) searchFilter.addEventListener('input', applyFilters);
}

function initAnalyticsCharts() {
  // 1. Taken vs Missed Donut Chart
  const donutCanvas = document.getElementById('chartTakenMissed');
  if (donutCanvas) {
    const taken = parseInt(donutCanvas.getAttribute('data-taken') || '28');
    const missed = parseInt(donutCanvas.getAttribute('data-missed') || '3');

    new Chart(donutCanvas.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: ['Taken Doses', 'Missed Doses'],
        datasets: [{
          data: [taken, missed],
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

  // 2. Weekly Adherence Line Chart
  const lineCanvas = document.getElementById('chartAdherenceTrend');
  if (lineCanvas) {
    new Chart(lineCanvas.getContext('2d'), {
      type: 'line',
      data: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
          label: 'Adherence Rate (%)',
          data: [100, 100, 83, 100, 100, 80, 100],
          borderColor: '#1769E0',
          backgroundColor: 'rgba(23, 105, 224, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 3,
          pointRadius: 4,
          pointBackgroundColor: '#1769E0'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            min: 50,
            max: 100,
            ticks: { callback: v => v + '%' },
            grid: { color: '#F1F5F9' }
          },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // 3. Monthly Medicine Consumption Bar Chart
  const barCanvas = document.getElementById('chartMedConsumption');
  if (barCanvas) {
    new Chart(barCanvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: ['Metformin', 'Amlodipine', 'Amoxicillin', 'Cetirizine', 'Vitamin D3'],
        datasets: [{
          label: 'Units Consumed',
          data: [56, 28, 20, 24, 28],
          backgroundColor: '#1769E0',
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

  // 4. Refill Statistics Chart
  const refillCanvas = document.getElementById('chartRefillStats');
  if (refillCanvas) {
    new Chart(refillCanvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: ['Amlodipine (30 tab)', 'Vitamin D3 (60 cap)', 'Metformin (60 tab)'],
        datasets: [{
          label: 'Refill Cost ($)',
          data: [15.50, 22.00, 14.50],
          backgroundColor: '#20B486',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { callback: v => '$' + v }, grid: { color: '#F1F5F9' } },
          x: { grid: { display: false } }
        }
      }
    });
  }
}

function initCsvExport() {
  const exportBtn = document.getElementById('btnExportCsv');
  if (!exportBtn) return;

  exportBtn.addEventListener('click', () => {
    const table = document.querySelector('.table-custom');
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    rows.forEach(row => {
      if (row.style.display !== 'none') {
        const cols = row.querySelectorAll('th, td');
        const rowData = [];
        cols.forEach(col => {
          let text = col.innerText.replace(/(\r\n|\n|\r)/gm, ' ').replace(/"/g, '""').trim();
          rowData.push(`"${text}"`);
        });
        csv.push(rowData.join(','));
      }
    });

    const csvContent = 'data:text/csv;charset=utf-8,' + csv.join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `medicare_history_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    showToast('success', 'Export Complete', 'Medicine history exported as CSV file.');
  });
}

