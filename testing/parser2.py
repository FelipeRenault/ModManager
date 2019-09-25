import os
import subprocess
from lxml import etree as et
import lxml.etree
import lxml.builder
import bs4 as bs
import pprint

a1 = "c:/Users/Rykari/Documents/Larian Studios/Divinity Original Sin 2 Definitive Edition/PlayerProfiles/Rykari/"
a2 = "modsettings.lsx"

''' Root structure of modsettings.lsx:
    <?xml version="1.0" encoding="UTF-8" ?>
    <save>
        <header version="2" />
        <version major="3" minor="6" revision="2" build="0" />
        <region id="ModuleSettings">
            <node id="root">
                <children>
                    <node id="ModOrder">
                        <children>

                            == ModOrder Nodes ==

                        </children>
                    </node>
                    <node id="Mods">
                        <children>

                            == Mods Nodes ==

                        </children>
                    </node>
                </children>
            </node>
        </region>
    </save>
'''

# Create Element Objects of ModOrder & Mods:
#ModOrder = tree.xpath('//node[@id="ModOrder"]')[0][0] # [0][0] Moves this element object into <Children>

# Create a dct of all mods in Mods
#inner_dictionary = { "Folder":folder, "MD5":md5, "Name":name, "UUID":uuid, "Version":version }
#outer_dictionary = { position : inner_dictionary }

# List of dictionaries containing file info pulled from modsettings.lsx
def mods_dictionary(path,file):

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

    parser = et.XMLParser(remove_blank_text=True)

    p = os.path.dirname(path)
    meta = os.path.join(p, file)
    tree = et.parse(meta, parser)

    Mods = tree.xpath('//node[@id="Mods"]')[0][0]

    l1 = []
    for mshortdesc in Mods:
        d1 = {}
        for i in mshortdesc:
            d1[i.attrib.get("id")] = i.attrib.get("value")
        l1.append(d1)
    if "Divinity: Original Sin 2" in l1[0]["Name"]:
        del l1[0]
    return l1
print(mods_dictionary(a1,a2))

# Create a function that writes to modsettings.lsx
def settings_writer():
    for i in mods_dictionary():
        new_module(i["UUID"])
    pass

# Create a Module element as object:
def new_module(uuid):

    ''' Example Module:
        <node id="Module">
            <attribute id="UUID" value="627f624f-e2b8-4b37-977e-03044e500fec" type="22" />
        </node>
    '''

    uuid = str(uuid)

    module = et.SubElement("ModOrder", "node")
    module.set("id", "Module")

    attribute_uuid = et.SubElement(module, "attribute")
    attribute_uuid.set("id", "UUID")
    attribute_uuid.set("value", uuid)
    attribute_uuid.set("type", "22")
    return module

# Create a ModuleShortDesc element as object:
def new_moduleshortdesc(folder,md5,name,uuid,version):
    ''' Example:

        <node id="ModuleShortDesc">
            <attribute id="Folder" value="DivinityOrigins_1301db3d-1f54-4e98-9be5-5094030916e4" type="30" />
            <attribute id="MD5" value="7bd3315f054f70b25d853a981d2898d7" type="23" />
            <attribute id="Name" value="Divinity: Original Sin 2" type="22" />
            <attribute id="UUID" value="1301db3d-1f54-4e98-9be5-5094030916e4" type="22" />
            <attribute id="Version" value="371202020" type="4" />
        </node>
    '''

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

# Write Module & ModuleShortDesc to file
def writer():
    f = open('testwrite.lsx','w')
    order = new_module("testuuid")
    desc = new_moduleshortdesc("testfolder", "testmd5", "testname", "testuuid", "testver")

    t1 = et.tostring(order, encoding="unicode",pretty_print=True)
    t2 = et.tostring(desc, encoding="unicode",pretty_print=True)
    #encoding vital as default is bytestring & lxml cannot write() this
    f.write(t1)
    f.write(t2)

writer()



''' lxml examples and explanations:

    for e1 in save: # This will return 3 elements with tags: Header, version and region
        print("Children of <{}>: {}".format(save.tag,e1.tag))
        for e2 in e1: # This will return 1 element: <node id="root">
            print("Children of <{}>: {}".format(e1.tag,e2.tag))
            for e3 in e2:
                print("Children of <{}>: {}".format(e2.tag,e3.tag))
                for e4 in e3:
                    print("Children of <{}>: <{} {}>".format(e3.tag, e4.tag, e4.attrib))
'''
