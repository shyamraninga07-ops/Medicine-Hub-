import os
from datetime import datetime, date, timedelta, timezone
from models import (
    db, User, FamilyMember, Prescription, MedicineReminder,
    DoseHistory, RefillAlert, RefillHistory, Pharmacy, PharmacyInventory, Notification
)

def seed_database(force_reset=False):
    """
    Populates the MediCare Hub database with realistic demonstration data.
    Ensures relationships between user, family profiles, prescriptions, reminders,
    refill alerts, dose histories, Rajkot pharmacies, and pharmacy inventories.
    """
    # If not forcing reset and user exists, skip to prevent duplicates
    if not force_reset and User.query.filter_by(email="demo@medicarehub.com").first():
        print("Demo database already seeded. Skipping seed.")
        return

    print("Seeding MediCare Hub with complete demonstration scenario...")

    # 1. Create Demonstration Account & Pharmacy Admin
    # Required: demo@medicarehub.com / Demo@123
    demo_user = User.query.filter_by(email="demo@medicarehub.com").first()
    if not demo_user:
        demo_user = User(
            name="Sarah Johnson",
            email="demo@medicarehub.com",
            phone="+91 98765 01234 (Demo)",
            role="user",
            avatar_url="/static/images/avatar-sarah.svg",
            notification_pref_browser=True,
            notification_pref_email=True,
            default_refill_threshold=5
        )
        demo_user.set_password("Demo@123")
        db.session.add(demo_user)

    # Secondary account for demonstration
    sarah_user = User.query.filter_by(email="sarah@medicarehub.com").first()
    if not sarah_user:
        sarah_user = User(
            name="Sarah Johnson",
            email="sarah@medicarehub.com",
            phone="+91 98765 01234 (Demo)",
            role="user",
            avatar_url="/static/images/avatar-sarah.svg",
            notification_pref_browser=True,
            notification_pref_email=True,
            default_refill_threshold=5
        )
        sarah_user.set_password("Password123!")
        db.session.add(sarah_user)

    # Pharmacy Admin Account
    pharmacy_admin = User.query.filter_by(email="healthplus@medicarehub.com").first()
    if not pharmacy_admin:
        pharmacy_admin = User(
            name="Dr. Marcus Vance (HealthPlus)",
            email="healthplus@medicarehub.com",
            phone="+91 98250 12345 (Demo)",
            role="pharmacy_admin",
            avatar_url="/static/images/avatar-doc.svg",
            notification_pref_browser=True
        )
        pharmacy_admin.set_password("Demo@123")
        db.session.add(pharmacy_admin)

    db.session.commit()

    # Clean existing data for demo_user to prevent duplicate constraints if reseeding
    for u in [demo_user, sarah_user]:
        if u:
            FamilyMember.query.filter_by(user_id=u.id).delete()
            Prescription.query.filter_by(user_id=u.id).delete()
            MedicineReminder.query.filter_by(user_id=u.id).delete()
            DoseHistory.query.filter_by(user_id=u.id).delete()
            RefillAlert.query.filter_by(user_id=u.id).delete()
            RefillHistory.query.filter_by(user_id=u.id).delete()
            Notification.query.filter_by(user_id=u.id).delete()
    db.session.commit()

    # 2. ADD FAMILY MEMBER DATA (Exact requested profiles)
    # Sarah Johnson: Age 32, Female, B+, Allergies: Penicillin, Condition: None
    fm_sarah = FamilyMember(
        user_id=demo_user.id,
        full_name="Sarah Johnson",
        relationship="Self",
        dob=date(1994, 4, 12),
        gender="Female",
        blood_group="B+",
        allergies="Penicillin",
        medical_conditions="None",
        emergency_contact="+91 98765 01234 (Self)",
        avatar_url="/static/images/avatar-sarah.svg",
        notes="Primary caregiver and account holder."
    )

    # John Johnson: Age 10, Male, O+, Allergies: None, Condition: Asthma
    fm_john = FamilyMember(
        user_id=demo_user.id,
        full_name="John Johnson",
        relationship="Child",
        dob=date(2016, 3, 15),
        gender="Male",
        blood_group="O+",
        allergies="None",
        medical_conditions="Asthma",
        emergency_contact="+91 98765 01234 (Sarah Johnson)",
        avatar_url="/static/images/avatar-john.svg",
        notes="Carry inhaler for acute asthma episodes during physical activity."
    )

    # Emma Johnson: Age 8, Female, A+, Allergies: Peanuts, Condition: None
    fm_emma = FamilyMember(
        user_id=demo_user.id,
        full_name="Emma Johnson",
        relationship="Child",
        dob=date(2018, 9, 5),
        gender="Female",
        blood_group="A+",
        allergies="Peanuts",
        medical_conditions="None",
        emergency_contact="+91 98765 01234 (Sarah Johnson)",
        avatar_url="/static/images/avatar-emma.svg",
        notes="Strict peanut-free diet; school nurse notified."
    )

    # David Johnson: Age 65, Male, AB+, Allergies: None, Condition: Hypertension
    fm_david = FamilyMember(
        user_id=demo_user.id,
        full_name="David Johnson",
        relationship="Parent",
        dob=date(1961, 8, 20),
        gender="Male",
        blood_group="AB+",
        allergies="None",
        medical_conditions="Hypertension, Type 2 Diabetes",
        emergency_contact="+91 98765 01234 (Sarah Johnson)",
        avatar_url="/static/images/avatar-david.svg",
        notes="Requires daily blood pressure and morning glucose tracking."
    )

    db.session.add_all([fm_sarah, fm_john, fm_emma, fm_david])
    db.session.commit()

    # 3. ADD PRESCRIPTION DATA (At least 10 sample prescriptions)
    today = date.today()

    prescriptions_data = [
        # 1. Paracetamol 500mg (Sarah / Family)
        {
            'member': fm_sarah,
            'name': 'Paracetamol 500mg',
            'generic': 'Acetaminophen',
            'cat': 'Tablets',
            'dose': 1.0,
            'unit': 'tablets',
            'freq': 'Twice daily',
            'slots': 'Morning, Night',
            'total': 30.0,
            'stock': 12.0,
            'low_threshold': 5,
            'start': today - timedelta(days=9),
            'doc': 'Dr. Anita Mehta, MD (Fictional Demo)',
            'doc_contact': '+91 98251 00111 (Demo)',
            'notes': 'For acute headache and fever as needed.'
        },
        # 2. Vitamin D3 1000 IU (Sarah) - Refill Soon (5 days left)
        {
            'member': fm_sarah,
            'name': 'Vitamin D3 1000 IU',
            'generic': 'Cholecalciferol',
            'cat': 'Capsules',
            'dose': 1.0,
            'unit': 'capsules',
            'freq': 'Once daily',
            'slots': 'Morning',
            'total': 60.0,
            'stock': 5.0,  # 5 days left -> Refill Soon
            'low_threshold': 5,
            'start': today - timedelta(days=55),
            'doc': 'Dr. Rajesh Patel, MD (Fictional Demo)',
            'doc_contact': '+91 98251 00222 (Demo)',
            'notes': 'Daily bone mineral density support.'
        },
        # 3. Metformin 500mg (David) - Refill Soon (3 days left)
        {
            'member': fm_david,
            'name': 'Metformin 500mg',
            'generic': 'Metformin HCl',
            'cat': 'Tablets',
            'dose': 1.0,
            'unit': 'tablets',
            'freq': 'Twice daily',
            'slots': 'Morning, Night',
            'total': 60.0,
            'stock': 6.0,  # 6 / 2 = 3 days left -> Refill Soon
            'low_threshold': 5,
            'start': today - timedelta(days=27),
            'doc': 'Dr. Bhavesh Shah, Diabetologist (Fictional Demo)',
            'doc_contact': '+91 98251 00333 (Demo)',
            'notes': 'Take with meals to reduce GI irritation.'
        },
        # 4. Amoxicillin 500mg (Emma) - Critical (2 days left)
        {
            'member': fm_emma,
            'name': 'Amoxicillin 500mg',
            'generic': 'Amoxicillin Trihydrate',
            'cat': 'Capsules',
            'dose': 1.0,
            'unit': 'capsules',
            'freq': 'Twice daily',
            'slots': 'Morning, Night',
            'total': 20.0,
            'stock': 4.0,  # 4 / 2 = 2 days left -> Critical
            'low_threshold': 5,
            'start': today - timedelta(days=8),
            'doc': 'Dr. Priya Dave, Pediatrician (Fictional Demo)',
            'doc_contact': '+91 98251 00444 (Demo)',
            'notes': 'Complete full prescribed course for ear infection.'
        },
        # 5. Cetirizine 10mg (John) - Sufficient (10 days left)
        {
            'member': fm_john,
            'name': 'Cetirizine 10mg',
            'generic': 'Cetirizine HCl',
            'cat': 'Tablets',
            'dose': 1.0,
            'unit': 'tablets',
            'freq': 'Once daily',
            'slots': 'Night',
            'total': 30.0,
            'stock': 10.0,  # 10 days left -> Sufficient
            'low_threshold': 5,
            'start': today - timedelta(days=20),
            'doc': 'Dr. Priya Dave, Pediatrician (Fictional Demo)',
            'doc_contact': '+91 98251 00444 (Demo)',
            'notes': 'Non-sedating antihistamine for seasonal allergy relief.'
        },
        # 6. Amlodipine 5mg (David) - Critical (1 day left)
        {
            'member': fm_david,
            'name': 'Amlodipine 5mg',
            'generic': 'Amlodipine Besylate',
            'cat': 'Tablets',
            'dose': 1.0,
            'unit': 'tablets',
            'freq': 'Once daily',
            'slots': 'Morning',
            'total': 30.0,
            'stock': 1.0,  # 1 day left -> Critical
            'low_threshold': 5,
            'start': today - timedelta(days=29),
            'doc': 'Dr. Ketan Joshi, Cardiologist (Fictional Demo)',
            'doc_contact': '+91 98251 00555 (Demo)',
            'notes': 'Daily blood pressure control tablet.'
        },
        # 7. Omeprazole 20mg (David) - Sufficient (22 days left)
        {
            'member': fm_david,
            'name': 'Omeprazole 20mg',
            'generic': 'Omeprazole Magnesium',
            'cat': 'Capsules',
            'dose': 1.0,
            'unit': 'capsules',
            'freq': 'Once daily',
            'slots': 'Morning',
            'total': 30.0,
            'stock': 22.0,
            'low_threshold': 5,
            'start': today - timedelta(days=8),
            'doc': 'Dr. Ketan Joshi, Cardiologist (Fictional Demo)',
            'doc_contact': '+91 98251 00555 (Demo)',
            'notes': 'Take 30 minutes before morning breakfast.'
        },
        # 8. Calcium 500mg (Sarah) - Sufficient (38 days left)
        {
            'member': fm_sarah,
            'name': 'Calcium 500mg',
            'generic': 'Calcium Carbonate + D3',
            'cat': 'Tablets',
            'dose': 1.0,
            'unit': 'tablets',
            'freq': 'Once daily',
            'slots': 'Afternoon',
            'total': 60.0,
            'stock': 38.0,
            'low_threshold': 5,
            'start': today - timedelta(days=22),
            'doc': 'Dr. Anita Mehta, MD (Fictional Demo)',
            'doc_contact': '+91 98251 00111 (Demo)',
            'notes': 'Daily bone and calcium dietary supplement.'
        },
        # 9. Azithromycin 500mg (John) - Short Course (3 days left)
        {
            'member': fm_john,
            'name': 'Azithromycin 500mg',
            'generic': 'Azithromycin Dihydrate',
            'cat': 'Tablets',
            'dose': 1.0,
            'unit': 'tablets',
            'freq': 'Once daily',
            'slots': 'Morning',
            'total': 5.0,
            'stock': 3.0,
            'low_threshold': 2,
            'start': today - timedelta(days=2),
            'doc': 'Dr. Ramesh Vora, Pulmonologist (Fictional Demo)',
            'doc_contact': '+91 98251 00666 (Demo)',
            'notes': '5-day antibiotic regimen for respiratory bronchial flare.'
        },
        # 10. Iron Supplement (Emma) - Sufficient (18 days left)
        {
            'member': fm_emma,
            'name': 'Iron Supplement',
            'generic': 'Ferrous Fumarate + Folic Acid',
            'cat': 'Tablets',
            'dose': 1.0,
            'unit': 'tablets',
            'freq': 'Once daily',
            'slots': 'Afternoon',
            'total': 30.0,
            'stock': 18.0,
            'low_threshold': 5,
            'start': today - timedelta(days=12),
            'doc': 'Dr. Priya Dave, Pediatrician (Fictional Demo)',
            'doc_contact': '+91 98251 00444 (Demo)',
            'notes': 'Pediatric iron therapy with vitamin C juice.'
        }
    ]

    saved_prescriptions = []
    for item in prescriptions_data:
        rx = Prescription(
            user_id=demo_user.id,
            family_member_id=item['member'].id,
            medicine_name=item['name'],
            generic_name=item['generic'],
            category=item['cat'],
            dosage_amount=item['dose'],
            dosage_unit=item['unit'],
            frequency=item['freq'],
            time_slots=item['slots'],
            total_quantity=item['total'],
            available_stock=item['stock'],
            low_stock_threshold=item['low_threshold'],
            start_date=item['start'],
            doctor_name=item['doc'],
            doctor_contact=item['doc_contact'],
            notes=item['notes'],
            status='Active'
        )
        rx.calculate_daily_consumption()
        db.session.add(rx)
        saved_prescriptions.append(rx)

    db.session.commit()

    # 4. ADD MEDICINE REMINDER DATA (At least 12 scheduled reminders)
    slot_times = {
        'Morning': '08:00',
        'Afternoon': '14:00',
        'Evening': '18:30',
        'Night': '20:00'
    }

    custom_hours = {
        'Metformin 500mg_Morning': '09:00',
        'Omeprazole 20mg_Morning': '08:30',
        'Calcium 500mg_Afternoon': '13:30',
        'Cetirizine 10mg_Afternoon': '14:00',
        'Amlodipine 5mg_Night': '20:00',
        'Metformin 500mg_Night': '21:00'
    }

    for rx in saved_prescriptions:
        slots = [s.strip() for s in rx.time_slots.split(',') if s.strip()]
        for slot in slots:
            time_str = custom_hours.get(f"{rx.medicine_name}_{slot}", slot_times.get(slot, '08:00'))
            rem = MedicineReminder(
                prescription_id=rx.id,
                user_id=demo_user.id,
                family_member_id=rx.family_member_id,
                time_slot=slot,
                reminder_time=time_str,
                is_active=True
            )
            db.session.add(rem)
    db.session.commit()

    # 5. ADD HISTORICAL DOSE RECORDS (At least 20 historical dose records across past 7 days)
    for days_back in range(7, 0, -1):
        hist_date = today - timedelta(days=days_back)
        date_str = hist_date.strftime('%Y-%m-%d')

        # Sarah: Vitamin D3 Morning
        db.session.add(DoseHistory(
            prescription_id=saved_prescriptions[1].id,
            user_id=demo_user.id,
            family_member_id=fm_sarah.id,
            scheduled_date=date_str,
            scheduled_time="Morning",
            dosage_taken=1.0,
            status='taken',
            taken_at=datetime.combine(hist_date, datetime.strptime("08:05", "%H:%M").time())
        ))

        # David: Metformin Morning
        db.session.add(DoseHistory(
            prescription_id=saved_prescriptions[2].id,
            user_id=demo_user.id,
            family_member_id=fm_david.id,
            scheduled_date=date_str,
            scheduled_time="Morning",
            dosage_taken=1.0,
            status='taken',
            taken_at=datetime.combine(hist_date, datetime.strptime("09:12", "%H:%M").time())
        ))

        # David: Amlodipine Morning
        db.session.add(DoseHistory(
            prescription_id=saved_prescriptions[5].id,
            user_id=demo_user.id,
            family_member_id=fm_david.id,
            scheduled_date=date_str,
            scheduled_time="Morning",
            dosage_taken=1.0,
            status='taken',
            taken_at=datetime.combine(hist_date, datetime.strptime("08:15", "%H:%M").time())
        ))

        # David: Metformin Night (1 missed dose on day 3)
        david_night_status = 'missed' if days_back == 3 else 'taken'
        db.session.add(DoseHistory(
            prescription_id=saved_prescriptions[2].id,
            user_id=demo_user.id,
            family_member_id=fm_david.id,
            scheduled_date=date_str,
            scheduled_time="Night",
            dosage_taken=1.0 if david_night_status == 'taken' else 0.0,
            status=david_night_status,
            taken_at=datetime.combine(hist_date, datetime.strptime("21:10", "%H:%M").time()) if david_night_status == 'taken' else None
        ))

        # John: Cetirizine Night (1 missed dose on day 5)
        john_night_status = 'missed' if days_back == 5 else 'taken'
        db.session.add(DoseHistory(
            prescription_id=saved_prescriptions[4].id,
            user_id=demo_user.id,
            family_member_id=fm_john.id,
            scheduled_date=date_str,
            scheduled_time="Night",
            dosage_taken=1.0 if john_night_status == 'taken' else 0.0,
            status=john_night_status,
            taken_at=datetime.combine(hist_date, datetime.strptime("20:45", "%H:%M").time()) if john_night_status == 'taken' else None
        ))

    # Today's Morning completed & missed doses:
    today_str = today.strftime('%Y-%m-%d')

    # 08:00 AM – Vitamin D3 – Sarah – Taken
    db.session.add(DoseHistory(
        prescription_id=saved_prescriptions[1].id,
        user_id=demo_user.id,
        family_member_id=fm_sarah.id,
        scheduled_date=today_str,
        scheduled_time="Morning",
        dosage_taken=1.0,
        status='taken',
        taken_at=datetime.combine(today, datetime.strptime("08:00", "%H:%M").time())
    ))

    # 09:00 AM – Metformin – David – Taken
    db.session.add(DoseHistory(
        prescription_id=saved_prescriptions[2].id,
        user_id=demo_user.id,
        family_member_id=fm_david.id,
        scheduled_date=today_str,
        scheduled_time="Morning",
        dosage_taken=1.0,
        status='taken',
        taken_at=datetime.combine(today, datetime.strptime("09:00", "%H:%M").time())
    ))

    # 08:00 AM – Amlodipine – David – Taken
    db.session.add(DoseHistory(
        prescription_id=saved_prescriptions[5].id,
        user_id=demo_user.id,
        family_member_id=fm_david.id,
        scheduled_date=today_str,
        scheduled_time="Morning",
        dosage_taken=1.0,
        status='taken',
        taken_at=datetime.combine(today, datetime.strptime("08:10", "%H:%M").time())
    ))

    # 08:30 AM – Omeprazole – David – Taken
    db.session.add(DoseHistory(
        prescription_id=saved_prescriptions[6].id,
        user_id=demo_user.id,
        family_member_id=fm_david.id,
        scheduled_date=today_str,
        scheduled_time="Morning",
        dosage_taken=1.0,
        status='taken',
        taken_at=datetime.combine(today, datetime.strptime("08:30", "%H:%M").time())
    ))

    # 08:00 AM – Azithromycin – John – Taken
    db.session.add(DoseHistory(
        prescription_id=saved_prescriptions[8].id,
        user_id=demo_user.id,
        family_member_id=fm_john.id,
        scheduled_date=today_str,
        scheduled_time="Morning",
        dosage_taken=1.0,
        status='taken',
        taken_at=datetime.combine(today, datetime.strptime("08:15", "%H:%M").time())
    ))

    # 08:00 AM – Paracetamol – Sarah – Missed (sample missed dose)
    db.session.add(DoseHistory(
        prescription_id=saved_prescriptions[0].id,
        user_id=demo_user.id,
        family_member_id=fm_sarah.id,
        scheduled_date=today_str,
        scheduled_time="Morning",
        dosage_taken=0.0,
        status='missed',
        taken_at=None,
        notes="Fever subsided; dose skipped"
    ))

    db.session.commit()

    # 6. ADD REFILL ALERT DATA (At least 5 sample refill alerts)
    refill_alerts_data = [
        RefillAlert(
            prescription_id=saved_prescriptions[3].id,  # Amoxicillin
            user_id=demo_user.id,
            medicine_name="Amoxicillin 500mg",
            remaining_stock=4.0,
            estimated_days_remaining=2,
            priority="critical",
            status="active"
        ),
        RefillAlert(
            prescription_id=saved_prescriptions[5].id,  # Amlodipine
            user_id=demo_user.id,
            medicine_name="Amlodipine 5mg",
            remaining_stock=1.0,
            estimated_days_remaining=1,
            priority="critical",
            status="active"
        ),
        RefillAlert(
            prescription_id=saved_prescriptions[2].id,  # Metformin
            user_id=demo_user.id,
            medicine_name="Metformin 500mg",
            remaining_stock=6.0,
            estimated_days_remaining=3,
            priority="soon",
            status="active"
        ),
        RefillAlert(
            prescription_id=saved_prescriptions[1].id,  # Vitamin D3
            user_id=demo_user.id,
            medicine_name="Vitamin D3 1000 IU",
            remaining_stock=5.0,
            estimated_days_remaining=5,
            priority="soon",
            status="active"
        ),
        RefillAlert(
            prescription_id=saved_prescriptions[4].id,  # Cetirizine
            user_id=demo_user.id,
            medicine_name="Cetirizine 10mg",
            remaining_stock=10.0,
            estimated_days_remaining=10,
            priority="normal",
            status="active"
        )
    ]
    db.session.add_all(refill_alerts_data)
    db.session.commit()

    # Past Refill History
    db.session.add(RefillHistory(
        prescription_id=saved_prescriptions[6].id,  # Omeprazole
        user_id=demo_user.id,
        previous_stock=2.0,
        added_quantity=30.0,
        new_stock=32.0,
        pharmacy_name="HealthPlus Pharmacy, Yagnik Road, Rajkot",
        cost=145.00,
        refilled_at=datetime.now(timezone.utc) - timedelta(days=8),
        notes="30-day bottle restocked by Sarah."
    ))
    db.session.add(RefillHistory(
        prescription_id=saved_prescriptions[7].id,  # Calcium
        user_id=demo_user.id,
        previous_stock=8.0,
        added_quantity=60.0,
        new_stock=68.0,
        pharmacy_name="CareWell Medical Store, Kalawad Road, Rajkot",
        cost=220.00,
        refilled_at=datetime.now(timezone.utc) - timedelta(days=22),
        notes="Standard 60-count calcium supplement."
    ))
    db.session.commit()

    # 7. ADD 8 FICTIONAL DEMONSTRATION PHARMACIES IN RAJKOT, GUJARAT, INDIA
    Pharmacy.query.delete()
    PharmacyInventory.query.delete()
    db.session.commit()

    rajkot_pharmacies = [
        Pharmacy(
            user_id=pharmacy_admin.id,
            name="HealthPlus Pharmacy (Demo)",
            license_number="GJ-RJT-DEMO-2024-01",
            address="Dr. Yagnik Road, Near Jagnath Plot",
            city="Rajkot, Gujarat 360001",
            phone="+91 98250 12345 (Demo)",
            email="healthplus.rajkot@demo-pharmacy.in",
            lat=22.2985,
            lng=70.7975,
            opening_hours="Open 24 Hours (Daily)",
            is_open_24h=True,
            is_verified=True,
            rating=4.9,
            reviews_count=214
        ),
        Pharmacy(
            name="CareWell Medical Store (Demo)",
            license_number="GJ-RJT-DEMO-2024-02",
            address="Kalawad Road, Opposite Crystal Mall",
            city="Rajkot, Gujarat 360005",
            phone="+91 98250 23456 (Demo)",
            email="carewell.rajkot@demo-pharmacy.in",
            lat=22.2850,
            lng=70.7690,
            opening_hours="08:00 AM - 11:00 PM",
            is_open_24h=False,
            is_verified=True,
            rating=4.8,
            reviews_count=182
        ),
        Pharmacy(
            name="MediLife Pharmacy (Demo)",
            license_number="GJ-RJT-DEMO-2024-03",
            address="Dr. Yagnik Road, Imperial Heights",
            city="Rajkot, Gujarat 360001",
            phone="+91 98250 34567 (Demo)",
            email="medilife.rajkot@demo-pharmacy.in",
            lat=22.3010,
            lng=70.7990,
            opening_hours="08:30 AM - 10:30 PM",
            is_open_24h=False,
            is_verified=True,
            rating=4.7,
            reviews_count=145
        ),
        Pharmacy(
            name="City Medical Store (Demo)",
            license_number="GJ-RJT-DEMO-2024-04",
            address="Dhebar Road, Near Civil Hospital Chowk",
            city="Rajkot, Gujarat 360001",
            phone="+91 98250 45678 (Demo)",
            email="citymed.rajkot@demo-pharmacy.in",
            lat=22.3080,
            lng=70.8040,
            opening_hours="08:00 AM - 10:00 PM",
            is_open_24h=False,
            is_verified=True,
            rating=4.6,
            reviews_count=129
        ),
        Pharmacy(
            name="Apollo Demo Pharmacy (Demo)",
            license_number="GJ-RJT-DEMO-2024-05",
            address="150 Feet Ring Road, Near Indira Circle",
            city="Rajkot, Gujarat 360005",
            phone="+91 98250 56789 (Demo)",
            email="apollo.rajkot@demo-pharmacy.in",
            lat=22.2920,
            lng=70.7780,
            opening_hours="Open 24 Hours",
            is_open_24h=True,
            is_verified=True,
            rating=4.9,
            reviews_count=268
        ),
        Pharmacy(
            name="Wellness Pharmacy (Demo)",
            license_number="GJ-RJT-DEMO-2024-06",
            address="University Road, Near Panchayat Nagar",
            city="Rajkot, Gujarat 360005",
            phone="+91 98250 67890 (Demo)",
            email="wellness.rajkot@demo-pharmacy.in",
            lat=22.2950,
            lng=70.7850,
            opening_hours="09:00 AM - 10:00 PM",
            is_open_24h=False,
            is_verified=True,
            rating=4.7,
            reviews_count=118
        ),
        Pharmacy(
            name="FamilyCare Medicals (Demo)",
            license_number="GJ-RJT-DEMO-2024-07",
            address="Tagore Road, Near Hemu Gadhvi Hall",
            city="Rajkot, Gujarat 360002",
            phone="+91 98250 78901 (Demo)",
            email="familycare.rajkot@demo-pharmacy.in",
            lat=22.2930,
            lng=70.8010,
            opening_hours="08:00 AM - 11:00 PM",
            is_open_24h=False,
            is_verified=True,
            rating=4.8,
            reviews_count=154
        ),
        Pharmacy(
            name="LifeLine Pharmacy (Demo)",
            license_number="GJ-RJT-DEMO-2024-08",
            address="Kuvadva Road, Near Parevadi Chowk",
            city="Rajkot, Gujarat 360003",
            phone="+91 98250 89012 (Demo)",
            email="lifeline.rajkot@demo-pharmacy.in",
            lat=22.3150,
            lng=70.8150,
            opening_hours="09:00 AM - 09:30 PM",
            is_open_24h=False,
            is_verified=True,
            rating=4.5,
            reviews_count=92
        )
    ]
    db.session.add_all(rajkot_pharmacies)
    db.session.commit()

    # 8. ADD AT LEAST 20 PHARMACY INVENTORY RECORDS
    p1 = rajkot_pharmacies[0]  # HealthPlus
    p2 = rajkot_pharmacies[1]  # CareWell
    p3 = rajkot_pharmacies[2]  # MediLife
    p4 = rajkot_pharmacies[3]  # City Medical
    p5 = rajkot_pharmacies[4]  # Apollo
    p6 = rajkot_pharmacies[5]  # Wellness
    p7 = rajkot_pharmacies[6]  # FamilyCare
    p8 = rajkot_pharmacies[7]  # LifeLine

    sample_inventory = [
        # HealthPlus (Yagnik Road) - Well stocked
        PharmacyInventory(pharmacy_id=p1.id, medicine_name="Metformin 500mg", brand_name="Glycomet 500", generic_name="Metformin HCl", category="Tablets", dosage_form="500mg tablet", unit_price=42.00, in_stock=True, stock_quantity=120, unit="tablets", prescription_required=True),
        PharmacyInventory(pharmacy_id=p1.id, medicine_name="Amoxicillin 500mg", brand_name="Mox 500", generic_name="Amoxicillin Trihydrate", category="Capsules", dosage_form="500mg capsule", unit_price=78.50, in_stock=True, stock_quantity=45, unit="capsules", prescription_required=True),
        PharmacyInventory(pharmacy_id=p1.id, medicine_name="Paracetamol 500mg", brand_name="Dolo 500", generic_name="Paracetamol", category="Tablets", dosage_form="500mg tablet", unit_price=25.00, in_stock=True, stock_quantity=200, unit="tablets", prescription_required=False),
        PharmacyInventory(pharmacy_id=p1.id, medicine_name="Amlodipine 5mg", brand_name="Amlong 5", generic_name="Amlodipine Besylate", category="Tablets", dosage_form="5mg tablet", unit_price=35.00, in_stock=True, stock_quantity=80, unit="tablets", prescription_required=True),
        PharmacyInventory(pharmacy_id=p1.id, medicine_name="Vitamin D3 1000 IU", brand_name="Calcirol D3", generic_name="Cholecalciferol", category="Capsules", dosage_form="1000 IU capsule", unit_price=95.00, in_stock=True, stock_quantity=50, unit="capsules", prescription_required=False),

        # CareWell (Kalawad Road)
        PharmacyInventory(pharmacy_id=p2.id, medicine_name="Metformin 500mg", brand_name="Glycomet 500", generic_name="Metformin HCl", category="Tablets", dosage_form="500mg tablet", unit_price=44.00, in_stock=True, stock_quantity=65, unit="tablets", prescription_required=True),
        PharmacyInventory(pharmacy_id=p2.id, medicine_name="Amoxicillin 500mg", brand_name="Novamox 500", generic_name="Amoxicillin", category="Capsules", dosage_form="500mg capsule", unit_price=82.00, in_stock=False, stock_quantity=0, unit="capsules", prescription_required=True),  # Out of stock
        PharmacyInventory(pharmacy_id=p2.id, medicine_name="Cetirizine 10mg", brand_name="Cetzine 10", generic_name="Cetirizine HCl", category="Tablets", dosage_form="10mg tablet", unit_price=38.00, in_stock=True, stock_quantity=90, unit="tablets", prescription_required=False),
        PharmacyInventory(pharmacy_id=p2.id, medicine_name="Omeprazole 20mg", brand_name="Omez 20", generic_name="Omeprazole Magnesium", category="Capsules", dosage_form="20mg capsule", unit_price=65.00, in_stock=True, stock_quantity=110, unit="capsules", prescription_required=False),
        PharmacyInventory(pharmacy_id=p2.id, medicine_name="Calcium 500mg", brand_name="Shelcal 500", generic_name="Calcium Carbonate", category="Tablets", dosage_form="500mg tablet", unit_price=110.00, in_stock=True, stock_quantity=40, unit="tablets", prescription_required=False),

        # MediLife (Imperial Heights)
        PharmacyInventory(pharmacy_id=p3.id, medicine_name="Amoxicillin 500mg", brand_name="Mox 500", generic_name="Amoxicillin", category="Capsules", dosage_form="500mg capsule", unit_price=76.00, in_stock=True, stock_quantity=35, unit="capsules", prescription_required=True),
        PharmacyInventory(pharmacy_id=p3.id, medicine_name="Amlodipine 5mg", brand_name="Stamlo 5", generic_name="Amlodipine", category="Tablets", dosage_form="5mg tablet", unit_price=36.50, in_stock=True, stock_quantity=55, unit="tablets", prescription_required=True),
        PharmacyInventory(pharmacy_id=p3.id, medicine_name="Azithromycin 500mg", brand_name="Azithral 500", generic_name="Azithromycin", category="Tablets", dosage_form="500mg tablet", unit_price=118.00, in_stock=True, stock_quantity=28, unit="tablets", prescription_required=True),
        PharmacyInventory(pharmacy_id=p3.id, medicine_name="Iron Supplement", brand_name="Autrin Capsule", generic_name="Ferrous Fumarate", category="Tablets", dosage_form="Tablet", unit_price=85.00, in_stock=True, stock_quantity=45, unit="tablets", prescription_required=False),

        # City Medical Store (Dhebar Road)
        PharmacyInventory(pharmacy_id=p4.id, medicine_name="Metformin 500mg", brand_name="Obimet 500", generic_name="Metformin HCl", category="Tablets", dosage_form="500mg tablet", unit_price=40.00, in_stock=False, stock_quantity=0, unit="tablets", prescription_required=True),  # Out of stock
        PharmacyInventory(pharmacy_id=p4.id, medicine_name="Paracetamol 500mg", brand_name="Calpol 500", generic_name="Paracetamol", category="Tablets", dosage_form="500mg tablet", unit_price=22.00, in_stock=True, stock_quantity=180, unit="tablets", prescription_required=False),
        PharmacyInventory(pharmacy_id=p4.id, medicine_name="Cetirizine 10mg", brand_name="Okacet 10", generic_name="Cetirizine HCl", category="Tablets", dosage_form="10mg tablet", unit_price=35.00, in_stock=True, stock_quantity=60, unit="tablets", prescription_required=False),

        # Apollo Demo Pharmacy (150ft Ring Road)
        PharmacyInventory(pharmacy_id=p5.id, medicine_name="Metformin 500mg", brand_name="Glycomet 500", generic_name="Metformin HCl", category="Tablets", dosage_form="500mg tablet", unit_price=45.00, in_stock=True, stock_quantity=150, unit="tablets", prescription_required=True),
        PharmacyInventory(pharmacy_id=p5.id, medicine_name="Amoxicillin 500mg", brand_name="Mox 500", generic_name="Amoxicillin", category="Capsules", dosage_form="500mg capsule", unit_price=80.00, in_stock=True, stock_quantity=75, unit="capsules", prescription_required=True),
        PharmacyInventory(pharmacy_id=p5.id, medicine_name="Amlodipine 5mg", brand_name="Amlopres 5", generic_name="Amlodipine Besylate", category="Tablets", dosage_form="5mg tablet", unit_price=37.00, in_stock=True, stock_quantity=95, unit="tablets", prescription_required=True),
        PharmacyInventory(pharmacy_id=p5.id, medicine_name="Vitamin D3 1000 IU", brand_name="D-Rise 1000", generic_name="Cholecalciferol", category="Capsules", dosage_form="1000 IU capsule", unit_price=105.00, in_stock=True, stock_quantity=80, unit="capsules", prescription_required=False),
        PharmacyInventory(pharmacy_id=p5.id, medicine_name="Azithromycin 500mg", brand_name="Azee 500", generic_name="Azithromycin", category="Tablets", dosage_form="500mg tablet", unit_price=125.00, in_stock=True, stock_quantity=40, unit="tablets", prescription_required=True),

        # Wellness Pharmacy (University Road)
        PharmacyInventory(pharmacy_id=p6.id, medicine_name="Vitamin D3 1000 IU", brand_name="Calcirol D3", generic_name="Cholecalciferol", category="Capsules", dosage_form="1000 IU capsule", unit_price=92.00, in_stock=True, stock_quantity=30, unit="capsules", prescription_required=False),
        PharmacyInventory(pharmacy_id=p6.id, medicine_name="Calcium 500mg", brand_name="Shelcal 500", generic_name="Calcium", category="Tablets", dosage_form="500mg tablet", unit_price=105.00, in_stock=True, stock_quantity=60, unit="tablets", prescription_required=False),
        PharmacyInventory(pharmacy_id=p6.id, medicine_name="Cetirizine 10mg", brand_name="Cetzine 10", generic_name="Cetirizine", category="Tablets", dosage_form="10mg tablet", unit_price=36.00, in_stock=True, stock_quantity=50, unit="tablets", prescription_required=False),

        # FamilyCare Medicals (Tagore Road)
        PharmacyInventory(pharmacy_id=p7.id, medicine_name="Amoxicillin 500mg", brand_name="Novamox 500", generic_name="Amoxicillin", category="Capsules", dosage_form="500mg capsule", unit_price=79.00, in_stock=True, stock_quantity=40, unit="capsules", prescription_required=True),
        PharmacyInventory(pharmacy_id=p7.id, medicine_name="Amlodipine 5mg", brand_name="Amlong 5", generic_name="Amlodipine", category="Tablets", dosage_form="5mg tablet", unit_price=34.00, in_stock=True, stock_quantity=45, unit="tablets", prescription_required=True),
        PharmacyInventory(pharmacy_id=p7.id, medicine_name="Omeprazole 20mg", brand_name="Ocid 20", generic_name="Omeprazole", category="Capsules", dosage_form="20mg capsule", unit_price=60.00, in_stock=True, stock_quantity=70, unit="capsules", prescription_required=False),

        # LifeLine Pharmacy (Kuvadva Road)
        PharmacyInventory(pharmacy_id=p8.id, medicine_name="Paracetamol 500mg", brand_name="Pacimol 500", generic_name="Paracetamol", category="Tablets", dosage_form="500mg tablet", unit_price=20.00, in_stock=True, stock_quantity=100, unit="tablets", prescription_required=False),
        PharmacyInventory(pharmacy_id=p8.id, medicine_name="Iron Supplement", brand_name="Dexorange", generic_name="Iron + Folic Acid", category="Tablets", dosage_form="Tablet", unit_price=88.00, in_stock=True, stock_quantity=30, unit="tablets", prescription_required=False)
    ]
    db.session.add_all(sample_inventory)
    db.session.commit()

    # 9. ADD NOTIFICATIONS
    notifications = [
        Notification(
            user_id=demo_user.id,
            title="Refill Alert: Critical Low Stock",
            message="Amoxicillin 500mg for Emma Johnson has only 4 capsules left (~2 days). Find nearby pharmacies in Rajkot now.",
            type="refill",
            link="/refill-alerts"
        ),
        Notification(
            user_id=demo_user.id,
            title="Refill Alert: Critical Low Stock",
            message="Amlodipine 5mg for David Johnson has only 1 tablet remaining (~1 day).",
            type="refill",
            link="/refill-alerts"
        ),
        Notification(
            user_id=demo_user.id,
            title="Refill Alert: Refill Soon",
            message="Metformin 500mg for David Johnson has 6 tablets remaining (~3 days).",
            type="refill",
            link="/refill-alerts"
        ),
        Notification(
            user_id=demo_user.id,
            title="Upcoming Afternoon Dose Reminder",
            message="Scheduled afternoon doses at 2:00 PM: Emma (Cetirizine 10mg, Iron Supplement), Sarah (Calcium 500mg).",
            type="reminder",
            link="/reminders"
        ),
        Notification(
            user_id=demo_user.id,
            title="Welcome to MediCare Hub Demo",
            message="Sample family health ecosystem initialized with 4 profiles, 10 active prescriptions, and 8 Rajkot pharmacies.",
            type="system",
            link="/dashboard"
        )
    ]
    db.session.add_all(notifications)
    db.session.commit()

    print("MediCare Hub database successfully seeded with complete Rajkot demo scenario!")

if __name__ == '__main__':
    from flask import Flask
    from config import Config
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        seed_database(force_reset=True)
