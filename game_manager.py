import os
from PIL import Image
import io
import time
import random
from shutil import copyfile
import base64
import cv2
from add_text import *
import re
from dataclasses import dataclass

"""
TO DO ASAP:
- TEST hypothesis
- Prepare target images
- Write pipeline for computing score

- minimum turns: 5 // can always be told explicity to data collectors
- add button to end game // they can always tell each other to start a new game
- add info to tell if they disconnected
- add continuous count of characters left so its easier to write out stuff
- score // can be calcualted later? can manually check quality of images, as long as semantic labels are correct
- after ending game, show score and images to both teller and drawer, then allow them to reconnect // can be added later

DRAWER MUST DRAW AN IMAGE AT EVERY TURN TO THE BEST OF HIS ABILITY. Even IF HE ASKS A QUESTION FOR CLARIFICATION.
"""

@dataclass
class GM:

    num_peeks:int

    def num_peeks_left(self, game_id):
        peeks = [x for x in os.listdir('data/'+game_id+'/') if "peek" in x]
        return len(peeks)

    def extract_int_from_path(self, path):
        try:
            result = re.findall(r'\d+', path)
            return int(result[0])
        except:
            return 0

    def use_one_peek(self, game_id):
        try:
            paths = [x for x in os.listdir('data/'+game_id+'/') if "peek" in x]
            to_del = sorted(paths, key=lambda x: self.extract_int_from_path(x), reverse=True)
            os.remove('data/'+game_id+'/'+to_del[0])
        except Exception as error:            
            print(error) 

    def peek(self, game_id):
        for i in range(int(self.current_turn(game_id)), -1, -1):
            path = 'data/' + game_id + '/synthetic_' + str(i) + '.jpg'            
            if os.path.isfile(path):                
                im = Image.open(path)
                imgByteArr = io.BytesIO()
                im.save(imgByteArr, format='JPEG') 
                self.use_one_peek(game_id) 
                return 'data:image/png;base64,'+base64.b64encode(imgByteArr.getvalue()).decode('ascii')
        return ''

    def get_target_label(self, game_id):
        if game_id and game_id.strip() != "":
            path = 'data/' + game_id + '/target_label.png'
            image = cv2.imread(path)    
            image = cv2.resize(image, (350, 350))
            text_mask = PutingText2Mask(image)
            image = Image.fromarray(text_mask)
            buffered = io.BytesIO()
            image.save(buffered, format="png")        
            img_str = 'data:image/png;base64,'+base64.b64encode(buffered.getvalue()).decode('ascii')
            return img_str
        return ''

    def get_target_image(self, game_id):
        imgByteArr = io.BytesIO()
        if game_id and game_id.strip() != "":
            im = Image.open('data/'+game_id+'/target_image.jpg')
            im.save(imgByteArr, format='PNG')        
            return 'data:image/png;base64,'+base64.b64encode(imgByteArr.getvalue()).decode('ascii')    
        return ''

    def select_target_image(self, game_id):        
        target_images = os.listdir('server_data/landscape_target/')
        if not os.path.exists('server_data/selected/'): os.mkdir('server_data/selected/')
        used_target_images = [x.replace('.txt', '') for x in os.listdir('server_data/selected/')]
        selected_target_image = target_images[0]
        idx = 0
        while True:
            if selected_target_image.replace('.jpg', '') not in used_target_images: break
            try:
                idx += 1
                selected_target_image = target_images[idx]
            except:
                # we finished all target images
                break
        with open('server_data/selected/'+selected_target_image.replace('.png', '.txt').replace('.jpg', '.txt'), 'w') as file: file.writelines(['selected'])
        copyfile('server_data/landscape_target/'+selected_target_image, 'data/'+game_id+'/target_image.jpg')

        copyfile('server_data/landscape_label/'+selected_target_image.replace('.jpg', '.png').replace('target_image', 'target_image_semantic'), 'data/'+game_id+'/target_label.png')
        return
                
    def new_game(self, game_id):        
        if not os.path.exists('data/'): os.mkdir('data/')                
        os.mkdir('data/'+game_id)
        self.select_target_image(game_id)
        with open('data/'+game_id+'/turn_history.txt', 'w') as file: file.writelines(['turn_0'])
        with open('data/'+game_id+'/user_turn.txt', 'w') as file: file.writelines(['teller'])
        for i in range(1, self.num_peeks+1):
            with open('data/'+game_id+'/peek_'+str(i)+'.txt', 'w') as file: file.writelines(['peek'])                

    def current_turn(self, game_id):
        try:
            with open('data/'+game_id+'/turn_history.txt', 'r') as file:            
                return (file.readlines()[0]).split('_')[1]
        except:
            return -1

    def active_user(self, game_id):
        try:
            with open('data/'+game_id+'/user_turn.txt', 'r') as file: return file.readlines()[0]
        except:
            return ""

    def save_message(self, text, game_id, synthetic_byte_data=None, semantic_byte_data=None):
        user = self.active_user(game_id)
        turn = self.current_turn(game_id)        

        # Save text from message        
        path_to_file = 'data/'+game_id+'/' + user + '_' + turn + '.txt'        
        with open(path_to_file, 'w') as file: file.writelines([text])
        
        # Potentially save an image
        if synthetic_byte_data is not None:
            image_output_path = 'data/'+game_id+'/' + 'synthetic_' + turn + '.jpg'
            image = Image.open(io.BytesIO(synthetic_byte_data))
            image.save(image_output_path)

        if semantic_byte_data is not None:
            image_output_path = 'data/'+game_id+'/' + 'semantic_' + turn + '.png'
            image = Image.open(io.BytesIO(semantic_byte_data))
            image.save(image_output_path)

        # Update our current turn and whether or not the drawer is next to speak
        if user == "teller":
            with open('data/'+game_id+'/user_turn.txt', 'w') as file: file.writelines(['drawer'])
        else:
            with open('data/'+game_id+'/user_turn.txt', 'w') as file: file.writelines(['teller'])
            new_turn_num = int(turn) + 1
            new_turn = 'turn_' + str(new_turn_num)
            with open('data/'+game_id+'/turn_history.txt', 'w') as file: file.writelines([new_turn])

    def format_dialog(self, game_id, replace="Drawer"):
        def try_append(paths):
            try:
                file_path = paths.pop()
                with open('data/'+game_id+'/'+file_path, 'r') as file:
                    if 'drawer' in file_path:
                        return file.readlines()[0].replace('You', 'Drawer') + '\n'
                    else:
                        return file.readlines()[0].replace('You', 'Teller') + '\n'
            except:
                return ""

        dialog = ""

        sorted_teller = sorted([x for x in os.listdir('data/'+game_id+'/') if 'teller' in x], key=lambda x: self.extract_int_from_path(x), reverse=True)
        sorted_drawer = sorted([x for x in os.listdir('data/'+game_id+'/') if 'drawer' in x], key=lambda x: self.extract_int_from_path(x), reverse=True)

        for i in range(0, max(len(sorted_drawer), len(sorted_teller))):
            dialog += try_append(sorted_teller)
            dialog += try_append(sorted_drawer)

        return dialog.replace(replace, 'You')

