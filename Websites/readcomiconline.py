import sys
sys.path.append('../Comic-dl')
from comic_dl_class import comic_site
import re
from base64 import b64decode

class readcomiconline(comic_site):
    search_link = "https://readcomiconline.li/Search/Comic/comicName="
    site = 'https://readcomiconline.li'

    def __init__(self,query):
        super().__init__()
        self.query = query
        return

    def is_chap_list(self,link):
        return 0 if '?id=' in link else 1

    def get_full_link(self,link):
        return link.split('&')[0]+'&readType=1&quality=hq'


    def find_images(self,link):
        soup = self.get_soup(link)
        if soup == None:
            return -1,None,None
        title = soup.find('title').get_text()
        title = self.format_title(title)
        enc = re.findall(r"lstImages.push\([\'|\"](.*?)[\'|\"]\);", str(soup))
        lnks = self.decode_images(enc)
        return 1,lnks,title


    def get_chaps(self,link):
        soup = self.get_soup(link)
        if soup == None:
            return -1
        name = soup.find('div',{'class':'heading'}).get_text()
        table = soup.find('ul',{"class":"list"})
        a = table.find_all("a")
        chapters = [self.site+i.get('href') for i in a]
        titles = [i.get_text() for i in a]
        #Get cover image
        cover_img = soup.find('div',{'class':'col cover'}).find('img').get('src')
        if 'https:' not in cover_img:
            cover_img = self.site+cover_img
        self.img_download(cover_img,'cover','downloads/temp/')
        self.chapters = [name,chapters,titles]
        return 1


    def get_search_titles(self,link):
        soup = self.get_soup(link)
        if soup == None:
            return -1, None
        titles = []
        table = soup.find_all('div',{'class':'col cover'})
        if table == []:
            return 0, None
        for box in table:
            imgLink = box.find('img').get('src')
            if 'https' not in imgLink:
                imgLink = self.site+imgLink
            titles.append([self.site+box.find('a').get('href'),box.find('img').get('title'),imgLink])
        return 1,titles

    def get_last_page(self,search_term):
        search_results = self.searchResults
        err,titles = self.get_search_titles(self.search_link+search_term)
        if err != 1:
            return err
        self.lPage = len(titles)//25 + (0 if len(titles)%25==0 else 1)
        for i in range(self.lPage):
            cur_page_res = []
            for j in range(i*25,min(i*25+25,len(titles))):
                cur_page_res.append(titles[j]) 
            search_results[i+1] = cur_page_res
        return 1

    def format_title(self,title):
        title = title.split(' ')
        end = title.index('-')
        title = " ".join(title[:end])
        title = title.translate(self.translator)
        title = ''.join(title.rsplit('Issue',1))
        title = re.sub('\s{2,}',' ',title)
        return title.strip()

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