from PIL import Image
import io
import os
import re
import webbrowser

class GauGan:

    @classmethod
    def set_download_path(self):
        download_path = input("Enter you path to downloads: ").strip()

        link_to_website = 'http://nvidia-research-mingyuliu.com/gaugan/'
        webbrowser.open_new_tab(link_to_website)        

        if download_path == "" and os.path.exists('download_path.txt'): return

        if not os.path.exists(download_path):
            raise Exception("Download path provided is not valid!")

        # Remove old path
        try:
            os.remove('download_path.txt')
        except:
            pass

        # Set new path
        with open('download_path.txt', 'w') as file: file.writelines([download_path])
        return

    @classmethod
    def get_download_path(self):
        with open('download_path.txt', 'r') as file:
            return file.readlines()[0].strip()

    @classmethod
    def new_game(self):
        print("Starting new game...")
        path = self.get_download_path() + "/"
        for file in os.listdir(path):
            if "gaugan_" in file: os.remove(path+file)

    @classmethod
    def synthetic(self):
        latest_image = self.get_latest_downloaded_image('output')   
        if latest_image:     
            return self.get_image_bytes(latest_image, image_format='JPEG')

    @classmethod
    def semantic(self):
        latest_image = self.get_latest_downloaded_image('input')        
        if latest_image:
            return self.get_image_bytes(latest_image)

    @classmethod
    def get_latest_downloaded_image(self, image_type='input'):
        ext = self.get_download_path()
        all_gan_gan_images = [x for x in os.listdir(ext) if "gaugan_"+image_type in x]
        sorted_images = sorted(all_gan_gan_images, key=lambda x: self.extract_int_from_image(x), reverse=True)
        try:
            return ext+'/'+sorted_images[0]
        except:
            return None
        
    @classmethod
    def extract_int_from_image(self, image):
        try:
            result = re.findall(r'\d+', image)
            return int(result[0])
        except:
            return 0

    @classmethod
    def get_image_bytes(self, path_to_image, image_format='PNG'):        
        imgByteArr = io.BytesIO()
        im = Image.open(path_to_image)
        im.save(imgByteArr, format=image_format)
        imgByteArr = imgByteArr.getvalue()
        return imgByteArr