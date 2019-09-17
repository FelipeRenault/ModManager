# Completed functions go here
import os
import bs4 as bs
from lxml import etree as et
import lz4.block
from struct import *
import unicodedata
import time
start = time.time()

a1 = "c:/Users/Rykari/Documents/Larian Studios/Divinity Original Sin 2 Definitive Edition/Mods/"
a2 = "AddedEnhancedTalents_b0dc4fb9-4774-4ff8-b2f8-523497556906_51fb2db2-5794-237f-5f24-41a892d5a04e.pak"
#a1 = "c:/Program Files (x86)/Steam/steamapps/common/Divinity Original Sin 2/Data/"
#a2 = "Game.pak"

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

    l1 = [] # List of dicts
    l2 = [] # List of exceptions
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
    return l1,l2

#for mods in data_list:
#    print(mods["Name"])

info = mods_dictionary(a1)
data_list = info[0]
error_list = info[1]
def get_installed():
    installed_list = []

    for mods in data_list:
        installed_list.append(mods["Name"])
    return installed_list
# x = get_installed()
# print(x)

def improved_get_package_info():
    installed_list = []

    # Create a tuple containing Name,Author,Version,UUID,Folder
    for mods in data_list:
        installed_list.append(
            (mods["Name"], mods["Author"], mods["Version"], mods["UUID"], mods["Folder"]))
    return installed_list

x = improved_get_package_info()
print(x)


#print(data_list[0])
#for i in mods_dictionary(a1)[0]:
#    print(i["Name"])

#p = os.path.dirname(a1)
#fullpath = os.path.join(a1,a2)
#print(parse_pak(fullpath).decode("utf-8"))
