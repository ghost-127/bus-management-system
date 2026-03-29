import os
import sys

# Ensure imports work by pointing to current directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db, User, Bus, Route, Stop, Timing

def run_tests():
    with app.app_context():
        # Setup admin test user
        email = 'admin_verify_123@test.com'
        admin = User.query.filter_by(email=email).first()
        if not admin:
            admin = User(name='Admin Verify', email=email, role='admin')
            admin.set_password('adminpass')
            db.session.add(admin)
            db.session.commit()
            
        client = app.test_client()
        client.post('/login', json={'email': email, 'password': 'adminpass'})
        
        print("1. Creating a test bus...")
        res = client.post('/api/buses', json={'bus_no': 'TEST-99', 'bus_type': 'regular', 'capacity': 40})
        bus_id = res.get_json()['id']
        
        print("2. Creating route with start/end points...")
        res = client.post('/api/routes', json={
            'name': 'Test Route',
            'bus_id': bus_id,
            'start_point': 'Alpha',
            'end_point': 'Omega',
            'distance_km': 15.0
        })
        route_id = res.get_json()['id']
        
        # Verify stops created
        stops = Stop.query.filter_by(route_id=route_id).order_by(Stop.sequence).all()
        print(f"   Stops automatically created: {len(stops)}")
        assert len(stops) == 2, "Failed to create 2 stops"
        assert stops[0].name == 'Alpha'
        assert stops[1].name == 'Omega'
        
        print("3. Creating multiple day schedule with round trip...")
        res = client.post('/api/timings', json={
            'bus_id': bus_id,
            'days_of_week': ['Monday', 'Wednesday'],
            'departure_time': '08:00',
            'arrival_time': '09:00',
            'return_departure_time': '16:00',
            'return_arrival_time': '17:00',
            'notes': 'Test Trip'
        })
        
        # Verify timings created
        timings = Timing.query.filter_by(bus_id=bus_id).all()
        print(f"   Timings automatically generated: {len(timings)}")
        assert len(timings) == 4, "Failed to create 4 timings (2 days x 2 trips)"
        
        mon_trips = [t for t in timings if t.day_of_week == 'Monday']
        assert len(mon_trips) == 2
        assert any('Return' in t.notes for t in mon_trips)
        
        print("Cleaning up test data...")
        for t in timings: db.session.delete(t)
        for s in stops: db.session.delete(s)
        route = db.session.get(Route, route_id)
        db.session.delete(route)
        bus = db.session.get(Bus, bus_id)
        db.session.delete(bus)
        
        admin = User.query.filter_by(email=email).first()
        db.session.delete(admin)
        db.session.commit()
        
        print("SUCCESS: Route and Timing enhancements verified.")

if __name__ == '__main__':
    run_tests()
