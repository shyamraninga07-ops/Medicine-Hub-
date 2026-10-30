# MediCare Hub – Family Medicine Management & Pharmacy Availability Platform

> **"Your Family's Health, In One Place."**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask Version](https://img.shields.io/badge/flask-3.1.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Web%20%7C%20Mobile%20Responsive-brightgreen.svg)]()

**MediCare Hub** is a modern, responsive, and functional healthcare SaaS web application designed to help families manage their health records, prescriptions, medicine schedules, refill reminders, and nearby pharmacy availability from one centralized platform.

---

## 🌟 Key Modules & Features

### 1. 🛡️ Healthcare Branding & UI/UX Design
- **Modern Healthcare Aesthetic:** Inspired by modern healthtech SaaS platforms with rounded cards (`border-radius: 16px`), soft depth shadows, clean badges, and intuitive typography (*Inter* & *Poppins*).
- **Brand Identity:** High-resolution SVG logo featuring a medical cross (+) and a heart/protective shield with blue and green gradients (`#1769E0` and `#20B486`). Includes a simplified icon version for the sidebar, browser favicon, and login badges.
- **Mobile First & Fully Responsive:** Collapsible hamburger sidebar for mobile and tablet screens, sticky top navigation with live date and real-time notification badge.

### 2. 🔐 Authentication & Session Security
- **Split-Screen Design:** Brand storytelling, healthcare hero illustrations, and an authentication form.
- **Role Support:** Family Caregiver / Individual and Community Pharmacy Manager.
- **Security:** Secure password hashing via Werkzeug, protected routes with session management, and CSRF protection.
- **One-Click Demo Login:** Fast login buttons pre-fill demonstration accounts for instant testing.

### 3. 📊 Main Health Dashboard
- **Real-Time Dynamic Statistics:**
  - *Total Family Members*
  - *Active Prescriptions*
  - *Today's Medicine Doses (Taken / Total Scheduled)*
  - *Pending Refill Alerts (Priority Badged)*
- **Interactive Widgets:**
  - *Today's Medicine Schedule* with 1-click **Taken** and **Missed** action buttons.
  - *7-Day Adherence Trend Chart* powered by Chart.js.
  - *Low-Stock & Predictive Refill Alerts* with direct link to pharmacy finder.
  - *Nearby Stocked Pharmacies* with live distance calculations.
  - *Recent Activity Feed* logging every dose recorded.

### 4. 👨‍👩‍👧‍👦 Family Health Record Management
- Dedicated health profiles for each family member (Sarah, David, John, Emma seeded by default).
- Automatic age calculation derived from date of birth.
- Blood group badge, allergy warnings, chronic conditions, emergency contacts, and clinical notes.
- Detailed Individual Health Record modal displaying member-specific prescriptions, dosage rules, and doctor contact details.
- Full CRUD operations with modal forms and validation.

### 5. 💊 Prescription Management
- Track complete medicine information:
  - Medicine name, strength, and generic name.
  - Medicine category (Tablets, Capsules, Syrup, Inhaler, Drops, Injection, Ointment, etc.).
  - Dosage amount and unit.
  - Frequency (Once daily, Twice daily, 3 times daily, As needed, etc.).
  - Administration time slots (Morning, Afternoon, Evening, Night).
  - Total pack size and current available stock.
  - Doctor name and direct phone dialer.
  - Prescription document attachment upload (PNG, JPG, PDF) with preview.
- Visual stock meter and estimated remaining supply days countdown.
- Live filtering by family member, active/completed status, and medicine name search.

### 6. ⏰ Medicine Reminder System
- Four daily dosing slots (Morning: 08:00 AM, Afternoon: 01:00 PM, Evening: 06:30 PM, Night: 09:00 PM) plus custom times.
- Daily schedule view & 7-day weekly schedule matrix view.
- **Browser Notification API:** Native desktop notifications notify users when scheduled dose times arrive while the app is active. Includes a "Test Notification" trigger.
- Complete database audit trail (`DoseHistory`) for every taken and missed dose.

### 7. 📉 Automatic Medicine Stock Tracking
- **Automatic Stock Deduction Logic:**
  - Marking a scheduled dose as **Taken** automatically decreases `available_stock` by the prescribed dose (e.g. -1 tablet).
  - Marking a dose as **Missed** leaves stock untouched.
  - **Duplicate Deduction Prevention:** Ensures the same scheduled dose slot for today cannot be deducted more than once.
  - Dynamically recalculates estimated remaining days:
    $$\text{Estimated Days} = \left\lfloor \frac{\text{Available Stock}}{\text{Daily Consumption}} \right\rfloor$$
  - When stock drops below the threshold (default 5 days or 5 units), an active `RefillAlert` is automatically generated and added to the notification queue.

### 8. ⚠️ Refill Alert System
- Dedicated Refill Alerts page with color-coded priority indicators:
  - 🟢 **Green (Sufficient Stock):** > 5 days of supply remaining.
  - 🟠 **Orange (Refill Soon):** 3 to 5 days remaining.
  - 🔴 **Red (Critical Stock):** $\le$ 2 days remaining or stock depleted.
- **Find Nearby Pharmacies Button:** Pre-fills the pharmacy locator search with the exact medicine name.
- **Mark as Refilled Modal:**
  - Enter newly purchased quantity (e.g. +30 tablets).
  - Increases available stock.
  - Logs previous stock, added quantity, new stock, purchase cost, and pharmacy name in `RefillHistory`.
  - Automatically resolves and dismisses the low-stock alert.

### 9. 📍 Pharmacy Availability Finder & Interactive Map
- **Leaflet.js + OpenStreetMap:** Real interactive map with custom colored SVG markers (blue for user, green for stocked pharmacies, red for out-of-stock) centered in Rajkot, Gujarat, India.
- **Geolocation Integration:** Automatically computes distance from Rajkot center (`22.3039, 70.8022`) or browser geolocation.
- **Haversine Distance Formula:** Computes real great-circle distance between the user and pharmacies:
  $$\text{distance} = 2 \cdot R \cdot \arcsin\left(\sqrt{\sin^2(\Delta\phi/2) + \cos(\phi_1)\cos(\phi_2)\sin^2(\Delta\lambda/2)}\right)$$
- **8 Fictional Pharmacies in Rajkot:** HealthPlus (Yagnik Rd), CareWell (Kalawad Rd), MediLife (Imperial Heights), City Medical (Dhebar Rd), Apollo (150ft Ring Rd), Wellness (University Rd), FamilyCare (Tagore Rd), and LifeLine (Kuvadva Rd).
- **Inventory Search & Filtering:** Filter pharmacies by medicine name/brand, distance radius (2 km, 5 km, 10 km, Any), and in-stock status.
- **Direct Actions:** One-click **Call Pharmacy** (`tel:...`) and **Get Directions** (links directly to Google Maps navigation).
- **Pharmacy Admin Portal:** Community pharmacy managers can log in, update opening hours, edit inventory quantities, and toggle in-stock availability.
- *Transparent Disclaimer:* Sample demonstration inventory data is clearly labeled.

### 10. 📈 Medicine History, Reports & CSV Export
- Comprehensive history log of doses taken and missed, refill records, and stock adjustments.
- Interactive filtering by date, family member, and status.
- Four interactive **Chart.js** data visualizations:
  1. *Dose Adherence Ratio (Donut Chart)*
  2. *7-Day Adherence Percentage Trajectory (Line Chart)*
  3. *Monthly Medicine Consumption Breakdown (Bar Chart)*
  4. *Medication Refill Costs (Bar Chart)*
- **Export to CSV:** Client-side CSV export of all filtered dose records.

### 11. ⚙️ Settings & Demonstration Reset
- Edit personal profile details (Name, email, phone).
- Change account password.
- Notification preferences (Browser desktop push, email digest, SMS/WhatsApp simulation).
- Configure default low-stock refill threshold (in days).
- **Reset Demo Data Button:** One-click reinitialization of the clean demonstration scenario.

---

## 🏗️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, Flask 3.1.3 |
| **Database** | SQLite with SQLAlchemy 2.0 ORM |
| **Authentication** | Flask Sessions with Werkzeug password hashing |
| **Frontend** | HTML5, Modern CSS3 (CSS Variables, Flexbox, Grid), Vanilla JavaScript (ES6+) |
| **Typography & Icons**| Google Fonts (*Inter*, *Poppins*), Font Awesome 6.5 |
| **Charts** | Chart.js 4.4.1 |
| **Maps** | Leaflet.js 1.9.4 with OpenStreetMap Tiles |
| **Notifications** | HTML5 Web Notifications API & Custom Toast System |

*Zero frontend frameworks (React, Angular, Vue) used, ensuring lightning-fast load times and pure web standard compliance.*

---

## 👥 Demonstration Accounts

The database comes pre-seeded with realistic demonstration accounts and sample records:

| Role | Email | Password | Name |
|---|---|---|---|
| **Demonstration Account** (Default) | `demo@medicarehub.com` | `Demo@123` | Sarah Johnson (Managing Sarah, David, John, Emma) |
| **Family Caregiver (Alternate)** | `sarah@medicarehub.com` | `Password123!` | Sarah Johnson |
| **Pharmacy Manager** | `healthplus@medicarehub.com` | `Demo@123` | Dr. Marcus Vance (HealthPlus, Rajkot) |

*(Quick demo login buttons on the login page allow 1-click access without typing).*

---

## 🚀 Quick Start Guide

### 1. Clone or Open the Repository
```bash
cd "d:\Medicine Hub"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

### 4. Open in Your Browser
Navigate to:
```
http://127.0.0.1:5000
```

---

## 🧪 Running Automated Unit Tests

A comprehensive unit test suite is included in `test_app.py` covering authentication, dashboard loading, automatic stock deduction, duplicate prevention, refill resolution, and pharmacy search:

```bash
python test_app.py
```

---

## 🔄 The Complete Core User Flow

Follow this walkthrough to experience the end-to-end functionality:

1. **Sign In:** Go to `http://127.0.0.1:5000/login` and click **"Sarah (Family Caregiver)"**.
2. **Review Dashboard:** Notice David Johnson's **Metformin 500mg** is in critical low stock (4 tablets left, 2 days of supply).
3. **Log a Scheduled Dose:** In the *Today's Medicine Schedule* widget, click **"Taken"** on David's dose.
   - The button instantly transforms to a green *Taken* badge.
   - A success toast appears displaying the updated stock (now 3 tablets left).
   - In the background, the database transaction reduced the available stock and logged the dose in `DoseHistory`.
4. **Trigger Refill Alert:** Notice the Pending Refill Alerts badge increments and alerts you.
5. **Find Nearby Pharmacies:** Click **"Find Nearby Pharmacies"** on the Metformin alert.
   - The Pharmacy Finder opens with `Metformin 500mg` pre-filled.
   - Nearby pharmacies appear on the Leaflet map and list with live distance (e.g. *HealthPlus Pharmacy: 0.8 km, In Stock: 85 tablets*).
6. **Mark as Refilled:** Click **"Refill Alerts"** in the sidebar $\rightarrow$ click **"Mark Refilled"**.
   - Enter `+60` tablets purchased from *HealthPlus Pharmacy* for `$14.50`.
   - Click **"Confirm Restock"**.
   - Available stock resets to 63 tablets (~31 days of supply).
   - The low-stock alert is automatically resolved!
7. **View Adherence Analytics:** Navigate to **Medicine History** to view the Chart.js adherence graphs and export the dose log to CSV.

---

## 📁 Project Structure

```
Medicine Hub/
│
├── app.py                      # Core Flask web application & API routes
├── config.py                   # Configuration, upload paths & session settings
├── models.py                   # SQLAlchemy ORM models (User, Family, Rx, Pharmacy, etc.)
├── seed_data.py                # Realistic demonstration scenario database seeder
├── test_app.py                 # Automated test suite
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation
│
├── database/
│   └── medicare.db             # SQLite database file
│
├── uploads/                    # Secure prescription image and document storage
│   ├── prescriptions/
│   └── avatars/
│
├── static/
│   ├── css/
│   │   ├── style.css           # Global design system, auth split-screen, modals & toasts
│   │   └── dashboard.css       # Widget styles, map layouts, rx cards, and charts
│   ├── js/
│   │   ├── main.js             # Toast system, modal helpers, browser notifications
│   │   ├── dashboard.js        # Live dose AJAX actions & adherence graph
│   │   ├── reminders.js        # Daily/weekly schedule view toggles & member filters
│   │   ├── pharmacy.js         # Leaflet map, geolocation, and Haversine distance search
│   │   └── history.js          # Chart.js analytics & CSV export
│   └── images/
│       ├── logo.svg            # Primary brand logo (Cross + Heart/Shield gradient)
│       ├── logo-icon.svg       # Compact brand icon & favicon
│       ├── default-avatar.svg  # Default profile avatar
│       ├── avatar-sarah.svg    # Sarah Johnson avatar
│       ├── avatar-david.svg    # David Johnson avatar
│       ├── avatar-john.svg     # John Johnson avatar
│       ├── avatar-emma.svg     # Emma Johnson avatar
│       ├── avatar-doc.svg      # Healthcare / Doctor avatar
│       └── healthcare-illustration.svg # Vector illustration for auth hero & empty states
│
└── templates/
    ├── base.html               # Master layout with responsive sidebar & topbar
    ├── login.html              # Split-screen sign in with one-click demo login
    ├── register.html           # Split-screen registration
    ├── forgot_password.html    # Password recovery
    ├── dashboard.html          # Dynamic health statistics, schedule & refill alerts
    ├── family.html             # Family member profiles & clinical summaries
    ├── prescriptions.html      # Prescription management with file upload & stock meters
    ├── reminders.html          # Dosing schedule, slot tabs & notification triggers
    ├── refill_alerts.html      # Color-coded stock alerts & restock modal
    ├── pharmacy_finder.html    # Interactive Leaflet map & nearby pharmacy availability
    ├── pharmacy_admin.html     # Pharmacy inventory management portal
    ├── history.html            # Adherence reports, Chart.js graphs & CSV export
    └── settings.html           # Preferences, password update & demo reset
```

---

## 🔒 Security & Best Practices

- **Password Hashing:** Passwords are never stored in plain text; hashed using industry-standard scrypt/pbkdf2 algorithms through `werkzeug.security`.
- **User Isolation:** All family profiles, prescriptions, reminders, and alerts strictly enforce `user_id` foreign key validation to prevent unauthorized data access across users.
- **Stock Transaction Safety:** Dosing reductions, refunds, and restocks are handled inside ACID database transactions with duplicate prevention constraints.
- **Sanitized Uploads:** File uploads restrict file extensions (`.png`, `.jpg`, `.jpeg`, `.pdf`) and use `werkzeug.utils.secure_filename` to prevent path traversal attacks.

---

## 📄 License
MediCare Hub is open-source software licensed under the [MIT License](LICENSE).

