import os
import math
from datetime import datetime, date, timedelta, timezone
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from config import Config
from models import (
    db, User, FamilyMember, Prescription, MedicineReminder,
    DoseHistory, RefillAlert, RefillHistory, Pharmacy, PharmacyInventory, Notification
)
from seed_data import seed_database

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

with app.app_context():
    db.create_all()
    seed_database()

# ==============================================================================
# Helper Functions & Context Processors
# ==============================================================================

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return db.session.get(User, user_id)
    return None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to access your dashboard.', 'info')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates great-circle distance between two coordinates in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def format_time_display(time_str):
    if not time_str:
        return '08:00 AM'
    try:
        t = datetime.strptime(time_str, '%H:%M')
        return t.strftime('%I:%M %p')
    except Exception:
        return time_str

@app.context_processor
def inject_global_data():
    current_user = get_current_user()
    pending_refills_count = 0
    unread_notifs_count = 0
    user_notifications = []
    
    if current_user:
        pending_refills_count = RefillAlert.query.filter_by(
            user_id=current_user.id, status='active'
        ).count()
        unread_notifs_count = Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).count()
        user_notifications = Notification.query.filter_by(
            user_id=current_user.id
        ).order_by(Notification.created_at.desc()).limit(8).all()

    today_str = datetime.now().strftime('%A, %b %d, %Y')
    return {
        'current_user': current_user,
        'pending_refills_count': pending_refills_count,
        'unread_notifs_count': unread_notifs_count,
        'user_notifications': user_notifications,
        'current_date_display': today_str
    }

