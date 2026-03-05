from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='student')  # 'student', 'admin', 'incharge'
    assigned_bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=True)  # for incharge only
    reg_no = db.Column(db.String(50), nullable=True)
    is_fee_paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'reg_no': self.reg_no,
            'assigned_bus_id': self.assigned_bus_id,
            'is_fee_paid': self.is_fee_paid,
            'created_at': self.created_at.strftime('%Y-%m-%d')
        }


class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    license_no = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    experience_years = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')  # active/inactive
    buses = db.relationship('Bus', backref='driver', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'license_no': self.license_no,
            'phone': self.phone,
            'experience_years': self.experience_years,
            'status': self.status,
            'bus_count': len(self.buses)
        }


class Bus(db.Model):
    __tablename__ = 'buses'
    id = db.Column(db.Integer, primary_key=True)
    bus_no = db.Column(db.String(50), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    bus_type = db.Column(db.String(20), default='regular')  # 'regular' or 'event'
    status = db.Column(db.String(20), default='active')
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True)
    routes = db.relationship('Route', backref='bus', lazy=True)
    timings = db.relationship('Timing', backref='bus', lazy=True)

    def to_dict(self):
        driver_name = self.driver.name if self.driver else 'Unassigned'
        route_name = self.routes[0].name if self.routes else 'No Route'
        return {
            'id': self.id,
            'bus_no': self.bus_no,
            'capacity': self.capacity,
            'bus_type': self.bus_type,
            'status': self.status,
            'driver_id': self.driver_id,
            'driver_name': self.driver.name if self.driver else 'Unassigned',
            'route_name': route_name
        }


class Route(db.Model):
    __tablename__ = 'routes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False)
    start_point = db.Column(db.String(100), nullable=False)
    end_point = db.Column(db.String(100), nullable=False)
    distance_km = db.Column(db.Float, default=0)
    stops = db.relationship('Stop', backref='route', lazy=True,
                            order_by='Stop.sequence', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'bus_id': self.bus_id,
            'bus_no': self.bus.bus_no if self.bus else '',
            'start_point': self.start_point,
            'end_point': self.end_point,
            'distance_km': self.distance_km,
            'stop_count': len(self.stops)
        }


class Stop(db.Model):
    __tablename__ = 'stops'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    sequence = db.Column(db.Integer, nullable=False)
    arrival_time = db.Column(db.String(10), nullable=True)
    departure_time = db.Column(db.String(10), nullable=True)
    landmark = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'route_id': self.route_id,
            'sequence': self.sequence,
            'arrival_time': self.arrival_time,
            'departure_time': self.departure_time,
            'landmark': self.landmark
        }


class Timing(db.Model):
    __tablename__ = 'timings'
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)  # Monday, Tuesday, etc.
    departure_time = db.Column(db.String(10), nullable=False)
    arrival_time = db.Column(db.String(10), nullable=False)
    notes = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'bus_id': self.bus_id,
            'bus_no': self.bus.bus_no if self.bus else '',
            'day_of_week': self.day_of_week,
            'departure_time': self.departure_time,
            'arrival_time': self.arrival_time,
            'notes': self.notes
        }


class Holiday(db.Model):
    __tablename__ = 'holidays'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(10), nullable=False)       # YYYY-MM-DD
    holiday_type = db.Column(db.String(30), default='No Service')  # No Service / Partial Service / Special
    description = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date,
            'holiday_type': self.holiday_type,
            'description': self.description or ''
        }



class ChangeRequest(db.Model):
    __tablename__ = 'change_requests'
    id           = db.Column(db.Integer, primary_key=True)
    incharge_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bus_id       = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False)
    request_type = db.Column(db.String(30), nullable=False)
    description  = db.Column(db.Text, nullable=False)
    status       = db.Column(db.String(20), default='pending')
    admin_notes  = db.Column(db.String(300), nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    incharge = db.relationship('User', foreign_keys=[incharge_id])
    bus      = db.relationship('Bus',  foreign_keys=[bus_id])

    def to_dict(self):
        return {
            'id':            self.id,
            'incharge_id':   self.incharge_id,
            'incharge_name': self.incharge.name if self.incharge else u'—',
            'bus_id':        self.bus_id,
            'bus_no':        self.bus.bus_no if self.bus else u'—',
            'request_type':  self.request_type,
            'description':   self.description,
            'status':        self.status,
            'admin_notes':   self.admin_notes or '',
            'created_at':    self.created_at.strftime('%Y-%m-%d %H:%M')
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    id            = db.Column(db.Integer, primary_key=True)
    title         = db.Column(db.String(150), nullable=False)
    message       = db.Column(db.Text, nullable=False)
    sender_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    sender     = db.relationship('User', foreign_keys=[sender_id])
    target_bus = db.relationship('Bus',  foreign_keys=[target_bus_id])

    def to_dict(self):
        return {
            'id':            self.id,
            'title':         self.title,
            'message':       self.message,
            'sender_id':     self.sender_id,
            'sender_name':   self.sender.name if self.sender else u'—',
            'sender_role':   self.sender.role if self.sender else u'—',
            'target_bus_id': self.target_bus_id,
            'target_bus_no': self.target_bus.bus_no if self.target_bus else 'All Students',
            'created_at':    self.created_at.strftime('%Y-%m-%d %H:%M')
        }
