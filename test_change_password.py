import os
import sys

# Ensure imports work by pointing to current directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db, User

def run_tests():
    with app.app_context():
        # Setup test user
        email = 'test_change_pwd_123@test.com'
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(name='Test User', email=email, role='student')
            user.set_password('oldpassword')
            db.session.add(user)
            db.session.commit()
        else:
            user.set_password('oldpassword')
            db.session.commit()
            
        client = app.test_client()
        
        print("1. Logging in...")
        resp = client.post('/login', json={'email': email, 'password': 'oldpassword'})
        print("Login:", resp.get_json())
        assert resp.get_json()['success'] == True
        
        print("2. Changing password...")
        resp = client.post('/change-password', json={
            'current_password': 'oldpassword', 
            'new_password': 'newpassword123'
        })
        print("Change Pwd:", resp.get_json())
        assert resp.get_json()['success'] == True
        
        print("3. Testing wrong current password...")
        resp = client.post('/change-password', json={
            'current_password': 'wrongpwd', 
            'new_password': 'newpassword123'
        })
        print("Wrong Pwd:", resp.get_json())
        assert resp.get_json()['success'] == False
        
        print("Cleaning up test user...")
        # Need to re-fetch to safely delete in session
        user = User.query.filter_by(email=email).first()
        db.session.delete(user)
        db.session.commit()
        print("SUCCESS: Tests passed.")

if __name__ == '__main__':
    run_tests()
