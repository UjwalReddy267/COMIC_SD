from Websites.comicextra import comicextra
from Websites.comiconline import comiconline
from Websites.readcomiconline import readcomiconline
from PyQt6.QtWidgets import *
import PyQt6.QtGui as qtg
from PyQt6 import uic,QtCore
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QEventLoop
import urllib.parse
import time

class startFrame(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        uic.loadUi('UI/start.ui',self)

class chaptersFrame(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        uic.loadUi('UI/ChaptersView.ui',self)

class searchFrame(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        uic.loadUi('UI/searchResults.ui',self)

class downloadsFrame(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        uic.loadUi('UI/download.ui',self)

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    pagesProgress = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._stop = False
    def download(self):
        a = self.a
        link = self.link
        a.comic_dl(link,self.progress)
        self.finished.emit()
    
    def lastPage(self):
        self.a.get_last_page(self.a.query)
        self.finished.emit()
    
    def search(self):
        for i in range(1,self.a.lPage+1):
            if i not in self.a.searchResults.keys():
                self.a.get_search_titles(i)
        
        for i in range(1,self.a.lPage+1):
            self.pagesProgress.emit(i)
            if i not in self.a.downloadedImages:
                self.page = i
                self.searchPageImages(False)
        self.finished.emit()

    def searchPageImages(self,emit = True):
        page = self.page
        
        if page not in self.a.downloadedImages:
            self.a.downloadedImages[page] = []
        for i in range(len(self.a.searchResults[page])):
            if self._stop:
                break
            if i not in self.a.downloadedImages[page]:
                self.a.img_download(self.a.searchResults[page][i][2],f'{page}_{i}','downloads/temp/')
                self.a.downloadedImages[page].append(i)
            self.progress.emit(i)

        if emit == True:
            print('Broken')
            self.finished.emit()
            
            

    def chapters(self):
        pass


class MainWindow(QMainWindow):
    page = 0
    def __init__(self):
        super(MainWindow,self).__init__()
        uic.loadUi('UI/stack.ui',self)
        self.thread = {}
        self.worker = {}
        self.startFrame = startFrame()
        self.chaptersFrame = chaptersFrame()
        self.searchFrame = searchFrame()
        self.downloadsFrame = downloadsFrame()

        self.mainStack.addWidget(self.startFrame)
        self.mainStack.addWidget(self.chaptersFrame)
        self.mainStack.addWidget(self.searchFrame)
        self.mainStack.addWidget(self.downloadsFrame)
        self.show()  
    
    def start(self):
        self.startFrame.siteSelector.hide()
        self.startFrame.goButton.clicked.connect(self.go)

    def go(self):
        query = self.startFrame.queryField.text()
        if '.' not in query or '/' not in query:
            self.startFrame.queryField.setDisabled(True)
            self.startFrame.startLabel.setText('Select a website')
            self.startFrame.siteSelector.show()
            self.startFrame.goButton.clicked.connect(lambda:self.search(query))
        else:
            self.parseLink(query)


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

            pBar = self.addPBar('name')
            pBar.setValue(0)
            self.mainStack.setCurrentIndex(3)
        
            self.createThread(1)
            self.worker[1].a = self.a
            self.worker[1].link = query
            self.thread[1].started.connect(self.worker[1].download)
            self.worker[1].progress.connect(lambda a:pBar.setValue(a))
            self.thread[1].start()


    def createThread(self,n):
        print(f'Thread {n} created')
        self.thread[n] = QThread()
        self.worker[n] = Worker()
        self.worker[n].moveToThread(self.thread[n])
        self.worker[n].finished.connect(self.thread[n].quit)
        self.thread[n].finished.connect(self.thread[n].deleteLater)
        self.worker[n].finished.connect(self.worker[n].deleteLater)

    def listChapters(self,link,back=False):

        self.mainStack.setCurrentIndex(1)
        #Check if button is connected
        index = self.chaptersFrame.downChapButton.metaObject().indexOfMethod('clicked()')
        method = self.chaptersFrame.downChapButton.metaObject().method(index)
        if self.chaptersFrame.downChapButton.isSignalConnected(method):
            self.chaptersFrame.downChapButton.clicked.disconnect()

        a = self.a
        if back == False:
            self.chaptersFrame.backButton.setDisabled(True)
            self.chaptersFrame.backButton.hide()
        else:
            self.chaptersFrame.backButton.clicked.connect(lambda:self.mainStack.setCurrentIndex(2))

        name,chapters,titles = a.get_chaps(link)
        self.chaptersFrame.coverImageLabel.setPixmap(qtg.QPixmap("downloads/temp/cover.jpg").scaled(self.chaptersFrame.coverImageLabel.size(),QtCore.Qt.AspectRatioMode.KeepAspectRatio,QtCore.Qt.TransformationMode.SmoothTransformation))
        self.chaptersFrame.comicNameLabel.setText(urllib.parse.unquote(name))

        font = qtg.QFont()
        font.setPointSize(12)
        self.chaptersFrame.chapterList.setFont(font)
        self.chaptersFrame.downChapButton.clicked.connect(self.selectedChapters)
        for i in range(len(titles)):
            item = QListWidgetItem()
            item.setText(titles[i])
            item.setData(3,chapters[i])
            self.chaptersFrame.chapterList.addItem(item)
    
    def selectedChapters(self):
        
        titles = [i.text() for i in self.chaptersFrame.chapterList.selectedItems()]
        links = [i.data(3) for i in self.chaptersFrame.chapterList.selectedItems()]
        self.mainStack.setCurrentIndex(3)
        self.downloadChaps(links,titles,0)
    
    def downloadChaps(self,links,titles,n):
        pBar = self.addPBar(titles[n])
        self.createThread(1)
        self.worker[1].a = self.a
        self.worker[1].link = links[n]
        self.thread[1].started.connect(self.worker[1].download)
        self.worker[1].progress.connect(lambda a:pBar.setValue(a))
        if n < len(links)-1:
            self.thread[1].finished.connect(lambda:self.downloadChaps(links,titles,n+1))
        self.thread[1].start()

        
    def addPBar(self,name):
        horizontalLayout = QHBoxLayout()
        label = QLabel(parent=self.downloadsFrame.scrollAreaWidgetContents)
        label.setObjectName(name)
        label.setMinimumSize(QtCore.QSize(200, 25))
        label.setMaximumSize(QtCore.QSize(16777215, 25))
        label.setText(name)
        label.setWordWrap(True)
        horizontalLayout.addWidget(label)
        progressBar = QProgressBar(parent=self.downloadsFrame.scrollAreaWidgetContents,value=0)
        progressBar.setMinimumSize(QtCore.QSize(0, 25))
        progressBar.setMaximumSize(QtCore.QSize(16777215, 25))
        horizontalLayout.addWidget(progressBar)
        self.downloadsFrame.verticalLayout.addLayout(horizontalLayout)
        return progressBar


    def search(self,query):
        site = self.startFrame.siteSelector.currentIndex()
        self.startFrame.siteSelector.setDisabled(True)
        self.startFrame.goButton.setDisabled(True)
        self.startFrame.startLabel.setText('Loading')
        if site == 0:
            self.a = readcomiconline(query)
        elif site == 1:
            self.a = comicextra(query)
        elif site == 2:
            self.a = comiconline(query)
        self.listResults(1)
        
    
    def listResults(self,page):
        try:
            for i in self.navButtons:
                self.searchFrame.horizontalLayout_2.removeWidget(i)
        except AttributeError:
            pass
        
        font = qtg.QFont()
        font.setPointSize(12)
        self.searchFrame.resultsList.setFont(font)
        self.navButtons = []
        self.imgUpPage = 0
        self.createThread(1)
        self.worker[1].a = self.a
        self.thread[1].started.connect(self.worker[1].lastPage)
        self.thread[1].finished.connect(lambda:self.showPage(1))
        self.thread[1].finished.connect(self.getSearchResults)
        self.thread[1].start()

    def getSearchResults(self):
        self.createThread(2)
        self.worker[2].a = self.a
        self.worker[2].calledBy = 1
        self.thread[2].started.connect(self.worker[2].search)
        self.thread[2].pagesProgress(self.updImgInd)
        self.worker[2].progress.connect(lambda index:self.addIcon(self.pageUpd,index,1))
        self.worker[2].finished.connect(lambda:print('Search done'))
        self.thread[2].start()
    def updImgInd(self,n):
        self.pageUpd = n
    def showPage(self,page):
        self.eventLoop = QEventLoop()
        self.page = page
        if self.a.lPage == 0:
            QtCore.QCoreApplication.instance().quit()
        self.mainStack.setCurrentIndex(2)
        self.searchFrame.resultsList.clear()
        lPage = self.a.lPage
        minPage = page-2 if (page-2)>0 else 1
        maxPage = minPage+4 if minPage+4<=lPage else lPage
        minPage = maxPage-4 if maxPage-minPage<4 and maxPage-minPage>0 else minPage
        
        for i in self.navButtons:
            self.searchFrame.horizontalLayout_2.removeWidget(i)
        
        self.navButtons = []
        navButton = QPushButton(parent = self.searchFrame.navBar)
        navButton.setMinimumSize(QtCore.QSize(30,30))
        navButton.setMaximumSize(QtCore.QSize(30,30))
        navButton.setText('<<')
        if page==1:
            navButton.setDisabled(True)
        navButton.clicked.connect(lambda :self.showPage(1))
        self.navButtons.append(navButton)
        self.searchFrame.horizontalLayout_2.addWidget(navButton)
        
        for i in range(minPage,maxPage+1):
            
            navButton = QPushButton(parent = self.searchFrame.navBar)
            navButton.setMinimumSize(QtCore.QSize(30,30))
            navButton.setMaximumSize(QtCore.QSize(30,30))
            navButton.setText(str(i))
            if i==page:
                navButton.setDisabled(True)
            self.searchFrame.horizontalLayout_2.addWidget(navButton)
            self.navButtons.append(navButton)
            navButton.clicked.connect(lambda state ,m = i:self.showPage(m))
        
        navButton = QPushButton(parent = self.searchFrame.navBar)
        navButton.setMinimumSize(QtCore.QSize(30,30))
        navButton.setMaximumSize(QtCore.QSize(30,30))
        navButton.setText('>>')
        navButton.clicked.connect(lambda :self.showPage(lPage))
        if page==lPage:
            navButton.setDisabled(True)
        self.searchFrame.horizontalLayout_2.addWidget(navButton)
        self.navButtons.append(navButton)

        for n,comic in enumerate(self.a.searchResults[page]):
            self.searchItems = []
            item = QListWidgetItem()
            item.setText(comic[1])
            item.setData(3,comic[0])
            self.searchFrame.resultsList.addItem(item)
            self.addIcon(page,n,3)

        while page not in self.a.searchResults.keys():
            pass
        
        try:
            self.worker[1].progress.connect(lambda index:self.addIcon(page,index,2))
            self.worker[1]._stop = True
            while self.thread[1].isRunning():
                self.eventLoop.processEvents()
        except RuntimeError:
            pass

        if page not in self.a.downloadedImages or (page in self.a.downloadedImages and len(self.a.downloadedImages[page])!=self.a.searchResults[page]):
            print('Here')
            self.createThread(1)
            self.worker[1].a = self.a
            self.worker[1].page = page
            self.thread[1].started.connect(self.worker[1].searchPageImages)
            self.worker[1].progress.connect(lambda index:self.addIcon(page,index,2))
            self.worker[1].finished.connect(lambda:print('Thread 1 destroyed'))
            self.thread[1].start()
        
        
        self.searchFrame.resultsList.itemClicked.connect(self.comicSelected)

    def comicSelected(self,clickedItem):
        self.listChapters(clickedItem.data(3),back=True)
    
    def addIcon(self,page,index,called):
        
        if page == self.page:
            print(f'Called By: {called} for page {page} index {index}')
            if page not in self.a.downloadedImages or (page in self.a.downloadedImages and index not in self.a.downloadedImages[page]):
                path = f"UI/load.png"
            else:
                path = f"downloads/temp/{page}_{index}.jpg"
            img = qtg.QPixmap(path)
            item = self.searchFrame.resultsList.item(index)
            icon = qtg.QIcon()
            icon.addPixmap(img, qtg.QIcon.Mode.Active, qtg.QIcon.State.On)
            self.searchFrame.resultsList.item(index).setIcon(icon)
            size = QtCore.QSize(100,100)
            self.searchFrame.resultsList.setIconSize(size)

