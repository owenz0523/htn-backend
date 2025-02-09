from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from sqlalchemy import func

os.makedirs('db', exist_ok=True)
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db', 'hackathon.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(20))
    badge_code = db.Column(db.String(100), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    scans = db.relationship('Scan', backref='user', lazy=True)
    
    def createFormat(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "badge_code": self.badge_code,
            "updated_at": self.updated_at.isoformat(),
            'scans': [scan.createFormat() for scan in self.scans]
        }
    
class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_name = db.Column(db.String(100), nullable=False)
    activity_category = db.Column(db.String(100), nullable=False)
    scanned_at = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def createFormat(self):
        return {
            "activity_name": self.activity_name,
            "activity_category": self.activity_category,
            "scanned at": self.scanned_at,
        }

@app.route("/test")
def test():
    return jsonify({"message": "Working"})

@app.route("/users", methods=["GET"])
def get_users():
    """
    Retrieve all users and their associated scan data
    
    Returns:
        JSON array of all users with their profile data + scan history
    """
    try:
        users = User.query.all()
        return jsonify([user.createFormat() for user in users])
    except Exception as e:
        return jsonify({
            "error": 'Failed to get users',
            "message": str(e)
        }), 500

@app.route("/users/<string:email>", methods=["GET"])
def get_user(email):
    """
    Retrieve a specific user by email
    
    Arguments:
        email (string) - the email of the user to retrieve
    
    Returns:
        JSON object of the user with their profile data + scan history
    """
    try:
        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify(user.createFormat())
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({
            "error": 'Failed to get user',
            "message": str(e)
        }), 500

@app.route("/users/<string:email>", methods=["PUT"])
def update_user(email):
    """
    Update a specific user by email.
    
    Arguments:
        email (string) - the email of the user to update
        
    Request Body:
        JSON object with the fields to update - (name, phone, badge_code)
    
    Returns:
        JSON object of the user with their updated profile data + scan history
    """
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        fields = ['name', 'phone', 'badge_code']
        for field in fields:
            if field in data:
                setattr(user, field, data[field])
            
        user.updated_at = datetime.now()
        db.session.commit()
            
        return jsonify(user.createFormat())
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": 'Failed to update user',
            "message": str(e)
        }), 500

@app.route("/scan/<string:badge_code>", methods=['PUT'])
def add_scan(badge_code):
    """
    Add a new scan for a user by badge_code
    
    Arguments:
        badge_code (string) - the badge code of the user to add a scan for
        
    Request Body:
        JSON object with the fields to add - (activity_name, activity_category)
    
    Returns:
        JSON object of the new scan data
    """
    try:
        user = User.query.filter_by(badge_code=badge_code).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        if not data or 'activity_name' not in data or 'activity_category' not in data:
            return jsonify({"error": "Missing required fields"}), 400
        
        new_scan = Scan(
            activity_name = data['activity_name'],
            activity_category = data['activity_category'],
            scanned_at = datetime.now(),
            user = user
        )
        
        user.updated_at = datetime.now()
        db.session.add(new_scan)
        db.session.commit()
        
        return jsonify({
            "scan_id": new_scan.id,
            "activity_name": new_scan.activity_name,
            "activity_category": new_scan.activity_category,
            "scanned_at": new_scan.scanned_at,
            "user": {
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "badge_code": user.badge_code,
                "updated_at": user.updated_at.isoformat()
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": 'Failed to add scan',
            "message": str(e)
        }), 500
        
@app.route("/scans", methods=["GET"])
def get_scans():
    """
    Retrieve aggregated scan data
    
    Query Parameters (optional):
        min_frequency (int) - the minimum number of scans (inclusive)
        max_frequency (int) - the maximum number of scans (inclusive)
        activity_category (string) - the activity category to filter by
    
    Returns:
        JSON object containing aggregated scan data
    """
    try:
        min_frequency = request.args.get('min_frequency', type=int)
        max_frequency = request.args.get('max_frequency', type=int)
        activity_category = request.args.get('activity_category', type=str)
        
        query = db.session.query(
            Scan.activity_name,
            Scan.activity_category,
            func.count(Scan.id).label('frequency')
        ).group_by(
            Scan.activity_name,
            Scan.activity_category
        )
        
        if activity_category:
            query = query.filter(Scan.activity_category == activity_category)
        
        results = query.all()
        
        scan_return = []
        for activity_name, activity_category, frequency in results:
            if min_frequency and frequency < min_frequency:
                continue
            if max_frequency and frequency > max_frequency:
                continue
            scan_return.append({
                "activity_name": activity_name,
                "activity_category": activity_category,
                "frequency": frequency
            })
        
        return jsonify({
            "scans": scan_return,
            "total_activities": len(scan_return)
        })
    
    except Exception as e:
        return jsonify({
            "error": 'Failed to get scan data',
            "message": str(e)
        }), 500
    

@app.errorhandler(404)
def notFoundError(error):
    return jsonify({"error": "Resource Not Found"}), 404

@app.errorhandler(400)
def badRequestError(error):
    return jsonify({"error": "Bad Request"}), 400

@app.errorhandler(500)
def internalServerError(error):
    return jsonify({"error": "Internal Server Error"}), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port = 3000)