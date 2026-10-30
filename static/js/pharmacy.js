/**
 * MediCare Hub – Pharmacy Availability Finder & Interactive Map
 * Leaflet.js map, OpenStreetMap tiles, real-time distance sorting, and sample inventory search in Rajkot, Gujarat
 */

let mapInstance = null;
let userMarker = null;
let pharmacyMarkers = [];
let userLocation = { lat: 22.3039, lng: 70.8022 }; // Default Rajkot, Gujarat, India
let pharmaciesData = [];

document.addEventListener('DOMContentLoaded', () => {
  initPharmacyFinder();
});

function initPharmacyFinder() {
  const mapElement = document.getElementById('map');
  if (!mapElement) return;

  // 1. Initialize Map centered on Rajkot
  mapInstance = L.map('map', {
    zoomControl: true,
    scrollWheelZoom: true
  }).setView([userLocation.lat, userLocation.lng], 13);

  // OpenStreetMap Tile Layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(mapInstance);

  // 2. Geolocation with Rajkot fallback
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        // If user is far from Rajkot, we keep Rajkot demo perspective or user perspective
        // For local demo presentation, Rajkot center is default anchor
        setUserMarker(userLocation);
        loadPharmaciesData();
      },
      (err) => {
        setUserMarker(userLocation);
        loadPharmaciesData();
      },
      { timeout: 5000 }
    );
  } else {
    setUserMarker(userLocation);
    loadPharmaciesData();
  }

  // 3. Check for pre-filled medicine URL param (e.g. from Refill Alert "Find Nearby Pharmacies" button)
  const urlParams = new URLSearchParams(window.location.search);
  const medParam = urlParams.get('medicine');
  if (medParam) {
    const searchInput = document.getElementById('pharmacyMedSearch');
    if (searchInput) {
      searchInput.value = medParam;
    }
  }

  // 4. Hook Filters
  const searchInput = document.getElementById('pharmacyMedSearch');
  const distanceFilter = document.getElementById('pharmacyDistanceFilter');
  const availabilityFilter = document.getElementById('pharmacyAvailabilityFilter');

  if (searchInput) searchInput.addEventListener('input', debounce(filterPharmacies, 250));
  if (distanceFilter) distanceFilter.addEventListener('change', filterPharmacies);
  if (availabilityFilter) availabilityFilter.addEventListener('change', filterPharmacies);
}

function setUserMarker(loc) {
  const userIcon = L.divIcon({
    className: 'custom-user-marker',
    html: `
      <div style="position: relative; width: 26px; height: 26px;">
        <div style="position: absolute; width: 26px; height: 26px; background: rgba(23, 105, 224, 0.3); border-radius: 50%; animation: pulse 2s infinite;"></div>
        <div style="position: absolute; top: 4px; left: 4px; width: 18px; height: 18px; background: #1769E0; border: 2.5px solid #FFFFFF; border-radius: 50%; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>
      </div>
    `,
    iconSize: [26, 26],
    iconAnchor: [13, 13]
  });

  if (userMarker) {
    userMarker.setLatLng([loc.lat, loc.lng]);
  } else {
    userMarker = L.marker([loc.lat, loc.lng], { icon: userIcon })
      .addTo(mapInstance)
      .bindPopup('<strong>Your Location (Rajkot Demo Center)</strong>');
  }
}

function loadPharmaciesData() {
  const medicineQuery = document.getElementById('pharmacyMedSearch')?.value.trim() || '';

  fetch(`/api/pharmacies/search?user_lat=${userLocation.lat}&user_lng=${userLocation.lng}&query=${encodeURIComponent(medicineQuery)}`)
    .then(res => res.json())
    .then(data => {
      pharmaciesData = data.pharmacies || [];
      renderPharmacyResults(pharmaciesData);
      renderMapMarkers(pharmaciesData);
    })
    .catch(err => {
      console.error('Error fetching pharmacies:', err);
      showToast('danger', 'Error', 'Failed to load pharmacy data.');
    });
}

function filterPharmacies() {
  loadPharmaciesData();
}

