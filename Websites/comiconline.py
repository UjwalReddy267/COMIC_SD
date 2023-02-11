import sys
sys.path.append('../Comic-dl')
from comic_dl_class import comic_site

class comiconline(comic_site):
    search_link = "https://comiconlinefree.net/comic-search?key="
    search_res_box = 'manga-box'

    def __init__(self,query):
        self.query = query
        return
    
    def is_chap_list(self,link):
        return 1 if link.split('/')[3] == 'comic' else 0

    def get_full_link(self,link):        
        if link.split('/')[-1] != 'full':
            link += 'full' if link[-1]=='/' else '/full'
        return link

    def find_images(self,link):
        soup = self.get_soup(link)
        title = soup.find_all('title')[0].get_text()
        title = self.format_title(title)
        img = soup.find_all('img',{"class":"lazyload chapter_img"})
        lnks = []
        for i in img:
            lnks.append(i['data-original'])
        return lnks,title

    def get_chaps(self,soup):
        a = soup.find_all("a",{"class","ch-name"})
        comics = [i.get('href') for i in a]
        titles = [i.get_text() for i in a]
        #Get cover image
        cover_img = soup.find('img',{'id':'series_image'}).get('src')
        self.img_download('https://'+cover_img.split('//')[-1],'cover',path='downloads/temp/')
        return comics,titles

    def no_results(self,soup):
        if len(soup.find_all('div',{"class":"general-nav"})) == 0:
            return 1
        else: return 0

    def get_search_titles(self,page):
        titles = []
        link = self.search_link+self.query+'&page='+str(page)
        soup = self.get_soup(link)
        table = soup.find_all('div',{'class':'manga-box'})

        if table == []: return None
        for n,box in enumerate(table):
            imgLink = box.find('img').get('src')
            titles.append([box.find_all('a')[0].get('href'),box.find_all('a')[1].get_text(),imgLink])
        return titles

    def get_last_page(self,search_term):
        
        results = self.searchResults
        n_page = 1
        
        
        
        while 1:
            soup = self.get_soup(self.search_link+search_term+'&page='+str(n_page))
            text = soup.find_all('div',{'class','general-nav'})[-1]
            try:
                last = text.find_all('a')[-1].get_text()
            except IndexError:
                results[1] = self.get_search_titles(self.search_link+search_term+'&page='+'1')
                if results[1] == None:
                    return 0
                return 1
            
            results[n_page] = self.get_search_titles(n_page)

            if last == 'Next':
                n_page = int(text.find_all('a')[-2].get_text())
                
            else:
                break
        
        return n_page





