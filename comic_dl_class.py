from bs4 import *
import requests
from zipfile import ZipFile
import urllib.request
import os
from tqdm.auto import tqdm
import re

class comic_site():
    bar_format = '{desc:40s}:{percentage:3.0f}%|{bar}|{n_fmt}/{total_fmt} [{elapsed}s, {rate_fmt}{postfix}]'
    escapes = ''.join([chr(char) for char in range(1, 32)])
    escapes+='/:?\\|*><\"\n'
    translator = str.maketrans('', '', escapes)
    driver = None

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

    def get_comics(self,link):
        if self.is_chap_list(link):
            self.multi_parse(link)
        else:
            self.comic_dl([link])

    def comic_dl(self,links):
        
        for cnt,link in enumerate(tqdm(links,position=0,colour='red',desc='Downloading',unit='comic',bar_format=self.bar_format,leave=False)):
            link = self.get_full_link(link)
            soup = self.get_soup(link)
            images,title = self.find_images(link)
            
            os.chdir('./downloads')
            fil = ZipFile(title+'.cbr','w')
            for i,image in enumerate(tqdm(images,desc=title,leave=False,colour='green',unit='image',position=1,bar_format=self.bar_format)):
                urllib.request.urlretrieve(image,str(i)+'.jpg')
                fil.write(''+str(i)+'.jpg')
                os.remove(str(i)+'.jpg')
            tqdm.write('{:40s}: Done'.format(title))
            fil.close()
        tqdm.write('Downloaded {} comics'.format(len(links)))
        os.chdir("..")
        return
    
    def multi_parse(self,link):
        soup = self.get_soup(link)
        comics,titles = self.get_chaps(soup)
        comics = comics[::-1]
        titles = titles[::-1]
        for i,title in enumerate(titles):
            print("{0:3d}) {1}".format(i+1,title))
        book_nums = input('Enter the serial number of the books (Ex: 10/1-2/4 10-15):').split(' ')
        links = []
        if '0' in book_nums:
            links.extend([comic for comic in comics])
        else:
            for loc in book_nums:
                ind = list(map(int,loc.split('-')))
                if len(ind)==1:
                    links.extend([comics[ind[0]-1]])
                elif len(ind)==2:
                    links.extend([comic for comic in comics[ind[0]-1:ind[1]]])
        os.system('cls')
        self.comic_dl(links)	
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