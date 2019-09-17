# Completed functions go here
import sys
import os
import lz4.block
from struct import *
import unicodedata
from lxml import etree as et
import binascii as asc
from bitstring import ConstBitStream as cbs

a1 = "c:/Users/Rykari/Documents/Larian Studios/Divinity Original Sin 2 Definitive Edition/Mods/"
#a2 = "EnemyUpgradeOverhaul_046aafd8-ba66-4b37-adfb-519c1a5d04d7.pak"
a2 = "GoodChemistry_1306e6f7-2d41-44d9-9d29-e85f59f24ecb.pak"

# Return meta.lsx of a pak as a string
def parse_pak(path, file):

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

    pak_file = os.path.join(path,file)

    with open(pak_file, "rb") as f:

        # Seek to the end -40 and read from there:
        f.seek(-40, 2)
        root = f.read()

        # Number of files in the file table list
        print(FileListOffset)

        f.seek(FileListOffset)
        test = f.read()[:4]
        print(test)

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

        # metastr is a bytestring. This will convert it and retain the structure:
        xml = metastr.decode("utf-8")
        root = et.fromstring(metastr)
        tree = et.tostring(root)
    return tree
print(parse_pak(a1,a2))
# List of dictionaries generator for intended info
def mods_dictionary(path):
    ''' info:

        Returns a list.
        Each element of this list is a dictionary.
        Each dictionary is a mod entry.
        Each dictionary contains Folder, MD5, Name, UUID & Version

        Example usage:

        Print name of all mods in the dict:
        for i in mods_dictionary():
            print(i["Name"])
    '''

    l1 = []
    p = os.path.dirname(path)

    for file in os.listdir(p):
        if file.endswith('.pak'):

            print('>>> Gathering data from ' + file.split('_',1)[0] + '...')
            d1 = {}
            # xml = meta.lsx as bytestring
            xml = parse_pak(p, file)
            tree = et.fromstring(xml)
            ModuleInfo = tree.xpath('//node[@id="ModuleInfo"]')[0]

            for attribute in ModuleInfo:
                d1[attribute.attrib.get("id")] = attribute.attrib.get("value")
            l1.append(d1)
        else:
            pass
    return l1

#print(mods_dictionary(a1))
