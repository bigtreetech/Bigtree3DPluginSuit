# Copyright (c) 2017 Looming
# Cura is released under the terms of the LGPLv3 or higher.

from . import Bigtree3DStore


def getMetaData():
    return {}


def register(app):
    return {
        "output_device": Bigtree3DStore.Bigtree3DStorePlugin(),
        }
