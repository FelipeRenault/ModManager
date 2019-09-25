# Completed functions go here
import sys
import os
import lz4.block
from struct import *
import unicodedata
from lxml import etree as et
from lxml import objectify
from bs4 import BeautifulSoup
import time
from io import BytesIO
start = time.time()
import xml.etree.ElementTree as ET

a1 = "c:/Users/Rykari/Documents/Larian Studios/Divinity Original Sin 2 Definitive Edition/Mods/"
current_path = os.path.dirname(os.path.realpath(__file__))
template_file = os.path.join(current_path,"template.xml")
test_file = os.path.join(current_path,"testwrite.xml")
lar_folder = os.path.join(os.environ['USERPROFILE'], "Documents\Larian Studios")
path_mods = os.path.join(lar_folder, "Divinity Original Sin 2 Definitive Edition\Mods")

current_path = os.path.dirname(os.path.realpath(__file__))
template_file = os.path.join(current_path,"template.xml")

tree = et.parse(template_file)
root = tree.getroot()

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

# Generator: List of Dictionaries
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

# Works:
#ModOrderTree = tree.findall('//node[@id="ModOrder"]')[0]
#ModOrder = ModOrderTree.find('children')


###########################
# Element generators
###########################


# Create a Module element as object:
def new_module(uuid):

    ''' Example Module:
        <node id="Module">
            <attribute id="UUID" value="627f624f-e2b8-4b37-977e-03044e500fec" type="22" />
        </node>
    '''
    # ModOrderTree = element tree object @ <node id="Module">
    ModOrderTree = root.xpath('.//node[@id="ModOrder"]')[0]

    # ModOrder = element tree object @ <children>
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

# Generator
def modsettingsWriter():
    info = mods_dictionary(a1)
    data_list = info[0]
    error_list = info[1]
    installed_list = []

    # Create a tuple containing Name,Author,Version,UUID,Folder
    for mods in data_list:
        with io.open('testwrite.lsx','w', encoding='utf-8') as f:
            order = new_module(mods["UUID"])
            desc = new_moduleshortdesc(mods["Name"], mods["Author"], mods["Version"], mods["UUID"], mods["Folder"])


            t1 = et.tostring(order, encoding="unicode",method="xml",pretty_print=True)
            t2 = et.tostring(desc, encoding="unicode",pretty_print=True)
            #   encoding vital as default is bytestring & lxml cannot write() this
            f.write(t1)
            f.write(t2)
            f.close()

            tree.write(test_file)

    f.close()


def generator2():

    # mods_dictionary returns 2 lists of dictionaries:
    info = mods_dictionary(a1)

    # info[0] contains a list of dictionaries.
    # Each dictionary contains information of each mod pulled from meta.lsx file inside each pak
    data_list = info[0]
    # error_list = info[1] # Not needed



    # For each dictionary inside data_list
    for mods in data_list:
        order = new_module(mods["UUID"])
        desc = new_moduleshortdesc(mods["Name"], mods["Author"], mods["Version"], mods["UUID"], mods["Folder"])

    tree.write(test_file)


def writer(file):
    generator2()

    parser = et.XMLParser(remove_blank_text=True)
    tree = et.parse(test_file,parser)
    tree.write(test_file, encoding='utf-8',pretty_print=True,xml_declaration=True)

writer(test_file)
