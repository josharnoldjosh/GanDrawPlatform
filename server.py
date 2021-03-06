from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room
import sys
from uuid import uuid4
from game_manager import GM
from server_config import config
from gevent.pywsgi import WSGIServer

# Our game manager
gm = GM(num_peeks=config["num_peeks"])

# Init the server
app = Flask(__name__)
app.config['SECRET_KEY'] = 'server'
socketio = SocketIO(app)

tellers = set()
drawers = set()
user_map = {}

@app.route('/')
def root():
    """ Send HTML from the server."""
    return "Hello, from the server for the GanDraw task."
    # return render_template('index.html')

@socketio.on('left_game')
def left_game(data):
    try:
        emit('game_over', {}, room=user_map[data['room']]['teller'])
        emit('game_over', {}, room=user_map[data['room']]['drawer'])
    except:
        pass

@socketio.on('get_num_peeks')
def get_num_peeks_left(data):
    game_id = data['room']
    num_peeks = gm.num_peeks_left(game_id)
    emit('send_num_peeks_to_client', {'num_peeks':num_peeks}, room=user_map[data['room']]['teller'])

@socketio.on('peek')
def peek(data):
    peek_image = gm.peek(data['room'])
    emit('send_peek_to_client', {'image':peek_image}, room=user_map[data['room']]['teller'])

@socketio.on('get_target_image_drawer')
def get_target_image(data):
    target_image = gm.get_target_image(data['room'])
    emit('send_target_image_to_client', {'image':target_image}, room=user_map[data['room']]['drawer'])

@socketio.on('get_target_image')
def get_target_image(data):    
    target_image = gm.get_target_image(data['room'])
    # print("Sending target image to client...")
    emit('send_target_image_to_client', {'image':target_image}, room=user_map[data['room']]['teller'])

@socketio.on('send_message')
def send_message(data):
    global user_map
    game_id = data['room']
    
    # do something here to save the image data
    if 'synthetic' in data.keys() and 'semantic' in data.keys():
        gm.save_message(data['text'], game_id, synthetic_byte_data=data['synthetic'], semantic_byte_data=data['semantic'])
    else:
        gm.save_message(data['text'], game_id)

    emit('update_text', {'text':gm.format_dialog(game_id, 'Teller')}, room=user_map[game_id]['teller'])
    emit('update_text', {'text':gm.format_dialog(game_id, 'Drawer')}, room=user_map[game_id]['drawer'])

    if gm.active_user(game_id=game_id) == "teller":
        emit('is_active', {'active':True}, room=user_map[game_id]['teller'])
        emit('is_active', {'active':False}, room=user_map[game_id]['drawer'])
    else:
        emit('is_active', {'active':False}, room=user_map[game_id]['teller'])
        emit('is_active', {'active':True}, room=user_map[game_id]['drawer'])

@socketio.on('connect')
def connect_users():
    pass

@socketio.on('pair_users')
def pair_users(data):    
    global tellers
    global drawers

    if data["user_type"] == "drawer": drawers.add(request.sid)
    else: tellers.add(request.sid)

    # if we have enough to make a pair, we make a pair
    if len(drawers) > 0 and len(tellers) > 0:
    
        # select target image
        # map room to requests to return info
        drawer = drawers.pop()
        teller = tellers.pop()

        new_room = str(uuid4())[:8]  
        global user_map
        user_map[new_room] = {'drawer':drawer, 'teller':teller}
        gm.new_game(new_room)      
        emit('paired', {'room':new_room}, room=drawer)
        emit('is_active', {'active':False}, room=drawer)

        emit('paired', {'room':new_room}, room=teller)
        emit('is_active', {'active':True}, room=teller)        

@socketio.on('get_target_label')
def get_target_label(data):
    image_str = gm.get_target_label(data['room'])  
    emit('send_target_label_to_client', {'image':image_str}, room=user_map[data['room']]['teller'])

if __name__ == '__main__':
    """ Run the app. """
    # socketio.run(app, port=3000)
    http_server = WSGIServer(('', 3000), app)
    http_server.serve_forever()