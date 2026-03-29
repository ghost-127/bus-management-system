import os, sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import app, db, User, Timing

def test_edit():
    with app.app_context():
        email = 'admin_verify_123@test.com'
        admin = User.query.filter_by(email=email).first()
        if not admin:
            admin = User(name='Admin Verify', email=email, role='admin')
            admin.set_password('adminpass')
            db.session.add(admin)
            db.session.commit()

        client = app.test_client()
        client.post('/login', json={'email': email, 'password': 'adminpass'})
        
        t = Timing.query.first()
        if not t:
            print("No timings exist in db!")
            return
            
        print("Original values:", t.bus_id, t.day_of_week, t.departure_time, t.arrival_time, t.notes)
        orig_day = t.day_of_week
        orig_dep = t.departure_time
        orig_arr = t.arrival_time
        orig_notes = t.notes
        
        # test put
        res = client.put(f'/api/timings/{t.id}', json={
            'bus_id': t.bus_id,
            'day_of_week': 'Sunday',
            'departure_time': '23:59',
            'arrival_time': '00:01',
            'notes': 'Edited via test script'
        })
        print("PUT Status CODE:", res.status_code)
        
        t_after = db.session.get(Timing, t.id)
        print("After update DB:", t_after.bus_id, t_after.day_of_week, t_after.departure_time, t_after.arrival_time, t_after.notes)
        
        # revert
        res_rev = client.put(f'/api/timings/{t.id}', json={
            'bus_id': t.bus_id,
            'day_of_week': orig_day,
            'departure_time': orig_dep,
            'arrival_time': orig_arr,
            'notes': orig_notes
        })
        print("Revert Status:", res_rev.status_code)

if __name__ == '__main__':
    test_edit()
