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
        try:
            r = requests.get(link)
            soup = BeautifulSoup(r.text,'html.parser')
        except requests.exceptions.ConnectionError:
            soup = None
        return soup

    def format_title(self,title,link = None,ret = False): #Define for child
        if link != None:
            soup = self.get_soup(link)
            if soup == None:
                return -1,None
            title = soup.find('title').get_text()
        title = title.split(' ')
        end = title.index('-')
        title = " ".join(title[:end])
        if ret:
            return 1,title
        title = title.translate(self.translator)
        title = title.replace('#TPB','')
        title = re.sub('\s{2,}',' ',title)
        return 1,title.strip()

    def comic_dl(self,link):
        print('Comic_DL')
        link = self.get_full_link(link)
        err,images,title = self.find_images(link)
        return err,images,title
    
    def img_download(self,src,name,path):
        try:
            res = requests.get(src, stream = True)
            with open(path+name+'.jpg','wb') as f:
                shutil.copyfileobj(res.raw, f)
            return 1
        except requests.exceptions.ConnectionError:
            return -1