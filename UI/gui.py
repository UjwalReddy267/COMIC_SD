from Websites.comicextra import comicextra
from Websites.comiconline import comiconline
from Websites.readcomiconline import readcomiconline
from PyQt6.QtWidgets import *
import PyQt6.QtGui as qtg
from PyQt6 import uic,QtCore
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QEventLoop
import urllib.parse


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
            if not self._stop:
                break
            if i not in self.a.searchResults.keys():
                self.a.get_search_titles(i)
        
        for i in range(1,self.a.lPage+1):
            if not self._stop:
                break
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
            self.finished.emit()
            

    def chapters(self):
        print('Getting Chapters')
        self.a.get_chaps(self.link)
        print('Done Getting Chapters')
        self.finished.emit()


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

    def reset(self):
        try:
            if 2 in self.worker:
                eventLoop = QEventLoop()
                self.worker[2]._stop = True
                while self.thread[2].isRunning():
                    eventLoop.processEvents()
        except RuntimeError:
            pass

        for i in range(self.mainStack.count()):
            self.mainStack.removeWidget(self.mainStack.widget(i))
        
        self.mainStack.addWidget(self.startFrame)
        self.mainStack.addWidget(self.chaptersFrame)
        self.mainStack.addWidget(self.searchFrame)
        self.mainStack.addWidget(self.downloadsFrame)
        self.start()

    def start(self):
        self.mainStack.setCurrentIndex(0)
        print('Start')
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
            self.getChaps(query)
        else:
            title = self.a.getTitle(query)
            self.downloadChaps([query],set_pbar=False)
            self.downloadsFrame.downloadNameLabel.setText(title)
            self.mainStack.setCurrentIndex(3)



    def createThread(self,n):
        self.thread[n] = QThread()
        self.worker[n] = Worker()
        self.worker[n].moveToThread(self.thread[n])
        self.worker[n].finished.connect(self.thread[n].quit)
        self.thread[n].finished.connect(self.thread[n].deleteLater)
        self.worker[n].finished.connect(self.worker[n].deleteLater)


    def getChaps(self,link,back = False):
        print('Called1')
        if back == False:
            self.chaptersFrame.backButton.setDisabled(True)
            self.chaptersFrame.backButton.hide()
        else:
            self.chaptersFrame.backButton.clicked.connect(lambda:self.mainStack.setCurrentIndex(2))
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
        print('called')
        name,chapters,titles = self.a.chapters
        #Check if button is connected
        try:
            self.chaptersFrame.downChapButton.clicked.disconnect()
        except TypeError:
            pass

        a = self.a        
        self.chaptersFrame.coverImageLabel.setPixmap(qtg.QPixmap("downloads/temp/cover.jpg").scaled(self.chaptersFrame.coverImageLabel.size(),QtCore.Qt.AspectRatioMode.KeepAspectRatio,QtCore.Qt.TransformationMode.SmoothTransformation))
        self.chaptersFrame.comicNameLabel.setText(urllib.parse.unquote(name))

        font = qtg.QFont()
        font.setPointSize(12)
        self.chaptersFrame.chapterList.setFont(font)
        self.chaptersFrame.downChapButton.clicked.connect(lambda:self.selectedChapters(name))
        
        for i in range(len(titles)):
            item = QListWidgetItem()
            item.setText(titles[i])
            item.setData(3,chapters[i])
            self.chaptersFrame.chapterList.addItem(item)
    

    def selectedChapters(self,name):
        titles = [i.text() for i in self.chaptersFrame.chapterList.selectedItems()]
        links = [i.data(3) for i in self.chaptersFrame.chapterList.selectedItems()]
        self.mainStack.setCurrentIndex(3)
        self.downloadsFrame.downloadNameLabel.setText(name)
        self.downloadChaps(links,titles,0)
    

    def downloadChaps(self,links,titles=None,n=0,set_pbar=True):
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
            self.thread[1].finished.connect(lambda:self.downloadsFrame.downloadsHome.setEnabled(True))
            self.thread[1].finished.connect(lambda:self.downloadsFrame.downloadsHome.clicked.connect(self.reset))
        self.thread[1].finished.connect(lambda:self.downloadsFrame.mainProgressBar.setValue(int(100*(n+1)/len(links))))
        
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
        self.worker[2].pagesProgress.connect(self.updImgInd)
        self.worker[2].progress.connect(lambda index:self.addIcon(self.pageUpd,index,1))
        self.thread[2].start()
    

    def updImgInd(self,n):
        self.pageUpd = n
    

    def showPage(self,page):
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
        minPage = maxPage-4 if maxPage-minPage<4 and maxPage-minPage>0 else minPage
        
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

