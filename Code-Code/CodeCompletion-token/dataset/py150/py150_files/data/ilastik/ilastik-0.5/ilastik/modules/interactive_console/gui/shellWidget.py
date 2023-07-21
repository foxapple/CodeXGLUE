# -*- python -*-
#
#       Copyright 2006-2009 - 2008 INRIA - CIRAD - INRA  
#
#       File author(s): Samuel Dufour-Kowalski <samuel.dufour@sophia.inria.fr>
#                       Christophe Pradal <christophe.prada@cirad.fr>
#
#       Distributed under the CeCILL v2 License.
#       See accompanying LICENSE section at the end of this file or 
#           http://www.cecill.info/licences/Licence_CeCILL_V2-en.html
# 
################################################################################
"""This module implements a QT4 python interpreter widget."""

__license__ = "CeCILL V2"


import sys
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

from PyQt4.Qsci import QsciScintilla, QsciLexerPython
from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QThread, QEvent

RedirectionEventId = QEvent.User+100
sys_stderr = None
sys_stdout = None
sys_stdin = None

try:
    import openalea.lpy.gui.py2exe_release
    py2exe_release = True
except:
    py2exe_release = False
    
#*******************************************************************************
# M u l t i p l e R e d i r e c t i o n                                        *
#*******************************************************************************

class MultipleRedirection:
    """ Dummy file which redirects stream to multiple file """

    def __init__(self, *streams):
        """ The stream is redirect to the file list 'files' """

        self.streams = streams

    def write(self, str):
        """ Emulate write function """

        for stream in self.streams:
            stream.write(str)


#*******************************************************************************
# T h r e a d e d R e d i r e c t i o n                                        *
#*******************************************************************************

class ThreadedRedirection:
    """ Dummy file which redirects stream to threaded gui output """

    def __init__(self,  guistream):
        """ The stream is redirect to the file list 'files' """

        self.guistream = guistream

    def write(self, str):
        """ Emulate write function """

        if self.guistream.thread() != QThread.currentThread():
            sys_stdout.write(str)
            e = QEvent(QEvent.Type(RedirectionEventId))
            e.txt = str
            QApplication.postEvent(self.guistream,e)
            pass
        else:
            self.guistream.write(str)

            
#*******************************************************************************
# G r a p h i c a l S t r e a m R e d i r e c t i o n                          *
#*******************************************************************************

class GraphicalStreamRedirection:
    """ Redirection of a stream as graphic output """
    
    def __init__(self):
        """  capture all interactive input/output """
        global sys_stdout, sys_stderr, sys_stdin
        if sys_stdout is None:  sys_stdout = sys.stdout
        if sys_stderr is None:  sys_stderr = sys.stderr
        if sys_stdin is None:   sys_stdin = sys.stdin
        sys.stdout   = ThreadedRedirection(self)
        if py2exe_release:
            sys.stderr   = ThreadedRedirection(self)
        else:
            sys.stderr   = MultipleRedirection(sys_stderr, ThreadedRedirection(self))
        sys.stdin    = self
        #self.multipleStdOutRedirection()

    def __del__(self):
        sys.stdout   = sys_stdout
        sys.stderr   = sys_stderr
        sys.stdin    = sys_stdin
        
    def customEvent(self,event):
        """ custom event processing. Redirection to write """
        if event.type() == RedirectionEventId:
            self.write(event.txt)
            
    def multipleRedirection(self, enabled):
        self.multipleStdErrRedirection(enabled)
        self.multipleStdOutRedirection(enabled)
            
            
    def multipleStdOutRedirection(self,enabled = True):
        """ make multiple (sys.stdout/pyconsole) or single (pyconsole) redirection of stdout """
        if enabled:
            sys.stdout   = MultipleRedirection(sys_stdout, ThreadedRedirection(self))
        else:
            sys.stdout   = sys_stdout
        
    def multipleStdErrRedirection(self,enabled = True):
        """ make multiple (sys.stderr/pyconsole) or single (pyconsole) redirection of stderr """
        if enabled:
            sys.stderr   = MultipleRedirection(sys_stderr, ThreadedRedirection(self))
        else:
            sys.stderr   = sys_stderr
            

