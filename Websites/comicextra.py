import sys
sys.path.append('../Comic-dl')
from comic_dl_class import comic_site

class comicextra(comic_site):
    image_location = 'src'
    search_link = "https://ww1.comicextra.com/comic-search?key="
    search_res_box = 'cartoon-box'
    lPage = 0

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
        img = soup.find_all('img',{"class":"chapter_img"})
        lnks = []
        for i in img:
            lnks.append(i['src'])
        return lnks,title

    def get_chaps(self,link):
        soup = self.get_soup(link)
        name = soup.find('span',{'class':'list-top-movie-item-vn'}).get_text()
        chap_list = soup.find('tbody',{"id":"list"})
        a = chap_list.find_all("a")
        chapters = [i.get('href') for i in a]
        titles = [i.get_text() for i in a]
        #Get cover image
        cover_img = soup.find('div',{'class':'movie-l-img'}).find('img').get('src')
        self.img_download(cover_img,'cover','downloads/temp/')
        return name,chapters,titles
    
    def no_results(self,soup):
        if len(soup.find_all('div',{'class':'general-nav'})) != 2:
            return 1
        else: return 0
    
    def get_search_titles(self,page):
        titles = []
        link = self.search_link+self.query+'&page='+str(page)
        soup = self.get_soup(link)
        table = soup.find_all('div',{'class':'cartoon-box'})
        if table == []: return None
        for n,box in enumerate(table):
            imgLink = box.find('img').get('src')
            titles.append([box.find_all('a')[0].get('href'),box.find_all('a')[1].get_text(),imgLink])
        return titles

    def get_last_page(self,search_term):
        results = self.searchResults      
        self.lPage = 1

        while 1:
            soup = self.get_soup(self.search_link+search_term+'&page='+str(self.lPage))
            text = soup.find_all('div',{'class','general-nav'})[-1]
            try:
                last = text.find_all('a')[-1].get_text()
                if last == 'Z':
                    return 0
            except IndexError:
                results[1] = self.get_search_titles(self.lPage)
                return 1
            
            results[self.lPage] = self.get_search_titles(self.lPage)
            if last == 'Next':
                self.lPage = int(text.find_all('a')[-2].get_text())
            else:
                break
        return



