from flask import Flask, render_template, session, redirect, url_for
from flask_socketio import SocketIO, emit
import sys
import socketio as sio_class
from uuid import uuid4
# from english import english
from PIL import Image
import os
from gau_gan import GauGan
from server_config import config
import webbrowser

# Path to downloads
GauGan.set_download_path()

# Session constants
session_room = ""
is_active_user = False

# Init our server for displaying the chat interface
app = Flask(__name__)
app.config['SECRET_KEY'] = 'drawer'
socketio = SocketIO(app)

# Socket to the server that collects our data
sio = sio_class.Client()

if config['localhost'] == True:
    sio.connect('http://localhost:3000')
else:
    sio.connect(config['external_server'])

@sio.on('send_target_image_to_client')
def send_target_image_to_client(data):        
    with app.test_request_context():
        socketio.emit('recieved_target_image', data)  

@sio.on('game_over')
def game_over(data):
    print("GAME OVER")
    with app.test_request_context():
        socketio.emit('left_game', data)

@sio.on('update_text')
def update_text(data):    
    with app.test_request_context():
        socketio.emit('update_text', data)

@sio.on('is_active')
def become_active(data):
    global is_active_user
    if data['active'] == True:
        # print('user is becoming active')
        is_active_user = True        
        socketio.emit('toggle_active', {'active':is_active_user})
    else:
        # print('user is disabled')
        is_active_user = False
        socketio.emit('toggle_active', {'active':is_active_user})

@sio.on('paired')
def did_pair(data):
    # print("pairing!")
    global session_room
    session_room = data['room']
    with app.test_request_context():            
        socketio.emit('redirect', {'path':'game'})

@socketio.on('target_image')
def target_image(data):
    global session_room
    sio.emit('get_target_image_drawer', {'room':session_room})

@socketio.on('new_game')
def new_game(data):  
    global is_active_user
    global session_room  
    sio.emit('left_game', {'room':session_room})    
    GauGan.new_game()    
    session_room = ""
    is_active_user = False    

@socketio.on('get_active_status')
def get_active_status(data):
    global is_active_user
    with app.test_request_context():
        # print(is_active_user, "active?")
        socketio.emit('toggle_active', {'active':is_active_user})
    global session_room    
    if session_room.strip() == "":
        with app.test_request_context():
            socketio.emit('pair_again', {'path':''})

@socketio.on('joined')
def connect_drawer_with_teller(data):
    global session_room
    if session_room != "":
        emit('redirect', {'path':'game'})
    else:    
        sio.emit('pair_users', {'user_type': 'drawer'})    
     
@socketio.on('send_message')
def send_message(data):
    global session_room
    text = "You: " + data["text"] + "\n\n"
    # result = english(text)
    # if result["can_send"] == True:
    emit('send_message_front_end', {'text':text})    

    semantic = GauGan.semantic()
    synthetic = GauGan.synthetic()

    sio.emit('send_message', {'text':text, 'room':session_room, 'semantic':semantic, 'synthetic':synthetic})    
    # else:
    #     emit('bad_english', {'info':result['info']})

@socketio.on('did_download_new_image')
def downloaded_new_image(data):    
    emit('can_send_message', {'send':GauGan.did_download_new_image()})    

@app.route('/game')
def game():    
    global session_room
    if session_room == "":
        with app.test_request_context():
            socketio.emit('pair_again', {'path':''})            
    return render_template('drawer.html')

@app.route('/')
def index():    
    global session_room    
    if session_room != "":
        socketio.emit('redirect', {'path':'game'})
        GauGan.new_game()
    else:
        sio.emit('pair_users', {'user_type': 'drawer'})    
    return render_template('connect.html')
    
if __name__ == '__main__':
    """ Run the app. """
    webbrowser.open_new_tab('http://localhost:5000')
    socketio.run(app, port=5000)