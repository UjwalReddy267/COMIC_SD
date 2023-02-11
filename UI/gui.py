from Websites.comicextra import comicextra
from Websites.comiconline import comiconline
from Websites.readcomiconline import readcomiconline
from PyQt6.QtWidgets import *
import PyQt6.QtGui as qtg
from PyQt6 import uic,QtCore
import os

class MainWindow(QMainWindow):
    n = 0
    searcLPage = 0
    def __init__(self):
        super(MainWindow,self).__init__()
        self.show()  
    
    def start(self):
        uic.loadUi('UI/Start.ui',self)
        self.goButton.clicked.connect(self.go)

    def go(self):
        query = self.queryField.text()
        if '.' not in query and '/' not in query:
            self.siteSelect(query)
        else:
            self.parseLink(query)

    def siteSelect(self,query):
        #self.startFrame.hide()
        uic.loadUi('UI/SiteSelector.ui',self)
        self.siteDownload.clicked.connect(lambda:self.search(query))

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
            self.a.comic_dl([query])
    
    def listChapters(self,link):
        a = self.a
        soup = a.get_soup(link)
        comics,titles = a.get_chaps(soup)
        #self.siteSelectorFrame.hide()
        uic.loadUi('UI/chapterView.ui',self)
        for i in range(len(titles)):
            item = QListWidgetItem()
            item.setText(titles[i])
            self.chapterList.addItem(item)
        self.downChapButton.clicked.connect(lambda:self.downloadChaps(comics))


    def downloadChaps(self,comics):
        links = []
        try:
            for i in self.chapterList.selectedIndexes():
                links.append(comics[i.row()])
        except IndexError:
            pass
        self.a.comic_dl(links)

    def search(self,query):
        site = self.siteSelector.currentIndex()
        if site == 0:
            self.a = readcomiconline(query)
        elif site == 1:
            self.a = comicextra(query)
        elif site == 2:
            self.a = comiconline(query)
        self.listResults()
        
    
    def listResults(self):
        uic.loadUi('UI/searchResults.ui',self)
        self.navButtons = []
        self.searchLPage = self.a.get_last_page(self.a.query)
        self.showPage(1)

    def showPage(self,page):
        self.resultsList.clear()
        lPage = self.searchLPage
        minPage = page-2 if (page-2)>0 else 1
        maxPage = minPage+4 if minPage+4<=lPage else lPage
        for i in self.navButtons:
            self.horizontalLayout_2.removeWidget(i)
        
        self.navButtons = []
        
        navButton = QPushButton(parent = self.navBar)
        navButton.setMinimumSize(QtCore.QSize(30,30))
        navButton.setMaximumSize(QtCore.QSize(30,30))
        navButton.setText('<<')
        if page==1:
            navButton.setDisabled(True)
        navButton.clicked.connect(lambda :self.showPage(1))
        self.navButtons.append(navButton)
        self.horizontalLayout_2.addWidget(navButton)
        


        for i in range(minPage,maxPage+1):
            
            navButton = QPushButton(parent = self.navBar)
            
            navButton.setMinimumSize(QtCore.QSize(30,30))
            navButton.setMaximumSize(QtCore.QSize(30,30))
            navButton.setText(str(i))
            if i==page:
                navButton.setDisabled(True)
            self.horizontalLayout_2.addWidget(navButton)
            self.navButtons.append(navButton)
            navButton.clicked.connect(lambda state ,m = i:self.showPage(m))
        
        navButton = QPushButton(parent = self.navBar)
        navButton.setMinimumSize(QtCore.QSize(30,30))
        navButton.setMaximumSize(QtCore.QSize(30,30))
        navButton.setText('>>')
        navButton.clicked.connect(lambda :self.showPage(lPage))
        if page==lPage:
            navButton.setDisabled(True)
        self.horizontalLayout_2.addWidget(navButton)
        self.navButtons.append(navButton)

        if page not in self.a.searchResults.keys():
            self.a.get_search_titles(page)

        for n,comic in enumerate(self.a.searchResults[page]):
            if not os.path.exists(f'downloads/temp/{page}_{n}'):
                self.a.img_download(comic[2],f'{page}_{n}','downloads/temp/')
            item = QListWidgetItem()
            icon = qtg.QIcon()
            icon.addPixmap(qtg.QPixmap(f"downloads/temp/{page}_{n}.jpg"), qtg.QIcon.Mode.Active, qtg.QIcon.State.On)
            item.setIcon(icon)
            size = QtCore.QSize(100,100)
            self.resultsList.setIconSize(size)
            item.setText(comic[1])
            item.setData(3,comic[0])
            self.resultsList.addItem(item)

        self.resultsList.itemClicked.connect(self.comicSelected)
    
    def comicSelected(self,clickedItem):
        self.listChapters(clickedItem.data(3))
