# Update 1
from flask import Flask, jsonify, request
import os

from flask_cors import CORS
import db
from dotenv import load_dotenv

load_dotenv()

db_conn = db.get_db_connection(os.getenv('DB_NAME'), os.getenv('DB_USERNAME'), os.getenv('DB_PASSWORD'), os.getenv('DB_HOST'), os.getenv('DB_PORT'))

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:4000"]}})

@app.route('/login', methods=['POST'])
def login_user_account():
    if db_conn is None:
        return jsonify({'status':'fail', 'message': 'Database connection failed'}), 500
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'status':'fail', 'message': 'username and password are required'}), 400
        
        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT password, failed_attempts FROM user_account WHERE LOWER(username) = LOWER(%s)",
            (username,)
        )
        result = cursor.fetchone()
        
        if result is None:
            cursor.close()
            return jsonify({'status':'fail', 'message': 'Invalid username or password'}), 401
        
        stored_password, failed_attempts = result
        
        if password == stored_password:
            cursor.execute(
                "UPDATE user_account SET failed_attempts = 0 WHERE LOWER(username) = LOWER(%s)",
                (username,)
            )
            db_conn.commit()
            cursor.close()
            return jsonify({'status':'success', 'message': 'Login successful'}), 200
        else:
            failed_attempts += 1
            cursor.execute(
                "UPDATE user_account SET failed_attempts = %s WHERE LOWER(username) = LOWER(%s)",
                (failed_attempts, username)
            )
            db_conn.commit()
            cursor.close()
            return jsonify({'status':'fail', 'message': 'Invalid username or password'}), 401
    except Exception as e:
        print(f"{str(e)}")
        db_conn.rollback()
        return jsonify({'status':'fail', 'message': str(e)}), 500

@app.route('/user-account/reset-password', methods=['PUT'])
def reset_user_account_password():
    if db_conn is None:
        return jsonify({'status':'fail', 'message': 'Database connection failed'}), 500
    
    try:
        data = request.get_json()
        username = data.get('username')
        new_password = data.get('new_password')
        
        if not username or not new_password:
            return jsonify({'status':'fail', 'message': 'username and new_password are required'}), 400
        
        cursor = db_conn.cursor()
        cursor.execute(
            "UPDATE user_account SET password = %s, failed_attempts = 0 WHERE LOWER(username) = LOWER(%s)",
            (new_password, username)
        )
        db_conn.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            return jsonify({'status':'fail', 'message': 'User not found'}), 404
        
        cursor.close()
        return jsonify({'status':'success', 'message': 'Password reset successfully. Failed attempts set to 0.'}), 200
    except Exception as e:
        print(f"{str(e)}")
        db_conn.rollback()
        return jsonify({'status':'fail', 'message': str(e)}), 500

# @app.route('/user-account/unlock', methods=['PUT'])
# def unlock_user_account():
#     if db_conn is None:
#         return jsonify({'error': 'Database connection failed'}), 500
    
#     try:
#         data = request.get_json()
#         username = data.get('username')
        
#         if not username:
#             return jsonify({'error': 'username is required'}), 400
        
#         cursor = db_conn.cursor()
#         cursor.execute(
#             "UPDATE user_account SET failed_attempts = 0 WHERE LOWER(username) = LOWER(%s)",
#             (username,)
#         )
#         db_conn.commit()
        
#         if cursor.rowcount == 0:
#             cursor.close()
#             return jsonify({'error': 'User not found'}), 404
        
#         cursor.close()
#         return jsonify({'message': 'User account unlocked. Failed attempts reset to 0.'}), 200
#     except Exception as e:
#         db_conn.rollback()
#         return jsonify({'error': str(e)}), 500

@app.route('/system/health', methods=['GET'])
def check_system_health():
    if db_conn is None:
        return jsonify({'status':'fail', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT FLOOR(EXTRACT(EPOCH FROM (NOW() - MAX(date_created)))/60)::INTEGER FROM facility_booking"
        )
        result = cursor.fetchone()
        cursor.close()
        
        minutes_since_last_booking = result[0] if result and result[0] is not None else None
        
        print(f"**** Minutes since last booking: {minutes_since_last_booking}")
        
        return jsonify({
            'status': 'success',
            'minutes_since_last_booking': minutes_since_last_booking
        }), 200

    except Exception as e:
        print(f"{str(e)}")
        return jsonify({'status':'fail', 'message': str(e)}), 500

@app.route('/booking', methods=['GET'])
def get_booking():
    if db_conn is None:
        return jsonify({'status':'fail', 'message': 'Database connection failed'}), 500
    
    try:
        username = request.args.get('username')
        
        if not username:
            return jsonify({'status':'fail', 'message': 'username parameter is required'}), 400
        
        cursor = db_conn.cursor()
        cursor.execute(
            """
            SELECT id, facility_type, from_date, to_date, username, date_created, date_updated
            FROM facility_booking
            WHERE LOWER(username) = LOWER(%s)
            ORDER BY date_created DESC
            """,
            (username,)
        )
        results = cursor.fetchall()
        cursor.close()
        
        bookings = []
        for row in results:
            bookings.append({
                'id': row[0],
                'facility_type': row[1],
                'from_date': row[2].isoformat() if row[2] else None,
                'to_date': row[3].isoformat() if row[3] else None,
                'username': row[4],
                'date_created': row[5].isoformat() if row[5] else None,
                'date_updated': row[6].isoformat() if row[6] else None
            })
        
        return jsonify({
            'status': 'success',
            'bookings': bookings
        }), 200

    except Exception as e:
        print(f"{str(e)}")
        return jsonify({'status':'fail', 'message': str(e)}), 500

@app.route('/booking', methods=['POST'])
def create_booking():
    if db_conn is None:
        return jsonify({'status':'fail', 'message': 'Database connection failed'}), 500
    
    try:
        data = request.get_json()
        facility_type = data.get('facility_type')
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        username = data.get('username')
        
        if not facility_type or not from_date or not to_date or not username:
            return jsonify({'status':'fail', 'message': 'facility_type, from_date, to_date, and username are required'}), 400
        
        cursor = db_conn.cursor()
        cursor.execute(
            """
            INSERT INTO facility_booking (facility_type, from_date, to_date, username, date_created)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id
            """,
            (facility_type, from_date, to_date, username)
        )
        booking_id = cursor.fetchone()[0]
        db_conn.commit()
        cursor.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Booking created successfully',
            'booking_id': booking_id
        }), 201

    except Exception as e:
        print(f"{str(e)}")
        db_conn.rollback()
        return jsonify({'status':'fail', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 9000)))