# ==============================================================================
# Authentication Routes
# ==============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            session.permanent = True
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'user')

        if not name or not email or not password:
            flash('All required fields must be provided.', 'error')
            return render_template('register.html')

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        avatar = '/static/images/avatar-doc.svg' if role == 'pharmacy_admin' else '/static/images/avatar-sarah.svg'
        new_user = User(
            name=name,
            email=email,
            phone=phone,
            role=role,
            avatar_url=avatar
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Add initial "Self" family member if caregiver
        if role == 'user':
            self_member = FamilyMember(
                user_id=new_user.id,
                full_name=name,
                relationship='Self',
                dob=date(1995, 1, 1),
                gender='Not Specified',
                blood_group='Unknown',
                avatar_url=avatar,
                notes='Account holder'
            )
            db.session.add(self_member)
            db.session.commit()

        session['user_id'] = new_user.id
        session['user_name'] = new_user.name
        session['user_role'] = new_user.role
        session.permanent = True
        flash('Account created successfully! Welcome to MediCare Hub.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        new_pass = request.form.get('new_password', '')
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(new_pass)
            db.session.commit()
            flash('Password updated successfully. You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('No account found with that email address.', 'error')
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been securely logged out.', 'info')
    return redirect(url_for('login'))

# ==============================================================================
# Dashboard Route
# ==============================================================================

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    
    # 1. Total family members
    total_members = FamilyMember.query.filter_by(user_id=user.id).count()

    # 2. Active prescriptions
    active_prescriptions = Prescription.query.filter_by(
        user_id=user.id, status='Active'
    ).all()
    active_prescriptions_count = len(active_prescriptions)

    # 3. Today's doses schedule
    today_date_str = date.today().strftime('%Y-%m-%d')
    today_schedule_items = []
    
    # Slot times reference
    slot_hours = {
        'Morning': '08:00 AM',
        'Afternoon': '01:00 PM',
        'Evening': '06:30 PM',
        'Night': '09:00 PM'
    }

    # Fetch today's dose history records for this user
    today_doses_history = DoseHistory.query.filter_by(
        user_id=user.id, scheduled_date=today_date_str
    ).all()
    history_map = {f"{h.prescription_id}_{h.scheduled_time}": h.status for h in today_doses_history}

    # Fetch configured reminders to use custom times
    user_reminders = MedicineReminder.query.filter_by(user_id=user.id).all()
    rem_map = {f"{r.prescription_id}_{r.time_slot}": r.reminder_time for r in user_reminders}

    for rx in active_prescriptions:
        slots = [s.strip() for s in (rx.time_slots or 'Morning').split(',') if s.strip()]
        for slot in slots:
            status = history_map.get(f"{rx.id}_{slot}", 'pending')
            custom_time = rem_map.get(f"{rx.id}_{slot}")
            time_display = format_time_display(custom_time) if custom_time else slot_hours.get(slot, '08:00 AM')
            today_schedule_items.append({
                'prescription': rx,
                'slot': slot,
                'time': time_display,
                'status': status,
                'is_taken': (status == 'taken'),
                'is_missed': (status == 'missed')
            })

    # Sort schedule by slot time
    slot_order = {'Morning': 1, 'Afternoon': 2, 'Evening': 3, 'Night': 4}
    today_schedule_items.sort(key=lambda x: slot_order.get(x['slot'], 5))

    today_total_doses = len(today_schedule_items)
    today_taken_count = sum(1 for item in today_schedule_items if item['is_taken'])
    today_remaining_count = sum(1 for item in today_schedule_items if item['status'] == 'pending')

    # 4. Low stock medicines
    low_stock_items = [rx for rx in active_prescriptions if rx.stock_status in ['critical', 'low']]

    # 5. Pending Refill Alerts
    pending_refills = RefillAlert.query.filter_by(
        user_id=user.id, status='active'
    ).order_by(RefillAlert.priority.asc()).all()

    # 6. Sample pharmacies
    sample_pharmacies = Pharmacy.query.limit(4).all()

    # 7. Recent health activity feed
    recent_doses = DoseHistory.query.filter_by(user_id=user.id).order_by(DoseHistory.taken_at.desc()).limit(4).all()
    recent_activities = []
    for d in recent_doses:
        recent_activities.append({
            'icon': 'fa-check' if d.status == 'taken' else 'fa-times',
            'title': f"{d.prescription.medicine_name if d.prescription else 'Dose'} marked as {d.status.capitalize()} ({d.family_member.full_name if d.family_member else ''})",
            'time': d.taken_at.strftime('%b %d, %I:%M %p') if d.taken_at else d.scheduled_date
        })
    if not recent_activities:
        recent_activities = [
            {'icon': 'fa-shield-alt', 'title': 'Account setup completed', 'time': 'Today'},
            {'icon': 'fa-pills', 'title': 'Prescription monitoring started', 'time': 'Today'}
        ]

    return render_template(
        'dashboard.html',
        active_page='dashboard',
        total_members=total_members,
        active_prescriptions_count=active_prescriptions_count,
        today_total_doses=today_total_doses,
        today_taken_count=today_taken_count,
        today_remaining_count=today_remaining_count,
        today_schedule_items=today_schedule_items,
        low_stock_items=low_stock_items,
        pending_refills_count=len(pending_refills),
        sample_pharmacies=sample_pharmacies,
        recent_activities=recent_activities
    )

# ==============================================================================
# Family Health Records Routes
# ==============================================================================

@app.route('/family')
@login_required
def family_profiles():
    user = get_current_user()
    members = FamilyMember.query.filter_by(user_id=user.id).order_by(FamilyMember.created_at.asc()).all()
    return render_template('family.html', active_page='family', family_members=members)

@app.route('/family/save', methods=['POST'])
@login_required
def save_family_member():
    user = get_current_user()
    member_id = request.form.get('member_id')
    full_name = request.form.get('full_name', '').strip()
    relationship = request.form.get('relationship', 'Self')
    dob_str = request.form.get('dob')
    gender = request.form.get('gender', 'Not Specified')
    blood_group = request.form.get('blood_group', 'Unknown')
    allergies = request.form.get('allergies', 'None known').strip()
    medical_conditions = request.form.get('medical_conditions', 'None').strip()
    emergency_contact = request.form.get('emergency_contact', '').strip()
    notes = request.form.get('notes', '').strip()

    dob = None
    if dob_str:
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            dob = date(1990, 1, 1)

    # Avatar selection logic
    avatar = '/static/images/default-avatar.svg'
    if relationship == 'Parent' or (dob and (date.today().year - dob.year) > 55):
        avatar = '/static/images/avatar-david.svg'
    elif relationship == 'Child':
        avatar = '/static/images/avatar-emma.svg' if gender == 'Female' else '/static/images/avatar-john.svg'
    elif gender == 'Female':
        avatar = '/static/images/avatar-sarah.svg'

    if member_id:
        member = FamilyMember.query.filter_by(id=member_id, user_id=user.id).first_or_404()
        member.full_name = full_name
        member.relationship = relationship
        if dob: member.dob = dob
        member.gender = gender
        member.blood_group = blood_group
        member.allergies = allergies
        member.medical_conditions = medical_conditions
        member.emergency_contact = emergency_contact
        member.notes = notes
        flash(f'Profile for {full_name} updated successfully.', 'success')
    else:
        member = FamilyMember(
            user_id=user.id,
            full_name=full_name,
            relationship=relationship,
            dob=dob or date(1990, 1, 1),
            gender=gender,
            blood_group=blood_group,
            allergies=allergies,
            medical_conditions=medical_conditions,
            emergency_contact=emergency_contact,
            avatar_url=avatar,
            notes=notes
        )
        db.session.add(member)
        flash(f'Family member {full_name} added successfully.', 'success')

    db.session.commit()
    return redirect(url_for('family_profiles'))

@app.route('/family/delete', methods=['POST'])
@login_required
def delete_family_member():
    user = get_current_user()
    member_id = request.form.get('member_id')
    member = FamilyMember.query.filter_by(id=member_id, user_id=user.id).first_or_404()
    name = member.full_name
    db.session.delete(member)
    db.session.commit()
    flash(f'{name} and associated prescriptions were removed.', 'info')
    return redirect(url_for('family_profiles'))

# ==============================================================================
# Prescriptions Management Routes
# ==============================================================================

@app.route('/prescriptions')
@login_required
def prescriptions():
    user = get_current_user()
    members = FamilyMember.query.filter_by(user_id=user.id).all()
    
    query = Prescription.query.filter_by(user_id=user.id)
    
    member_filter = request.args.get('member_id', type=int)
    if member_filter:
        query = query.filter_by(family_member_id=member_filter)
        
    status_filter = request.args.get('status')
    if status_filter:
        query = query.filter_by(status=status_filter)
        
    search_q = request.args.get('search', '').strip()
    if search_q:
        query = query.filter(
            (Prescription.medicine_name.ilike(f'%{search_q}%')) |
            (Prescription.doctor_name.ilike(f'%{search_q}%'))
        )
        
    all_prescriptions = query.order_by(Prescription.created_at.desc()).all()
    
    return render_template(
        'prescriptions.html',
        active_page='prescriptions',
        prescriptions=all_prescriptions,
        family_members=members,
        selected_member_id=member_filter,
        selected_status=status_filter,
        search_query=search_q
    )

@app.route('/prescriptions/save', methods=['POST'])
@login_required
def save_prescription():
    user = get_current_user()
    rx_id = request.form.get('prescription_id')
    family_member_id = request.form.get('family_member_id', type=int)
    medicine_name = request.form.get('medicine_name', '').strip()
    generic_name = request.form.get('generic_name', '').strip()
    category = request.form.get('category', 'Tablets')
    dosage_amount = request.form.get('dosage_amount', type=float) or 1.0
    dosage_unit = request.form.get('dosage_unit', 'tablets')
    frequency = request.form.get('frequency', 'Once daily')
    
    time_slots_list = request.form.getlist('time_slot')
    time_slots = ', '.join(time_slots_list) if time_slots_list else 'Morning'
    
    total_quantity = request.form.get('total_quantity', type=float) or 30.0
    available_stock = request.form.get('available_stock', type=float) or total_quantity
    low_stock_threshold = request.form.get('low_stock_threshold', type=int) or 5
    doctor_name = request.form.get('doctor_name', '').strip()
    doctor_contact = request.form.get('doctor_contact', '').strip()
    notes = request.form.get('notes', '').strip()

    # Handle document upload
    file = request.files.get('prescription_document')
    doc_path = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if ext in app.config['ALLOWED_EXTENSIONS']:
            save_name = f"rx_{user.id}_{int(datetime.now(timezone.utc).timestamp())}_{filename}"
            full_path = os.path.join(app.config['PRESCRIPTIONS_UPLOAD_FOLDER'], save_name)
            file.save(full_path)
            doc_path = f"/uploads/prescriptions/{save_name}"

    if rx_id:
        rx = Prescription.query.filter_by(id=rx_id, user_id=user.id).first_or_404()
        rx.family_member_id = family_member_id
        rx.medicine_name = medicine_name
        rx.generic_name = generic_name
        rx.category = category
        rx.dosage_amount = dosage_amount
        rx.dosage_unit = dosage_unit
        rx.frequency = frequency
        rx.time_slots = time_slots
        rx.total_quantity = total_quantity
        rx.available_stock = available_stock
        rx.low_stock_threshold = low_stock_threshold
        rx.doctor_name = doctor_name
        rx.doctor_contact = doctor_contact
        rx.notes = notes
        if doc_path: rx.document_path = doc_path
        rx.calculate_daily_consumption()
        flash(f'Prescription for {medicine_name} updated.', 'success')
    else:
        rx = Prescription(
            user_id=user.id,
            family_member_id=family_member_id,
            medicine_name=medicine_name,
            generic_name=generic_name,
            category=category,
            dosage_amount=dosage_amount,
            dosage_unit=dosage_unit,
            frequency=frequency,
            time_slots=time_slots,
            total_quantity=total_quantity,
            available_stock=available_stock,
            low_stock_threshold=low_stock_threshold,
            doctor_name=doctor_name,
            doctor_contact=doctor_contact,
            document_path=doc_path,
            notes=notes,
            status='Active'
        )
        rx.calculate_daily_consumption()
        db.session.add(rx)
        db.session.flush()

        # Create reminders
        slot_hours = {'Morning': '08:00', 'Afternoon': '13:00', 'Evening': '18:30', 'Night': '21:00'}
        for slot in time_slots_list:
            rem = MedicineReminder(
                prescription_id=rx.id,
                user_id=user.id,
                family_member_id=family_member_id,
                time_slot=slot,
                reminder_time=slot_hours.get(slot, '08:00')
            )
            db.session.add(rem)

        flash(f'Prescription for {medicine_name} added successfully.', 'success')

    # Check if stock requires an immediate refill alert
    if rx.stock_status in ['critical', 'low']:
        existing_alert = RefillAlert.query.filter_by(prescription_id=rx.id, status='active').first()
        if not existing_alert:
            alert = RefillAlert(
                prescription_id=rx.id,
                user_id=user.id,
                medicine_name=rx.medicine_name,
                remaining_stock=rx.available_stock,
                estimated_days_remaining=rx.estimated_remaining_days,
                priority='critical' if rx.stock_status == 'critical' else 'soon',
                status='active'
            )
            db.session.add(alert)

    db.session.commit()
    return redirect(url_for('prescriptions'))

@app.route('/prescriptions/delete', methods=['POST'])
@login_required
def delete_prescription():
    user = get_current_user()
    rx_id = request.form.get('prescription_id')
    rx = Prescription.query.filter_by(id=rx_id, user_id=user.id).first_or_404()
    med_name = rx.medicine_name
    db.session.delete(rx)
    db.session.commit()
    flash(f'Prescription for {med_name} removed.', 'info')
    return redirect(url_for('prescriptions'))

# ==============================================================================
# Medicine Reminders & Dose Recording (Automatic Stock Deduction)
# ==============================================================================

@app.route('/reminders')
@login_required
def medicine_reminders():
    user = get_current_user()
    members = FamilyMember.query.filter_by(user_id=user.id).all()
    active_prescriptions = Prescription.query.filter_by(user_id=user.id, status='Active').all()

    today_date_str = date.today().strftime('%Y-%m-%d')
    slot_hours = {
        'Morning': '08:00 AM',
        'Afternoon': '01:00 PM',
        'Evening': '06:30 PM',
        'Night': '09:00 PM'
    }

    # Fetch today's dose history
    doses_today = DoseHistory.query.filter_by(user_id=user.id, scheduled_date=today_date_str).all()
    history_map = {f"{h.prescription_id}_{h.scheduled_time}": h.status for h in doses_today}

    user_reminders = MedicineReminder.query.filter_by(user_id=user.id).all()
    rem_map = {f"{r.prescription_id}_{r.time_slot}": r.reminder_time for r in user_reminders}

    doses_by_slot = {'Morning': [], 'Afternoon': [], 'Evening': [], 'Night': []}

    for rx in active_prescriptions:
        slots = [s.strip() for s in (rx.time_slots or 'Morning').split(',') if s.strip()]
        for slot in slots:
            if slot in doses_by_slot:
                status = history_map.get(f"{rx.id}_{slot}", 'pending')
                custom_time = rem_map.get(f"{rx.id}_{slot}")
                time_display = format_time_display(custom_time) if custom_time else slot_hours.get(slot, '08:00 AM')
                doses_by_slot[slot].append({
                    'prescription': rx,
                    'slot': slot,
                    'time': time_display,
                    'status': status,
                    'is_taken': (status == 'taken'),
                    'is_missed': (status == 'missed')
                })

    return render_template(
        'reminders.html',
        active_page='reminders',
        family_members=members,
        active_prescriptions=active_prescriptions,
        doses_by_slot=doses_by_slot
    )

@app.route('/api/doses/record', methods=['POST'])
@login_required
def record_dose_api():
    """
    CRITICAL REQUIREMENT: Automatic medicine stock deduction logic.
    - If status == 'taken': decrease stock by prescription.dosage_amount.
    - If status == 'missed': do not decrease stock.
    - Prevent duplicate deductions for same dose slot on same day.
    - Check threshold & trigger Refill Alert if depleted.
    """
    user = get_current_user()
    data = request.get_json() or {}

    prescription_id = data.get('prescription_id')
    scheduled_time = data.get('scheduled_time', 'Morning')
    status = data.get('status', 'taken')  # 'taken' or 'missed'
    scheduled_date = data.get('scheduled_date', date.today().strftime('%Y-%m-%d'))

    rx = Prescription.query.filter_by(id=prescription_id, user_id=user.id).first()
    if not rx:
        return jsonify({'success': False, 'message': 'Prescription not found'}), 404

    # 1. Prevent duplicate dose recording for same slot on same day
    existing_dose = DoseHistory.query.filter_by(
        prescription_id=rx.id,
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time
    ).first()

    refill_alert_created = False

    try:
        if existing_dose:
            # If changing from taken to missed or vice versa
            if existing_dose.status != status:
                if status == 'taken':
                    # Was missed or pending, now taken -> deduct stock
                    rx.available_stock = max(0.0, rx.available_stock - (rx.dosage_amount or 1.0))
                elif existing_dose.status == 'taken' and status == 'missed':
                    # Was taken, now changing to missed -> refund stock
                    rx.available_stock = min(rx.total_quantity, rx.available_stock + (rx.dosage_amount or 1.0))
                existing_dose.status = status
                existing_dose.taken_at = datetime.now(timezone.utc) if status == 'taken' else None
        else:
            # New dose record
            dosage_deducted = 0.0
            if status == 'taken':
                dosage_deducted = rx.dosage_amount or 1.0
                rx.available_stock = max(0.0, rx.available_stock - dosage_deducted)

            new_history = DoseHistory(
                prescription_id=rx.id,
                user_id=user.id,
                family_member_id=rx.family_member_id,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                dosage_taken=dosage_deducted,
                status=status,
                taken_at=datetime.now(timezone.utc) if status == 'taken' else None
            )
            db.session.add(new_history)

        # 2. Recalculate estimated supply & check refill alert threshold
        est_days = rx.estimated_remaining_days
        threshold = rx.low_stock_threshold or user.default_refill_threshold or 5

        if rx.available_stock <= 0 or est_days <= threshold:
            existing_alert = RefillAlert.query.filter_by(
                prescription_id=rx.id, status='active'
            ).first()

            priority = 'critical' if (rx.available_stock <= 0 or est_days <= 2) else 'soon'

            if not existing_alert:
                alert = RefillAlert(
                    prescription_id=rx.id,
                    user_id=user.id,
                    medicine_name=rx.medicine_name,
                    remaining_stock=rx.available_stock,
                    estimated_days_remaining=est_days,
                    priority=priority,
                    status='active'
                )
                db.session.add(alert)
                refill_alert_created = True

                # In-app notification
                notif = Notification(
                    user_id=user.id,
                    title=f"Low Stock: {rx.medicine_name}",
                    message=f"{rx.medicine_name} for {rx.family_member.full_name} has only {int(rx.available_stock)} units left (~{est_days} days). Find nearby pharmacies now.",
                    type='refill',
                    link='/refill-alerts'
                )
                db.session.add(notif)
            else:
                existing_alert.remaining_stock = rx.available_stock
                existing_alert.estimated_days_remaining = est_days
                existing_alert.priority = priority

        db.session.commit()

        # Dynamic counts for client UI update
        today_taken_count = DoseHistory.query.filter_by(
            user_id=user.id, scheduled_date=scheduled_date, status='taken'
        ).count()
        active_refills = RefillAlert.query.filter_by(user_id=user.id, status='active').count()

        return jsonify({
            'success': True,
            'medicine_name': rx.medicine_name,
            'remaining_stock': round(rx.available_stock, 1),
            'estimated_days': est_days,
            'stock_status': rx.stock_status,
            'refill_alert_created': refill_alert_created,
            'today_taken_count': today_taken_count,
            'active_refill_count': active_refills
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/reminders/check-due')
@login_required
def check_due_reminders():
    """Returns scheduled doses that are pending for browser notification."""
    user = get_current_user()
    today_str = date.today().strftime('%Y-%m-%d')
    now = datetime.now()
    hour = now.hour

    # Match hour to slot
    current_slot = 'Morning'
    if 11 <= hour < 16:
        current_slot = 'Afternoon'
    elif 16 <= hour < 20:
        current_slot = 'Evening'
    elif hour >= 20 or hour < 5:
        current_slot = 'Night'

    # Check for active prescriptions in this slot that haven't been taken yet
    prescriptions = Prescription.query.filter_by(user_id=user.id, status='Active').all()
    due_list = []

    for rx in prescriptions:
        slots = [s.strip() for s in (rx.time_slots or '').split(',') if s.strip()]
        if current_slot in slots:
            taken = DoseHistory.query.filter_by(
                prescription_id=rx.id, scheduled_date=today_str, scheduled_time=current_slot
            ).first()
            if not taken:
                due_list.append({
                    'id': rx.id,
                    'medicine_name': rx.medicine_name,
                    'patient_name': rx.family_member.full_name,
                    'dosage': f"{rx.dosage_amount} {rx.dosage_unit}",
                    'slot_name': current_slot
                })

    return jsonify({'due_reminders': due_list})

# ==============================================================================
# Refill Alert System Routes
# ==============================================================================

@app.route('/refill-alerts')
@login_required
def refill_alerts():
    user = get_current_user()
    
    # Active alerts
    alerts = RefillAlert.query.filter_by(
        user_id=user.id, status='active'
    ).order_by(RefillAlert.priority.asc(), RefillAlert.created_at.desc()).all()
    
    critical_alerts = [a for a in alerts if a.priority == 'critical']
    
    # Recent refill history
    refill_logs = RefillHistory.query.filter_by(
        user_id=user.id
    ).order_by(RefillHistory.refilled_at.desc()).limit(10).all()

    return render_template(
        'refill_alerts.html',
        active_page='refills',
        alerts=alerts,
        critical_alerts=critical_alerts,
        refill_logs=refill_logs
    )

@app.route('/refills/record', methods=['POST'])
@login_required
def record_refill():
    """
    CRITICAL REQUIREMENT: When a user marks a medicine as refilled:
    - Update available stock
    - Save refill history
    - Update the refill date
    - Recalculate estimated remaining days
    - Automatically resolve previous low-stock alert
    """
    user = get_current_user()
    rx_id = request.form.get('prescription_id', type=int)
    added_qty = request.form.get('added_quantity', type=float) or 30.0
    pharmacy_name = request.form.get('pharmacy_name', '').strip()
    cost = request.form.get('cost', type=float)
    notes = request.form.get('notes', '').strip()

    rx = Prescription.query.filter_by(id=rx_id, user_id=user.id).first_or_404()
    
    prev_stock = rx.available_stock
    new_stock = prev_stock + added_qty
    rx.available_stock = new_stock
    rx.total_quantity = max(rx.total_quantity, new_stock)
    
    # Save Refill History
    history = RefillHistory(
        prescription_id=rx.id,
        user_id=user.id,
        previous_stock=prev_stock,
        added_quantity=added_qty,
        new_stock=new_stock,
        pharmacy_name=pharmacy_name or 'Community Pharmacy',
        cost=cost,
        refilled_at=datetime.now(timezone.utc),
        notes=notes
    )
    db.session.add(history)

    # Automatically resolve active RefillAlert
    active_alerts = RefillAlert.query.filter_by(prescription_id=rx.id, status='active').all()
    for alert in active_alerts:
        alert.status = 'resolved'
        alert.resolved_at = datetime.now(timezone.utc)

    # In-app notification
    notif = Notification(
        user_id=user.id,
        title=f"Refill Logged: {rx.medicine_name}",
        message=f"Added {int(added_qty)} {rx.dosage_unit}. New available stock is {int(new_stock)} (~{rx.estimated_remaining_days} days).",
        type='refill',
        link='/refill-alerts'
    )
    db.session.add(notif)

    db.session.commit()
    flash(f'{rx.medicine_name} successfully refilled (+{int(added_qty)} units). Stock alert resolved.', 'success')
    return redirect(url_for('refill_alerts'))

@app.route('/refills/dismiss', methods=['POST'])
@login_required
def dismiss_refill_alert():
    user = get_current_user()
    alert_id = request.form.get('alert_id', type=int)
    alert = RefillAlert.query.filter_by(id=alert_id, user_id=user.id).first_or_404()
    alert.status = 'dismissed'
    db.session.commit()
    flash(f'Alert for {alert.medicine_name} dismissed.', 'info')
    return redirect(url_for('refill_alerts'))

# ==============================================================================
# Pharmacy Availability Finder & Map API
# ==============================================================================

@app.route('/pharmacy-finder')
@login_required
def pharmacy_finder():
    prefilled_med = request.args.get('medicine', '').strip()
    return render_template(
        'pharmacy_finder.html',
        active_page='pharmacy',
        prefilled_medicine=prefilled_med
    )

@app.route('/api/pharmacies/search')
@login_required
def api_pharmacy_search():
    """
    Returns pharmacies in Rajkot with Haversine distance from user location
    and inventory stock for searched medicine query.
    """
    user_lat = request.args.get('user_lat', type=float) or 22.3039
    user_lng = request.args.get('user_lng', type=float) or 70.8022
    query = request.args.get('query', '').strip()

    pharmacies = Pharmacy.query.all()
    results = []

    for pharm in pharmacies:
        dist = haversine_distance(user_lat, user_lng, pharm.lat, pharm.lng)
        pharm_dict = pharm.to_dict()
        pharm_dict['distance_km'] = dist
        pharm_dict['all_inventory'] = [item.to_dict() for item in pharm.inventory_items]

        # Check inventory for query
        searched_inv = None
        if query:
            match = PharmacyInventory.query.filter(
                PharmacyInventory.pharmacy_id == pharm.id,
                (PharmacyInventory.medicine_name.ilike(f'%{query}%')) |
                (PharmacyInventory.brand_name.ilike(f'%{query}%')) |
                (PharmacyInventory.generic_name.ilike(f'%{query}%'))
            ).first()
            if match:
                searched_inv = match.to_dict()
            else:
                searched_inv = {
                    'in_stock': False,
                    'stock_quantity': 0,
                    'medicine_name': query,
                    'is_missing': True
                }
        else:
            first_item = PharmacyInventory.query.filter_by(pharmacy_id=pharm.id).first()
            if first_item:
                searched_inv = first_item.to_dict()

        pharm_dict['searched_inventory'] = searched_inv
        results.append(pharm_dict)

    # Sort results by distance ascending
    results.sort(key=lambda x: x['distance_km'])

    return jsonify({'pharmacies': results})

# ==============================================================================
# Pharmacy Admin Portal Routes
# ==============================================================================

@app.route('/pharmacy-admin')
@login_required
def pharmacy_admin():
    user = get_current_user()
    pharmacy = Pharmacy.query.filter_by(user_id=user.id).first()
    if not pharmacy:
        # Fallback to first pharmacy in system for demonstration admin mode
        pharmacy = Pharmacy.query.first()
    return render_template('pharmacy_admin.html', active_page='pharmacy_admin', pharmacy=pharmacy)

@app.route('/pharmacy-admin/inventory/save', methods=['POST'])
@login_required
def save_pharmacy_inventory():
    inv_id = request.form.get('inventory_id')
    pharmacy_id = request.form.get('pharmacy_id', type=int)
    medicine_name = request.form.get('medicine_name', '').strip()
    brand_name = request.form.get('brand_name', '').strip()
    category = request.form.get('category', 'Tablets')
    stock_quantity = request.form.get('stock_quantity', type=int) or 0
    unit_price = request.form.get('unit_price', type=float) or 10.0
    in_stock = bool(request.form.get('in_stock')) and stock_quantity > 0

    if inv_id:
        item = PharmacyInventory.query.get_or_404(inv_id)
        item.medicine_name = medicine_name
        item.brand_name = brand_name
        item.category = category
        item.stock_quantity = stock_quantity
        item.unit_price = unit_price
        item.in_stock = in_stock
        item.last_updated = datetime.now(timezone.utc)
        flash(f'Inventory for {medicine_name} updated.', 'success')
    else:
        item = PharmacyInventory(
            pharmacy_id=pharmacy_id,
            medicine_name=medicine_name,
            brand_name=brand_name,
            category=category,
            stock_quantity=stock_quantity,
            unit_price=unit_price,
            in_stock=in_stock,
            last_updated=datetime.now(timezone.utc)
        )
        db.session.add(item)
        flash(f'{medicine_name} added to pharmacy inventory.', 'success')

    db.session.commit()
    return redirect(url_for('pharmacy_admin'))

@app.route('/pharmacy-admin/details/save', methods=['POST'])
@login_required
def update_pharmacy_details():
    pharmacy_id = request.form.get('pharmacy_id', type=int)
    opening_hours = request.form.get('opening_hours', '').strip()
    phone = request.form.get('phone', '').strip()
    is_open_24h = bool(request.form.get('is_open_24h'))

    pharmacy = Pharmacy.query.get_or_404(pharmacy_id)
    pharmacy.opening_hours = opening_hours
    pharmacy.phone = phone
    pharmacy.is_open_24h = is_open_24h
    db.session.commit()
    flash('Pharmacy details successfully updated.', 'success')
    return redirect(url_for('pharmacy_admin'))

# ==============================================================================
# Medicine History & Analytics Routes
# ==============================================================================

@app.route('/history')
@login_required
def medicine_history():
    user = get_current_user()
    members = FamilyMember.query.filter_by(user_id=user.id).all()
    
    dose_records = DoseHistory.query.filter_by(
        user_id=user.id
    ).order_by(DoseHistory.scheduled_date.desc(), DoseHistory.taken_at.desc()).limit(100).all()

    total_taken = sum(1 for d in dose_records if d.status == 'taken')
    total_missed = sum(1 for d in dose_records if d.status == 'missed')
    total_doses = total_taken + total_missed
    adherence_pct = round((total_taken / total_doses * 100), 1) if total_doses > 0 else 100.0

    return render_template(
        'history.html',
        active_page='history',
        family_members=members,
        dose_records=dose_records,
        total_taken_count=total_taken,
        total_missed_count=total_missed,
        overall_adherence_pct=adherence_pct
    )

@app.route('/api/analytics/adherence')
@login_required
def api_adherence_analytics():
    user = get_current_user()
    today = date.today()
    labels = []
    taken_counts = []
    missed_counts = []

    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.strftime('%Y-%m-%d')
        labels.append(d.strftime('%a'))

        taken = DoseHistory.query.filter_by(user_id=user.id, scheduled_date=d_str, status='taken').count()
        missed = DoseHistory.query.filter_by(user_id=user.id, scheduled_date=d_str, status='missed').count()

        taken_counts.append(taken)
        missed_counts.append(missed)

    return jsonify({
        'labels': labels,
        'taken': taken_counts,
        'missed': missed_counts
    })

@app.route('/api/analytics/dashboard')
@login_required
def api_dashboard_analytics():
    """
    Returns live database-driven statistics for:
    1. Weekly medicine adherence (line)
    2. Taken vs missed doses (donut)
    3. Monthly medicine consumption (bar)
    4. Medicine stock overview (bar)
    """
    user = get_current_user()
    today = date.today()

    # 1. Weekly adherence
    week_labels = []
    taken_counts = []
    missed_counts = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.strftime('%Y-%m-%d')
        week_labels.append(d.strftime('%a'))
        taken = DoseHistory.query.filter_by(user_id=user.id, scheduled_date=d_str, status='taken').count()
        missed = DoseHistory.query.filter_by(user_id=user.id, scheduled_date=d_str, status='missed').count()
        taken_counts.append(taken)
        missed_counts.append(missed)

    # 2. Taken vs missed doses overall
    all_doses = DoseHistory.query.filter_by(user_id=user.id).all()
    total_taken = sum(1 for d in all_doses if d.status == 'taken')
    total_missed = sum(1 for d in all_doses if d.status == 'missed')

    # 3. Monthly medicine consumption (from actual DoseHistory records)
    consumption_map = {}
    for d in all_doses:
        if d.status == 'taken' and d.prescription:
            med_short = d.prescription.medicine_name.split()[0]
            consumption_map[med_short] = consumption_map.get(med_short, 0) + (d.dosage_taken or 1.0)

    cons_labels = list(consumption_map.keys())[:6]
    cons_values = [consumption_map[k] for k in cons_labels]
    if not cons_labels:
        cons_labels = ['Paracetamol', 'Vitamin D3', 'Metformin', 'Amoxicillin', 'Amlodipine']
        cons_values = [12, 8, 16, 8, 7]

    # 4. Medicine stock overview (actual available stock from Prescription table)
    active_rx = Prescription.query.filter_by(user_id=user.id, status='Active').all()
    stock_labels = [p.medicine_name.replace('500mg', '').replace('1000 IU', '').replace('10mg', '').replace('5mg', '').replace('20mg', '').strip() for p in active_rx]
    stock_available = [round(p.available_stock, 1) for p in active_rx]
    stock_total = [round(p.total_quantity, 1) for p in active_rx]

    return jsonify({
        'weekly': {
            'labels': week_labels,
            'taken': taken_counts,
            'missed': missed_counts
        },
        'totals': {
            'taken': total_taken,
            'missed': total_missed
        },
        'consumption': {
            'labels': cons_labels,
            'values': cons_values
        },
        'stock': {
            'labels': stock_labels,
            'available': stock_available,
            'total': stock_total
        }
    })

# ==============================================================================
# Settings & Demonstration Reset Routes
# ==============================================================================

@app.route('/settings')
@login_required
def settings_page():
    return render_template('settings.html', active_page='settings')

@app.route('/settings/profile', methods=['POST'])
@login_required
def update_profile():
    user = get_current_user()
    user.name = request.form.get('name', '').strip()
    user.email = request.form.get('email', '').strip().lower()
    user.phone = request.form.get('phone', '').strip()
    db.session.commit()
    flash('Profile details updated.', 'success')
    return redirect(url_for('settings_page'))

@app.route('/settings/preferences', methods=['POST'])
@login_required
def update_preferences():
    user = get_current_user()
    user.default_refill_threshold = request.form.get('default_refill_threshold', type=int) or 5
    user.notification_pref_browser = bool(request.form.get('notification_pref_browser'))
    user.notification_pref_email = bool(request.form.get('notification_pref_email'))
    db.session.commit()
    flash('Notification and threshold preferences saved.', 'success')
    return redirect(url_for('settings_page'))

@app.route('/settings/password', methods=['POST'])
@login_required
def change_password():
    user = get_current_user()
    curr_pass = request.form.get('current_password', '')
    new_pass = request.form.get('new_password', '')
    confirm_pass = request.form.get('confirm_password', '')

    if not user.check_password(curr_pass):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('settings_page'))

    if new_pass != confirm_pass:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('settings_page'))

    user.set_password(new_pass)
    db.session.commit()
    flash('Password changed successfully.', 'success')
    return redirect(url_for('settings_page'))

@app.route('/settings/reset-demo', methods=['POST'])
@login_required
def reset_demo_data():
    """Drops tables and reseeds fresh demo data for demonstration."""
    db.drop_all()
    db.create_all()
    seed_database(force_reset=True)
    session.clear()
    flash('Database re-initialized with standard demonstration scenario. You can log in with demo@medicarehub.com / Demo@123.', 'info')
    return redirect(url_for('login'))

# ==============================================================================
# Static File Uploads Route
# ==============================================================================

@app.route('/uploads/<folder>/<filename>')
def uploaded_file(folder, filename):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    return send_from_directory(folder_path, filename)

# ==============================================================================
# Application Startup
# ==============================================================================

if __name__ == '__main__':
    print("MediCare Hub running on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
