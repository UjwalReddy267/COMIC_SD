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
            
            os.chdir('./downloads')
            fil = ZipFile(title+'.cbr','w')
            for i,image in enumerate(tqdm(images,desc=title,leave=False,colour='green',unit='image',position=1,bar_format=self.bar_format)):
                self.img_download(image,str(i))
                fil.write(''+str(i)+'.jpg')
                os.remove(str(i)+'.jpg')
            tqdm.write('{:40s}: Done'.format(title))
            fil.close()
            os.chdir("..")

        tqdm.write('Downloaded {} comics'.format(len(links)))
        return
    
  

    def get_search_results(self,search_term):
	
        search_results,last_page = self.get_last_page(search_term)
        if last_page == None:
            print('Not found')
            return
        
        req_page = 1

        while 1:
            os.system('cls')
            if req_page not in search_results:
                soup = self.get_soup(self.search_link+search_term+'&page='+str(req_page)) #Define for child
                search_results[req_page]=self.get_search_titles(soup)
            
            cur_page_results = search_results[req_page] #Define for child
            print('Page: {}/{}'.format(req_page,last_page))
            for i in range(len(cur_page_results)): print("{:2d}. {}".format(i+1,cur_page_results[i][1]) )
            while 1:
                request = input('\033[K Enter -1 for previous page, 0 for next page or serial number to select the comic. Enter \'>\' followed by page numnber to skip to page (Ex. >10): ')
                if request == '0':
                    if req_page == last_page:
                        print('This is the last page',end='\033[A\r')
                        continue
                    req_page += 1
                    break
                elif request == '-1':
                    if req_page == 1:
                        print('This is the first page',end='\033[A\r')
                        continue
                    req_page -=1
                    break
                elif '>' in request:
                    if not(0 < int(request.split('>')[-1]) <= last_page) :
                        print('Page Not available',end='\033[A\r')
                        continue
                    elif int(int(request.split('>')[-1]) == req_page):
                        print('Already on requested page',end='\033[A\r')
                        continue
                    req_page = int(request.split('>')[-1])
                    break
                else:
                    if int(request)>len(cur_page_results) or int(request)<-1:
                        print('Wrong option',end='\033[A\r')
                        continue
                    os.system('cls')
                    self.multi_parse(cur_page_results[int(request)-1][0])
                    return
        return

    def img_download(self,src,name):
        res = requests.get(src, stream = True)

        with open(name+'.jpg','wb') as f:
            shutil.copyfileobj(res.raw, f)
