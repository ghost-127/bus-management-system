import time
from app import app, db
from models import User, Bus, Stop
from flask_login import login_user

with app.test_client() as c:
    with app.app_context():
        incharge = User.query.filter_by(role='incharge').first()
        bus = Bus.query.get(incharge.assigned_bus_id)
        route = bus.routes[0]
        stops = sorted(route.stops, key=lambda s: s.sequence)
        
        print(f"Setting bus to 'In Transit' at Stop 2: {stops[1].name}")
        
        # 1. Update to "In Transit" at Stop 2
        with c.session_transaction() as sess:
            sess['_user_id'] = str(incharge.id)
            sess['_fresh'] = True
            
        payload = {
            'current_status': 'In Transit',
            'current_stop_id': stops[1].id
        }
        res_put = c.put(f'/api/buses/{bus.id}/live-update', json=payload)
        print("Status update:", res_put.status_code)
        
        print("Done. Ready for visual inspection by user.")
