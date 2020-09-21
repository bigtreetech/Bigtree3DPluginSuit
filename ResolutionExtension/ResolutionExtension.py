# Copyright (c) 2017 Ultimaker B.V.
# This Resolution Extension is released under the terms of the AGPLv3 or higher.

import sys
import os
import os.path
# from PyQt5.QtCore import QUrl #To find the QML for the dialogue window.
# from PyQt5.QtQml import QQmlComponent, QQmlContext #To create the dialogue window.

from UM.Application import Application #To listen to the event of creating the main window, and get the QML engine.
from UM.Extension import Extension #The PluginObject we're going to extend.
from UM.Logger import Logger #Adding messages to the log.
from UM.PluginRegistry import PluginRegistry #Getting the location of Hello.qml.

from PyQt5.QtCore import QUrl,Qt
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QFile, QFileInfo, QIODevice,QTextStream

class ResolutionExtension(Extension): #Extension inherits from PluginObject, and provides some useful helper functions for adding an item to the application menu.
    ##  Creates an instance of this extension. This is basically the starting
    #   point of your code.
    #
    #   This is called by the register() function in __init__.py, which gets
    #   called during plug-in loading. That all happens before the splash screen
    #   even appears, so this code needs to be efficient. Also, be aware, that
    #   many things have not been loaded yet at this point.
    def __init__(self):
        super().__init__()
        #A typical use of this constructor is to register some function to be
        #called upon some event in Uranium, or to add a menu item. In this case,
        #we will do both.


        ## Creating a menu item. ##
        #An extension can add several menu items. They all get placed under one header. This sets the title of that header.
        self.setMenuName("Icon Resolution Extension")

        #We'll add one item that says hello to the user.
        self.addMenuItem("Set Icon Resolution", self.setresolution) #When the user clicks the menu item, the sayHello function is called.

        #Lazy-load the window. Create it when we first want to say hello.
        self.setler_window = None

        ## Reacting to an event. ##
        Application.getInstance().mainWindowChanged.connect(self.logMessage) #When the main window is created, log a message.

    ##  Creates a small dialogue window that says hello to the user.
    def setresolution(self):
        if not self.setler_window: #Don't create more than one.
            self.setler_window = self._createDialogue()
        self.setler_window.show()


    ##  Adds a message to the log, as an example of how to listen to events.
    def logMessage(self):
        Logger.log("i", "Set Icon Resolution.")

    ##  Creates a modal dialogue.
    # @call_on_qt_thread
    def _createDialogue(self):
        CONFIGPATH = os.path.join(sys.path[0],"plugins\\ResolutionExtension\\Resolution.txt")
        CODEC = "UTF-8"
        if QFile(CONFIGPATH).exists() == False:#Create Default Configuration
            fh = QFile(CONFIGPATH)
            fh.open(QIODevice.WriteOnly)
            stream = QTextStream(fh)
            stream.setCodec(CODEC)
            stream << "70,70\r\n"
            stream << "95,80\r\n"
            stream << "95,95\r\n"
            stream << "160,140\r\n"
            fh.close()
            os.startfile(CONFIGPATH)
        else:
            os.startfile(CONFIGPATH)