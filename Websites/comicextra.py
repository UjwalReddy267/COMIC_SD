import sys
sys.path.append('../Comic-dl')
from comic_dl_class import comic_site

class comicextra(comic_site):
    search_link = "https://ww1.comicextra.com/comic-search?key="
    search_res_box = 'cartoon-box'

    def __init__(self,query):
        super().__init__()
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
        if soup == None:
            return -1,None,None
        title = soup.find('title').get_text()
        title = self.format_title(title)
        img = soup.find_all('img',{"class":"chapter_img"})
        lnks = []
        for i in img:
            lnks.append(i['src'])
        return 1,lnks,title

    def get_chaps(self,link):
        soup = self.get_soup(link)
        if soup == None:
            return -1
        name = soup.find('span',{'class':'list-top-movie-item-vn'}).get_text()
        chap_list = soup.find('tbody',{"id":"list"})
        a = chap_list.find_all("a")
        chapters = [i.get('href') for i in a]
        titles = [i.get_text() for i in a]
        #Get cover image
        cover_img = soup.find('div',{'class':'movie-l-img'}).find('img').get('src')
        self.img_download(cover_img,'cover','downloads/temp/')
        self.chapters = [name,chapters,titles]
        return 1
    
    def get_search_titles(self,page):
        titles = []
        link = self.search_link+self.query+'&page='+str(page)
        soup = self.get_soup(link)
        if soup == None:
            return -1
        table = soup.find_all('div',{'class':'cartoon-box'})
        if table == []: return 0
        for box in table:
            imgLink = box.find('img').get('src')
            titles.append([box.find_all('a')[0].get('href'),box.find_all('a')[1].get_text(),imgLink])
        self.searchResults[page] = titles
        return 1

    def get_last_page(self,search_term):     
        self.lPage = 1
        while 1:
            soup = self.get_soup(self.search_link+search_term+'&page='+str(self.lPage))
            if soup == None:
                return -1
            text = soup.find_all('div',{'class','general-nav'})[-1]
            try:
                last = text.find_all('a')[-1].get_text()
                if last == 'Z':
                    self.lPage = 0
                    return
            except IndexError:
                err = self.get_search_titles(self.lPage)
                if err!=1:
                    return err
                self.lPage = 1
                return
            self.get_search_titles(self.lPage)
            if last == 'Next':
                self.lPage = int(text.find_all('a')[-2].get_text())
            else:
                break
        return 1