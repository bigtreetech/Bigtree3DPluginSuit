# Copyright (c) 2017 Ultimaker B.V.
# This example is released under the terms of the AGPLv3 or higher.

from . import ResolutionExtension

def getMetaData():
    return {}

def register(app):
    return {"extension": ResolutionExtension.ResolutionExtension()}
