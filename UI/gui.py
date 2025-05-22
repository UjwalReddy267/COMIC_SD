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
import time

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
            if self._stop:
                self.finished.emit()
                return
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
            # Ensure self._stop is checked in this loop too
            while progress<100 and not self._stop:
                progress = 0
                all_runnables_finished = True
                for runnable in runnables:
                    progress += runnable.progress
                    if hasattr(runnable, 'links') and runnable.progress < len(runnable.links): # Assuming runnable.links exists
                        all_runnables_finished = False
                
                if images: # Avoid division by zero if images is empty
                    current_progress = (100*progress)//len(images) if len(images) > 0 else 100
                else:
                    current_progress = 100

                self.downloadProgress.emit(n,current_progress)
                
                # Break if all runnables are done or if _stop is signaled
                if all_runnables_finished and progress >= len(images):
                    break
                if self._stop: # Check stop flag here to exit loop early
                    self.finished.emit()
                    return
                QThread.msleep(100) # Small delay to avoid tight loop, let other events process

            if self._stop: # Check again before file operations
                self.finished.emit()
                return

            fil = ZipFile('downloads/'+title+'.cbr','w')
            for i in range(len(images)):
                if self._stop: # Check before each write operation
                    fil.close() # Attempt to close the zip file
                    # Potentially delete partially created zip file if required
                    self.finished.emit()
                    return
                fil.write('downloads/temp/'+str(i)+'.jpg')
            fil.close()
            if self._stop:
                self.finished.emit()
                return
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
                self.finished.emit()
                return
            if i not in self.a.searchResults.keys():
                err = self.a.get_search_titles(i)
                if err != 1:
                    self.error.emit(err)
                    return
        for i in range(1,self.a.lPage+1):
            if self._stop:
                self.finished.emit()
                return
            if i not in self.a.downloadedImages:
                self.page = i
                self.searchPageImages(False)
            self.pagesProgress.emit(i)
        self.finished.emit()


    def searchPageImages(self,emit = True):
        page = self.page
        if page not in self.a.downloadedImages:
            self.a.downloadedImages[page] = []

        # Wait for searchResults to be populated, but check _stop flag
        max_wait_time_ms = 30000  # Max wait 30 seconds for results to appear
        current_wait_time_ms = 0
        wait_interval_ms = 100

        while page not in self.a.searchResults:
            if self._stop:
                if emit: self.finished.emit()
                return
            if current_wait_time_ms >= max_wait_time_ms:
                self.error.emit(-2) # Indicate a timeout or missing data error
                return
            QThread.msleep(wait_interval_ms)
            current_wait_time_ms += wait_interval_ms
            
        # Ensure page is still in searchResults after waiting, in case of race conditions or changes
        if page not in self.a.searchResults: 
            self.error.emit(-2) # Indicate a timeout or missing data error
            return

        for i in range(len(self.a.searchResults[page])):
            if self._stop:
                if emit:
                    self.finished.emit()
                return
            if i not in self.a.downloadedImages[page]:
                # Check _stop before potentially long blocking call
                if self._stop:
                    if emit: self.finished.emit()
                    return
                err = self.a.img_download(self.a.searchResults[page][i][2],f'{page}_{i}','downloads/temp/')
                if err == -1: # Connection error from img_download
                    self.error.emit(-1)
                    return
                elif err == -2 and self._stop: # Assuming img_download might return a specific code if interrupted by _stop
                    if emit: self.finished.emit()
                    return
                self.a.downloadedImages[page].append(i)
            self.progress.emit(i)
        if emit:
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
        self.homeButton.clicked.connect(lambda:self.mainStack.setCurrentIndex(0))
        self.homeButton.clicked.connect(lambda:self.homeButton.hide())
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
        self.downloadsFrame.setStyleSheet(self.colors['startFrame'])
        self.chaptersFrame.setStyleSheet(self.colors['chaptersView'])
        self.searchFrame.setStyleSheet(self.colors['resultsView'])
        self.downloadsFrame.setStyleSheet(self.colors['downloadsView']+self.colors['mainProgressBar'])

        # Define pastel styles directly for reliable application
        genericButton_style = "QPushButton{background-color:#B0E0E6; color:#36454F; border:1px solid #36454F; padding:5px 10px; border-radius:5px;} QPushButton:hover{background-color:#C0E8Ee;} QPushButton:disabled{background-color:#D3D3D3; color:#A9A9A9;}"
        lineEdit_style = "QLineEdit{background-color:#E6E6FA; color:#36454F; border:1px solid #B0E0E6; border-radius:3px; padding: 3px;}"
        comboBox_style = "QComboBox{background-color:#E6E6FA; color:#36454F; border:1px solid #B0E0E6; border-radius:3px; padding:3px;} QComboBox QAbstractItemView{background-color:#E6E6FA; color:#36454F; selection-background-color:#B0E0E6;}"

        # Apply generic styles to specific widgets
        if hasattr(self, 'homeButton'): # These are on self.stack
            self.homeButton.setStyleSheet(genericButton_style)
        if hasattr(self, 'downloadButton'):
            self.downloadButton.setStyleSheet(genericButton_style)
        if hasattr(self, 'backButton'):
            self.backButton.setStyleSheet(genericButton_style)
        
        if hasattr(self.startFrame, 'goButton'):
            self.startFrame.goButton.setStyleSheet(genericButton_style)
        if hasattr(self.startFrame, 'queryField'):
            self.startFrame.queryField.setStyleSheet(lineEdit_style)
        if hasattr(self.startFrame, 'siteSelector'):
            self.startFrame.siteSelector.setStyleSheet(comboBox_style)


    def reset(self):
        self.centralWidget().deleteLater()
        keys = list(self.worker.keys())
        for i in keys:
            if i in self.thread and self.thread[i].isRunning():
                if i in self.worker:
                    self.worker[i]._stop = True
                self.thread[i].quit()
                if not self.thread[i].wait(5000):  # Wait for 5 seconds
                    print(f"Thread {i} did not terminate gracefully, forcing termination.")
                    self.thread[i].terminate()
                    self.thread[i].wait()  # Wait for termination to complete
            # Clean up worker and thread references if they still exist
            if i in self.worker:
                del self.worker[i]
            if i in self.thread:
                del self.thread[i]
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
            self.startFrame.startLabel.setText('Select a website and click Go again')
            self.startFrame.siteSelector.show()
            # Disconnect previous connections to avoid multiple calls or logic errors
            try:
                self.startFrame.goButton.clicked.disconnect()
            except TypeError: # No connections
                pass
            # Now, clicking Go will initiate the search with the selected site
            self.startFrame.goButton.clicked.connect(lambda: self.search(query))
            # Optionally, disable the button until a site is selected, then re-enable.
            # For now, allow clicking Go again, which will trigger search.
            # self.startFrame.goButton.setDisabled(True) # Consider this if site selection must happen first
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
        self.homeButton.setDisabled(True)
        if back:
            self.backButton.clicked.connect(lambda:self.clearPage(self.page))
        self.chaptersFrame.chapterList.clear()
        self.chaptersFrame.comicNameLabel.setText('Loading...')
        self.chaptersFrame.coverImageLabel.clear()
        self.mainStack.setCurrentIndex(1)
        if 1 in self.thread and self.thread[1].isRunning():
            if 1 in self.worker:
                self.worker[1]._stop = True
            self.thread[1].quit()
            if not self.thread[1].wait(5000):
                print("Thread 1 (getChaps) did not terminate gracefully, forcing termination.")
                self.thread[1].terminate()
                self.thread[1].wait()
            # Clean up worker and thread references if they still exist
            if 1 in self.worker:
                del self.worker[1]
            if 1 in self.thread:
                del self.thread[1]
        self.createThread(1)
        self.worker[1].a = self.a
        self.worker[1].link = link
        self.thread[1].started.connect(self.worker[1].chapters)
        self.thread[1].finished.connect(lambda:self.listChapters(back))
        self.thread[1].start()


    def listChapters(self,back):
        self.homeButton.setDisabled(False)
        if back:
            self.backButton.show()
        self.homeButton.show()
        name,chapters,titles = self.a.chapters
        #Check if button is connected
        try:
            self.downloadButton.clicked.disconnect()
        except TypeError:
            pass    
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
        # Use thread ID 1 as per existing logic for self.createThread(1)
        # The original code uses thread ID 2 for stopping but creates thread 1.
        # This seems like a bug. Assuming we stop thread 1 if it's running.
        if 1 in self.thread and self.thread[1].isRunning():
            if 1 in self.worker:
                self.worker[1]._stop = True
            self.thread[1].quit()
            if not self.thread[1].wait(5000):
                print("Thread 1 (downloadChaps) did not terminate gracefully, forcing termination.")
                self.thread[1].terminate()
                self.thread[1].wait()
            if 1 in self.worker: # Clean up after stopping
                del self.worker[1]
            if 1 in self.thread:
                del self.thread[1]

        self.createThread(1) # This will now correctly create thread 1
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
        self.homeButton.setDisabled(True)
        self.startFrame.startLabel.setText('Loading...')
        self.startFrame.siteSelector.hide()
        self.startFrame.queryField.hide()
        self.startFrame.goButton.hide()
        if site == 0:
            self.a = readcomiconline(query)
        elif site == 1:
            self.a = comicextra(query)
        elif site == 2:
            self.a = comiconline(query)
        self.getLastPage()


    def getLastPage(self):
        self.navButtons = []
        self.createThread(1)
        self.worker[1].a = self.a
        self.thread[1].started.connect(self.worker[1].lastPage)
        self.thread[1].finished.connect(self.getSearchResults)
        self.thread[1].finished.connect(lambda:self.homeButton.setDisabled(False))
        self.thread[1].finished.connect(self.showPage)
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
        
        self.page = page
        #Change to results page
        self.mainStack.setCurrentIndex(2)
        #Calculate the indices of last and first nav buttons
        minPage = max(page-2,1) if max(page-2,1)+4<self.a.lPage else max(self.a.lPage-4,1)
        maxPage = min(minPage+4,self.a.lPage)
        #Delete all nav buttons
        for i in self.navButtons:
            self.searchFrame.horizontalLayout_2.removeWidget(i[0])
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
        if page==self.a.lPage:
            self.addNavButton('>>',self.a.lPage,True)
        else:
            self.addNavButton('>>',self.a.lPage,False)
        if self.searchFrame.navBar.isHidden():
            self.searchFrame.navBar.show()
        
        while page not in self.a.searchResults.keys():
            pass

        #Add search results
        for n,comic in enumerate(self.a.searchResults[page]):
            self.searchItems = []
            item = QListWidgetItem()
            item.setText(comic[1])
            item.setData(3,comic[0])
            self.searchFrame.resultsList.addItem(item)
            self.addIcon(page,n,3)
        
        self.searchFrame.resultsList.itemPressed.connect(self.comicSelected)
        #Get images of search results
        if page not in self.a.downloadedImages or (page in self.a.downloadedImages and len(self.a.downloadedImages[page])!=self.a.searchResults[page]):
            self.createThread(1)
            self.worker[1].a = self.a
            self.worker[1].page = page
            self.thread[1].started.connect(self.worker[1].searchPageImages)
            self.worker[1].progress.connect(lambda index:self.addIcon(page,index,2))
            self.thread[1].start()
        

    def clearPage(self,page):
        for button,__ in self.navButtons:
            button.setDisabled(True)
        if 1 in self.thread and self.thread[1].isRunning():
            if 1 in self.worker:
                self.worker[1]._stop = True
            self.thread[1].quit()
            if not self.thread[1].wait(5000):
                print("Thread 1 (clearPage) did not terminate gracefully, forcing termination.")
                self.thread[1].terminate()
                self.thread[1].wait()
            # Clean up worker and thread references if they still exist
            if 1 in self.worker:
                del self.worker[1]
            if 1 in self.thread:
                del self.thread[1]
        self.searchFrame.resultsList.clear()
        self.searchFrame.resultsList.resetVerticalScrollMode()
        self.showPage(page)

    def comicSelected(self,clickedItem):
        self.searchFrame.resultsList.itemPressed.disconnect()
        self.getChaps(clickedItem.data(3),back=True)
    

    def addNavButton(self,text,page,disabled):
        navButton = QPushButton(parent = self.searchFrame.navBar)
        navButton.setText(text)
        navButton.setMinimumSize(QSize(30,30))
        navButton.setMaximumSize(QSize(30,30))
        
        # Apply generic button style
        genericButton_style = "QPushButton{background-color:#B0E0E6; color:#36454F; border:1px solid #36454F; padding:5px; border-radius:5px;} QPushButton:hover{background-color:#C0E8Ee;} QPushButton:disabled{background-color:#D3D3D3; color:#A9A9A9;}"
        # Adjusted padding for smaller nav buttons
        if text == "<<" or text == ">>":
             navButton.setStyleSheet(genericButton_style.replace("padding:5px 10px", "padding:5px"))
        else: # Numeric page buttons
             navButton.setStyleSheet(genericButton_style.replace("padding:5px 10px", "padding:5px; min-width: 20px;"))


        navButton.clicked.connect(lambda :self.clearPage(page))
        navButton.setDisabled(disabled)
        navButton.clicked.connect(self.searchFrame.navBar.hide)
        self.navButtons.append([navButton,disabled])
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
        # Use pop with a default to avoid KeyError if already deleted elsewhere (e.g. forceful termination)
        self.worker[n].finished.connect(lambda i=n:self.worker.pop(i, None))
        self.worker[n].error.connect(self.handleError)
        self.worker[n].error.connect(self.thread[n].quit)

      
    def addPBar(self,name):
        horizontalLayout = QHBoxLayout()
        label = QLabel(parent=self.downloadsFrame)
        label.setObjectName(name)
        label.setMinimumSize(QSize(200, 25))
        label.setMaximumSize(QSize(500, 50))
        label.setText(name)
        label.setWordWrap(True)
        font = qtg.QFont()
        font.setPointSize(16)
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
        item.setSizeHint(QSize(100,100))
        self.downloadsFrame.progressList.addItem(item)
        self.downloadsFrame.progressList.setItemWidget(item,widget)
        return progressBar

    def handleError(self,err):
        # Ensure we are on the start page
        if self.mainStack.currentIndex() != 0:
            self.mainStack.setCurrentIndex(0)

        # Reset UI elements on the startFrame to allow a new attempt
        self.startFrame.startLabel.setText('An error occurred. Please try again.')
        if err == -1:
            self.startFrame.startLabel.setText('Connection Error. Check your internet and try again.')
        elif err == 0:
            self.startFrame.startLabel.setText('Comic or chapter not found.')
        elif err == -2: # Specific timeout error from Worker.searchPageImages
             self.startFrame.startLabel.setText('Operation timed out while fetching search page details.')


        self.startFrame.queryField.show()
        self.startFrame.queryField.setDisabled(False)
        self.startFrame.queryField.clear() # Clear previous query

        self.startFrame.siteSelector.hide() # Keep site selector hidden initially

        self.startFrame.goButton.show()
        self.startFrame.goButton.setDisabled(False)
        # Disconnect any existing connections from goButton (e.g., from a pending search)
        try:
            self.startFrame.goButton.clicked.disconnect()
        except TypeError: # No connections
            pass
        # Reconnect goButton to the initial self.go method
        self.startFrame.goButton.clicked.connect(self.go)

        # Ensure main navigation buttons are in a sensible state
        self.homeButton.setDisabled(False) # Already done, but good to confirm
        self.homeButton.show() # Should generally be visible if an error occurs, allowing reset
        
        # Hide buttons that are not relevant to the start page or error state
        if self.downloadButton: # Check if button exists
            self.downloadButton.hide()
        if self.backButton: # Check if button exists
            self.backButton.hide()
