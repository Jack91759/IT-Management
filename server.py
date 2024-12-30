from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devices.db'
db = SQLAlchemy(app)
x64os = ''
anydesk_keys = {
    'DESKTOP-D6VFD7S': '1458603825',
    'DESKTOP-AHLN5N0': '1430342759'
}



class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cpu_usage = db.Column(db.Float, nullable=False)
    memory_usage = db.Column(db.Float, nullable=False)
    disk_usage = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    os = db.Column(db.String(50), nullable=True)
    anydesk = db.Column(db.String(50), nullable=True)


class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='pending')
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


def convert_utc_to_local(utc_time):
    local_tz = pytz.timezone('America/Detroit')  # Replace with your local time zone
    # Ensure UTC time is localized to UTC before converting
    utc_time = utc_time.replace(tzinfo=pytz.utc)  # Localize UTC time
    return utc_time.astimezone(local_tz)


def format_timestamp(local_time):
    print(f'Local Time: {local_time}')
    return local_time.strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return jsonify('Contact me at Hack37studios@outlook.com')

@app.route('/register', methods=['POST'])
def register_device():
    global x64os
    windowsdev = ['DESKTOP-D6VFD7S', 'DESKTOP-AHLN5N0']
    data = request.json
    anydesk_key = anydesk_keys.get(data['name'], '')
    if data['name'] in windowsdev:
        x64os = 'Windows'
    elif data['name'] == '':
        x64os = 'Raspbian'
    else:
        x64os = 'Unknown'
        print(data['name'])
    vary = ''
    device = Device(
        name=data['name'],
        cpu_usage=data['cpu_usage'],
        memory_usage=data['memory_usage'],
        disk_usage=data['disk_usage'],
        os=x64os,
        anydesk=anydesk_key
    )
    db.session.add(device)
    db.session.commit()
    return jsonify({'message': 'Device registered successfully'})


@app.route('/action', methods=['POST'])
def perform_action():
    data = request.json
    device_name = data['device_name']
    action = data['action']

    device = Device.query.filter_by(name=device_name).first()
    if device:
        new_action = Action(device_name=device_name, action=action)
        db.session.add(new_action)
        db.session.commit()
        return jsonify({'message': f'Action {action} queued for device {device_name}'})
    else:
        return jsonify({'message': 'Device not found'}), 404


@app.route('/get_action', methods=['GET'])
def get_action():
    device_name = request.args.get('device_name')
    action = Action.query.filter_by(device_name=device_name, status='pending').order_by(Action.timestamp.asc()).first()

    if action:
        action.status = 'in_progress'
        db.session.commit()
        return jsonify({'action': action.action, 'timestamp': action.timestamp})
    else:
        return jsonify({'message': 'No pending actions'})


@app.route('/devices', methods=['GET'])
def get_devices():
    # Subquery to find the latest timestamp for each device by name
    subquery = db.session.query(
        Device.name,
        db.func.max(Device.timestamp).label('max_timestamp')
    ).group_by(Device.name).subquery()

    # Join the Device table with the subquery to get the full details of the latest record for each device
    devices = db.session.query(
        Device.id,
        Device.name,
        Device.cpu_usage,
        Device.memory_usage,
        Device.disk_usage,
        Device.timestamp,
        Device.os,
        Device.anydesk
    ).join(
        subquery,
        (Device.name == subquery.c.name) & (Device.timestamp == subquery.c.max_timestamp)
    ).order_by(Device.id.desc()).all()

    # Convert timestamps from UTC to local time and format them
    devices_with_local_time = []
    for device in devices:
        device_with_local_time = device._asdict()  # Convert SQLAlchemy object to dictionary
        local_time = convert_utc_to_local(device.timestamp)  # Convert UTC timestamp
        device_with_local_time['timestamp'] = format_timestamp(local_time)  # Format timestamp
        devices_with_local_time.append(device_with_local_time)

    print(devices_with_local_time)  # Debugging: Check the updated devices list with formatted timestamps

    return render_template('devices.html', devices=devices_with_local_time)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001)
