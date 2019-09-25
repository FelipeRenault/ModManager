import sys
#from PySide2 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDropEvent
from PyQt5.QtWidgets import QTableWidget, QAbstractItemView, QTableWidgetItem, QWidget, QHBoxLayout, QApplication, QListWidget, QMessageBox
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from ui import ModManagerUI
import os
import subprocess
from lxml import etree as et
import lxml.etree
import lxml.builder
from configobj import ConfigObj
from glob import glob
import os
import bs4 as bs
import lz4.block
from struct import *
import unicodedata
import time
start = time.time()

'''
Core function of the whole application:

1. Get information from all installed mods
DONE

2. Display them in a tree widget
DONE

3. Create, save & load custom load orders as xml
FUNCTIONAL BUT NOT FINISHED - AUTO POPULATE WHEN CHANGED | Add update btn

4.Reordering via drag and drop. Including multi select.
FUNCTIONAL BUT NOT FINISHED - NEEDS SHORTCUTS VIA EVENT LISTENERS

5. Allow the user to add custom groups
{WIP}

'''

current_path = os.path.dirname(os.path.realpath(__file__))
uifile = os.path.join(current_path,"ui\ModManager.ui")
template_file = os.path.join(current_path,"template.xml")






class ModManager(ModManagerUI.Ui_MainWindow, QtWidgets.QMainWindow):

    def __init__(self):
        super(ModManager, self).__init__()
        #self.setupUi(self)
        uic.loadUi(uifile, self)
        self.setWindowTitle("Divinity: Original Sin 2 Mod Manager")

        # Buttons
        self.button_UserFolder.clicked.connect(self.select_UserFolder)
        self.btnCreateLO.clicked.connect(self.fnCreateLO)
        self.btnDeleteLO.clicked.connect(self.fnDeleteLO)
        self.button_GameFolder.clicked.connect(self.select_GameFolder)
        self.radio_DE.toggled.connect(lambda:self.select_Mode(self.radio_DE))
        self.radio_Classic.toggled.connect(lambda:self.select_Mode(self.radio_Classic))
        self.comboBox_Profiles.activated[str].connect(self.getCurrentSelectedProfile)
        self.saveToLO.clicked.connect(self.updateLO)
        self.btnAddGroup.clicked.connect(self.addgroup)
        self.button_Launch.clicked.connect(self.fnLaunch)
        self.btnOpenFolderMods.clicked.connect(self.fnOpenModsFolder)
        self.btnOpenWorkshopFolder.clicked.connect(self.fnOpenWorkshopFolder)
        self.btnOpenGameFolder.clicked.connect(self.fnOpenGameFolder)
        self.combo_customlo.activated[str].connect(self.getCLOD)

        headerchange = self.treeFinalView.header()
        headerchange.setVisible(True)
        headerchange.resizeSection(0,25)
        headerchange.setSectionsMovable(False)
        headerchange.setEnabled(True)
        headerchange.setDefaultAlignment(Qt.AlignCenter)
        self.treeFinalView.setColumnHidden(6,1)
        self.treeFinalView.setColumnHidden(5,1)
        self.treeFinalView.setColumnHidden(4,1)
        self.treeFinalView.setColumnHidden(3,1)
        self.treeFinalView.setColumnHidden(2,0)

        # -- Variables -- #
        lar_folder = os.path.join(os.environ['USERPROFILE'], "Documents\Larian Studios")
        game_folder = os.path.join(os.environ['PROGRAMFILES(X86)'], "Steam\steamapps\common\Divinity Original Sin 2")
        self.workshop_folder = os.path.join(os.environ['PROGRAMFILES(X86)'], "Steam\steamapps\workshop\content/435150")
        self.gamefolder = None # PATH 2 GAME FOLDER
        self.larfolder = None # PATH TO LARIAN FOLDER
        self.path_mods = None # PATH TO MODS FOLDER
        self.path_profiles = None # PATH TO PROFILES FOLDER
        self.path_exe = None # PATH TO EXE
        self.profiles = None # ?
        self.selectedProfile = None # VALUE OF THE CURRENTLY SELECTED PROFILE
        self.selectedLO = None # VALUE OF THE CURRENTLY SELECTED LOAD ORDER
        self.data_list = None # DICTIONARY OF MODS
        self.loadOrder_list = None # LIST OF UUIDS 4 SORTING data_list MOD ORDER
        self.enabled_list = None # LIST OF UUID'S FOR ENABLING data_list
        self.final_dct = self.getFinalAsDct() # DICTIONARY OF DATA DISPLAYED IN LIST INCLUDING ENABLE STATUS
        self.sorted_list = None # SORTED data_list
        self.dirCLO = "userdata\CLOD"
        self.busy = False # USED FOR PROCESS MANAGEMENT AKA IMPATIENT RETARD CONTROL

        # -- Auto insert best guess at Larian folder -- #
        for dirs in os.listdir(lar_folder):

            if 'Divinity Original Sin 2' or 'Divinity Original Sin 2 Definitive Edition' in os.path.isdir(os.path.join(lar_folder, dirs)):
            # If relevant folders are found:

                # Insert the path
                self.textbox_UserFolder.setText(lar_folder)

                # Enable the field
                self.textbox_UserFolder.setDisabled(False)

                # Set larfolder to be the path in the Larian Folder text box
                self.larfolder = self.textbox_UserFolder.toPlainText()

                # Set path_profiles
                self.path_profiles = os.path.join(self.larfolder, "Divinity Original Sin 2 Definitive Edition\\PlayerProfiles\\")

                # Set path_mods
                self.path_mods = os.path.join(self.larfolder, "Divinity Original Sin 2 Definitive Edition\\Mods\\")

                # Since path has been found populate installed mods list:
                #self.table_TestImport_fn()

                # Changing this to write an item to treeFinalView that has all data needed (name, authour etc)
        if self.larfolder:
            self.data_list = self.mods_dictionary(self.path_mods)[0]
            if len(self.data_list) != int(0):
                print(self.data_list)
                self.populateInstalledFinal(self.data_list)
                self.populate_LO()
            else:
                return



        # -- Auto insert best guess at game folder -- #
        for dirs in os.listdir(game_folder):

            if 'bin' or 'DefEd' in os.path.isdir(os.path.join(game_folder, dirs)):
            # If we find these folders:

                self.textbox_GameFolder.setText(game_folder)
                # Insert the path into text box

                self.textbox_GameFolder.setDisabled(False)
                # Enable the Text box

                self.gamefolder = self.textbox_GameFolder.toPlainText()
                # Set gamefolder to be the path in the Game Folder text box

        # -- If MM auto found folders, this will enable DE/Classic Fields -- #
        if self.gamefolder and self.larfolder:
            self.radio_Classic.setEnabled(True)
            self.radio_DE.setEnabled(True)

    #
    #   END OF __init__
    #


    # ========================= BUTTON FUNCTIONS
    def fnCreateLO(self):
        text, ok = QtWidgets.QInputDialog.getText(self,'Create custom load order:','Enter Name:')

        if ok:
            if not os.path.isfile(os.path.join(current_path, self.dirCLO,str(text+".xml"))):
                f = open(os.path.join(current_path, self.dirCLO,str(text+".xml")), "w")
                f.write("")
                f.close
                self.populate_LO()
            else:
                QMessageBox.about(self, "Error", "This file already exists, try another name")

    def fnDeleteLO(self):
        try:
            qb = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question,'','Are you sure you want to delete '+self.selectedLO+'?', QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No)
        except AttributeError as e:
            QMessageBox.about(self, "Error", "Please select a load order")
            return


        result = qb.exec_()

        if result == qb.Yes:
            for file in next(os.walk(os.path.join(current_path,self.dirCLO)))[2]:
                if file == str(self.selectedLO):
                    os.remove(os.path.join(current_path,self.dirCLO,self.selectedLO))
            self.populate_LO()
        else:
            return

    def fnOpenWorkshopFolder(self):
        path = os.path.realpath(self.workshop_folder)
        os.startfile(path)

    def fnOpenModsFolder(self):
        path = os.path.realpath(self.path_mods)
        os.startfile(path)

    def fnOpenGameFolder(self):
        path = os.path.realpath(self.gamefolder)
        os.startfile(path)

    def updateLO(self):

        def oldsavefn(self):
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;XML Files (*.xml)",options=options)
            file = open(filename,'w')
            file.write("")
            file.close()
            # Need to incorporate the writer function here
            self.modsettingsWriter(filename)

        try:
            qb = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question,'','Are you sure you want to update '+self.selectedLO+'?', QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No)
        except AttributeError as e:
            QMessageBox.about(self, "Error", "Please select a load order")
            return

        result = qb.exec_()

        if result == qb.Yes:
            if self.selectedLO != None:
                self.modsettingsWriter(os.path.join(current_path, self.dirCLO,self.selectedLO))
        else:
            return

    def fnLaunch():
        pass

    def select_UserFolder(self):
        user_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Larian Folder")
        if user_path:
            self.textbox_UserFolder.setText(user_path)
            self.larfolder = user_path
            self.enable_select_mode()
        return larfolder

    def select_GameFolder(self):
        game_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Game Folder"
            )
        if game_path:
            self.textbox_GameFolder.setText(game_path)
            self.gamefolder = game_path
            self.enable_select_mode()

    # DE / Classic radio button handler
    def select_Mode(self,b):
        if b.text() == "DE":
            if b.isChecked() == True:
                # Set relevant Paths
                self.path_profiles = os.path.join(self.larfolder, "Divinity Original Sin 2 Definitive Edition\\PlayerProfiles\\")
                self.path_mods = os.path.join(self.larfolder, "Divinity Original Sin 2 Definitive Edition\\Mods\\")
                self.path_exe = os.path.join(self.gamefolder, "DefEd\\bin\\EoCApp.exe")

                # Set relevant Vars
                self.profiles = self.lst_profiles(self.path_profiles)
                # Functions

                self.comboBox_Profiles.setEnabled(True)

                # Populate Profiles
                self.populate_profiles()
                # Change Launch button accordingly
                self.button_Launch.setText("Launch DE")

        if b.text() == "Classic":
            # Set Clasic Paths
            if b.isChecked() == True:
                # Call fn that handles DE paths
                # Ignored for now

                # Change launch button accordingly
                self.button_Launch.setText("Launch Classic")

    # Add Group btn fn
    # NOTE: UNFINISHED
    def addgroup(self):
        text, ok = QtWidgets.QInputDialog.getText(self,'Create grouping:','Enter name for grouping:')

        if ok:
            items = QtWidgets.QTreeWidgetItem(self.treeFinalView)
            items.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDropEnabled | Qt.ItemIsUserCheckable)
            items.setCheckState(0,1)
            items.setText(6,str("True"))
            items.setText(1,str(text))



    # ========================= COMBO BOX FUNCTIONS
    # Save the name of the currently selected LO to self.selectedLO
    def getCLOD(self):

        if not self.busy:

            # init error handling:
            if self.selectedProfile == None:
                QMessageBox.about(self, "Error", "Please select a profile")
                self.selectedLO = None
                self.populate_LO()
                return

            if str(self.combo_customlo.currentText()) != str("--Chose a custom LO--"):

                # Save current text to a string:
                self.selectedLO = str(self.combo_customlo.currentText())

                file = os.path.join(current_path, self.dirCLO, self.selectedLO)

                # if it's empty don't bother doing anything:
                if os.stat(file).st_size != 0:
                    # Otherwise reorder the list:
                    self.reorderInstalledFinal(file)

                print("Currently Selected Load Order is " + self.selectedLO)
            else:
                self.selectedLO = None
        else:
            return

    # Save the name of the currently selected profile to self.selectedProfile
    def getCurrentSelectedProfile(self):
        if str(self.comboBox_Profiles.currentText()) != str("--Chose a Profile--"):
            self.selectedProfile = str(self.comboBox_Profiles.currentText())
            print("Currently Selected Profile is " + self.selectedProfile)

        else:
            self.selectedProfile = None



    # ========================= POPULATE FUNCTIONS
    # Populates profile list
    def populate_profiles(self):

        # Clean list
        self.comboBox_Profiles.clear()

        # Add a blank by default
        items = QtWidgets.QComboBox.addItem(self.comboBox_Profiles, str("--Chose a Profile--"))

        for e in self.profiles:
            items = QtWidgets.QComboBox.addItem(self.comboBox_Profiles,str(e))

    # Populates LOs
    def populate_LO(self):

        clods = next(os.walk(os.path.join(current_path, self.dirCLO)))[2]
        # Clean list
        self.combo_customlo.clear()

        # Add a blank by default
        if len(os.listdir(os.path.join(current_path, self.dirCLO)))==0:
            items = QtWidgets.QComboBox.addItem(self.combo_customlo, str("--Create a custom LO--"))
        else:
            items = QtWidgets.QComboBox.addItem(self.combo_customlo, str("--Chose a custom LO--"))

        for e in clods:
            items = QtWidgets.QComboBox.addItem(self.combo_customlo,str(e))

    # Populate Tree View with data
    def populateInstalledFinal(self, somelist):
        # Clear treeFinalView
        self.treeFinalView.clear()

        # Add an item to treeFinalView & setText to relevant columns
        for i, mods in enumerate(somelist):
            items = QtWidgets.QTreeWidgetItem(self.treeFinalView)
            items.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
            items.setCheckState(0,0)

            # handles population when there's no enabled list to compare
            if self.enabled_list != None:
                if mods["UUID"] in self.enabled_list:
                    items.setCheckState(0,2)
                else:
                    items.setCheckState(0,0)

            if mods["Name"]:
                items.setText(1,str(mods["Name"]))
            else:
                items.setText(2,str('NONE'))

            if mods["Author"]:
                items.setText(2,str(mods["Author"]))
            else:
                items.setText(2,str('NONE'))

            if mods["Version"]:
                items.setText(3,str(mods["Version"]))
            else:
                items.setText(3,str('NONE'))

            if mods["UUID"]:
                items.setText(4,str(mods["UUID"]))
            else:
                items.setText(4,str('NONE'))

            if mods["Folder"]:
                items.setText(5,str(mods["Folder"]))
            else:
                items.setText(5,str('NONE'))

            for i in range(1, self.treeFinalView.headerItem().columnCount() -1):
                self.treeFinalView.resizeColumnToContents(i)

    def busytest(func):
        def inner(self, *args, **kwargs):
            job_function = func(self,*args, **kwargs)
            import runner.py

            self.combo_customlo.setEnabled(False)
        return inner


    # Reorder list based on a modsettings file
    @busytest
    def reorderInstalledFinal(self, file=""):

        if file =="":
            file = os.path.join(self.path_profiles, self.selectedProfile, "modsettings.lsx")
        try:
            self.getLoadOrderFromFile(file)
        except AttributeError as e:
            QMessageBox.about(self, "Error", "Please select a profile")
            return

        # Turn the lstLoadOrder into an index dictionary:
        lstdct = {uuid: i for i, uuid in enumerate(self.loadOrder_list)}

        # import data_lst
        self.sorted_list = self.data_list

        # self.sorted_list.sort(key=lambda x: lstdct[x["UUID"]])

        try:
            self.sorted_list.sort(key=lambda x: lstdct.get(x["UUID"], float('inf')))
        except KeyError as e:
            self.sorted_list.sort(key=lambda x: lstdct[x["UUID"], float('inf')])
            QMessageBox.about(self, "Error", "KeyError - Reason '%s'" % str(e))
            return
        # Then repopulate it:
        self.getEnabledOrderFromFile(file)
        self.populateInstalledFinal(self.sorted_list)

    # Ticks boxes in viewer based on UUID's under 'Mods' node
    def enableInstalledFinal(self):
        try:
            self.getEnabledOrderFromFile()
        except AttributeError as e:
            QMessageBox.about(self, "Error", "Shit!! A motherfuckin' bug!! SQUISH IT!!!")
            return


        if len(self.enabled_list) <= int(1):
            QMessageBox.about(self, "Error", "There are no mods to enable")
            return
        else:
            # get the number of items in treeFinalView & for loop:
            for i in range(self.treeFinalView.topLevelItemCount()):

                # set the topmost item to variable:
                current_item = self.treeFinalView.topLevelItem(i)

                # if column 4 UUID is in enabled_list then check box in column 0
                if current_item.data(4,Qt.DisplayRole) in self.enabled_list:
                    current_item.setCheckState(0,2)

                # Otherwise Uncheck it
                else:
                    current_item.setCheckState(0,0)

    # Find UUID of each node in ModOrder & save them to self.enabled_list as a list
    def getLoadOrderFromFile(self,file=""):
        if not file:
            file = os.path.join(self.path_profiles, self.selectedProfile, "modsettings.lsx")

        # We have an ordered dict of UUID's created by getLoadOrderFromFile (self.loadOrder_list)
        if self.selectedProfile != None:
            tree = et.parse(file)
            installed_mods_root = tree.xpath('//node[@id="ModOrder"]')[0]
            imr = installed_mods_root
            installed_mods = imr.xpath('.//node[@id="Module"]')
            im = installed_mods
            lstLoadOrder = []

            for mname in im:
                temp = mname.xpath('.//attribute[contains(@id, "UUID")]')
                uuid = [t.get('value') for t in temp][0]
                if uuid != "1301db3d-1f54-4e98-9be5-5094030916e4":
                    lstLoadOrder.append(uuid)
            self.loadOrder_list = lstLoadOrder

        else:
            return

    # Find UUID of each node in Mods & save them to self.enabled_list as a list
    def getEnabledOrderFromFile(self,file=""):
        if not file:
            file = os.path.join(self.path_profiles, self.selectedProfile, "modsettings.lsx")
        # We have an ordered dict of UUID's created by getLoadOrderFromFile (self.loadOrder_list)

        if self.selectedProfile != None:
            tree = et.parse(file)
            installed_mods_root = tree.xpath('//node[@id="Mods"]')[0]
            imr = installed_mods_root
            installed_mods = imr.xpath('.//node[@id="ModuleShortDesc"]')
            im = installed_mods
            lstIsEnabled = []

            for mname in im:
                temp = mname.xpath('.//attribute[contains(@id, "UUID")]')
                uuid = [t.get('value') for t in temp][0]
                if uuid != "1301db3d-1f54-4e98-9be5-5094030916e4":
                    lstIsEnabled.append(uuid)
            self.enabled_list = lstIsEnabled
        else:
            return




    # ========================= READ/WRITE/LIST/PARSE FUNCTIONS
    # returns the foldernames in playerprofiles as a list
    def lst_profiles(self,path):
        temp_profile_lst = next(os.walk(path))[1]
        try:
            temp_profile_lst.remove("Debug_Client_Profile_1")
        except ValueError:
            pass
        return temp_profile_lst

    # Get the name of all items in a widget
    def getAllItemsFinal(self):
        # Part of getAllItemsFinal
        def getAllSubtreesFromWidget(tree_widget_item):
            nodes = []
            nodes.append(tree_widget_item)
            for i in range(tree_widget_item.childCount()):
                nodes.extend(getAllSubtreesFromWidget(tree_widget_item(i)))
            return nodes

        # Part of getAllItemsFinal
        def getAllItemsFromWidget(tree_widget_item):
            #semi - pseudo code:
            allItems = []
            for i in range(tree_widget_item.topLevelItemCount()):
                top_item = tree_widget_item.topLevelItem(i)
                allItems.extend(getAllSubtreesFromWidget(top_item))
            return allItems

        return getAllItemsFromWidget(self.treeFinalView)

    # Return meta.lsx of a pak
    def parse_pak(self,fullpath):
        ''' Info:

            Dependencies:
                import os
                import lz4.block
                from struct import *
                import unicodedata

            Example usage:

            print(parse_pak(path,file))

            for files in location:
                etc etc

        '''

        with open(fullpath, "rb") as f:

            # Seek to the end -40 and read from there:
            f.seek(-40, 2)
            root = f.read()

            # Get values from the LSPKHeader13 structure:
            Version, FileListOffset, FileListSize, NumParts, SomePartVar, ArchiveGuid = unpack(
                '3I2h24s', root)

            # Number of files in the file table list
            f.seek(FileListOffset)
            FileCount = unpack('I', f.read()[:4])[0]

            # Grab file table list
            f.seek(FileListOffset)
            FileTableList = f.read()[4:FileListSize]

            # Use FileEntry13 structure to calculate the uncompressed size per entry:
            FileEntry13Size = 256 + (32 * 6)

            # Decompress FileTableList using the uncompressed size of all entries:
            DecompressFileTableList = lz4.block.decompress(
                FileTableList, FileCount*FileEntry13Size)

            def desensitize(text):
                return unicodedata.normalize("NFKD", text.casefold())

            def metacheck(text, name):
                dname = desensitize(str(name, encoding="utf-8"))
                tname = desensitize(text)
                return dname.find(tname)

            # Use iter_unpack to find vars for Meta.lsx:
            compare = "meta.lsx"
            for Name, OffsetInFile, SizeOnDisk, UncompressedSize, ArchivePart, Flags, Crc in iter_unpack('256s6I', DecompressFileTableList):
                if metacheck(compare, Name) != -1:
                    Meta = {"Name": Name, "OffsetInFile": OffsetInFile, "SizeOnDisk": SizeOnDisk,
                            "UncompressedSize": UncompressedSize, "ArchivePart": ArchivePart, "Flags": Flags, "Crc": Crc}
            if Meta["Flags"] & 15 == 2:
                f.seek(Meta["OffsetInFile"])
                meta_file = f.read()[:Meta["SizeOnDisk"]]
                metastr = lz4.block.decompress(meta_file, Meta["UncompressedSize"])
            else:
                f.seek(Meta["OffsetInFile"])
                metastr = f.read()[Meta["UncompressedSize"]:]

            # REMEMBER: metastr is a bytestring.
            # use xml = parse_pak(path).decode("utf-8") to convert to literal xml string
        return metastr

    # Generator: List of Dictionaries
    def mods_dictionary(self,path):
        ''' info:

            Returns a list.
            Each element of this list is a dictionary.
            Each dictionary is a mod entry.
            Each dictionary contains Folder, MD5, Name, UUID & Version

            Example usage:

            Print name of all mods in the dict:
            for i in mods_dictionary(a1):
                print(i["Name"])
        '''

        l1 = [] # List of dicts
        l2 = [] # List of exceptions
        p = os.path.dirname(path)

        for file in os.listdir(p):
            if file.endswith('.pak'):

                fullpath = os.path.join(p, file)
                #print('>>> Gathering data from ' + file.split('_', 1)[0] + '...')
                d1 = {}

                try:
                    xml = self.parse_pak(fullpath)
                except Exception as e:
                    # Will eventually expand this to yield a dict of mods that have a set of reasons for failing.
                    print(">>> ERROR!!! " + file + " cannot be read")
                    if "unpack requires a buffer of 4 bytes" in str(e):
                        print("File is corrupt")
                    else:
                        print("Error Message: " + str(e))
                    l2.append(file)

                tree = et.fromstring(xml)
                ModuleInfo = tree.xpath('//node[@id="ModuleInfo"]')[0]
                for attribute in ModuleInfo:
                    d1[attribute.attrib.get("id")] = attribute.attrib.get("value")
                l1.append(d1)
            else:
                pass

        print("{} of {} pak files read & successfully imported in {} seconds".format(
            len(l1),
            len(l1)+len(l2),
            time.time()-start
            ))
        return l1,l2

    # Returns a list of dictionaries from treeFinalView
    def getFinalAsDct(self):

        l3 = []

        # get the number of items in treeFinalView & for loop:
        for i in range(self.treeFinalView.topLevelItemCount()-1):

            d3 = {}
            # set the topmost item to variable:
            current_item = self.treeFinalView.topLevelItem(i)

            if self.treeFinalView.topLevelItem(i).checkState(0) == 2: # 0 = column number
                # Append the each entry in item to dictionary
                d3[self.treeFinalView.headerItem().text(0)] = str('Enabled')
                name = current_item.data(1,0)
            else:
                # Append the each entry in item to dictionary
                d3[self.treeFinalView.headerItem().text(0)] = str('Disabled')
            # get number of columns
            for j in range(self.treeFinalView.headerItem().columnCount() -1):
                d3[self.treeFinalView.headerItem().text(j+1)] = current_item.data(j+1,0)



            # Append the dictionary to the list
            l3.append(d3)
        return l3

    # File parser for saving lsx/xml files
    def modsettingsWriter(self,file):
        tree = et.parse(template_file)
        root = tree.getroot()
        # Create a Module element as object:
        def new_module(uuid):

            ''' Example Module:
                <node id="Module">
                    <attribute id="UUID" value="627f624f-e2b8-4b37-977e-03044e500fec" type="22" />
                </node>
            '''

            ModOrderTree = tree.xpath('//node[@id="ModOrder"]')[0]
            ModOrder = ModOrderTree.find('children')

            uuid = str(uuid)

            module = et.SubElement(ModOrder, "node")
            module.set("id", "Module")

            attribute_uuid = et.SubElement(module, "attribute")
            attribute_uuid.set("id", "UUID")
            attribute_uuid.set("value", uuid)
            attribute_uuid.set("type", "22")
            return module

        # Create a ModuleShortDesc element as object:
        def new_moduleshortdesc(name, author, version, uuid, folder):
            ''' Example:

                <node id="ModuleShortDesc">
                    <attribute id="Folder" value="DivinityOrigins_1301db3d-1f54-4e98-9be5-5094030916e4" type="30" />
                    <attribute id="MD5" value="7bd3315f054f70b25d853a981d2898d7" type="23" />
                    <attribute id="Name" value="Divinity: Original Sin 2" type="22" />
                    <attribute id="UUID" value="1301db3d-1f54-4e98-9be5-5094030916e4" type="22" />
                    <attribute id="Version" value="371202020" type="4" />
                </node>
            '''

            ModsTree = tree.xpath('//node[@id="Mods"]')[0]
            Mods = ModsTree.find('children')
            md5 = ""


            folder, md5, name, uuid, version = str(folder), str(md5), str(name), str(uuid), str(version)

            moduleshortdesc = et.SubElement(Mods, "node")
            moduleshortdesc.set("id", "ModuleShortDesc")

            attribute_folder = et.SubElement(moduleshortdesc, "attribute")
            attribute_folder.set("id", "Folder")
            attribute_folder.set("value", folder)
            attribute_folder.set("type", "30")

            attribute_md5 = et.SubElement(moduleshortdesc, "attribute")
            attribute_md5.set("id", "MD5")
            attribute_md5.set("value", md5)
            attribute_md5.set("type", "23")

            attribute_name = et.SubElement(moduleshortdesc, "attribute")
            attribute_name.set("id", "Name")
            attribute_name.set("value", name)
            attribute_name.set("type", "22")

            attribute_uuid = et.SubElement(moduleshortdesc, "attribute")
            attribute_uuid.set("id", "UUID")
            attribute_uuid.set("value", uuid)
            attribute_uuid.set("type", "22")

            attribute_version = et.SubElement(moduleshortdesc, "attribute")
            attribute_version.set("id", "Version")
            attribute_version.set("value", version)
            attribute_version.set("type", "4")

            return moduleshortdesc

        # Writes some mess to a file
        def generator(final_dictionary):
            data_list = final_dictionary
            # For each dictionary inside data_list
            for mods in data_list:
                order = new_module(mods["UUID"])
                if mods["E"] == str('Enabled'):
                    desc = new_moduleshortdesc(mods["Name"], mods["Author"], mods["Version"], mods["UUID"], mods["Folder"])

            tree.write(file)

        generator(self.getFinalAsDct())

        parser = et.XMLParser(remove_blank_text=True)
        tree = et.parse(file, parser)
        tree.write(file, encoding='utf-8',pretty_print=True,xml_declaration=True)


if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    qt_app = ModManager()
    qt_app.show()
    app.exec_()
