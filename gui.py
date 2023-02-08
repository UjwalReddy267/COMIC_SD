from tkinter import *
from Websites.comicextra import comicextra
from Websites.comiconline import comiconline
from Websites.readcomiconline import readcomiconline


class gui():
    root = None
    searchFrames = {}
    searchLPage = 0
    a = None

    def __init__(self):
        self.root = Tk()
        return

    def clear_window(self,win): 
        for widget in win.winfo_children():
            widget.destroy()

    def start(self):
        root = self.root
        #root.geometry("1000x1000") 
        query_box = Entry(root)
        query_box.grid(row=0,column=0)
        go_button = Button(root,text='Go!',command=lambda:self.go(query_box.get()))
        go_button.grid(row=1,column=0)
        return root

    def go(self,query):
        if '.' not in query and '/' not in query:
            self.site_select(query)
        else:
            self.parseLink(query)

    def site_select(self,query):
        root = self.root
        self.clear_window(root)
        global r
        r = IntVar()
        r.set(1)
        Label(root,text='Select Website').grid(row=0,column=0)
        Radiobutton(root,text='comicextra',variable=r,value=1).grid(row=1,column=0,sticky=W)
        Radiobutton(root,text='comiconlinefree',variable=r,value=2).grid(row=2,column=0,sticky=W)
        Radiobutton(root,text='readcomiconline',variable=r,value=3).grid(row=3,column=0,sticky=W)
        Button(root,text='Search',command=lambda:self.search(query,r.get())).grid(row=4,column=0)


    def parseLink(self,query):
        if 'comicextra' in query:
            self.a = comicextra(query)
        elif 'comiconlinefree' in query:
            self.a = comiconline(query)
        elif 'readcomiconline' in query:
            self.a = readcomiconline(query)
        
        if self.a.is_chap_list(query):
            self.listChapters(query)
        else:
            self.download([query])
     

    def listChapters(self,link):
        a = self.a
        soup = a.get_soup(link)
        comics,titles = a.get_chaps(soup)
        root = self.root
        self.clear_window(root)
        scrollBar = Scrollbar(root)
        listBox = Listbox(root,selectmode=EXTENDED,yscrollcommand=scrollBar.set,height=25,width=75)

        for i in range(len(titles)):
            listBox.insert(i,titles[i])

        listBox.grid(row=0,column=0)
        scrollBar.config( command = listBox.yview )
        scrollBar.grid(row=0,column=1,sticky=N+S+E)

        Button(root,text='Download',command=lambda:self.downloadChaps(comics,listBox.curselection())).grid()

    def downloadChaps(self,comics,selection):
        a = self.a
        links = []
        for i in selection:
            links.append(comics[i])
        self.download(links)

    def download(self,links):
        self.a.comic_dl(links)


    def search(self,query,site):
        if site == 1:
            self.a = comicextra(query)
        elif site == 2:
            self.a = comiconline(query)
        elif site == 3:
            self.a = readcomiconline(query)
        self.searchLPage = self.a.get_last_page(query)
        self.clear_window(self.root)
        self.listResults(0,1)

    def listResults(self,curPage,newPage):
        newPage = int(newPage)
        if newPage not in self.searchFrames:
            self.searchFrames[newPage] = self.createFrame(newPage)
        
        if curPage != 0:
            self.searchFrames[curPage].pack_forget()
        self.searchFrames[newPage].pack()


    def createFrame(self,page):
        a = self.a
        root = self.root
        lpage = self.searchLPage
        
        minPage = page-2 if (page-2)>0 else 1
        maxPage = minPage+4 if minPage+4<=lpage else lpage

        outerFrame = Frame(root,highlightbackground='red',highlightthickness=2)
        innerFrame = Frame(outerFrame,width= 400,height=400,highlightbackground='blue',highlightthickness=2)

        for n,j in enumerate(range(minPage,maxPage+1)):
            nav = Button(outerFrame,text=str(j),command=lambda m = j: self.listResults(page,m))
            if j==page:
                nav['state'] = 'disabled'
            nav.grid(row=1,column=n)

        searchResults = a.searchResults

        if page not in searchResults:    
            searchResults[page] = a.get_search_titles(a.search_link+a.query)    
        
        for i in range(len(searchResults[page])):
            a.img_download(searchResults[page][i][2],str(page)+'_'+str(i),'downloads/temp/')
            titleFrame = Frame(innerFrame,highlightbackground='black',highlightthickness=2,width = 550,height=10,cursor='hand2')
            label = Label(titleFrame,text = searchResults[page][i][1])
            label.pack()
            titleFrame.bind('<Button-1>',lambda event,m = i:self.listChapters(searchResults[page][m][0]))
            label.bind('<Button-1>',lambda event,m = i:self.listChapters(searchResults[page][m][0]))
            titleFrame.grid(sticky=E+W,row=i,column=0)
            titleFrame.tkraise(aboveThis=label)
        innerFrame.grid(row=0,column=0,columnspan=5,pady=(0,50))
        return outerFrame