#*******************************************************************************
# S c i S h e l l                                                              *
#*******************************************************************************

class SciShell(QsciScintilla,GraphicalStreamRedirection):
    """
    SciShell is a Python shell based in QScintilla.
    It is inspired by PyCute (pycute.py) : http://gerard.vermeulen.free.fr (GPL)
    and Eric4 shell (shell.py) : http://www.die-offenbachs.de/eric/index.html (GPL)
    """
    
    def __init__(self, interpreter, message="", log='', parent=None):
        """Constructor.
        @param interpreter : InteractiveInterpreter in which
        the code will be executed

        @param message : welcome message string
        
        @param  'parent' : specifies the parent widget.
        If no parent widget has been specified, it is possible to
        exit the interpreter by Ctrl-D.
        """

        QsciScintilla.__init__(self, parent)
        GraphicalStreamRedirection.__init__(self)
        
        self.interpreter = interpreter
        
        # user interface setup
        self.setAutoIndent(True)
        self.setAutoCompletionThreshold(2)
        self.setAutoCompletionSource(QsciScintilla.AcsDocument)
        # Lexer
        self.setLexer(QsciLexerPython(self))

        # Search
        self.incrementalSearchString = ""
        self.incrementalSearchActive = False
        self.inRawMode = False
        self.echoInput = True
            
        # Initialize _history
        self.historyLists = {}
        self.maxHistoryEntries = 30
        self._history = []
        self.histidx = -1
        
        self.reading = 0
        # interpreter prompt.
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "... "


        #self.completionText = ""
        # Excecution Status
        self.more = False
        # Multi line execution Buffer
        self.execlines = []

        # interpreter banner
        self.write('The shell running Python %s on %s.\n' %
                   (sys.version, sys.platform))
        self.write('Type "copyright", "credits" or "license"'
                   ' for more information on Python.\n')
        self.write(message+'\n')
        #self.write("help -> Python help system.\n")
        self.write(" object? -> Print details about 'object'\n\n")
        self.write(sys.ps1)


        #self.standardCommands().clearKeys()
        self.keymap = {
            Qt.Key_Backspace : self.__QScintillaDeleteBack,
            Qt.Key_Delete : self.__QScintillaDelete,
            Qt.Key_Return : self.__QScintillaNewline,
            Qt.Key_Enter : self.__QScintillaNewline,
            Qt.Key_Tab : self.__QScintillaTab,
            Qt.Key_Left : self.__QScintillaCharLeft,
            Qt.Key_Right : self.__QScintillaCharRight,
            Qt.Key_Up : self.__QScintillaLineUp,
            Qt.Key_Down : self.__QScintillaLineDown,
            Qt.Key_Home : self.__QScintillaVCHome,
            Qt.Key_End : self.__QScintillaLineEnd,
            }

        self.connect(self, QtCore.SIGNAL('userListActivated(int, const QString)'),
                     self.__completionListSelected)

        self.setFocus()
        self.setFocusPolicy(QtCore.Qt.StrongFocus)


    def customEvent(self,event):
        GraphicalStreamRedirection.customEvent(self,event)
        QsciScintilla.customEvent(self,event)

    def clear(self):
        """ Clear shell """
        QsciScintilla.clear(self)

    def get_interpreter(self):
        """ Return the interpreter object """

        return self.interpreter
        

    def flush(self):
        """
        Simulate stdin, stdout, and stderr.
        """
        pass


    def isatty(self):
        """
        Simulate stdin, stdout, and stderr.
        """
        return 1
    

    def readline(self):
        """
        Simulate stdin, stdout, and stderr.
        """
        self.reading = 1
        line, col = self.__getEndPos()
        self.setCursorPosition(line, col)

        buf = ""
        
        if len(buf) == 0:
            return '\n'
        else:
            return buf


    def write(self, s):
        """
        Simulate stdin, stdout, and stderr.
        """

        line, col = self.__getEndPos()
        self.setCursorPosition(line, col)
        self.insert(s)

        line, col = self.__getEndPos()
        self.setCursorPosition(line, col)

        self.prline, self.prcol = self.getCursorPosition()

        self.ensureCursorVisible()
        self.ensureLineVisible(line)

        
    ###########################################

    def __getEndPos(self):
        """
        Private method to return the line and column of the last character.
        
        @return tuple of two values (int, int) giving the line and column
        """
        line = self.lines() - 1
        return (line, self.lineLength(line))

    
    def paste(self):
        """
        Reimplemented slot to handle the paste action.
        """

        lines = unicode(QtGui.QApplication.clipboard().text())
        self.__executeLines(lines)
        
        
    def __middleMouseButton(self):
        """
        Private method to handle the middle mouse button press.
        """
        lines = unicode(QtGui.QApplication.clipboard().text(
            QtGui.QClipboard.Selection))
        self.__executeLines(lines)

        
    def __executeLines(self, lines):
        """
        Private method to execute a set of lines as multiple commands.
        
        :param lines: multiple lines of text to be executed as single
            commands (string)

        """
        
        for line in lines.splitlines(True):
            if line.endswith("\r\n"):
                fullline = True
                cmd = line[:-2]
            elif line.endswith("\r") or line.endswith("\n"):
                fullline = True
                cmd = line[:-1]
            else:
                fullline = False
            
            self.__insertTextAtEnd(line)
            if fullline:
                self.__executeCommand(cmd)

                
    def __executeCommand(self, cmd):
        """
        Private slot to execute a command.
        
        @param cmd command to be executed by debug client (string)
        """

        if not cmd:  cmd = ''
        else:
            if len(self._history) == self.maxHistoryEntries:
                del self._history[0]
            self._history.append(QtCore.QString(cmd))
            self.histidx = -1

        if(cmd.endswith('?')):
                self.__showHelp(cmd)
                return

        # Execute command
        self.execlines.append(str(cmd))
        source = '\n'.join(self.execlines)
        self.more = self.interpreter.runsource(source)

        if self.more:
            self.write(sys.ps2)
        else:
            self.write(sys.ps1)
            self.execlines = []
        
    
    def __insertText(self, s):
        """
        Insert text at the current cursor position.
        """

        line, col = self.getCursorPosition()
        self.insertAt(s, line, col)
        self.setCursorPosition(line, col + len(str(s)))


    def __insertTextAtEnd(self, s):
        """
        Private method to insert some text at the end of the command line.
        @param s text to be inserted (string or QString)
        """
        line, col = self.__getEndPos()
        self.setCursorPosition(line, col)
        self.insert(s)
        self.prline, self.prcol = self.__getEndPos()
        self.setCursorPosition(self.prline, self.prcol)


        
    def __isCursorOnLastLine(self):
        """
        Private method to check, if the cursor is on the last line.
        """
        cline, ccol = self.getCursorPosition()
        return cline == self.lines() - 1


    def contextMenuEvent(self, e):
        pass


    def mousePressEvent(self, event):
        """
        Protected method to handle the mouse press event.
        
        @param event the mouse press event (QMouseEvent)
        """
        self.setFocus()
        if event.button() == Qt.MidButton:
            self.__middleMouseButton()
        else:
            QsciScintilla.mousePressEvent(self, event)


    def keyPressEvent(self, ev):
        """
        Re-implemented to handle the user input a key at a time.
        
        @param ev key event (QKeyEvent)
        """
        txt = ev.text()
        key = ev.key()
        
        ctrl = ev.modifiers() & Qt.ControlModifier
        shift = ev.modifiers() & Qt.ShiftModifier
        # See it is text to insert.
        if(self.keymap.has_key(key) and not shift and not ctrl):
            self.keymap[key]()

        elif ev == QtGui.QKeySequence.Paste:
            self.paste()

        elif self.__isCursorOnLastLine() and txt.length() :

            QsciScintilla.keyPressEvent(self, ev)
            self.incrementalSearchActive = True
            
            if(txt == '.'):
                self.__showDynCompletion()        

        elif(ctrl or shift):
            QsciScintilla.keyPressEvent(self, ev)
        else:
            ev.ignore()



    def __QScintillaTab(self):
        """
        Private method to handle the Tab key.
        """
        if self.isListActive():
            self.SendScintilla(QsciScintilla.SCI_TAB)
        elif self.__isCursorOnLastLine():
            line, index = self.getCursorPosition()
            buf = unicode(self.text(line)).replace(sys.ps1, "").replace(sys.ps2, "")
            if self.more and not buf[:index-len(sys.ps2)].strip():
                self.SendScintilla(QsciScintilla.SCI_TAB)
             
        
    def __QScintillaDeleteBack(self):
        """
        Private method to handle the Backspace key.
        """
        if self.__isCursorOnLastLine():
            line, col = self.getCursorPosition()
            ac = self.isListActive()
            oldLength = self.text(line).length()
            
            if self.text(line).startsWith(sys.ps1):
                if col > len(sys.ps1):
                    self.SendScintilla(QsciScintilla.SCI_DELETEBACK)
                    
            elif self.text(line).startsWith(sys.ps2):
                if col > len(sys.ps2):
                    self.SendScintilla(QsciScintilla.SCI_DELETEBACK)

            elif col > 0:
                self.SendScintilla(QsciScintilla.SCI_DELETEBACK)

        
    def __QScintillaDelete(self):
        """
        Private method to handle the delete command.
        """
        if self.__isCursorOnLastLine():
            if self.hasSelectedText():
                lineFrom, indexFrom, lineTo, indexTo = self.getSelection()
                if self.text(lineFrom).startsWith(sys.ps1):
                    if indexFrom >= len(sys.ps1):
                        self.SendScintilla(QsciScintilla.SCI_CLEAR)

                elif self.text(lineFrom).startsWith(sys.ps2):
                    if indexFrom >= len(sys.ps2):
                        self.SendScintilla(QsciScintilla.SCI_CLEAR)
                        
                elif indexFrom >= 0:
                    self.SendScintilla(QsciScintilla.SCI_CLEAR)
                    
                self.setSelection(lineTo, indexTo, lineTo, indexTo)
            else:
                self.SendScintilla(QsciScintilla.SCI_CLEAR)

        
        
    def __QScintillaNewline(self):
        """
        Private method to handle the Return key.
        """
        if self.__isCursorOnLastLine():
            if self.isListActive():
                self.SendScintilla(QsciScintilla.SCI_NEWLINE)
            elif self.reading:
                self.reading = 0
       
            else:
                self.incrementalSearchString = ""
                self.incrementalSearchActive = False
                line, col = self.__getEndPos()
                self.setCursorPosition(line,col)
                buf = unicode(self.text(line)).replace(sys.ps1, "").replace(sys.ps2, "")
                self.insert('\n')
                self.__executeCommand(buf)

        # add and run selection
        else:
            s= self.selectedText()
            self.__insertTextAtEnd(s)

        
    def __QScintillaCharLeft(self, allLinesAllowed = False):
        """
        Private method to handle the Cursor Left command.
        """
        
        if self.__isCursorOnLastLine() or allLinesAllowed:
            line, col = self.getCursorPosition()
            if self.text(line).startsWith(sys.ps1):
                if col > len(sys.ps1):
                    self.SendScintilla(QsciScintilla.SCI_CHARLEFT)
                    
            elif self.text(line).startsWith(sys.ps2):
                if col > len(sys.ps2):
                    
                    self.SendScintilla(QsciScintilla.SCI_CHARLEFT)
            elif col > 0:
                
                self.SendScintilla(QsciScintilla.SCI_CHARLEFT)

        
    def __QScintillaCharRight(self):
        """
        Private method to handle the Cursor Right command.
        """
        if self.__isCursorOnLastLine():
            self.SendScintilla(QsciScintilla.SCI_CHARRIGHT)


    def __QScintillaVCHome(self):
        """
        Private method to handle the Home key.
        """
        if self.isListActive():
            self.SendScintilla(QsciScintilla.SCI_VCHOME)
        elif self.__isCursorOnLastLine():
            line, col = self.getCursorPosition()
            if self.text(line).startsWith(sys.ps1):
                col = len(sys.ps1)
            elif self.text(line).startsWith(sys.ps2):
                col = len(sys.ps2)
            else:
                col = 0
            self.setCursorPosition(line, col)

        
    def __QScintillaLineEnd(self):
        """
        Private method to handle the End key.
        """
        if self.isListActive():
            self.SendScintilla(QsciScintilla.SCI_LINEEND)
        elif self.__isCursorOnLastLine():
            self.SendScintilla(QsciScintilla.SCI_LINEEND)

        
    def __QScintillaLineUp(self):
        """
        Private method to handle the Up key.
        """
        if self.isListActive():
            self.SendScintilla(QsciScintilla.SCI_LINEUP)
        else:
            line, col = self.__getEndPos()
            buf = unicode(self.text(line)).replace(sys.ps1, "").replace(sys.ps2, "")
            if buf and self.incrementalSearchActive:
                if self.incrementalSearchString:
                    idx = self.__rsearchHistory(self.incrementalSearchString, 
                                                self.histidx)
                    if idx >= 0:
                        self.histidx = idx
                        self.__useHistory()
                else:
                    idx = self.__rsearchHistory(buf)
                    if idx >= 0:
                        self.histidx = idx
                        self.incrementalSearchString = buf
                        self.__useHistory()
            else:
                if self.histidx < 0:
                    self.histidx = len(self._history)
                if self.histidx > 0:
                    self.histidx = self.histidx - 1
                    self.__useHistory()

        
    def __QScintillaLineDown(self):
        """
        Private method to handle the Down key.
        """
        if self.isListActive():
            self.SendScintilla(QsciScintilla.SCI_LINEDOWN)
        else:
            line, col = self.__getEndPos()
            buf = unicode(self.text(line)).replace(sys.ps1, "").replace(sys.ps2, "")
            if buf and self.incrementalSearchActive:
                if self.incrementalSearchString:
                    idx = self.__searchHistory(self.incrementalSearchString, self.histidx)
                    if idx >= 0:
                        self.histidx = idx
                        self.__useHistory()
                else:
                    idx = self.__searchHistory(buf)
                    if idx >= 0:
                        self.histidx = idx
                        self.incrementalSearchString = buf
                        self.__useHistory()
            else:
                if self.histidx >= 0 and self.histidx < len(self._history):
                    self.histidx += 1
                    self.__useHistory()
  

    def __useHistory(self):
        """
        Private method to display a command from the _history.
        """
        if self.histidx < len(self._history):
            cmd = self._history[self.histidx]
        else:
            cmd = QtCore.QString()
            self.incrementalSearchString = ""
            self.incrementalSearchActive = False

        self.setCursorPosition(self.prline, self.prcol + len(self.more and sys.ps1 or sys.ps2))
        self.setSelection(self.prline,self.prcol,\
                          self.prline,self.lineLength(self.prline))
        self.removeSelectedText()
        self.__insertText(cmd)

        
    def __searchHistory(self, txt, startIdx = -1):
        """
        Private method used to search the _history.
        
        @param txt text to match at the beginning (string or QString)
        @param startIdx index to start search from (integer)
        @return index of 
        """
        if startIdx == -1:
            idx = 0
        else:
            idx = startIdx + 1
        while idx < len(self._history) and \
              not self._history[idx].startsWith(txt):
            idx += 1
        return idx
    
        
    def __rsearchHistory(self, txt, startIdx = -1):
        """
        Private method used to reverse search the _history.
        
        @param txt text to match at the beginning (string or QString)
        @param startIdx index to start search from (integer)
        @return index of 
        """
        if startIdx == -1:
            idx = len(self._history) - 1
        else:
            idx = startIdx - 1
        while idx >= 0 and \
              not self._history[idx].startsWith(txt):
            idx -= 1
        return idx


    def focusNextPrevChild(self, next):
        """
        Reimplemented to stop Tab moving to the next window.
        
        While the user is entering a multi-line command, the movement to
        the next window by the Tab key being pressed is suppressed.
        
        @param next next window
        @return flag indicating the movement
        """
        if next and self.more:
            return False
    
        return QsciScintilla.focusNextPrevChild(self,next)


    def __get_current_line(self):
        """ Return the current line """

        line, col = self.__getEndPos()
        self.setCursorPosition(line,col)
        buf = unicode(self.text(line)).replace(sys.ps1, "").replace(sys.ps2, "")
        text = buf.split()[-1][:-1]
        return text


    def __showHelp(self, text):

        #text = self.__get_current_line()
        self.__executeCommand('help(%s)'%(text[:-1],))
        #self.__QScintillaNewline()
        #self.__insertTextAtEnd(text)

        
    def __showDynCompletion(self):
        """
        Display a completion list based on the last token
        """

        text = self.__get_current_line()
        
        try:
            locals = self.interpreter.locals
            obj = eval(text, globals(), self.interpreter.locals)
            l = dir(obj)
            #l = filter(lambda x : not x.startswith('__'), l)
            self.__showCompletions(l, text) 
        except : pass
        

    def __showCompletions(self, tcompletions, text):
        """
        Private method to display the possible completions.
        """
        if len(tcompletions) == 0:
            return
        
        completions = []
        
        for i, c in enumerate(tcompletions):
            if c[0] != "_":
                completions.append(c)
        
        if len(completions) > 1:
            completions.sort()
            comps = QtCore.QStringList()
            for comp in completions:
                comps.append(comp)
            self.showUserList(1, comps)
            #self.completionText = text
        else:
            txt = completions[0]
            if text != "":
                txt = txt.replace(text, "")
            self.__insertText(txt)
            #self.completionText = ""

        
    def __completionListSelected(self, id, txt):
        """
        Private slot to handle the selection from the completion list.
        
        @param id the ID of the user list (should be 1) (integer)
        @param txt the selected text (QString)
        """

        # Remove already written characters
        line, col = self.__getEndPos()
        self.setCursorPosition(line,col)
        buf = unicode(self.text(line))
        ind = len(buf) - buf.rfind(".") - 1

        if id == 1:
            txt = unicode(txt[ind:])
            #if self.completionText != "":
            #   txt = txt.replace(self.completionText, "")
            self.__insertText(txt)
            #self.completionText = ""


    # Drag and Drop support
    def dragEnterEvent(self, event):
        event.setAccepted(event.mimeData().hasFormat("text/plain"))


    def dragMoveEvent(self, event):
        if (event.mimeData().hasFormat("text/plain")):
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

            
    def dropEvent(self, event):

        if(event.mimeData().hasFormat("text/plain")):
            line = event.mimeData().text()
            self.__insertTextAtEnd(line)
            self.setFocus()
            
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()

        else:
            event.ignore()

def main():
    # Test the widget independently.
    from code import InteractiveInterpreter as Interpreter
    a = QtGui.QApplication(sys.argv)

    # Restore default signal handler for CTRL+C
    import signal; signal.signal(signal.SIGINT, signal.SIG_DFL)

    interpreter = Interpreter()
    aw = SciShell(interpreter)

    # static resize
    aw.resize(600,400)

    aw.show()
    a.exec_()


#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__=="__main__":
    main()
