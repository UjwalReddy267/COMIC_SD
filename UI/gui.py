from Websites.comicextra import comicextra
from Websites.comiconline import comiconline
from Websites.readcomiconline import readcomiconline
from PyQt6.QtWidgets import *
import PyQt6.QtGui as qtg
from PyQt6 import uic
from PyQt6.QtCore import *
import urllib.parse
import sys
import json
import requests
import shutil
from zipfile import ZipFile

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


class Runnable(QRunnable):
    def __init__(self,links,n):
        super().__init__()
        self.n = n
        self.links = links
        self.progress = 0

    def run(self):
        for i,src in enumerate(self.links):
            res = requests.get(src, stream = True)
            with open('downloads/temp/'+str(self.n+i)+'.jpg','wb') as f:
                shutil.copyfileobj(res.raw, f)
            self.progress+=1


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    pagesProgress = pyqtSignal(int)
    error = pyqtSignal(int)
    downloadProgress = pyqtSignal(int,int)

    def __init__(self):
        super().__init__()
        self._stop = False

    def download(self):
        comics = self.comics
        for n,comic in enumerate(comics):
            err,images,title = self.a.comic_dl(comic)
            if err!=1:
                self.error.emit(err)
                return
            threadCount = min(QThreadPool.globalInstance().maxThreadCount()//2,4)
            pool = QThreadPool.globalInstance()
            runnables = []
            l = len(images)
            t = threadCount
            index = [i*(l//t)+min(i,l%t) for i in range(t+1)]
            for i in range(threadCount):
                runnable = Runnable(images[index[i]:index[i+1]],index[i])
                runnables.append(runnable)
                pool.start(runnable)
            progress = 0
            while progress<100:
                progress = 0
                for runnable in runnables:
                    progress += runnable.progress
                progress = (100*progress)//len(images)
                self.downloadProgress.emit(n,progress)
            fil = ZipFile('downloads/'+title+'.cbr','w')
            for i in range(len(images)):
                fil.write('downloads/temp/'+str(i)+'.jpg')
            fil.close()
            self.progress.emit(100*(n+1)//len(comics))
        self.finished.emit()


    def lastPage(self):
        err = self.a.get_last_page(self.a.query)
        if err!=1:
            self.error.emit(err)
            return
        self.finished.emit()


    def search(self):
        for i in range(1,self.a.lPage+1):
            if self._stop:
                break
            if i not in self.a.searchResults.keys():
                err = self.a.get_search_titles(i)
                if err != 1:
                    self.error.emit(err)
                    return
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
        while page not in self.a.searchResults:
            pass
        for i in range(len(self.a.searchResults[page])):
            if self._stop:
                break
            if i not in self.a.downloadedImages[page]:
                err = self.a.img_download(self.a.searchResults[page][i][2],f'{page}_{i}','downloads/temp/')
                if err == -1:
                    self.error.emit(-1)
                    return
                self.a.downloadedImages[page].append(i)
            self.progress.emit(i)
        if emit == True:
            self.finished.emit()
            

    def chapters(self):
        err = self.a.get_chaps(self.link)
        if err != 1:
            self.error.emit(err)
            return
        self.finished.emit()


class MainWindow(QMainWindow):
    page = 0
    def __init__(self,json):
        super().__init__()
        if json:
            self.json = json
        else:
            self.json = sys_path+'UI\\colors.json'
        self.setGeometry(370,50,800,100)
        font = qtg.QFont()
        font.setStyleName('Helvetica')
        self.setFont(font)
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
        self.verticalLayout.setContentsMargins(0,0,0,0)
        self.mainStack = self.stack.mainStack
        widget.setLayout(self.verticalLayout)
        
        self.homeButton = self.stack.homeButton
        self.downloadButton = self.stack.downloadButton
        self.backButton = self.stack.backButton
        self.homeButton.clicked.connect(self.reset)
        
        self.startFrame = startFrame()
        self.chaptersFrame = chaptersFrame()
        self.searchFrame = searchFrame()
        self.downloadsFrame = downloadsFrame()

        self.mainStack.addWidget(self.startFrame)
        self.mainStack.addWidget(self.chaptersFrame)
        self.mainStack.addWidget(self.searchFrame)
        self.mainStack.addWidget(self.downloadsFrame)
        self.setColors()
        self.show()  
    
    def setColors(self):
        self.colors = json.load(open(self.json))
        self.stack.setStyleSheet(self.colors['mainFrame'])
        self.chaptersFrame.setStyleSheet(self.colors['chaptersView'])
        self.searchFrame.setStyleSheet(self.colors['resultsView'])
        self.downloadsFrame.setStyleSheet(self.colors['downloadsView']+self.colors['progressBar'])


    def reset(self):
        self.centralWidget().deleteLater()
        for i in self.worker:
            try:
                if i in self.worker:
                    eventLoop = QEventLoop()
                    self.worker[i]._stop = True
                    while self.thread[i].isRunning():
                        eventLoop.processEvents()
            except RuntimeError:
                pass
        self.fillStack()
        self.start()

    def start(self):
        self.mainStack.setCurrentIndex(0)
        self.startFrame.siteSelector.hide()
        self.startFrame.goButton.clicked.connect(self.go)
        self.homeButton.hide()
        self.downloadButton.hide()
        self.backButton.hide()


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
            err,title = self.a.format_title(None,query,ret=True)
            if err == -1:
                self.handleError(-1)
            else:
                self.downloadChaps([query],set_pbar=False)
                self.downloadsFrame.downloadNameLabel.setText(title)
                self.mainStack.setCurrentIndex(3)


    def getChaps(self,link,back = False):
        if back:
            self.backButton.clicked.connect(lambda:self.showPage(self.page))
        self.chaptersFrame.chapterList.clear()
        self.chaptersFrame.comicNameLabel.setText('Loading...')
        self.chaptersFrame.coverImageLabel.clear()
        self.mainStack.setCurrentIndex(1)
        try:
            eventLoop = QEventLoop()
            self.worker[1]._stop = True
            while self.thread[1].isRunning():
                eventLoop.processEvents()
        except (RuntimeError,KeyError):
            pass
        self.createThread(1)
        self.worker[1].a = self.a
        self.worker[1].link = link
        self.thread[1].started.connect(self.worker[1].chapters)
        self.worker[1].finished.connect(lambda:self.listChapters(back))
        self.thread[1].start()


    def listChapters(self,back):
        if back:
            self.backButton.show()
        self.homeButton.show()
        name,chapters,titles = self.a.chapters
        #Check if button is connected
        try:
            self.downloadButton.clicked.disconnect()
        except TypeError:
            pass

        a = self.a        
        self.chaptersFrame.coverImageLabel.setPixmap(qtg.QPixmap("downloads/temp/cover.jpg").scaled(self.chaptersFrame.coverImageLabel.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        self.chaptersFrame.comicNameLabel.setText(urllib.parse.unquote(name))
        self.downloadButton.show()
        self.downloadButton.clicked.connect(lambda:self.selectedChapters(name))
        
        self.chaptersFrame.chapterList.setIconSize(QSize(15,15))
        for i in range(len(titles)):
            item = QListWidgetItem()
            item.setText(titles[i])
            item.setData(3,chapters[i])
            icon = qtg.QIcon()
            icon.addPixmap(qtg.QPixmap(sys_path+'UI\\agenda.png'),qtg.QIcon.Mode.Active, qtg.QIcon.State.On)
            item.setIcon(icon)
            self.chaptersFrame.chapterList.addItem(item)
    

    def selectedChapters(self,name):
        if not self.backButton.isHidden():
            self.backButton.hide()
        titles = [i.text() for i in self.chaptersFrame.chapterList.selectedItems()]
        links = [i.data(3) for i in self.chaptersFrame.chapterList.selectedItems()]
        self.mainStack.setCurrentIndex(3)
        self.downloadsFrame.downloadNameLabel.setText(name)
        self.downloadChaps(links,titles)
    

    def downloadChaps(self,links,titles=None,set_pbar=True):
        self.homeButton.hide()
        self.downloadButton.hide()
        pBars = []
        if set_pbar:
            for i in range(len(links)):
                pBars.append(self.addPBar(titles[i]))
        else:
            pBars.append(self.downloadsFrame.mainProgressBar)
        eventLoop = QEventLoop()
        try:
            if 2 in self.worker:
                self.worker[2]._stop = True
                while self.thread[2].isRunning():
                    eventLoop.processEvents()
        except RuntimeError:
            pass
        self.createThread(1)
        self.worker[1].a = self.a
        self.worker[1].comics = links
        self.worker[1].downloadProgress.connect(lambda i,n:pBars[i].setValue(n))
        self.worker[1].progress.connect(lambda i:self.downloadsFrame.mainProgressBar.setValue(i))
        self.thread[1].started.connect(self.worker[1].download)
        self.thread[1].start()
        self.worker[1].finished.connect(self.homeButton.show)


    def search(self,query):
        site = self.startFrame.siteSelector.currentIndex()
        self.startFrame.siteSelector.setDisabled(True)
        self.startFrame.goButton.setDisabled(True)
        self.homeButton.setDisabled(True)
        self.startFrame.startLabel.setText('Loading...')
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

        self.navButtons = []
        self.imgUpPage = 0
        self.createThread(1)
        self.worker[1].a = self.a
        self.thread[1].started.connect(self.worker[1].lastPage)
        self.thread[1].finished.connect(self.getSearchResults)
        self.thread[1].finished.connect(lambda:self.homeButton.setDisabled(False))
        self.worker[1].finished.connect(self.showPage)
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
    

    def showPage(self,page=1):
        if not self.backButton.isHidden():
            self.backButton.hide()
        if not self.downloadButton.isHidden():
            self.downloadButton.hide()
        try:
            self.searchFrame.resultsList.itemClicked.disconnect()
        except TypeError:
            pass
        try:
            eventLoop = QEventLoop()
            self.worker[1]._stop = True
            i=0
            while self.thread[1].isRunning():
                eventLoop.processEvents()
                i+=1
                print(f'Waiting:{i}')
        except RuntimeError:
            pass
        self.page = page
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
            self.addNavButton(text = '<<',page = 1,disabled=False)
        else:
            self.addNavButton(text = '<<',page = 1,disabled=False)
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
            brush = qtg.QBrush(qtg.QColor(255,255,255))
            brush.setStyle(Qt.BrushStyle.SolidPattern)
            item.setForeground(brush)
            item.setData(3,comic[0])
            #item.
            self.searchFrame.resultsList.addItem(item)
            self.addIcon(page,n,3)
        #Wait for search results of page
        while page not in self.a.searchResults.keys():
            pass
        #Get images of search results
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
        navButton.setMinimumSize(QSize(30,30))
        navButton.setMaximumSize(QSize(30,30))
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
            icon = qtg.QIcon()
            icon.addPixmap(img, qtg.QIcon.Mode.Active, qtg.QIcon.State.On)
            self.searchFrame.resultsList.item(index).setIcon(icon)
            size = QSize(100,100)
            self.searchFrame.resultsList.setIconSize(size)


    def createThread(self,n):
        self.thread[n] = QThread()
        self.worker[n] = Worker()
        self.worker[n].moveToThread(self.thread[n])
        self.worker[n].finished.connect(self.thread[n].quit)
        self.thread[n].finished.connect(self.thread[n].deleteLater)
        self.worker[n].finished.connect(self.worker[n].deleteLater)
        self.worker[n].error.connect(self.handleError)
        self.worker[n].error.connect(self.thread[n].quit)

      
    def addPBar(self,name):
        horizontalLayout = QHBoxLayout()
        label = QLabel(parent=self.downloadsFrame)
        label.setObjectName(name)
        label.setMinimumSize(QSize(200, 25))
        label.setMaximumSize(QSize(300, 25))
        label.setText(name)
        label.setWordWrap(True)
        font = qtg.QFont()
        font.setPointSize(12)
        label.setFont(font)
        horizontalLayout.addWidget(label)
        progressBar = QProgressBar(parent=self.downloadsFrame,value=0)
        progressBar.setMinimumSize(QSize(50, 25))
        progressBar.setMaximumSize(QSize(300, 25))
        progressBar.setStyleSheet(self.colors['progressBar'])
        spacer  = QSpacerItem(40,20,QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        horizontalLayout.addWidget(progressBar)
        horizontalLayout.addItem(spacer)
        widget = QWidget()
        widget.setLayout(horizontalLayout)
        item = QListWidgetItem()
        item.setSizeHint(QSize(100,50))
        self.downloadsFrame.progressList.addItem(item)
        self.downloadsFrame.progressList.setItemWidget(item,widget)
        return progressBar

    def handleError(self,err):
        if self.mainStack.currentIndex !=0:
            self.mainStack.setCurrentIndex(0)
        self.startFrame.siteSelector.hide()
        self.startFrame.queryField.hide()
        self.startFrame.goButton.hide()
        self.homeButton.setDisabled(False)
        if err == -1:
            self.startFrame.startLabel.setText('Connection Error. Try again later')
        elif err == 0:
            self.startFrame.startLabel.setText('Not found')
