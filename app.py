from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from functools import wraps
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from models import db, User, Driver, Bus, Route, Stop, Timing, Holiday
import os

try:
    import email_config as ecfg
    _mail_configured = (ecfg.MAIL_USERNAME != 'your_email@gmail.com')
except ImportError:
    _mail_configured = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'busmanag_secret_2024_xk9z'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///busmanag.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail config (loaded from email_config.py)
if _mail_configured:
    app.config['MAIL_SERVER']   = ecfg.MAIL_SERVER
    app.config['MAIL_PORT']     = ecfg.MAIL_PORT
    app.config['MAIL_USE_TLS']  = ecfg.MAIL_USE_TLS
    app.config['MAIL_USERNAME'] = ecfg.MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = ecfg.MAIL_PASSWORD
    app.config['MAIL_DEFAULT_SENDER'] = ecfg.MAIL_SENDER

mail = Mail(app)
ts   = URLSafeTimedSerializer(app.config['SECRET_KEY'])

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────── AUTH ROUTES ────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        data = request.get_json() or request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            return jsonify({'success': True, 'role': user.role}), 200
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
    return render_template('login.html')


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or request.form
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    reg_no = data.get('reg_no', '').strip()
    if not all([name, email, password]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 409
    user = User(name=name, email=email, role='student', reg_no=reg_no)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({'success': True, 'role': 'student'}), 201


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ─────────────────────────── FORGOT / RESET PASSWORD ────────────────────────────

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        data  = request.get_json() or request.form
        email = data.get('email', '').strip().lower()
        user  = User.query.filter_by(email=email).first()
        # Always return success to prevent user enumeration
        if user and _mail_configured:
            token     = ts.dumps(email, salt='password-reset')
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message(
                subject='Reset Your College Bus Management Password',
                recipients=[email]
            )
            msg.html = f"""
            <div style="font-family:Inter,sans-serif;max-width:480px;margin:auto;background:#111827;color:#f1f5f9;padding:32px;border-radius:16px;">
                <h2 style="color:#818cf8;margin-top:0;">Password Reset</h2>
                <p>Hello <strong>{user.name}</strong>,</p>
                <p>We received a request to reset your password for the <strong>College Bus Management</strong> portal.</p>
                <a href="{reset_url}" style="display:inline-block;margin:20px 0;padding:12px 28px;background:linear-gradient(135deg,#6366f1,#06b6d4);color:#fff;border-radius:8px;text-decoration:none;font-weight:700;">Reset Password</a>
                <p style="font-size:12px;color:#6b7280;">This link expires in <strong>30 minutes</strong>. If you didn't request this, ignore this email.</p>
                <p style="font-size:12px;color:#6b7280;">Or copy this link: {reset_url}</p>
            </div>"""
            try:
                mail.send(msg)
            except Exception as e:
                return jsonify({'success': False, 'message': f'Email error: {str(e)}'}), 500
        return jsonify({'success': True, 'message': 'If that email exists, a reset link has been sent.'})
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    try:
        email = ts.loads(token, salt='password-reset', max_age=1800)  # 30 min
    except (SignatureExpired, BadSignature):
        return render_template('reset_password.html', error='This reset link has expired or is invalid.', token=None)

    if request.method == 'POST':
        data     = request.get_json() or request.form
        password = data.get('password', '')
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters.'}), 400
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found.'}), 404
        user.set_password(password)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password updated! You can now sign in.'})
    return render_template('reset_password.html', token=token, error=None)


# ─────────────────────────── STUDENT PAGES ────────────────────────────

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    return render_template('student/dashboard.html')


@app.route('/student/buses')
@login_required
def student_buses():
    return render_template('student/buses.html')


@app.route('/student/route/<int:bus_id>')
@login_required
def student_route(bus_id):
    bus = Bus.query.get_or_404(bus_id)
    return render_template('student/route.html', bus=bus)


@app.route('/student/timings')
@login_required
def student_timings():
    return render_template('student/timings.html')


# ─────────────────────────── ADMIN PAGES ────────────────────────────

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    return render_template('admin/dashboard.html')


@app.route('/admin/buses')
@login_required
def admin_buses():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    return render_template('admin/buses.html')


@app.route('/admin/routes')
@login_required
def admin_routes():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    return render_template('admin/routes.html')


@app.route('/admin/stops')
@login_required
def admin_stops():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    return render_template('admin/stops.html')


@app.route('/admin/timings')
@login_required
def admin_timings():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    return render_template('admin/timings.html')


@app.route('/admin/drivers')
@login_required
def admin_drivers():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    return render_template('admin/drivers.html')


@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    return render_template('admin/users.html')


@app.route('/admin/holidays')
@login_required
def admin_holidays():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    return render_template('admin/holidays.html')


@app.route('/admin/route-stops')
@login_required
def admin_route_stops():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))
    return render_template('admin/stops.html')


