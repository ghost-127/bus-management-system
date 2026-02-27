from app import app, db
from models import User, Driver, Bus, Route, Stop, Timing


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # --- Users ---
        admin = User(name='Admin User', email='admin@college.edu', role='admin', reg_no='ADM001')
        admin.set_password('admin123')

        students = []
        for i in range(1, 6):
            s = User(name=f'Student {i}', email=f'student{i}@college.edu',
                     role='student', reg_no=f'REG{2024+i:04d}')
            s.set_password('student123')
            students.append(s)

        db.session.add(admin)
        db.session.add_all(students)
        db.session.commit()

        # --- Drivers ---
        d1 = Driver(name='Rajan Kumar', license_no='KL01-2021-001', phone='9876543210',
                    experience_years=8, status='active')
        d2 = Driver(name='Suresh Nair', license_no='KL01-2019-042', phone='9876543211',
                    experience_years=12, status='active')
        d3 = Driver(name='Mohan Das', license_no='KL01-2022-088', phone='9876543212',
                    experience_years=5, status='active')
        db.session.add_all([d1, d2, d3])
        db.session.commit()

        # --- Buses ---
        b1 = Bus(bus_no='KL-01-BUS-101', capacity=45, status='active', driver_id=d1.id)
        b2 = Bus(bus_no='KL-01-BUS-102', capacity=40, status='active', driver_id=d2.id)
        b3 = Bus(bus_no='KL-01-BUS-103', capacity=50, status='active', driver_id=d3.id)
        db.session.add_all([b1, b2, b3])
        db.session.commit()

        # --- Routes ---
        r1 = Route(name='City Centre Route', bus_id=b1.id,
                   start_point='College Gate', end_point='City Centre', distance_km=12.5)
        r2 = Route(name='North Campus Route', bus_id=b2.id,
                   start_point='North Campus', end_point='Railway Station', distance_km=8.0)
        r3 = Route(name='South Extension Route', bus_id=b3.id,
                   start_point='College Gate', end_point='South Junction', distance_km=15.0)
        db.session.add_all([r1, r2, r3])
        db.session.commit()

        # --- Stops for Route 1 ---
        stops_r1 = [
            Stop(name='College Gate', route_id=r1.id, sequence=1, arrival_time='07:00', departure_time='07:05', landmark='Main Entrance'),
            Stop(name='Library Junction', route_id=r1.id, sequence=2, arrival_time='07:10', departure_time='07:12', landmark='Near Central Library'),
            Stop(name='Park View', route_id=r1.id, sequence=3, arrival_time='07:20', departure_time='07:22', landmark='City Park'),
            Stop(name='Market Square', route_id=r1.id, sequence=4, arrival_time='07:30', departure_time='07:32', landmark='Old Market'),
            Stop(name='City Centre', route_id=r1.id, sequence=5, arrival_time='07:45', departure_time=None, landmark='Final Stop'),
        ]
        # --- Stops for Route 2 ---
        stops_r2 = [
            Stop(name='North Campus', route_id=r2.id, sequence=1, arrival_time='08:00', departure_time='08:05', landmark='North Gate'),
            Stop(name='Hospital Cross', route_id=r2.id, sequence=2, arrival_time='08:15', departure_time='08:17', landmark='Govt Hospital'),
            Stop(name='Tech Park', route_id=r2.id, sequence=3, arrival_time='08:25', departure_time='08:27', landmark='IT Park'),
            Stop(name='Railway Station', route_id=r2.id, sequence=4, arrival_time='08:40', departure_time=None, landmark='Final Stop'),
        ]
        # --- Stops for Route 3 ---
        stops_r3 = [
            Stop(name='College Gate', route_id=r3.id, sequence=1, arrival_time='09:00', departure_time='09:05', landmark='Main Entrance'),
            Stop(name='Stadium Road', route_id=r3.id, sequence=2, arrival_time='09:15', departure_time='09:17', landmark='Sports Complex'),
            Stop(name='Lotus Nagar', route_id=r3.id, sequence=3, arrival_time='09:25', departure_time='09:27', landmark='Lotus Nagar Gate'),
            Stop(name='South Mall', route_id=r3.id, sequence=4, arrival_time='09:35', departure_time='09:37', landmark='Shopping Mall'),
            Stop(name='South Junction', route_id=r3.id, sequence=5, arrival_time='09:50', departure_time=None, landmark='Final Stop'),
        ]
        db.session.add_all(stops_r1 + stops_r2 + stops_r3)

        # --- Timings ---
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        timings = []
        for day in days:
            timings.append(Timing(bus_id=b1.id, day_of_week=day, departure_time='07:05', arrival_time='07:45'))
            timings.append(Timing(bus_id=b2.id, day_of_week=day, departure_time='08:05', arrival_time='08:40'))
            timings.append(Timing(bus_id=b3.id, day_of_week=day, departure_time='09:05', arrival_time='09:50'))
        db.session.add_all(timings)
        db.session.commit()

        print("[OK] Database seeded successfully!")
        print("   Admin:   admin@college.edu / admin123")
        print("   Student: student1@college.edu / student123")


if __name__ == '__main__':
    seed()
