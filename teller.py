from flask import Flask, render_template, session, redirect, url_for
from flask_socketio import SocketIO, emit
import sys
import socketio as sio_class
from uuid import uuid4
from server_config import config
import webbrowser

session_room = ""
is_active_user = False

# Init the server
app = Flask(__name__)
app.config['SECRET_KEY'] = 'teller'
socketio = SocketIO(app)

# Socket to server
sio = sio_class.Client()

if config['localhost'] == True:
    sio.connect('http://localhost:3000/')
else:
    sio.connect('https://language.cs.ucdavis.edu/')

@sio.on('game_over')
def game_over(data):
    print("GAME OVER")
    with app.test_request_context():
        socketio.emit('left_game', data)

@sio.on('send_num_peeks_to_client')
def send_num_peeks_to_client(data):
    with app.test_request_context(): socketio.emit('recieved_num_peeks', data) 

@sio.on('send_peek_to_client')
def send_peek_to_client(data):
    with app.test_request_context(): socketio.emit('recieved_peek', data) 

@sio.on('send_target_label_to_client')
def send_target_label_to_client(data):
    with app.test_request_context(): socketio.emit('recieved_target_label', data)

@sio.on('update_text')
def update_text(data):
    with app.test_request_context(): socketio.emit('update_text', data)

@sio.on('is_active')
def become_active(data):
    global is_active_user
    if data['active'] == True:
        # print('user is becoming active')
        is_active_user = True        
        with app.test_request_context(): socketio.emit('toggle_active', {'active':is_active_user})
    else:
        # print('user is disabled')
        is_active_user = False
        with app.test_request_context(): socketio.emit('toggle_active', {'active':is_active_user})

@sio.on('paired')
def my_event(data):
    # print("request to pair!")
    global session_room
    session_room = data['room']
    with app.test_request_context():    
        socketio.emit('redirect', {'path':'game'})
        # print('emitted signal')

@sio.on('send_target_image_to_client')
def send_target_image_to_client(data):        
    with app.test_request_context():
        socketio.emit('recieved_target_image', data)        

@socketio.on('get_num_peeks')
def get_num_peeks_left(data):
    sio.emit('get_num_peeks', {'room':session_room})

@socketio.on('peek')
def peek(data):
    sio.emit('peek', {'room':session_room})

@socketio.on('target_image')
def target_image(data):
    sio.emit('get_target_image', {'room':session_room})

@socketio.on('target_label')
def target_image(data):
    sio.emit('get_target_label', {'room':session_room})

@socketio.on('new_game')
def new_game(data):
    global is_active_user
    global session_room
    sio.emit('left_game', {'room':session_room})
    session_room = ""
    is_active_user = False
    emit('pair_again', {'path':''})

@socketio.on('get_active_status')
def get_active_status(data):
    global is_active_user
    with app.test_request_context():        
        socketio.emit('toggle_active', {'active':is_active_user})
    global session_room    
    if session_room.strip() == "":
        with app.test_request_context():
            socketio.emit('pair_again', {'path':''})

@socketio.on('joined')
def connect_drawer_with_teller(data):
    global session_room   
    # print('session', session_room) 
    if session_room != "":
        emit('redirect', {'path':'game'})
    else:
        sio.emit('pair_users', {'user_type': 'teller'})    

@socketio.on('send_message')
def send_message(data):
    global session_room
    text = "You: " + data["text"] + "\n\n"
    # result = english(text)
    # if result["can_send"] == True:
    emit('send_message_front_end', {'text':text})                        
    sio.emit('send_message', {'text':text, 'room':session_room})    
    # else:
        # emit('bad_english', {'info':result['info']})    

@app.route('/game')
def game():    
    global session_room
    if session_room == "":
        with app.test_request_context():
            socketio.emit('pair_again', {'path':''})
    return render_template('teller.html')

@app.route('/')
def index():
    global session_room    
    # print('session', session_room)
    if session_room != "":
        socketio.emit('redirect', {'path':'game'})
    else:
        sio.emit('pair_users', {'user_type': 'teller'})
    return render_template('connect.html')

if __name__ == '__main__':
    """ Run the app. """
    webbrowser.open_new_tab('http://localhost:5001')
    socketio.run(app, port=5001)     