# ─────────────────────────── API : CURRENT USER ────────────────────────────

@app.route('/api/me')
@login_required
def api_me():
    return jsonify(current_user.to_dict())


# ─────────────────────────── API : BUSES ────────────────────────────

@app.route('/api/buses', methods=['GET'])
@login_required
def api_buses():
    buses = Bus.query.all()
    return jsonify([b.to_dict() for b in buses])


@app.route('/api/buses', methods=['POST'])
@login_required
@admin_required
def api_buses_create():
    data = request.get_json()
    b = Bus(bus_no=data['bus_no'], capacity=int(data.get('capacity', 40)),
            status=data.get('status', 'active'),
            driver_id=data.get('driver_id') or None)
    db.session.add(b)
    db.session.commit()
    return jsonify(b.to_dict()), 201


@app.route('/api/buses/<int:bid>', methods=['PUT'])
@login_required
@admin_required
def api_buses_update(bid):
    b = Bus.query.get_or_404(bid)
    data = request.get_json()
    b.bus_no = data.get('bus_no', b.bus_no)
    b.capacity = int(data.get('capacity', b.capacity))
    b.status = data.get('status', b.status)
    b.driver_id = data.get('driver_id') or None
    db.session.commit()
    return jsonify(b.to_dict())


@app.route('/api/buses/<int:bid>', methods=['DELETE'])
@login_required
@admin_required
def api_buses_delete(bid):
    b = Bus.query.get_or_404(bid)
    db.session.delete(b)
    db.session.commit()
    return jsonify({'success': True})


# ─────────────────────────── API : ROUTES ────────────────────────────

@app.route('/api/routes', methods=['GET'])
@login_required
def api_routes():
    routes = Route.query.all()
    return jsonify([r.to_dict() for r in routes])


@app.route('/api/routes/<int:rid>', methods=['GET'])
@login_required
def api_route_detail(rid):
    r = Route.query.get_or_404(rid)
    d = r.to_dict()
    d['stops'] = [s.to_dict() for s in r.stops]
    return jsonify(d)


@app.route('/api/routes', methods=['POST'])
@login_required
@admin_required
def api_routes_create():
    data = request.get_json()
    r = Route(name=data['name'], bus_id=int(data['bus_id']),
              start_point=data['start_point'], end_point=data['end_point'],
              distance_km=float(data.get('distance_km', 0)))
    db.session.add(r)
    db.session.commit()
    return jsonify(r.to_dict()), 201


@app.route('/api/routes/<int:rid>', methods=['PUT'])
@login_required
@admin_required
def api_routes_update(rid):
    r = Route.query.get_or_404(rid)
    data = request.get_json()
    r.name = data.get('name', r.name)
    r.bus_id = int(data.get('bus_id', r.bus_id))
    r.start_point = data.get('start_point', r.start_point)
    r.end_point = data.get('end_point', r.end_point)
    r.distance_km = float(data.get('distance_km', r.distance_km))
    db.session.commit()
    return jsonify(r.to_dict())


@app.route('/api/routes/<int:rid>', methods=['DELETE'])
@login_required
@admin_required
def api_routes_delete(rid):
    r = Route.query.get_or_404(rid)
    db.session.delete(r)
    db.session.commit()
    return jsonify({'success': True})


