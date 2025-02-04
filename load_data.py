from main import app, db, User, Scan
from datetime import datetime
import json

def load_data():
    with app.app_context():
        db.session.query(Scan).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        with open('example_data.json') as f:
            data = json.load(f)
        
        for user in data:
            new_user = User(
                name = user['name'],
                email = user['email'],
                phone = user['phone'],
                badge_code = user['badge_code'],
                updated_at = datetime.now()
            )
            db.session.add(new_user)
            
            for scan in user['scans']:
                new_scan = Scan(
                    activity_name = scan['activity_name'],
                    activity_category = scan['activity_category'],
                    scanned_at = datetime.fromisoformat(scan['scanned_at']),
                    user = new_user
                )
                db.session.add(new_scan)
        
        db.session.commit()
        print("data loaded !!!")

if __name__ == "__main__":
    load_data()