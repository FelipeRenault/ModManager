from PySide2 import QtWidgets
from ui import ModManagerUI
import os
import platform
import subprocess
import lxml.etree
import lxml.builder
from configobj import ConfigObj
from shutil import which
from distutils.spawn import find_executable

drive, game, user, profiles = "C:/", "Program Files (x86)/Steam/steamapps/common/Divinity Original Sin 2", "Users/Rykari/Documents/Larian Studios/", "Divinity Original Sin 2 Definitive Edition/PlayerProfiles"

def cConfig(path):
    ini = ConfigObj()
    ini.filename = path
    ini["paths"] = {}
    # Paths should be structured: [drive, game, user, profiles]
    ini["paths"]["DE"] = [drive, game, user, profiles]
    #ini["paths"]["Classic"] = [drive, game, user, profiles]
    ini.write()

def lst_profiles():
    path_profiles = os.path.join(ini["DE"][0], ini["DE"][2], ini["DE"][3])
    return next(os.walk(path_profiles))[1]

print(lst_profiles())

#gamefolder = "Divinity Original Sin 2"
#startfolder = "C:/"
#for root,dirs,files in os.walk(startfolder):
#    if gamefolder in dirs:
#        if (root + "\\Classic\EoCApp.exe") or (root + "\\DefEd\Bin\EoCApp.exe"):
#            print(root + "\\" + gamefolder)
#            break
#
#userfolder = "Larian Studios"
#startfolder = "C:/"
#for root, dirs, files in os.walk(startfolder):
#    if userfolder in dirs:
#        if (root + "\\Divinity Original Sin 2") or (root + "\\Divinity Original Sin 2 #Definitive Edition"):
#            print(root + "\\" + userfolder)
#            break
#
#
