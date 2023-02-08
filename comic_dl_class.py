from bs4 import *
import requests
from zipfile import ZipFile
import urllib.request
import os
from tqdm.auto import tqdm
import re
import shutil

class comic_site():
    bar_format = '{desc:40s}:{percentage:3.0f}%|{bar}|{n_fmt}/{total_fmt} [{elapsed}s, {rate_fmt}{postfix}]'
    escapes = ''.join([chr(char) for char in range(1, 32)])
    escapes+='/:?\\|*><\"\n'
    translator = str.maketrans('', '', escapes)
    searchResults = {}
    query = ''

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


    def comic_dl(self,links):
        
        for cnt,link in enumerate(tqdm(links,position=0,colour='red',desc='Downloading',unit='comic',bar_format=self.bar_format,leave=False)):
            link = self.get_full_link(link)
            soup = self.get_soup(link)
            images,title = self.find_images(link)
            
            fil = ZipFile('downloads/'+title+'.cbr','w')
            for i,image in enumerate(tqdm(images,desc=title,leave=False,colour='green',unit='image',position=1,bar_format=self.bar_format)):
                self.img_download(image,str(i),path='downloads/temp/')
                fil.write('downloads/temp/'+str(i)+'.jpg')
            tqdm.write('{:40s}: Done'.format(title))
            fil.close()
        tqdm.write('Downloaded {} comics'.format(len(links)))
        return
    
    def img_download(self,src,name,path=''):
        res = requests.get(src, stream = True)

        with open(path+name+'.jpg','wb') as f:
            shutil.copyfileobj(res.raw, f)
