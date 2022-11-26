import sys
sys.path.append('../Comic-dl')
from comic_dl_class import comic_site

class comiconline(comic_site):
    search_link = "https://comiconlinefree.net/comic-search?key="
    #search_res_box = ["div","class","manga-box"]
    search_res_box = 'manga-box'

    def __init__(self,query):
        #self.get_comics(query)
        if query == '2' or '.com' not in query or len(query.split('.com')[-1])<=1:
            search_term = input('Enter search term: ')
            self.get_search_results(search_term)
        else:
            self.get_comics(query)

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
        return comics,titles

    def no_results(self,soup):
        if len(soup.find_all('div',{"class":"general-nav"})) == 0:
            return 1
        else: return 0

    def get_search_titles(self,soup):
        titles = []
        table = soup.find_all('div',{'class':'manga-box'})
        if table == []: return None
        for box in table:
            titles.append([box.find_all('a')[0].get('href'),box.find_all('a')[1].get_text()])
        return titles

    def get_last_page(self,search_term):
        results = {}

        soup = self.get_soup(self.search_link+search_term)
        n_page = 1
        while 1:
            text = soup.find_all('div',{'class','general-nav'})[-1]
            try:
                last = text.find_all('a')[-1].get_text()
            except IndexError:
                soup = self.get_soup(self.search_link+search_term+'&page='+'1')
                results[1] = self.get_search_titles(soup)
                if results[1] == None:
                    return None,None
                return results, 1
            
            if last == 'Next':
                n_page = text.find_all('a')[-2].get_text()
                cur_page = int(text.find_all('a')[-2].get_text())
                soup = self.get_soup(self.search_link+search_term+'&page='+n_page)
                results[cur_page] = self.get_search_titles(soup)
            else:
                return results,int(n_page)





