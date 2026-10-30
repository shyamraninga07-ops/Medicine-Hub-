from datetime import datetime, date, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import math

db = SQLAlchemy()

def now_utc():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user', 'pharmacy_admin'
    avatar_url = db.Column(db.String(255), default='/static/images/default-avatar.svg')
    
    # Preferences
    notification_pref_browser = db.Column(db.Boolean, default=True)
    notification_pref_email = db.Column(db.Boolean, default=True)
    notification_pref_sms = db.Column(db.Boolean, default=False)
    default_refill_threshold = db.Column(db.Integer, default=5)  # in days
    
    created_at = db.Column(db.DateTime, default=now_utc)
    
    # Relationships
    family_members = db.relationship('FamilyMember', backref='user', cascade='all, delete-orphan', lazy=True)
    prescriptions = db.relationship('Prescription', backref='user', cascade='all, delete-orphan', lazy=True)
    dose_histories = db.relationship('DoseHistory', backref='user', cascade='all, delete-orphan', lazy=True)
    refill_alerts = db.relationship('RefillAlert', backref='user', cascade='all, delete-orphan', lazy=True)
    refill_histories = db.relationship('RefillHistory', backref='user', cascade='all, delete-orphan', lazy=True)
    notifications = db.relationship('Notification', backref='user', cascade='all, delete-orphan', lazy=True)
    pharmacies = db.relationship('Pharmacy', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'avatar_url': self.avatar_url,
            'default_refill_threshold': self.default_refill_threshold,
            'notification_pref_browser': self.notification_pref_browser
        }


class FamilyMember(db.Model):
    __tablename__ = 'family_members'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    relationship = db.Column(db.String(50), default='Self')  # Self, Spouse, Child, Parent, Sibling, Grandparent, Other
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), default='Not Specified')  # Male, Female, Other
    blood_group = db.Column(db.String(10), default='Unknown')  # A+, A-, B+, B-, AB+, AB-, O+, O-, Unknown
    allergies = db.Column(db.Text, default='None known')
    medical_conditions = db.Column(db.Text, default='None')
    emergency_contact = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(255), default='')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=now_utc)
    
    # Relationships
    prescriptions = db.relationship('Prescription', backref='family_member', cascade='all, delete-orphan', lazy=True)
    dose_histories = db.relationship('DoseHistory', backref='family_member', cascade='all, delete-orphan', lazy=True)

    @property
    def age(self):
        if not self.dob:
            return 0
        today = date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'relationship': self.relationship,
            'dob': self.dob.strftime('%Y-%m-%d') if self.dob else '',
            'age': self.age,
            'gender': self.gender,
            'blood_group': self.blood_group,
            'allergies': self.allergies,
            'medical_conditions': self.medical_conditions,
            'emergency_contact': self.emergency_contact,
            'avatar_url': self.avatar_url,
            'notes': self.notes
        }