function renderPharmacyResults(pharmacies) {
  const container = document.getElementById('pharmacyResultsList');
  const countBadge = document.getElementById('pharmacyCountBadge');
  if (!container) return;

  const distMax = parseFloat(document.getElementById('pharmacyDistanceFilter')?.value || '999');
  const availOnly = document.getElementById('pharmacyAvailabilityFilter')?.value === 'in_stock';
  const query = document.getElementById('pharmacyMedSearch')?.value.trim();

  let filtered = pharmacies.filter(p => {
    if (p.distance_km > distMax) return false;
    if (availOnly && (!p.searched_inventory || !p.searched_inventory.in_stock || p.searched_inventory.is_missing)) return false;
    return true;
  });

  if (countBadge) countBadge.textContent = `${filtered.length} found`;

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="padding: 2.5rem 1rem;">
        <div class="empty-state-icon" style="width: 54px; height: 54px; font-size: 1.4rem;">
          <i class="fas fa-prescription-bottle-alt"></i>
        </div>
        <h4>No Matching Pharmacies Found</h4>
        <p style="font-size: 0.82rem;">Try widening the distance radius or checking another medicine name. Displaying fictional demonstration data for Rajkot.</p>
      </div>
    `;
    return;
  }

  let html = '';
  filtered.forEach(p => {
    let invStatusHtml = '';

    if (query && p.searched_inventory) {
      if (p.searched_inventory.is_missing) {
        invStatusHtml = `
          <div class="pharmacy-inventory-status inventory-out-of-stock">
            <span><i class="fas fa-times-circle"></i> <strong>Currently Unavailable</strong></span>
            <small>Not in Store Inventory</small>
          </div>
        `;
      } else if (p.searched_inventory.in_stock && p.searched_inventory.stock_quantity > 0) {
        invStatusHtml = `
          <div class="pharmacy-inventory-status inventory-in-stock">
            <span><i class="fas fa-check-circle"></i> <strong>In Stock:</strong> ${p.searched_inventory.stock_quantity} ${p.searched_inventory.unit} (₹${p.searched_inventory.unit_price.toFixed(2)})</span>
            <small style="color: var(--healthcare-green-dark); font-weight: 600;">Available Now</small>
          </div>
        `;
      } else {
        invStatusHtml = `
          <div class="pharmacy-inventory-status inventory-out-of-stock">
            <span><i class="fas fa-times-circle"></i> <strong>Currently Unavailable</strong> (0 in stock)</span>
            <small>Call to Confirm</small>
          </div>
        `;
      }
    } else if (p.searched_inventory && p.searched_inventory.in_stock) {
      invStatusHtml = `
        <div class="pharmacy-inventory-status inventory-in-stock">
          <span><i class="fas fa-pills"></i> <strong>Featured Stock:</strong> ${escapeHtml(p.searched_inventory.medicine_name)} (₹${p.searched_inventory.unit_price.toFixed(2)})</span>
          <small>In Stock</small>
        </div>
      `;
    } else {
      invStatusHtml = `
        <div class="pharmacy-inventory-status inventory-unconfirmed">
          <span><i class="fas fa-phone-alt"></i> <strong>Call to Confirm</strong></span>
          <small>Standard Catalog</small>
        </div>
      `;
    }

    const openBadge = p.is_open_24h || p.is_open_now 
      ? '<span class="badge badge-success"><i class="fas fa-clock"></i> Open Now</span>' 
      : '<span class="badge badge-navy"><i class="fas fa-door-closed"></i> Closed</span>';

    html += `
      <div class="pharmacy-result-card" data-pharmacy-id="${p.id}" onclick="selectPharmacy(${p.id})">
        <div class="pharmacy-name-row">
          <div class="pharmacy-title">${escapeHtml(p.name)}</div>
          <div class="pharmacy-distance">${p.distance_km.toFixed(1)} km</div>
        </div>
        <div class="pharmacy-address">
          <i class="fas fa-map-marker-alt"></i> ${escapeHtml(p.address)}, ${escapeHtml(p.city)}
        </div>
        <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.4rem; flex-wrap: wrap;">
          ${openBadge}
          <span style="font-size: 0.78rem; color: #D97706; font-weight: 600;">
            <i class="fas fa-star"></i> ${p.rating} (${p.reviews_count} reviews)
          </span>
          <span style="font-size: 0.75rem; color: #627D98;">• ${escapeHtml(p.opening_hours)}</span>
        </div>

        ${invStatusHtml}

        <div class="pharmacy-card-footer" style="display: flex; gap: 0.4rem; flex-wrap: wrap;">
          <button type="button" class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); openPharmacyDetails(${p.id})">
            <i class="fas fa-info-circle"></i> View Details
          </button>
          <button type="button" class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); callPharmacyDemo('${escapeHtml(p.name)}', '${escapeHtml(p.phone)}')">
            <i class="fas fa-phone"></i> Call Pharmacy
          </button>
          <a href="https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lng}" target="_blank" class="btn btn-primary btn-sm" onclick="event.stopPropagation()">
            <i class="fas fa-directions"></i> Get Directions
          </a>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function renderMapMarkers(pharmacies) {
  pharmacyMarkers.forEach(m => mapInstance.removeLayer(m));
  pharmacyMarkers = [];

  const bounds = L.latLngBounds();
  if (userLocation) bounds.extend([userLocation.lat, userLocation.lng]);

  pharmacies.forEach(p => {
    let pinColor = '#1769E0';
    if (p.searched_inventory) {
      if (p.searched_inventory.is_missing || !p.searched_inventory.in_stock) {
        pinColor = '#EF5350';
      } else {
        pinColor = '#20B486';
      }
    }

    const customPin = L.divIcon({
      className: 'custom-pharmacy-pin',
      html: `
        <div style="background-color: ${pinColor}; width: 34px; height: 34px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.25); border: 2px solid #FFFFFF;">
          <i class="fas fa-plus" style="transform: rotate(45deg); color: #FFFFFF; font-size: 13px;"></i>
        </div>
      `,
      iconSize: [34, 34],
      iconAnchor: [17, 34],
      popupAnchor: [0, -34]
    });

    const marker = L.marker([p.lat, p.lng], { icon: customPin }).addTo(mapInstance);
    
    let popupContent = `
      <div style="font-family: 'Inter', sans-serif; padding: 4px; min-width: 220px;">
        <h4 style="margin: 0 0 4px 0; color: #102A43; font-size: 14px;">${escapeHtml(p.name)}</h4>
        <div style="color: #627D98; font-size: 12px; margin-bottom: 6px;">${escapeHtml(p.address)}</div>
        <div style="font-size: 12px; font-weight: 600; color: #1769E0; margin-bottom: 8px;">
          ${p.distance_km ? p.distance_km.toFixed(1) + ' km away' : ''} • ${escapeHtml(p.opening_hours)}
        </div>
        <div style="display: flex; gap: 4px; flex-wrap: wrap;">
          <button type="button" class="btn btn-secondary btn-sm" style="padding: 2px 7px; font-size: 11px;" onclick="openPharmacyDetails(${p.id})">Details</button>
          <button type="button" class="btn btn-secondary btn-sm" style="padding: 2px 7px; font-size: 11px;" onclick="callPharmacyDemo('${escapeHtml(p.name)}', '${escapeHtml(p.phone)}')">Call</button>
          <a href="https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lng}" target="_blank" class="btn btn-primary btn-sm" style="padding: 2px 7px; font-size: 11px;">Directions</a>
        </div>
      </div>
    `;

    marker.bindPopup(popupContent);
    marker.pharmacyId = p.id;

    marker.on('click', () => {
      highlightPharmacyCard(p.id);
    });

    pharmacyMarkers.push(marker);
    bounds.extend([p.lat, p.lng]);
  });

  if (pharmacies.length > 0) {
    mapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
  }
}

