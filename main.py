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
    scans = db.relationship('Scan', backref='user', lazy=True)
    
    def createFormat(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "badge_code": self.badge_code,
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
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify(user.createFormat())
    return jsonify({"error": "User not found"}), 404

@app.route("/users/<string:email>", methods=["PUT"])
def update_user(email):
    user = User.query.filter_by(email=email).first()
    if user:
        data = request.get_json()
        fields = ['name', 'phone', 'badge_code']
        
        for field in fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.updated_at = datetime.now()
        db.session.commit()
        
    return jsonify({"error": "User not found"}), 404



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