# ─────────────────────────── API : STOPS ────────────────────────────

@app.route('/api/stops', methods=['GET'])
@login_required
def api_stops():
    route_id = request.args.get('route_id')
    q = Stop.query
    if route_id:
        q = q.filter_by(route_id=int(route_id))
    stops = q.order_by(Stop.sequence).all()
    return jsonify([s.to_dict() for s in stops])


@app.route('/api/stops', methods=['POST'])
@login_required
@admin_required
def api_stops_create():
    data = request.get_json()
    s = Stop(name=data['name'], route_id=int(data['route_id']),
             sequence=int(data.get('sequence', 1)),
             arrival_time=data.get('arrival_time'),
             departure_time=data.get('departure_time'),
             landmark=data.get('landmark', ''))
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201


@app.route('/api/stops/<int:sid>', methods=['PUT'])
@login_required
@admin_required
def api_stops_update(sid):
    s = Stop.query.get_or_404(sid)
    data = request.get_json()
    s.name = data.get('name', s.name)
    s.sequence = int(data.get('sequence', s.sequence))
    s.arrival_time = data.get('arrival_time', s.arrival_time)
    s.departure_time = data.get('departure_time', s.departure_time)
    s.landmark = data.get('landmark', s.landmark)
    db.session.commit()
    return jsonify(s.to_dict())


@app.route('/api/stops/<int:sid>', methods=['DELETE'])
@login_required
@admin_required
def api_stops_delete(sid):
    s = Stop.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'success': True})


# ─────────────────────────── API : TIMINGS ────────────────────────────

@app.route('/api/timings', methods=['GET'])
@login_required
def api_timings():
    bus_id = request.args.get('bus_id')
    q = Timing.query
    if bus_id:
        q = q.filter_by(bus_id=int(bus_id))
    timings = q.all()
    return jsonify([t.to_dict() for t in timings])


@app.route('/api/timings', methods=['POST'])
@login_required
@admin_required
def api_timings_create():
    data = request.get_json()
    t = Timing(bus_id=int(data['bus_id']), day_of_week=data['day_of_week'],
               departure_time=data['departure_time'], arrival_time=data['arrival_time'],
               notes=data.get('notes', ''))
    db.session.add(t)
    db.session.commit()
    return jsonify(t.to_dict()), 201


@app.route('/api/timings/<int:tid>', methods=['PUT'])
@login_required
@admin_required
def api_timings_update(tid):
    t = Timing.query.get_or_404(tid)
    data = request.get_json()
    t.bus_id = int(data.get('bus_id', t.bus_id))
    t.day_of_week = data.get('day_of_week', t.day_of_week)
    t.departure_time = data.get('departure_time', t.departure_time)
    t.arrival_time = data.get('arrival_time', t.arrival_time)
    t.notes = data.get('notes', t.notes)
    db.session.commit()
    return jsonify(t.to_dict())


@app.route('/api/timings/<int:tid>', methods=['DELETE'])
@login_required
@admin_required
def api_timings_delete(tid):
    t = Timing.query.get_or_404(tid)
    db.session.delete(t)
    db.session.commit()
    return jsonify({'success': True})


# ─────────────────────────── API : DRIVERS ────────────────────────────

@app.route('/api/drivers', methods=['GET'])
@login_required
def api_drivers():
    drivers = Driver.query.all()
    return jsonify([d.to_dict() for d in drivers])


@app.route('/api/drivers', methods=['POST'])
@login_required
@admin_required
def api_drivers_create():
    data = request.get_json()
    d = Driver(name=data['name'], license_no=data['license_no'],
               phone=data['phone'], experience_years=int(data.get('experience_years', 0)),
               status=data.get('status', 'active'))
    db.session.add(d)
    db.session.commit()
    return jsonify(d.to_dict()), 201