function selectPharmacy(id) {
  highlightPharmacyCard(id);

  const marker = pharmacyMarkers.find(m => m.pharmacyId === id);
  if (marker) {
    mapInstance.flyTo(marker.getLatLng(), 15, { duration: 0.8 });
    marker.openPopup();
  }
}

function highlightPharmacyCard(id) {
  document.querySelectorAll('.pharmacy-result-card').forEach(card => {
    if (parseInt(card.getAttribute('data-pharmacy-id')) === id) {
      card.classList.add('active');
      card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
      card.classList.remove('active');
    }
  });
}

function openPharmacyDetails(id) {
  const p = pharmaciesData.find(item => item.id === id);
  if (!p) return;

  document.getElementById('modalPharmName').textContent = p.name;

  let invRows = '';
  if (p.all_inventory && p.all_inventory.length > 0) {
    invRows = p.all_inventory.map(inv => `
      <tr>
        <td><strong>${escapeHtml(inv.medicine_name)}</strong><br><small style="color: var(--text-muted);">${escapeHtml(inv.brand_name || '')}</small></td>
        <td><span class="badge badge-navy">${escapeHtml(inv.category)}</span></td>
        <td><strong>₹${inv.unit_price.toFixed(2)}</strong></td>
        <td>
          ${inv.in_stock && inv.stock_quantity > 0 
            ? `<span class="badge badge-success"><i class="fas fa-check"></i> In Stock (${inv.stock_quantity})</span>` 
            : `<span class="badge badge-danger"><i class="fas fa-times"></i> Out of Stock</span>`}
        </td>
      </tr>
    `).join('');
  } else {
    invRows = '<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No catalog items listed. Please call to confirm stock.</td></tr>';
  }

  document.getElementById('modalPharmBody').innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-light);">
      <div>
        <h4 style="font-size: 1.15rem; color: var(--dark-navy); margin-bottom: 0.25rem;">${escapeHtml(p.name)}</h4>
        <div style="font-size: 0.85rem; color: var(--text-muted);"><i class="fas fa-map-marker-alt" style="color: var(--primary-blue);"></i> ${escapeHtml(p.address)}, ${escapeHtml(p.city)}</div>
        <div style="font-size: 0.85rem; color: var(--primary-blue); margin-top: 0.25rem;"><i class="fas fa-phone"></i> ${escapeHtml(p.phone)}</div>
      </div>
      <div style="text-align: right;">
        <span class="badge badge-success" style="font-size: 0.75rem;">${escapeHtml(p.opening_hours)}</span>
        <div style="font-size: 0.8rem; color: #D97706; font-weight: 700; margin-top: 0.35rem;">
          <i class="fas fa-star"></i> ${p.rating} (${p.reviews_count} reviews)
        </div>
      </div>
    </div>

    <div style="margin-bottom: 1rem;">
      <h5 style="font-size: 0.92rem; color: var(--dark-navy); margin-bottom: 0.5rem;"><i class="fas fa-boxes" style="color: var(--primary-blue);"></i> Pharmacy Store Catalog</h5>
      <div class="table-responsive" style="max-height: 240px; overflow-y: auto;">
        <table class="table-custom">
          <thead>
            <tr>
              <th>Medicine</th>
              <th>Category</th>
              <th>Unit Price</th>
              <th>Availability</th>
            </tr>
          </thead>
          <tbody>
            ${invRows}
          </tbody>
        </table>
      </div>
    </div>

    <div style="background-color: var(--bg-color); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 0.75rem; font-size: 0.78rem; color: var(--text-muted);">
      <i class="fas fa-info-circle" style="color: var(--primary-blue);"></i> <strong>Demonstration Note:</strong> All phone numbers and medicine inventory counts are simulated for project presentation purposes.
    </div>
  `;

  document.getElementById('modalPharmFooter').innerHTML = `
    <button type="button" class="btn btn-secondary" onclick="callPharmacyDemo('${escapeHtml(p.name)}', '${escapeHtml(p.phone)}')">
      <i class="fas fa-phone"></i> Call (${escapeHtml(p.phone)})
    </button>
    <a href="https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lng}" target="_blank" class="btn btn-primary">
      <i class="fas fa-directions"></i> Get Directions
    </a>
    <button type="button" class="btn btn-secondary" onclick="closeModal('pharmacyDetailModal')">Close</button>
  `;

  openModal('pharmacyDetailModal');
}

function callPharmacyDemo(pharmacyName, phone) {
  showToast('info', 'Simulated Call (Demo Mode)', `Dialing ${pharmacyName} at ${phone}. No real phone call is placed.`);
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function escapeHtml(string) {
  if (!string) return '';
  return String(string).replace(/[&<>"']/g, function (s) {
    return {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[s];
  });
}
