from Websites.comicextra import comicextra
from Websites.comiconline import comiconline
from Websites.readcomiconline import readcomiconline
from PyQt6.QtWidgets import *
import PyQt6.QtGui as qtg
from PyQt6 import uic,QtCore
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QEventLoop
import urllib.parse
import sys

try:
    sys_path = sys._MEIPASS+'\\'
except AttributeError:
    sys_path = ''
class startFrame(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        uic.loadUi(sys_path+'UI\\start.ui',self)


class chaptersFrame(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        uic.loadUi(sys_path+'UI\\ChaptersView.ui',self)


class searchFrame(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        uic.loadUi(sys_path+'UI\\searchResults.ui',self)


class downloadsFrame(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        uic.loadUi(sys_path+'UI\\download.ui',self)

class stack(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        uic.loadUi(sys_path+'UI\\stack.ui',self)


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
            if not self._stop:
                break
            if i not in self.a.searchResults.keys():
                self.a.get_search_titles(i)
        for i in range(1,self.a.lPage+1):
            if self._stop:
                break
            if i not in self.a.downloadedImages:
                self.page = i
                self.searchPageImages(False)
            self.pagesProgress.emit(i)
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
            self.finished.emit()
            

    def chapters(self):
        self.a.get_chaps(self.link)
        self.finished.emit()


class MainWindow(QMainWindow):
    page = 0
    def __init__(self):
        super().__init__()
        self.setGeometry(350,100,800,500)
        self.fillStack()

    def fillStack(self):
        self.thread = {}
        self.worker = {}
        self.navButtons = []
        self.pageUpd = 0

        widget = QWidget(self)
        self.setCentralWidget(widget)
        self.verticalLayout = QVBoxLayout()
        self.stack = stack()
        self.verticalLayout.addWidget(self.stack)
        self.mainStack = self.stack.mainStack
        widget.setLayout(self.verticalLayout)
        
        self.homeButton = self.stack.homeButton
        self.downloadButton = self.stack.downloadButton
        self.homeButton.clicked.connect(self.reset)
        
        self.startFrame = startFrame()
        self.chaptersFrame = chaptersFrame()
        self.searchFrame = searchFrame()
        self.downloadsFrame = downloadsFrame()

        self.mainStack.addWidget(self.startFrame)
        self.mainStack.addWidget(self.chaptersFrame)
        self.mainStack.addWidget(self.searchFrame)
        self.mainStack.addWidget(self.downloadsFrame)
        self.show()  

    def reset(self):
        for i in self.worker:
            try:
                if i in self.worker:
                    eventLoop = QEventLoop()
                    self.worker[i]._stop = True
                    while self.thread[i].isRunning():
                        eventLoop.processEvents()
            except RuntimeError:
                pass

        
        self.centralWidget().deleteLater
        self.fillStack()
        self.start()

    def start(self):
        self.mainStack.setCurrentIndex(0)
        self.startFrame.siteSelector.hide()
        self.startFrame.goButton.clicked.connect(self.go)
        self.homeButton.hide()
        self.downloadButton.hide()


    def go(self):
        self.homeButton.show()
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
            self.getChaps(query)
        else:
            title = self.a.getTitle(query)
            self.downloadChaps([query],set_pbar=False)
            self.downloadsFrame.downloadNameLabel.setText(title)
            self.mainStack.setCurrentIndex(3)


    def getChaps(self,link,back = False):
        self.homeButton.hide()
        self.chaptersFrame.backButton.setDisabled(True)
        if back == False:
            self.chaptersFrame.backButton.hide()
        else:
            #self.chaptersFrame.backButton.clicked.connect(lambda:self.mainStack.setCurrentIndex(2))
            self.chaptersFrame.backButton.clicked.connect(lambda:self.showPage(self.page))
        self.chaptersFrame.chapterList.clear()
        self.chaptersFrame.comicNameLabel.setText('Loading...')
        self.chaptersFrame.coverImageLabel.clear()
        self.mainStack.setCurrentIndex(1)
        try:
            self.worker[1]._stop = True
            while self.thread[1].isRunning():
                self.eventLoop.processEvents()
        except (RuntimeError,KeyError):
            pass
        self.createThread(1)
        self.worker[1].a = self.a
        self.worker[1].link = link
        self.thread[1].started.connect(self.worker[1].chapters)
        self.worker[1].finished.connect(lambda:self.listChapters())
        self.thread[1].start()


    def listChapters(self):
        self.chaptersFrame.backButton.setDisabled(False)
        self.homeButton.show()
        #self.homeButton.show()
        name,chapters,titles = self.a.chapters
        #Check if button is connected
        try:
            self.downloadButton.clicked.disconnect()
            #self.chaptersFrame.downChapButton.clicked.disconnect()
        except TypeError:
            pass

        a = self.a        
        self.chaptersFrame.coverImageLabel.setPixmap(qtg.QPixmap("downloads/temp/cover.jpg").scaled(self.chaptersFrame.coverImageLabel.size(),QtCore.Qt.AspectRatioMode.KeepAspectRatio,QtCore.Qt.TransformationMode.SmoothTransformation))
        self.chaptersFrame.comicNameLabel.setText(urllib.parse.unquote(name))

        font = qtg.QFont()
        font.setPointSize(12)
        self.chaptersFrame.chapterList.setFont(font)
        #self.chaptersFrame.downChapButton.clicked.connect(lambda:self.selectedChapters(name))
        self.downloadButton.show()
        self.downloadButton.clicked.connect(lambda:self.selectedChapters(name))
        
        
        for i in range(len(titles)):
            item = QListWidgetItem()
            item.setText(titles[i])
            item.setData(3,chapters[i])
            self.chaptersFrame.chapterList.addItem(item)
        #self.homeButton.clicked.connect(self.downloadButton.hide)
        #self.homeButton.clicked.connect(self.homeButton.hide)
    

    def selectedChapters(self,name):
        titles = [i.text() for i in self.chaptersFrame.chapterList.selectedItems()]
        links = [i.data(3) for i in self.chaptersFrame.chapterList.selectedItems()]
        self.mainStack.setCurrentIndex(3)
        self.downloadsFrame.downloadNameLabel.setText(name)
        self.downloadChaps(links,titles,0)
    

    def downloadChaps(self,links,titles=None,n=0,set_pbar=True):
        self.homeButton.hide()
        self.downloadButton.hide()
        if set_pbar:
            pBar = self.addPBar(titles[n])
        else:
            pBar = self.downloadsFrame.mainProgressBar
        self.createThread(1)
        self.worker[1].a = self.a
        self.worker[1].link = links[n]
        self.thread[1].started.connect(self.worker[1].download)
        self.worker[1].progress.connect(lambda a:pBar.setValue(a))
        if n < len(links)-1:
            self.thread[1].finished.connect(lambda:self.downloadChaps(links,titles,n+1))
        if n==len(links)-1:
            self.thread[1].finished.connect(self.homeButton.show)
        self.thread[1].finished.connect(lambda:self.downloadsFrame.mainProgressBar.setValue(int(100*(n+1)/len(links))))        
        self.thread[1].start()


    def search(self,query):
        site = self.startFrame.siteSelector.currentIndex()
        self.startFrame.siteSelector.setDisabled(True)
        self.startFrame.goButton.setDisabled(True)
        self.homeButton.setDisabled(True)
        self.startFrame.startLabel.setText('Loading')
        if site == 0:
            self.a = readcomiconline(query)
        elif site == 1:
            self.a = comicextra(query)
        elif site == 2:
            self.a = comiconline(query)
        self.getLastPage()


    def getLastPage(self):
        
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
        self.thread[1].finished.connect(self.getSearchResults)
        self.thread[1].finished.connect(lambda:self.homeButton.setDisabled(False))
        self.thread[1].finished.connect(lambda:self.showPage(1))
        self.thread[1].start()


    def getSearchResults(self):
        self.createThread(2)
        self.worker[2].a = self.a
        self.worker[2].calledBy = 1
        self.thread[2].started.connect(self.worker[2].search)
        self.worker[2].pagesProgress.connect(self.updImgInd)
        self.worker[2].progress.connect(lambda index:self.addIcon(self.pageUpd,index,1))
        self.thread[2].start()
    

    def updImgInd(self,n):
        self.pageUpd = n
    

    def showPage(self,page):

        if not self.downloadButton.isHidden():
            self.downloadButton.hide()
        try:
            self.searchFrame.resultsList.itemClicked.disconnect()
        except TypeError:
            pass
        self.eventLoop = QEventLoop()
        self.page = page
        if self.a.lPage == 0:
            #Quit if no results. Will add 404 page later
            QtCore.QCoreApplication.instance().quit()
        #Change to results page
        self.mainStack.setCurrentIndex(2)
        #Clear results
        self.searchFrame.resultsList.clear()
        lPage = self.a.lPage
        #Calculate the indices of last and first nav buttons
        minPage = page-2 if (page-2)>0 else 1
        maxPage = minPage+4 if minPage+4<=lPage else lPage
        minPage = maxPage-4 if maxPage-minPage<4 and maxPage-4>0 else minPage
        
        #Delete all nav buttons
        for i in self.navButtons:
            self.searchFrame.horizontalLayout_2.removeWidget(i)
        
        self.navButtons = []
        #Add << button
        if page==1:
            navButton = self.addNavButton(text = '<<',page = 1,disabled=False)
        else:
            navButton = self.addNavButton(text = '<<',page = 1,disabled=False)
        #Add page buttons
        for i in range(minPage,maxPage+1):
            if i==page:
                self.addNavButton(str(i),i,True)
            else:
                self.addNavButton(str(i),i,False)
        #Add >> button
        if page==lPage:
            self.addNavButton('>>',lPage,True)
        else:
            self.addNavButton('>>',lPage,False)
        #Add search results
        for n,comic in enumerate(self.a.searchResults[page]):
            self.searchItems = []
            item = QListWidgetItem()
            item.setText(comic[1])
            item.setData(3,comic[0])
            self.searchFrame.resultsList.addItem(item)
            self.addIcon(page,n,3)

        #Wait for search results of page
        while page not in self.a.searchResults.keys():
            pass
        #Get images of search results
        try:
            self.worker[1]._stop = True
            while self.thread[1].isRunning():
                self.eventLoop.processEvents()
        except RuntimeError:
            pass

        if page not in self.a.downloadedImages or (page in self.a.downloadedImages and len(self.a.downloadedImages[page])!=self.a.searchResults[page]):
            self.createThread(1)
            self.worker[1].a = self.a
            self.worker[1].page = page
            self.thread[1].started.connect(self.worker[1].searchPageImages)
            self.worker[1].progress.connect(lambda index:self.addIcon(page,index,2))
            self.thread[1].start()
        self.searchFrame.resultsList.itemClicked.connect(self.comicSelected)

    def comicSelected(self,clickedItem):
        self.getChaps(clickedItem.data(3),back=True)
    

    def addNavButton(self,text,page,disabled):
        navButton = QPushButton(parent = self.searchFrame.navBar)
        navButton.setText(text)
        navButton.setMinimumSize(QtCore.QSize(30,30))
        navButton.setMaximumSize(QtCore.QSize(30,30))
        navButton.clicked.connect(lambda :self.showPage(page))
        navButton.setDisabled(disabled)
        self.navButtons.append(navButton)
        self.searchFrame.horizontalLayout_2.addWidget(navButton)


    def addIcon(self,page,index,called):
        if page == self.page:
            if page not in self.a.downloadedImages or (page in self.a.downloadedImages and index not in self.a.downloadedImages[page]):
                path = sys_path+"UI\\load.png"
            else:
                path = f"downloads/temp/{page}_{index}.jpg"
            img = qtg.QPixmap(path)
            item = self.searchFrame.resultsList.item(index)
            icon = qtg.QIcon()
            icon.addPixmap(img, qtg.QIcon.Mode.Active, qtg.QIcon.State.On)
            self.searchFrame.resultsList.item(index).setIcon(icon)
            size = QtCore.QSize(100,100)
            self.searchFrame.resultsList.setIconSize(size)


    def createThread(self,n):
        self.thread[n] = QThread()
        self.worker[n] = Worker()
        self.worker[n].moveToThread(self.thread[n])
        self.worker[n].finished.connect(self.thread[n].quit)
        self.thread[n].finished.connect(self.thread[n].deleteLater)
        self.worker[n].finished.connect(self.worker[n].deleteLater)

      
    def addPBar(self,name):
        horizontalLayout = QHBoxLayout()
        label = QLabel(parent=self.downloadsFrame.scrollAreaWidgetContents)
        label.setObjectName(name)
        label.setMinimumSize(QtCore.QSize(200, 25))
        label.setMaximumSize(QtCore.QSize(300, 25))
        label.setText(name)
        label.setWordWrap(True)
        font = qtg.QFont()
        font.setPointSize(12)
        label.setFont(font)
        horizontalLayout.addWidget(label)
        progressBar = QProgressBar(parent=self.downloadsFrame.scrollAreaWidgetContents,value=0)
        progressBar.setMinimumSize(QtCore.QSize(50, 25))
        progressBar.setMaximumSize(QtCore.QSize(300, 25))
        horizontalLayout.addWidget(progressBar)
        self.downloadsFrame.verticalLayout.addLayout(horizontalLayout)
        return progressBar