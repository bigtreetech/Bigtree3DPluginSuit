# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Platform import Platform
from UM.Logger import Logger


def getMetaData():
    return {}

def register(app):
    if Platform.isWindows():
        from . import BigtreeWindowsRemovableDrivePlugin
        return { "output_device": BigtreeWindowsRemovableDrivePlugin.BigtreeWindowsRemovableDrivePlugin() }
    elif Platform.isOSX():
        from . import BigtreeOSXRemovableDrivePlugin
        return { "output_device": BigtreeOSXRemovableDrivePlugin.BigtreeOSXRemovableDrivePlugin() }
    elif Platform.isLinux():
        from . import BigtreeLinuxRemovableDrivePlugin
        return { "output_device": BigtreeLinuxRemovableDrivePlugin.BigtreeLinuxRemovableDrivePlugin() }
    else:
        Logger.log("e", "Unsupported system, thus no removable device hotplugging support available.")
        return { }