@app.route('/api/drivers/<int:did>', methods=['PUT'])
@login_required
@admin_required
def api_drivers_update(did):
    d = Driver.query.get_or_404(did)
    data = request.get_json()
    d.name = data.get('name', d.name)
    d.license_no = data.get('license_no', d.license_no)
    d.phone = data.get('phone', d.phone)
    d.experience_years = int(data.get('experience_years', d.experience_years))
    d.status = data.get('status', d.status)
    db.session.commit()
    return jsonify(d.to_dict())


@app.route('/api/drivers/<int:did>', methods=['DELETE'])
@login_required
@admin_required
def api_drivers_delete(did):
    d = Driver.query.get_or_404(did)
    db.session.delete(d)
    db.session.commit()
    return jsonify({'success': True})


# ─────────────────────────── API : USERS ────────────────────────────

@app.route('/api/users', methods=['GET'])
@login_required
@admin_required
def api_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@app.route('/api/users/<int:uid>/role', methods=['PUT'])
@login_required
@admin_required
def api_users_role(uid):
    u = User.query.get_or_404(uid)
    data = request.get_json()
    new_role = data.get('role')
    if new_role not in ('student', 'admin'):
        return jsonify({'error': 'Invalid role'}), 400
    u.role = new_role
    db.session.commit()
    return jsonify(u.to_dict())


@app.route('/api/users/<int:uid>', methods=['DELETE'])
@login_required
@admin_required
def api_users_delete(uid):
    if uid == current_user.id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    u = User.query.get_or_404(uid)
    db.session.delete(u)
    db.session.commit()
    return jsonify({'success': True})


# ─────────────────────────── API : STATS ────────────────────────────

@app.route('/api/stats')
@login_required
def api_stats():
    return jsonify({
        'buses': Bus.query.count(),
        'routes': Route.query.count(),
        'stops': Stop.query.count(),
        'drivers': Driver.query.count(),
        'students': User.query.filter_by(role='student').count(),
        'admins': User.query.filter_by(role='admin').count(),
        'active_buses': Bus.query.filter_by(status='active').count(),
        'active_drivers': Driver.query.filter_by(status='active').count(),
        'holidays': Holiday.query.count(),
    })


# ─────────────────────────── API : HOLIDAYS ────────────────────────────

@app.route('/api/holidays', methods=['GET'])
@login_required
def api_holidays():
    holidays = Holiday.query.order_by(Holiday.date).all()
    return jsonify([h.to_dict() for h in holidays])


@app.route('/api/holidays', methods=['POST'])
@login_required
@admin_required
def api_holidays_create():
    data = request.get_json()
    if not data.get('name') or not data.get('date'):
        return jsonify({'error': 'Name and date are required'}), 400
    h = Holiday(
        name=data['name'],
        date=data['date'],
        holiday_type=data.get('holiday_type', 'No Service'),
        description=data.get('description', '')
    )
    db.session.add(h)
    db.session.commit()
    return jsonify(h.to_dict()), 201


@app.route('/api/holidays/<int:hid>', methods=['PUT'])
@login_required
@admin_required
def api_holidays_update(hid):
    h = Holiday.query.get_or_404(hid)
    data = request.get_json()
    h.name = data.get('name', h.name)
    h.date = data.get('date', h.date)
    h.holiday_type = data.get('holiday_type', h.holiday_type)
    h.description = data.get('description', h.description)
    db.session.commit()
    return jsonify(h.to_dict())


@app.route('/api/holidays/<int:hid>', methods=['DELETE'])
@login_required
@admin_required
def api_holidays_delete(hid):
    h = Holiday.query.get_or_404(hid)
    db.session.delete(h)
    db.session.commit()
    return jsonify({'success': True})


# ─────────────────────────── API : ROUTES WITH STOPS ────────────────────────────

@app.route('/api/routes/with-stops', methods=['GET'])
@login_required
def api_routes_with_stops():
    routes = Route.query.all()
    result = []
    for r in routes:
        rd = r.to_dict()
        rd['stops'] = [s.to_dict() for s in sorted(r.stops, key=lambda x: x.sequence)]
        result.append(rd)
    return jsonify(result)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