class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    family_member_id = db.Column(db.Integer, db.ForeignKey('family_members.id', ondelete='CASCADE'), nullable=False, index=True)
    
    medicine_name = db.Column(db.String(150), nullable=False)
    generic_name = db.Column(db.String(150), nullable=True)
    category = db.Column(db.String(50), default='Tablets')  # Tablets, Capsules, Syrup, Inhaler, Drops, Injection, Ointment
    
    # Dosage and intake
    dosage_amount = db.Column(db.Float, default=1.0)  # e.g., 1 tablet, 5 ml
    dosage_unit = db.Column(db.String(30), default='tablets')  # tablets, capsules, ml, puffs, drops
    frequency = db.Column(db.String(50), default='Once daily')  # Once daily, Twice daily, 3 times daily, 4 times daily, As needed
    time_slots = db.Column(db.String(120), default='Morning')  # Comma-separated: Morning, Afternoon, Evening, Night
    
    # Stock Management
    total_quantity = db.Column(db.Float, default=30.0)
    available_stock = db.Column(db.Float, default=30.0)
    low_stock_threshold = db.Column(db.Integer, default=5)  # threshold in remaining days or units
    daily_consumption = db.Column(db.Float, default=1.0)  # automatically calculated
    
    # Dates & Doctor
    start_date = db.Column(db.Date, default=date.today)
    end_date = db.Column(db.Date, nullable=True)
    doctor_name = db.Column(db.String(120), nullable=True)
    doctor_contact = db.Column(db.String(60), nullable=True)
    document_path = db.Column(db.String(255), nullable=True)  # Prescription image or PDF
    
    # Status
    status = db.Column(db.String(20), default='Active')  # Active, Completed, Expired, Paused
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=now_utc)
    updated_at = db.Column(db.DateTime, default=now_utc, onupdate=now_utc)
    
    # Relationships
    reminders = db.relationship('MedicineReminder', backref='prescription', cascade='all, delete-orphan', lazy=True)
    dose_histories = db.relationship('DoseHistory', backref='prescription', cascade='all, delete-orphan', lazy=True)
    refill_alerts = db.relationship('RefillAlert', backref='prescription', cascade='all, delete-orphan', lazy=True)
    refill_histories = db.relationship('RefillHistory', backref='prescription', cascade='all, delete-orphan', lazy=True)

    def calculate_daily_consumption(self):
        """Calculates expected daily units consumed based on frequency and dosage amount."""
        freq_map = {
            'Once daily': 1.0,
            'Twice daily': 2.0,
            '3 times daily': 3.0,
            '4 times daily': 4.0,
            'Every 8 hours': 3.0,
            'Every 12 hours': 2.0,
            'Every 6 hours': 4.0,
            'Once weekly': 1.0 / 7.0,
            'As needed': 0.5  # estimate for calculations
        }
        multiplier = freq_map.get(self.frequency, 1.0)
        # If specific time slots provided (e.g. Morning, Night), count slots
        if self.time_slots and self.frequency not in ['As needed', 'Once weekly']:
            slots = [s.strip() for s in self.time_slots.split(',') if s.strip()]
            if slots:
                multiplier = float(len(slots))
        self.daily_consumption = max(0.1, (self.dosage_amount or 1.0) * multiplier)
        return self.daily_consumption

    @property
    def estimated_remaining_days(self):
        daily = self.daily_consumption or self.calculate_daily_consumption()
        if daily <= 0:
            return 999
        if self.available_stock <= 0:
            return 0
        return math.floor(self.available_stock / daily)

    @property
    def stock_status(self):
        days = self.estimated_remaining_days
        if self.available_stock <= 0 or days <= 2:
            return 'critical'
        elif days <= (self.low_stock_threshold or 5):
            return 'low'
        return 'sufficient'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'family_member_id': self.family_member_id,
            'family_member_name': self.family_member.full_name if self.family_member else '',
            'medicine_name': self.medicine_name,
            'generic_name': self.generic_name,
            'category': self.category,
            'dosage_amount': self.dosage_amount,
            'dosage_unit': self.dosage_unit,
            'frequency': self.frequency,
            'time_slots': self.time_slots,
            'total_quantity': self.total_quantity,
            'available_stock': self.available_stock,
            'daily_consumption': self.daily_consumption,
            'estimated_remaining_days': self.estimated_remaining_days,
            'stock_status': self.stock_status,
            'low_stock_threshold': self.low_stock_threshold,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else '',
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else '',
            'doctor_name': self.doctor_name,
            'doctor_contact': self.doctor_contact,
            'document_path': self.document_path,
            'status': self.status,
            'notes': self.notes
        }


class MedicineReminder(db.Model):
    __tablename__ = 'medicine_reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    family_member_id = db.Column(db.Integer, db.ForeignKey('family_members.id', ondelete='CASCADE'), nullable=False)
    
    time_slot = db.Column(db.String(30), default='Morning')  # Morning, Afternoon, Evening, Night, Custom
    reminder_time = db.Column(db.String(10), default='08:00')  # 24-hr format "HH:MM"
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_utc)


class DoseHistory(db.Model):
    __tablename__ = 'dose_histories'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    family_member_id = db.Column(db.Integer, db.ForeignKey('family_members.id', ondelete='CASCADE'), nullable=False)
    
    scheduled_date = db.Column(db.String(12), nullable=False, index=True)  # YYYY-MM-DD
    scheduled_time = db.Column(db.String(20), nullable=False)  # e.g. "Morning", "08:00"
    dosage_taken = db.Column(db.Float, default=1.0)
    status = db.Column(db.String(20), nullable=False)  # 'taken', 'missed'
    taken_at = db.Column(db.DateTime, default=now_utc)
    notes = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('prescription_id', 'scheduled_date', 'scheduled_time', name='uq_dose_per_slot_day'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'prescription_id': self.prescription_id,
            'medicine_name': self.prescription.medicine_name if self.prescription else '',
            'family_member_id': self.family_member_id,
            'family_member_name': self.family_member.full_name if self.family_member else '',
            'scheduled_date': self.scheduled_date,
            'scheduled_time': self.scheduled_time,
            'dosage_taken': self.dosage_taken,
            'status': self.status,
            'taken_at': self.taken_at.strftime('%Y-%m-%d %H:%M') if self.taken_at else '',
            'notes': self.notes
        }


