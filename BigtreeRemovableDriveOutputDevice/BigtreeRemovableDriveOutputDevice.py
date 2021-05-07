# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import os
import os.path

from PyQt5.QtCore import QUrl,Qt,QSize,QFile, QFileInfo, QIODevice,QTextStream,QByteArray
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.FileHandler.WriteFileJob import WriteFileJob
from UM.FileHandler.FileWriter import FileWriter #To check against the write modes (text vs. binary).
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator
from UM.OutputDevice.OutputDevice import OutputDevice
from UM.OutputDevice import OutputDeviceError

from UM.i18n import i18nCatalog

from cura.Snapshot import Snapshot
from cura.Utils.Threading import call_on_qt_thread
from cura.CuraApplication import CuraApplication

catalog = i18nCatalog("cura")
CODEC = "UTF-8"

class BigtreeRemovableDriveOutputDevice(OutputDevice):
    def __init__(self, device_id, device_name):
        super().__init__(device_id)

        self.setName(device_name)
        self.setShortDescription(catalog.i18nc("@action:button Preceded by 'Ready to'.", "Bigtree3D to Removable Drive"))
        self.setDescription(catalog.i18nc("@item:inlistbox", "Bigtree3D to {0}").format(device_name))
        self.setIconName("Bigtree_SD")
        self.setPriority(1)

        self._writing = False
        self._stream = None

    ##  Request the specified nodes to be written to the removable drive.
    #
    #   \param nodes A collection of scene nodes that should be written to the
    #   removable drive.
    #   \param file_name \type{string} A suggestion for the file name to write
    #   to. If none is provided, a file name will be made from the names of the
    #   meshes.
    #   \param limit_mimetypes Should we limit the available MIME types to the
    #   MIME types available to the currently active machine?
    #
    def requestWrite(self, nodes, file_name = None, filter_by_machine = False, file_handler = None, **kwargs):
        filter_by_machine = True # This plugin is intended to be used by machine (regardless of what it was told to do)
        if self._writing:
            raise OutputDeviceError.DeviceBusyError()

        # Formats supported by this application (File types that we can actually write)
        if file_handler:
            file_formats = file_handler.getSupportedFileTypesWrite()
        else:
            file_formats = Application.getInstance().getMeshFileHandler().getSupportedFileTypesWrite()

        if filter_by_machine:
            container = Application.getInstance().getGlobalContainerStack().findContainer({"file_formats": "*"})

            # Create a list from supported file formats string
            machine_file_formats = [file_type.strip() for file_type in container.getMetaDataEntry("file_formats").split(";")]

            # Take the intersection between file_formats and machine_file_formats.
            format_by_mimetype = {format["mime_type"]: format for format in file_formats}
            file_formats = [format_by_mimetype[mimetype] for mimetype in machine_file_formats] #Keep them ordered according to the preference in machine_file_formats.

        if len(file_formats) == 0:
            Logger.log("e", "There are no file formats available to write with!")
            raise OutputDeviceError.WriteRequestFailedError(catalog.i18nc("@info:status", "There are no file formats available to write with!"))
        preferred_format = file_formats[0]

        # Just take the first file format available.
        if file_handler is not None:
            writer = file_handler.getWriterByMimeType(preferred_format["mime_type"])
        else:
            writer = Application.getInstance().getMeshFileHandler().getWriterByMimeType(preferred_format["mime_type"])

        extension = preferred_format["extension"]

        if file_name is None:
            file_name = self._automaticFileName(nodes)

        if extension:  # Not empty string.
            extension = "." + extension
        file_name = os.path.join(self.getId()[8:], os.path.splitext(file_name)[0] + extension)

        try:
            Logger.log("d", "Writing to %s", file_name)
            # Using buffering greatly reduces the write time for many lines of gcode
            if preferred_format["mode"] == FileWriter.OutputMode.TextMode:
                self._stream = open(file_name, "wt", buffering = 1, encoding = "utf-8")
            else: #Binary mode.
                self._stream = open(file_name, "wb", buffering = 1)
            job = WriteFileJob(writer, self._stream, nodes, preferred_format["mode"])
            job.setFileName(file_name)
            job.progress.connect(self._onProgress)
            job.finished.connect(self._onFinished)

            message = Message(catalog.i18nc("@info:progress Don't translate the XML tags <filename>!", "Saving to Removable Drive <filename>{0}</filename>").format(self.getName()), 0, False, -1, catalog.i18nc("@info:title", "Saving"))
            message.show()

            self.writeStarted.emit(self)

            job.setMessage(message)
            self._writing = True
            job.start()
        except PermissionError as e:
            Logger.log("e", "Permission denied when trying to write to %s: %s", file_name, str(e))
            raise OutputDeviceError.PermissionDeniedError(catalog.i18nc("@info:status Don't translate the XML tags <filename> or <message>!", "Could not save to <filename>{0}</filename>: <message>{1}</message>").format(file_name, str(e))) from e
        except OSError as e:
            Logger.log("e", "Operating system would not let us write to %s: %s", file_name, str(e))
            raise OutputDeviceError.WriteRequestFailedError(catalog.i18nc("@info:status Don't translate the XML tags <filename> or <message>!", "Could not save to <filename>{0}</filename>: <message>{1}</message>").format(file_name, str(e))) from e

    @call_on_qt_thread
    def getbackcolor(self):
        fcolor = 0x00000000
        CONFIGPATH = os.path.join(CuraApplication.getInstance().getPluginRegistry().getPluginPath("BigtreeExtension"),"config.txt")
        if QFile(CONFIGPATH).exists() == True:
            fh = QFile(CONFIGPATH)
            fh.open(QIODevice.ReadOnly)
            stream = QTextStream(fh)
            stream.setCodec(CODEC)
            while stream.atEnd() == False:
                tem = stream.readLine()
                if tem.startswith("# backcolor"):
                    var = int(0 if (tem.split("="))[1].strip().lower() == "" else (tem.split("="))[1].strip().lower())
                    if var < 0:
                        var = 0
                    if var > 255:
                        var = 255
                if tem.startswith("# backcolor_red"):
                    fcolor = fcolor | (var<<16)
                if tem.startswith("# backcolor_green"):
                    fcolor = fcolor | (var<<8)
                if tem.startswith("# backcolor_blue"):
                    fcolor = fcolor | var
            fh.close()
        return fcolor
        
    @call_on_qt_thread
    def overread(self,msize):
        moutdata = ""
        img = Snapshot.snapshot(width = msize.width(), height = msize.height()).scaled(msize.width(),msize.height(),Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        moutdata = moutdata + ";"+(hex(msize.width())[2:]).rjust(4,'0')+(hex(msize.height())[2:]).rjust(4,'0')+"\r\n"
        pos = QSize(0,0)
        fcolor = self.getbackcolor()
        for ypos in range(0,img.height()):
            qrgb = ";"
            for xpos in range(0,img.width()):
                data = img.pixel(xpos,ypos)
                pos.setWidth(pos.width()+1)
                if (data & 0x00FFFFFF) == 0x00000000:
                    data = fcolor
                qrgb = qrgb + (hex(((data & 0x00F80000) >> 8 ) | ((data & 0x0000FC00) >> 5 ) | ((data & 0x000000F8) >> 3 ))[2:]).rjust(4,'0')
            pos.setWidth(0)
            pos.setHeight(pos.height()+1)
            moutdata = moutdata + qrgb + "\r\n"
        return moutdata

    ##  Generate a file name automatically for the specified nodes to be saved
    #   in.
    #
    #   The name generated will be the name of one of the nodes. Which node that
    #   is can not be guaranteed.
    #
    #   \param nodes A collection of nodes for which to generate a file name.
    def _automaticFileName(self, nodes):
        for root in nodes:
            for child in BreadthFirstIterator(root):
                if child.getMeshData():
                    name = child.getName()
                    if name:
                        return name
        raise OutputDeviceError.WriteRequestFailedError(catalog.i18nc("@info:status Don't translate the tag {device}!", "Could not find a file name when trying to write to {device}.").format(device = self.getName()))

    def _onProgress(self, job, progress):
        self.writeProgress.emit(self, progress)
    
    @call_on_qt_thread
    def overseek(self):
        outdatar = ""
        CONFIGPATH = os.path.join(CuraApplication.getInstance().getPluginRegistry().getPluginPath("BigtreeExtension"),"config.txt")
        if QFile(CONFIGPATH).exists() == False:#Default
            outdatar = outdatar + self.overread(QSize(70,70))
            outdatar = outdatar + self.overread(QSize(95,80))
            outdatar = outdatar + self.overread(QSize(95,95))
            outdatar = outdatar + self.overread(QSize(160,140))
            outdatar = outdatar + self.overread(QSize(200,200))
        else:
            fh = QFile(CONFIGPATH)
            fh.open(QIODevice.ReadOnly)
            stream = QTextStream(fh)
            stream.setCodec(CODEC)
            while stream.atEnd() == False:
                tem = stream.readLine()
                if tem[0] == '#':
                    continue
                tems = tem.split(",")
                if len(tems) == 2 and tems[0].isdigit() and tems[1].isdigit():
                    outdatar = outdatar + self.overread(QSize(int(tems[0]),int(tems[1])))
            fh.close()
        return outdatar

    @call_on_qt_thread
    def extruder_M2O(self):
        flag = False
        CONFIGPATH = os.path.join(CuraApplication.getInstance().getPluginRegistry().getPluginPath("BigtreeExtension"),"config.txt")
        if QFile(CONFIGPATH).exists() == True:
            fh = QFile(CONFIGPATH)
            fh.open(QIODevice.ReadOnly)
            stream = QTextStream(fh)
            stream.setCodec(CODEC)
            while stream.atEnd() == False:
                tem = stream.readLine()
                if tem.startswith("# extruder_M2O"):
                    if (tem.split("="))[1].strip().lower() == "yes":
                        flag = True
                else:
                    continue
            fh.close()
        return flag
        
    def _onFinished(self, job):
        if self._stream:
            # Explicitly closing the stream flushes the write-buffer
            try:
                self._stream.close()
                self._stream = None
                self.do_snap(job.getFileName())
            except:
                Logger.logException("w", "An execption occured while trying to write to removable drive.")
                message = Message(catalog.i18nc("@info:status", "Could not save to removable drive {0}: {1}").format(self.getName(),str(job.getError())),
                                  title = catalog.i18nc("@info:title", "Error"))
                message.show()
                self.writeError.emit(self)
                return

        self._writing = False
        self.writeFinished.emit(self)
        if job.getResult():
            message = Message(catalog.i18nc("@info:status", "Saved to Removable Drive {0} as {1}").format(self.getName(), os.path.basename(job.getFileName())), title = catalog.i18nc("@info:title", "File Saved"))
            message.addAction("eject", catalog.i18nc("@action:button", "Eject"), "eject", catalog.i18nc("@action", "Eject removable device {0}").format(self.getName()))
            message.actionTriggered.connect(self._onActionTriggered)
            message.show()
            self.writeSuccess.emit(self)
        else:
            message = Message(catalog.i18nc("@info:status", "Could not save to removable drive {0}: {1}").format(self.getName(), str(job.getError())), title = catalog.i18nc("@info:title", "Warning"))
            message.show()
            self.writeError.emit(self)
        job.getStream().close()

    @call_on_qt_thread
    def do_snap(self,gfile):
        img = Snapshot.snapshot(width = 200, height = 200).scaled(200,200,Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        outdata = ""
        outdata = outdata + self.overseek()
        outdata = outdata + "; bigtree thumbnail end\r\n\r\n"
        outdata = outdata + self.material_usage()
        
        fh = QFile(gfile)
        fh.open(QIODevice.ReadOnly)
        stream = QTextStream(fh)
        stream.setCodec(CODEC)
        fg = stream.readAll() + "\r\n"
        if self.extruder_M2O() == True:
            fg = fg.replace("M104 T0",";M104 T0")
            fg = fg.replace("M104 T1",";M104 T1")
            fg = fg.replace("M109 T0",";M109 T0")
            fg = fg.replace("M109 T1",";M109 T1")
        fh.close()
        bigtree3dfile = os.path.splitext(gfile)[0]+"[Bigtree].gcode"
        fh = QFile(bigtree3dfile)
        fh.open(QIODevice.WriteOnly)
        stream = QTextStream(fh)
        stream.setCodec(CODEC)
        stream << outdata
        stream << fg
        fh.close()
        os.remove(gfile)

    def _onActionTriggered(self, message, action):
        if action == "eject":
            if Application.getInstance().getOutputDeviceManager().getOutputDevicePlugin("RemovableDriveOutputDevice").ejectDevice(self):
                message.hide()

                eject_message = Message(catalog.i18nc("@info:status", "Ejected {0}. You can now safely remove the drive.").format(self.getName()), title = catalog.i18nc("@info:title", "Safely Remove Hardware"))
            else:
                eject_message = Message(catalog.i18nc("@info:status", "Failed to eject {0}. Another program may be using the drive.").format(self.getName()), title = catalog.i18nc("@info:title", "Warning"))
            eject_message.show()
            
    # Appends mterial usage for display on the BTT TFT
    def material_usage(self):
        command = "M118 P0 filament_data L:{filament_amount}m \r\nM118 P0 filament_data W:{filament_weight}g\r\nM118 P0 filament_data C:{filament_cost} \r\n"
        command = command.replace("{filament_amount}", str(Application.getInstance().getPrintInformation().materialLengths))
        command = command.replace("{filament_weight}", str(Application.getInstance().getPrintInformation().materialWeights))
        command = command.replace("{filament_cost}", str(Application.getInstance().getPrintInformation().materialCosts))
        return command
