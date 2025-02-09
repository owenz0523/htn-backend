# Hack the North 2025 Backend Challenge - @owenz0523

## Overview
REST API to manage hackathon attendee data and their activity participation through badge scans. 

## Setup Instructions

### Installation
1. Clone repository 
```bash
git clone [<>](https://github.com/owenz0523/htn-backend.git)
cd htn-backend
```
2. Install requirements
```bash
pip install -r requirements.txt
```
3. Create + load database
```bash
python main.py
python load_data.py
```

### Running Tests
```bash
python -m unittest testing.py -v
```

## API Documentation

### GET /users
Retrives all users and their scan histories.

Response:
```json
[
  {
    "id": "int",
    "name": "string",
    "email": "string",
    "phone": "string",
    "badge_code": "string",
    "updated_at": "ISO-8601 timestamp",
    "scans": [
      {
        "activity_name": "string",
        "activity_category": "string",
        "scanned_at": "ISO-8601 timestamp"
      }
    ]
  }
]
```

### GET /users/<email>
Retrieves a specific user's data.

Response: Same format as GET /users above

### PUT /users/<email>
Updates a user's information.

Request Body:
```json
{
  "name": "string (optional)",
  "phone": "string (optional)",
  "badge_code": "string (optional)"
}
```

Response: Updated user object, same format as above

### PUT /scan/<badge_code>
Records a new activity scan for a user.

Request Body:
```json
{
  "activity_name": "string",
  "activity_category": "string"
}
```

Response:
```json
{
  "scan_id": "integer",
  "activity_name": "string",
  "activity_category": "string",
  "scanned_at": "ISO-8601 timestamp",
  "user": {
    "name": "string",
    "email": "string",
    "phone": "string",
    "badge_code": "string",
    "updated_at": "ISO-8601 timestamp"
  }
}
```

### GET /scans
Retrieved aggregated data on scans with optional filters.

Query Parameters:
- min_frequency (int) : the minimum number of scans (inclusive)
- max_frequency (int) : the maximum number of scans (inclusive)
- activity_category (string) : the activity category to filter by

Response:
```json
{
    "scans": [
        {
            "activity_name": "string",
            "activity_category": "string",
            "frequency": "integer"
        }
    ],
    "total_activities": "integer"
}
```

## Design Decisions

### Database Schema + Endpoints
- Two database tables - one for users and one for scans
- Columns were created by referencing the JSON file
- Added IDs to keep track of rows
- Used emails as identification for users
- Used badge codes as identification for scans
- All scans must be associated with a user
- Followed instructions to make endpoints in order to keep it straightforward
- Used basic tools (Flask + SQLite) to keep it simple (no need to worry about scaling)


### Assumptions
- Badge codes are constant for any user
- Activity names and categories are case sensitive
- Users can scan multiple times for any activity
- Emails are normal (no strange characters)
- Phone numbers might be weird (made it a string)