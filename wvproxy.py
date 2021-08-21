#!/usr/bin/env python3

import base64
import sys
import time
import uuid
from collections import defaultdict

from flask import Flask, render_template, request
from flask_socketio import SocketIO
from pymp4.parser import Box


app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')
sessions = defaultdict(dict)


def log(message, *args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    kwargs.setdefault('flush', True)
    print(message, *args, **kwargs)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/wvproxy.js', methods=['GET'])
def wvproxy_js():
    return render_template('wvproxy.js')


@app.route('/api', methods=['POST'])
def api():
    req = request.get_json()

    method = req['method']

    authorized = False
    with open('authorized_users.txt') as fd:
        for line in fd.read().splitlines():
            name, token = line.split()
            if token == req['token']:
                log(f'[{name}] {req}')
                authorized = True
                break

    if not authorized:
        log(f'[anonymous] {req}')
        return {
            'status_code': 403,
            'message': 'Invalid token',
        }

    del req['token']

    if method == 'GetChallenge':
        session_id = str(uuid.uuid4())
        req['params']['session_id'] = session_id

        try:
            Box.parse(base64.b64decode(req['params']['init']))
        except OSError:
            req['params']['init'] = base64.b64encode(Box.build(dict(
                type=b'pssh',
                version=0,
                flags=0,
                system_ID=uuid.UUID('edef8ba9-79d6-4ace-a3c8-27dcd51d21ed'),
                init_data=base64.b64decode(req['params']['init']),
            ))).decode()

        socketio.emit('GetChallenge', req)

        start = time.time()
        log('Waiting for challenge', end='')
        while not sessions[session_id]:
            if time.time() - start > 15:
                return {
                    'status_code': 504,
                    'message': 'Request timed out',
                }
            log('.', end='')
            time.sleep(0.5)

        return {
            'status_code': 200,
            'message': {
                'session_id': session_id,
                'challenge': base64.b64encode(sessions[session_id]['challenge']).decode(),
            }
        }
    elif method == 'GetKeys':
        session_id = req['params']['session_id']
        if session_id not in sessions:
            return {
                'status_code': 400,
                'message': 'Invalid session ID',
            }

        socketio.emit('GetKeys', req)

        start = time.time()
        log('Waiting for keys', end='')
        while 'keys' not in sessions[session_id]:
            if time.time() - start > 15:
                return {
                    'status_code': 504,
                    'message': 'Request timed out',
                }
            log('.', end='')
            time.sleep(0.5)

        return {
            'status_code': 200,
            'message': {
                'keys': sessions[session_id]['keys'],
            },
        }
    elif method == 'GetKeysX':
        return {
            'status_code': 400,
            'message': 'Not implemented',
        }
    else:
        return {
            'status_code': 400,
            'message': 'Unknown method',
        }


@socketio.on('SetChallenge')
def on_set_challenge(res):
    log('\nGot challenge')
    log(base64.b64encode(res['challenge']))
    sessions[res['session_id']]['challenge'] = res['challenge']


@socketio.on('SetKeys')
def on_set_keys(res):
    log('\nGot keys')
    log(res['keys'])
    sessions[res['session_id']]['keys'] = res['keys']


if __name__ == '__main__':
    socketio.run(app)
