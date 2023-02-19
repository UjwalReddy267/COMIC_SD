from bs4 import *
import requests
from zipfile import ZipFile
from tqdm.auto import tqdm
import re
import shutil
from PyQt6.QtWidgets import *


class comic_site():
    def __init__(self):
        self.escapes = ''.join([chr(char) for char in range(1, 32)])
        self.escapes+='/:?\\|*><\"\n'
        self.translator = str.maketrans('', '', self.escapes)
        self.searchResults = {}
        self.query = ''
        self.lPage = 0
        self.downloadedImages = {}


    def get_soup(self,link):
        r = requests.get(link)
        soup = BeautifulSoup(r.text,'html.parser')
        return soup

    def format_title(self,title): #Define for child
        title = title.split(' ')
        end = title.index('-')
        title = " ".join(title[:end])
        title = title.translate(self.translator)
        title = title.replace('#TPB','')
        title = re.sub('\s{2,}',' ',title)
        return title.strip()

    def getTitle(self,link):
        soup = self.get_soup(link) 
        title = soup.find('title').get_text()
        title = title.split(' ')
        end = title.index('-')
        title = " ".join(title[:end])
        return title

    def comic_dl(self,link):
        print('Comic_DL')
        link = self.get_full_link(link)
        images,title = self.find_images(link)
        return images,title
    
    def img_download(self,src,name,path):
        res = requests.get(src, stream = True)
        with open(path+name+'.jpg','wb') as f:
            shutil.copyfileobj(res.raw, f)
