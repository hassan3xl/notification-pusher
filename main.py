from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room
import redis, os, functools

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

# Redis as the message queue lets multiple socketio worker
# processes stay in sync (required once you scale past 1 process)
socketio = SocketIO(app, message_queue=os.environ['REDIS_URL'], cors_allowed_origins="*")
r = redis.from_url(os.environ['REDIS_URL'])

API_KEYS = set(os.environ['VALID_API_KEYS'].split(','))  # or look up in a DB table

def require_api_key(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key not in API_KEYS:
            return jsonify({'error': 'invalid api key'}), 401
        return f(*args, **kwargs)
    return wrapper

# --- Ingest: other apps call this ---
@app.route('/notify', methods=['POST'])
@require_api_key
def notify():
    data = request.get_json()
    channel = data['channel']    # e.g. a user_id or app name
    payload = data['message']    # arbitrary JSON payload

    socketio.emit('notification', payload, room=channel)
    return jsonify({'status': 'sent'}), 200

# --- Delivery: clients connect and subscribe to a channel ---
@socketio.on('subscribe')
def on_subscribe(data):
    channel = data['channel']
    token = data.get('token')  # validate this against a per-user token, not the API key
    # verify token belongs to `channel` before joining
    join_room(channel)

if __name__ == '__main__':
    socketio.run(app)