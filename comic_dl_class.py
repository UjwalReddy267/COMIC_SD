from bs4 import *
import requests
from zipfile import ZipFile
from tqdm.auto import tqdm
import re
import shutil
import time
from PyQt6.QtWidgets import *


class comic_site():
    bar_format = '{desc:40s}:{percentage:3.0f}%|{bar}|{n_fmt}/{total_fmt} [{elapsed}s, {rate_fmt}{postfix}]'
    escapes = ''.join([chr(char) for char in range(1, 32)])
    escapes+='/:?\\|*><\"\n'
    translator = str.maketrans('', '', escapes)
    searchResults = {}
    query = ''
    lPage = 0
    downloadedImages = {}

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

    def comic_dl(self,link,progress):
        link = self.get_full_link(link)
        images,title = self.find_images(link)
        fil = ZipFile('downloads/'+title+'.cbr','w')
        for i,image in enumerate(images):
            self.img_download(image,str(i),path='downloads/temp/')
            fil.write('downloads/temp/'+str(i)+'.jpg')
            progress.emit(100*(i+1)//len(images))
        fil.close()



    def img_download(self,src,name,path=''):
        res = requests.get(src, stream = True)

        with open(path+name+'.jpg','wb') as f:
            shutil.copyfileobj(res.raw, f)
