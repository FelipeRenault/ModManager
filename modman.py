import sys
#from PySide2 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDropEvent
from PyQt5.QtWidgets import QTableWidget, QAbstractItemView, QTableWidgetItem, QWidget, QHBoxLayout, QApplication, QListWidget
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

#test

current_path = os.path.dirname(os.path.realpath(__file__))
uifile = os.path.join(current_path,"ui\ModManager.ui")
#print(ConfigObj(os.path.join(current_path, "MMSettings.ini")))


class TableWidgetDragRows(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def dropEvent(self, event: QDropEvent):
        if not event.isAccepted() and event.source() == self:
            drop_row = self.drop_on(event)

            rows = sorted(set(item.row() for item in self.selectedItems()))
            rows_to_move = [[QTableWidgetItem(self.item(row_index, column_index)) for column_index in range(self.columnCount())]
                            for row_index in rows]
            for row_index in reversed(rows):
                self.removeRow(row_index)
                if row_index < drop_row:
                    drop_row -= 1

            for row_index, data in enumerate(rows_to_move):
                row_index += drop_row
                self.insertRow(row_index)
                for column_index, column_data in enumerate(data):
                    self.setItem(row_index, column_index, column_data)
            event.accept()
            for row_index in range(len(rows_to_move)):
                self.item(drop_row + row_index, 0).setSelected(True)
                self.item(drop_row + row_index, 1).setSelected(True)
        super().dropEvent(event)

    def drop_on(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return self.rowCount()

        return index.row() + 1 if self.is_below(event.pos(), index) else index.row()

    def is_below(self, pos, index):
        rect = self.visualRect(index)
        margin = 2
        if pos.y() - rect.top() < margin:
            return False
        elif rect.bottom() - pos.y() < margin:
            return True
        # noinspection PyTypeChecker
        return rect.contains(pos, True) and not (int(self.model().flags(index)) & Qt.ItemIsDropEnabled) and pos.y() >= rect.center().y()


class ModManager(ModManagerUI.Ui_MainWindow, QtWidgets.QMainWindow):

    def __init__(self):
        super(ModManager, self).__init__()
        #self.setupUi(self)
        uic.loadUi(uifile, self)
        self.setWindowTitle("Divinity: Original Sin 2 Mod Manager")
        # Buttons
        self.button_UserFolder.clicked.connect(self.select_UserFolder)
        self.button_GameFolder.clicked.connect(self.select_GameFolder)
        self.radio_DE.toggled.connect(lambda:self.select_Mode(self.radio_DE))
        self.radio_Classic.toggled.connect(lambda:self.select_Mode(self.radio_Classic))
        self.checkbox_HideDisabled.toggled.connect(lambda:self.hide_disabled(self.checkbox_HideDisabled))
        self.comboBox_Profiles.activated[str].connect(self.populate_InstalledMods)
        self.comboBox_Profiles.activated[str].connect(self.populate_LO2)
        self.button_EnableDisableMods.clicked.connect(
            self.EnableDisable_Button)
        self.window2 = None

    # -- Add layout in tab_test -- #
        layout = QtWidgets.QHBoxLayout()
        self.tab_test.setLayout(layout)

    # -- Add Widget to layout in tab_test -- #
        self.table_TestImport = TableWidgetDragRows()
        layout.addWidget(self.table_TestImport)

        self.table_TestImport.setColumnCount(5)
        self.table_TestImport.setHorizontalHeaderLabels(['Name', 'Author', 'Version','UUID','Folder'])


        self.resize(400, 400)
        self.show()

    # -- Init Functions -- #
        self.clean_IM()
        self.clean_LO()

    # -- Variables -- #
        lar_folder = os.path.join(os.environ['USERPROFILE'], "Documents\Larian Studios")
        game_folder = os.path.join(os.environ['PROGRAMFILES(X86)'], "Steam\steamapps\common\Divinity Original Sin 2")
        gamefolder = None
        larfolder = None
        path_mods = None
        path_profiles = None
        path_exe = None
        profiles = None


    # -- Auto insert best guess at Larian folder -- #
        for dirs in os.listdir(lar_folder):

            if 'Divinity Original Sin 2' or 'Divinity Original Sin 2 Definitive Edition' in os.path.isdir(os.path.join(lar_folder, dirs)):
            # If relevant folders are found:

                self.textbox_UserFolder.setText(lar_folder)
                # Insert the path

                self.textbox_UserFolder.setDisabled(False)
                # Enable the field

                self.larfolder = self.textbox_UserFolder.toPlainText()
                # Set larfolder to be the path in the Larian Folder text box

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

    def enable_select_mode(self):
        if self.gamefolder and self.larfolder:
            self.radio_Classic.setEnabled(True)
            self.radio_DE.setEnabled(True)

# -- DE / Classic radio button handler-- #
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

                # Enable Tab Widget
                self.tab_Main.setEnabled(True)

                # Enable Profiles
                self.comboBox_Profiles.setEnabled(True)
                self.tree_LoadOrder.setEnabled(True)
                self.list_InstalledMods.setEnabled(True)

                # Populate Profiles
                self.populate_profiles()
                # Change Launch button accordingly
                self.button_Launch.setText("Launch DE")
                print(self.path_profiles, self.path_mods)

        if b.text() == "Classic":
            # Set Clasic Paths
            if b.isChecked() == True:
                # Call fn that handles DE paths
                # Ignored for now

                # Change launch button accordingly
                self.button_Launch.setText("Launch Classic")

# -- Hide Disabled button handler-- #
    def hide_disabled(self,b):
        if b.text() == "Hide Disabled":
            if b.isChecked() == True:
                # Set relevant Paths
                pass


    def EnableDisable_Button(self):
        if self.window2 is None:
            self.window2 = Form2(self)
        self.window2.show()


# -- Handles all table/List/Tree population -- #
    def populate_profiles(self):

        # -- Populate table_TestImport Widget -- #
        self.table_TestImport.setColumnCount(5)
        self.table_TestImport.setHorizontalHeaderLabels(['Name', 'Author', 'Version','UUID','Folder'])

        # Create a list of tuples where each tuple contains the above headers
        # IE: ('Name', 'Author', 'Version','UUID','Folder')
        def improved_get_package_info():
            info = self.mods_dictionary(self.path_mods)
            data_list = info[0]
            error_list = info[1]
            installed_list = []

            # Create a tuple containing Name,Author,Version,UUID,Folder
            for mods in data_list:
                installed_list.append(
                    (mods["Name"], mods["Author"], mods["Version"], mods["UUID"], mods["Folder"]))
            return installed_list

        items = improved_get_package_info()

        self.table_TestImport.setRowCount(len(items))
        for i, (name,author,version,uuid,folder) in enumerate(items):
            self.table_TestImport.setItem(i,0,QTableWidgetItem(name))
            self.table_TestImport.setItem(i,1,QTableWidgetItem(author))
            self.table_TestImport.setItem(i,2,QTableWidgetItem(version))
            self.table_TestImport.setItem(i,3,QTableWidgetItem(uuid))
            self.table_TestImport.setItem(i,4,QTableWidgetItem(folder))

        self.resize(500,500)
        self.show()

        # Clean list
        self.comboBox_Profiles.clear()

        # Add a blank by default
        items = QtWidgets.QComboBox.addItem(self.comboBox_Profiles, str(" "))

        for e in self.profiles:
            if e != "Debug_Client_Profile_1":
                items = QtWidgets.QComboBox.addItem(self.comboBox_Profiles,str(e))


    def lst_profiles(self,path):
        return next(os.walk(path))[1]

    def getModSettingsLSX(self,profile):
        modsettings = os.path.join(ini["drives"][0], ini["userfolder"],ini["user_de"],"PlayerProfiles/", ini["current_profile", "modsettings.lsx"])
        return modsettings

    def populate_InstalledMods(self,profile):
        self.list_InstalledMods.setEnabled(True)

        # Return meta.lsx of a pak
        def parse_pak(fullpath):
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

        #Generator: List of Dictionaries
        def mods_dictionary(path):
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

            l1 = []  # List of dicts
            l2 = []  # List of exceptions
            p = os.path.dirname(path)

            for file in os.listdir(p):
                if file.endswith('.pak'):

                    fullpath = os.path.join(p, file)
                    #print('>>> Gathering data from ' + file.split('_', 1)[0] + '...')
                    d1 = {}

                    try:
                        xml = parse_pak(fullpath)
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
                    #print(xml.decode("utf-8"))
                else:
                    pass

            print("{} of {} pak files read & successfully imported in {} seconds".format(
                len(l1),
                len(l1)+len(l2),
                time.time()-start
            ))
            return l1, l2


        info = self.mods_dictionary(self.path_mods)
        data_list = info[0]
        error_list = info[1]

        def get_installed():
            installed_list = []

            for mods in data_list:
                installed_list.append(mods["Name"])
            return installed_list

        self.list_InstalledMods.clear()  # Clears the Installed Mods table
        y = get_installed()
        for i, e in enumerate(y):
            items = QtWidgets.QListWidgetItem(self.list_InstalledMods)
            items.setFlags(QtCore.Qt.ItemIsSelectable |
                            QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled)
            #items.setText(0,str(i))
            items.setText(str(e))

    def populate_LO2(self,profile):
        self.tree_LoadOrder.setEnabled(True)

        def get_loadorder():
            modsettings = os.path.join(self.path_profiles, profile, "modsettings.lsx")
            tree = et.parse(modsettings)
            installed_mods_root = tree.xpath('//node[@id="Mods"]')[0]
            imr = installed_mods_root
            installed_mods = imr.xpath('.//node[@id="ModuleShortDesc"]')
            im = installed_mods
            name_list = []

            for mname in im:
                temp = mname.xpath('.//attribute[contains(@id, "Name")]')
                name = [t.get('value') for t in temp][0]
                name_list.append(name)

            return name_list

        self.tree_LoadOrder.clear()  # Clears the Load order
        x = get_loadorder()
        #print(x)
        #x = [x for x in range(0,10)]
        for i, e in enumerate(x):
            if str(e) != "Divinity: Original Sin 2":
                items = QtWidgets.QTreeWidgetItem(self.tree_LoadOrder)
                items.setFlags(QtCore.Qt.ItemIsSelectable |
                            QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled)

                # ------------
                # Here I want to add an if statement that removes mods from 'Installed'

                # Search installed mods with name of mod currently being iterated over.
                li = self.list_InstalledMods.findItems(str(e), Qt.MatchExactly)
                # NOTE: findItems returns a QListWidgetItem as a list.
                    # : To find the text of this object use .text()
                    # : As seen below
                item = li[0].text()
                # If found delete from installed mods
                if str(e) == item:
                    li[0].setFlags(li[0].flags() & ~Qt.ItemIsSelectable)
                    #li[0].setHidden(True)

                # -------------

                items.setText(0, str(e))

    def clean_LO(self):
        self.tree_LoadOrder.clear()  # Clears the Load order

    def clean_IM(self):
        self.list_InstalledMods.clear()  # Clears the Load order

    def active_profile_check():
        pass

    def profile_list_firstrun():
        '''Create a list of profiles and set up a MM folder for each'''
        pass

    def profile_list_check():
        pass

    def installed_firstrun():
        pass

    def installed_check():
        pass

    def toggle_EnableDisable():
        pass

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
                #print(xml.decode("utf-8"))
            else:
                pass

        print("{} of {} pak files read & successfully imported in {} seconds".format(
            len(l1),
            len(l1)+len(l2),
            time.time()-start
            ))
        return l1,l2


if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    qt_app = ModManager()
    qt_app.show()
    app.exec_()
