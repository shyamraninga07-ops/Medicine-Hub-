import unittest
from datetime import date, timedelta
from app import app
from models import db, User, FamilyMember, Prescription, DoseHistory, RefillAlert, RefillHistory, Pharmacy, PharmacyInventory
from seed_data import seed_database

class MediCareHubTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_01_login_and_auth(self):
        """Test login with seeded demo account demo@medicarehub.com / Demo@123."""
        response = self.client.post('/login', data={
            'email': 'demo@medicarehub.com',
            'password': 'Demo@123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hello, Sarah', response.data)

    def test_02_dashboard_widgets(self):
        """Test dashboard loads dynamic data."""
        with self.client.session_transaction() as sess:
            user = User.query.filter_by(email='demo@medicarehub.com').first()
            sess['user_id'] = user.id
            sess['user_name'] = user.name
            sess['user_role'] = user.role

        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Today's Medicine Schedule", response.data)
        self.assertIn(b'Active Prescriptions', response.data)
        self.assertIn(b'DEMO MODE', response.data)

    def test_03_automatic_stock_deduction_and_refill_alert(self):
        """Test dose marking decreases stock & triggers refill alert."""
        user = User.query.filter_by(email='demo@medicarehub.com').first()
        rx = Prescription.query.filter_by(user_id=user.id, medicine_name='Metformin 500mg').first()
        initial_stock = rx.available_stock

        test_date = '2026-12-01'
        # Clean any prior test run for this date
        DoseHistory.query.filter_by(prescription_id=rx.id, scheduled_date=test_date).delete()
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess['user_id'] = user.id

        # 1. Mark as taken
        res = self.client.post('/api/doses/record', json={
            'prescription_id': rx.id,
            'scheduled_time': 'Afternoon',
            'status': 'taken',
            'scheduled_date': test_date
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        
        # Verify stock decreased
        rx_updated = db.session.get(Prescription, rx.id)
        self.assertAlmostEqual(rx_updated.available_stock, initial_stock - rx.dosage_amount)

        # 2. Duplicate prevention test
        res_dup = self.client.post('/api/doses/record', json={
            'prescription_id': rx.id,
            'scheduled_time': 'Afternoon',
            'status': 'taken',
            'scheduled_date': test_date
        })
        self.assertEqual(res_dup.status_code, 200)
        rx_after_dup = db.session.get(Prescription, rx.id)
        # Stock should NOT decrease a second time!
        self.assertAlmostEqual(rx_after_dup.available_stock, rx_updated.available_stock)

        # 3. Mark as missed test
        initial_miss_stock = rx_after_dup.available_stock
        res_miss = self.client.post('/api/doses/record', json={
            'prescription_id': rx.id,
            'scheduled_time': 'Custom_Slot',
            'status': 'missed',
            'scheduled_date': test_date
        })
        self.assertEqual(res_miss.status_code, 200)
        rx_after_miss = db.session.get(Prescription, rx.id)
        # Missed dose must NOT reduce stock
        self.assertEqual(rx_after_miss.available_stock, initial_miss_stock)

    def test_04_refill_and_alert_resolution(self):
        """Test marking a medicine as refilled updates stock and resolves alert."""
        user = User.query.filter_by(email='demo@medicarehub.com').first()
        rx = Prescription.query.filter_by(user_id=user.id, medicine_name='Metformin 500mg').first()
        current_stock = rx.available_stock

        with self.client.session_transaction() as sess:
            sess['user_id'] = user.id

        # Record refill
        res = self.client.post('/refills/record', data={
            'prescription_id': rx.id,
            'added_quantity': 30.0,
            'pharmacy_name': 'HealthPlus Pharmacy (Demo), Rajkot',
            'cost': 14.50
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        rx_after_refill = db.session.get(Prescription, rx.id)
        self.assertAlmostEqual(rx_after_refill.available_stock, current_stock + 30.0)

        # Verify alert resolved
        alert = RefillAlert.query.filter_by(prescription_id=rx.id, status='active').first()
        self.assertIsNone(alert)

    def test_05_pharmacy_search_in_rajkot(self):
        """Test pharmacy search API with location in Rajkot and query."""
        with self.client.session_transaction() as sess:
            user = User.query.filter_by(email='demo@medicarehub.com').first()
            sess['user_id'] = user.id

        res = self.client.get('/api/pharmacies/search?user_lat=22.3039&user_lng=70.8022&query=Metformin')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('pharmacies', data)
        self.assertEqual(len(data['pharmacies']), 8)
        
        # Check first pharmacy has distance_km and searched_inventory
        first_p = data['pharmacies'][0]
        self.assertIn('distance_km', first_p)
        self.assertIn('searched_inventory', first_p)
        self.assertTrue(first_p['distance_km'] >= 0)
        self.assertIn('Rajkot', first_p['city'])

if __name__ == '__main__':
    unittest.main()
