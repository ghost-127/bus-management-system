from app import app, db
from models import Bus, Timing

with app.app_context():
    bus = Bus(bus_no='TEST-EVENT-1', capacity=40, bus_type='event', status='active')
    db.session.add(bus)
    db.session.commit()
    print(f'Created Event Bus: ID {bus.id}')
    
    try:
        t = Timing(bus_id=bus.id, day_of_week='Monday', departure_time='08:00', arrival_time='09:00')
        db.session.add(t)
        db.session.commit()
        print('Successfully added Timing!')
    except Exception as e:
        print('Error:', e)