class RefillAlert(db.Model):
    __tablename__ = 'refill_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    medicine_name = db.Column(db.String(150), nullable=False)
    remaining_stock = db.Column(db.Float, nullable=False)
    estimated_days_remaining = db.Column(db.Integer, default=0)
    priority = db.Column(db.String(20), default='soon')  # 'critical', 'soon', 'normal'
    status = db.Column(db.String(20), default='active')  # 'active', 'resolved', 'dismissed'
    
    created_at = db.Column(db.DateTime, default=now_utc)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'prescription_id': self.prescription_id,
            'medicine_name': self.medicine_name,
            'family_member_name': self.prescription.family_member.full_name if (self.prescription and self.prescription.family_member) else 'Unknown',
            'remaining_stock': self.remaining_stock,
            'dosage_unit': self.prescription.dosage_unit if self.prescription else 'units',
            'estimated_days_remaining': self.estimated_days_remaining,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.strftime('%b %d, %Y %I:%M %p') if self.created_at else ''
        }


class RefillHistory(db.Model):
    __tablename__ = 'refill_histories'
    
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    previous_stock = db.Column(db.Float, default=0.0)
    added_quantity = db.Column(db.Float, nullable=False)
    new_stock = db.Column(db.Float, nullable=False)
    pharmacy_name = db.Column(db.String(150), nullable=True)
    cost = db.Column(db.Float, nullable=True)
    refilled_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'prescription_id': self.prescription_id,
            'medicine_name': self.prescription.medicine_name if self.prescription else '',
            'previous_stock': self.previous_stock,
            'added_quantity': self.added_quantity,
            'new_stock': self.new_stock,
            'pharmacy_name': self.pharmacy_name,
            'cost': self.cost,
            'refilled_at': self.refilled_at.strftime('%b %d, %Y') if self.refilled_at else '',
            'notes': self.notes
        }


class Pharmacy(db.Model):
    __tablename__ = 'pharmacies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    license_number = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), default='Metro Health City')
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    opening_hours = db.Column(db.String(100), default='8:00 AM - 10:00 PM')
    is_open_24h = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Float, default=4.8)
    reviews_count = db.Column(db.Integer, default=128)
    created_at = db.Column(db.DateTime, default=now_utc)
    
    # Relationships
    inventory_items = db.relationship('PharmacyInventory', backref='pharmacy', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'license_number': self.license_number,
            'address': self.address,
            'city': self.city,
            'phone': self.phone,
            'email': self.email,
            'lat': self.lat,
            'lng': self.lng,
            'opening_hours': self.opening_hours,
            'is_open_24h': self.is_open_24h,
            'is_verified': self.is_verified,
            'rating': self.rating,
            'reviews_count': self.reviews_count
        }


class PharmacyInventory(db.Model):
    __tablename__ = 'pharmacy_inventories'
    
    id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.id', ondelete='CASCADE'), nullable=False, index=True)
    medicine_name = db.Column(db.String(150), nullable=False, index=True)
    brand_name = db.Column(db.String(150), nullable=True)
    generic_name = db.Column(db.String(150), nullable=True)
    category = db.Column(db.String(50), default='Tablets')
    dosage_form = db.Column(db.String(50), default='500mg')
    unit_price = db.Column(db.Float, default=12.50)
    in_stock = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer, default=50)
    unit = db.Column(db.String(30), default='tablets')
    prescription_required = db.Column(db.Boolean, default=True)
    last_updated = db.Column(db.DateTime, default=now_utc, onupdate=now_utc)

    def to_dict(self):
        return {
            'id': self.id,
            'pharmacy_id': self.pharmacy_id,
            'pharmacy_name': self.pharmacy.name if self.pharmacy else '',
            'medicine_name': self.medicine_name,
            'brand_name': self.brand_name,
            'generic_name': self.generic_name,
            'category': self.category,
            'dosage_form': self.dosage_form,
            'unit_price': self.unit_price,
            'in_stock': self.in_stock,
            'stock_quantity': self.stock_quantity,
            'unit': self.unit,
            'prescription_required': self.prescription_required,
            'last_updated': self.last_updated.strftime('%b %d, %Y %I:%M %p') if self.last_updated else ''
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(30), default='reminder')  # reminder, refill, system, stock
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now_utc)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%b %d, %I:%M %p') if self.created_at else ''
        }
