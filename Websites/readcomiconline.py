import sys
sys.path.append('../Comic-dl')
from comic_dl_class import comic_site
import re
from base64 import b64decode

class readcomiconline(comic_site):
    search_link = "https://readcomiconline.li/Search/Comic/comicName="
    site = 'https://readcomiconline.li'
    def __init__(self,query):
        if '.li' not in query : #or len(query.split('.li')[-1])<=1
            self.get_search_results(query)
        else:
            self.get_comics(query)
            print(query)
        return

    def is_chap_list(self,link):
        return 0 if '?id=' in link else 1

    def format_title(self,title): #Define for child
        title = title.split(' ')
        end = title.index('-')
        title = " ".join(title[:end])
        title = title.translate(self.translator)
        title = ''.join(title.rsplit('Issue',1))
        title = re.sub('\s{2,}',' ',title)
        return title.strip()

    def get_full_link(self,link):
        return link.split('&')[0]+'&readType=1&quality=hq'

    def find_images(self,link):
        soup = self.get_soup(link)
        title = soup.find('title').get_text()
        title = self.format_title(title)
        enc = re.findall(r"lstImages.push\([\'|\"](.*?)[\'|\"]\);", str(soup))
        lnks = self.decode_images(enc)
        return lnks,title

    def decode_images(self,enc):
        for i in range(len(enc)):
            enc[i] = enc[i].replace('_x236','d').replace('_x945','g')
            if enc[i].find('https')!=0:
                m = enc[i]
                z = m[m.find('?'):]
                if m.find('=s0?')>0:
                    m = m[0:m.find('=s0?')]
                    qual = '=s0'
                else:
                    m = m[0:m.find('=s1600?')]
                    qual = '=s1600'
                m = m[4:22]+m[25:]
                m = m[0:-6] + m[-2] + m[-1]
                m = b64decode(m).decode('utf-8')
                m = m[0:13]+m[17:]
                m = m[0:-2]+qual
                m = m+z
                m = 'https://2.bp.blogspot.com/'+m
                enc[i] = m
        return enc


    def get_chaps(self,soup):
        table = soup.find('ul',{"class":"list"})
        a = table.find_all("a")
        comics = [self.site+i.get('href') for i in a]
        titles = [i.get_text() for i in a]
        return comics,titles

    def get_search_titles(self,soup):
        titles = []
        for box in soup.find_all('div',{'class':'cartoon-box'}):
            titles.append([self.site+box.find_all('a')[0].get('href'),box.find_all('a')[1].get_text()])
        return titles

    def get_last_page(self,search_term):
        search_results = {}
        links = []
        titles = []
        soup = self.get_soup(self.search_link+search_term)
        table = soup.find_all('div',{'class':'col cover'})
        if table == []: return None, None
        for a in table:
            links.append(self.site+a.find('a').get('href'))
            titles.append(a.find('img').get('title'))
        last_page = len(links)//25 + (0 if len(links)%25==0 else 1)
        for i in range(last_page):
            cur_page_res = []
            for j in range(i*25,min(i*25+25,len(titles))):
                cur_page_res.append([links[j],titles[j]]) 
            search_results[i+1] = cur_page_res

        return search_results,last_page




