import unittest
import json
import os
from main import app, db, User, Scan
from datetime import datetime

class TestAPI(unittest.TestCase):
    def setUp(self):
        """
        Set up test client and test database
        """
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['Testing'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db', 'test.db')
        
        with app.app_context():
            db.create_all()
            
            test_user = User(
                name = "Test User",
                email = "test@example.com",
                phone = "555-555-5555",
                badge_code = "test-badge",
                updated_at = datetime.now()
            )
            db.session.add(test_user)
            
            test_scan = Scan(
                activity_name = "Test Activity",
                activity_category = "Test Category",
                scanned_at = datetime.now(),
                user = test_user
            )
            db.session.add(test_scan)
            
            db.session.commit()
            
    def tearDown(self):
        """
        Clean up test database
        """
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_get_users(self):
        """
        Test /users endpoint
        """
        with app.test_client() as client:
            response = client.get('/users')
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['name'], 'Test User')
            self.assertEqual(data[0]['email'], 'test@example.com')
    
    def test_get_user(self):
        """
        Test /users/<email> endpoint
        """
        with app.test_client() as client:
            response = client.get('/users/test@example.com')
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['name'], 'Test User')
            self.assertEqual(len(data['scans']), 1)
    
    def test_get_user_not_found(self):
        """
        Test /users/<email> endpoint with invalid email
        """
        with app.test_client() as client:
            response = client.get('/users/invalid@example/com')
            self.assertEqual(response.status_code, 404)
    
    def test_update_user(self):
        """
        Test /users/<email> endpoint with PUT method
        """
        with app.test_client() as client:
            updated_user = {
                'name': 'Updated User',
                'phone': '999-999-9999'
            }
            
            response = client.put('/users/test@example.com', json=updated_user)
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['name'], 'Updated User')
            self.assertEqual(data['phone'], '999-999-9999')
    
    def test_add_scan(self):
        """
        Test /scan/<badge_code> endpoint with PUT method
        """
        with app.test_client() as client:
            new_scan = {
                'activity_name': 'New Activity',
                'activity_category': 'New Category'
            }
            
            response = client.put('/scan/test-badge', json=new_scan)
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['activity_name'], 'New Activity')
            self.assertEqual(data['activity_category'], 'New Category')
    
    def test_get_scans(self):
        """
        Test /scans/<badge_code> endpoint
        """
        with app.test_client() as client:
            response = client.get('/scans')
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('scans', data)

    def test_get_scans_with_filters(self):
        """
        Test /scans/<badge_code> endpoint with filters
        """
        with app.app_context():
            test_user = User.query.first()
            for _ in range(5):
                new_scan = Scan(
                    activity_name = "Frequent_Activity",
                    activity_category = "Frequent_Category",
                    scanned_at = datetime.now(),
                    user = test_user
                )
                db.session.add(new_scan)
            db.session.commit()
        
        with app.test_client() as client:
            response = client.get('/scans?min_frequency=5')
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            for scan in data['scans']:
                self.assertTrue(scan['frequency'] >= 5)
            
            response = client.get('/scans?activity_category=Frequent_Category')
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            for scan in data['scans']:
                self.assertEqual(scan['activity_name'], 'Frequent_Activity')
        
    
if __name__ == "__main__":
    unittest.main()