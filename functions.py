import os
from lxml import etree as et
import bs4 as bs


if not ConfigObj(os.path.join(current_path, "MMSettings.ini")):
    self.cConfig(os.path.join(current_path, "MMSettings.ini"))
else:
    self.ini = ConfigObj(os.path.join(current_path, "MMSettings.ini"))

def getBasePaths(self):
    drives = "C:/"
    game = "Program Files (x86)/Steam/steamapps/common/Divinity Original Sin 2/"
    user = "Users/Rykari/Documents/Larian Studios/"
    lst_base = [drives, game, user]
    return lst_base

def cConfig(self, path):
    ini = ConfigObj()
    ini.filename = path
    ini["base paths"] = {}
    ini["base paths"]["drives"] = [self.getBasePaths()]
    ini["base paths"]["gamefolder"] = self.getBasePaths()[1]
    ini["base paths"]["userfolder"] = self.getBasePaths()[2]
    ini["base paths"]["user_de"] = "Divinity Original Sin 2 Definitive Edition/"
    ini["base paths"]["user_classic"] = "Divinity Original Sin 2/"
    ini["base paths"]["DefED"] = "DefEd/"

    ini["data"] = {}
    ini["data"]["current_profile"] = "Derp"
    ini.write()

# https://www.youtube.com/watch?v=5N066ISH8og


base_path = os.path.dirname(os.path.realpath(__file__))
xml_file = os.path.join(base_path, "data\\modsettings.lsx")

tree = et.parse(xml_file)

installed_mods_root = tree.xpath('//node[@id="Mods"]')[0]
loaded_mods_root = tree.xpath('//node[@id="ModOrder"]')[0]
imr = installed_mods_root
lmr = loaded_mods_root

installed_mods = imr.xpath('.//node[@id="ModuleShortDesc"]')
loaded_mods = lmr.xpath('.//node[@id="Module"]')
im = installed_mods
lm = loaded_mods

number_of_installed_mods = len(im)
number_of_loaded_mods = len(lm)
nim = number_of_installed_mods
nlm = number_of_loaded_mods


folder_list = []
md5_list = []
name_list = []
uuid_list = []
version_list = []

for mfolder in im:
    temp = mfolder.xpath('.//attribute[contains(@id, "Folder")]')
    name = [t.get('value') for t in temp][0]
    folder_list.append(name)

for mmd5 in im:
    temp = mmd5.xpath('.//attribute[contains(@id, "MD5")]')
    md5 = [t.get('value') for t in temp][0]
    md5_list.append(md5)

for mname in im:
    temp = mname.xpath('.//attribute[contains(@id, "Name")]')
    name = [t.get('value') for t in temp][0]
    name_list.append(name)

for muuid in im:
    temp = muuid.xpath('.//attribute[contains(@id, "UUID")]')
    uuid = [t.get('value') for t in temp][0]
    uuid_list.append(uuid)

for mversion in im:
    temp = mversion.xpath('.//attribute[contains(@id, "Version")]')
    version = [t.get('value') for t in temp][0]
    version_list.append(version)

full_list = []


def get_details(mod_object):

    def name():
        return [details]


for num in im:
    temp = mfolder.xpath('.//attribute[contains(@id, "Folder")]')
    name = [t.get('value') for t in temp][0]
    temp = mmd5.xpath('.//attribute[contains(@id, "MD5")]')
    md5 = [t.get('value') for t in temp][0]
    temp = mname.xpath('.//attribute[contains(@id, "Name")]')
    name = [t.get('value') for t in temp][0]
    temp = muuid.xpath('.//attribute[contains(@id, "UUID")]')
    uuid = [t.get('value') for t in temp][0]
    temp = mversion.xpath('.//attribute[contains(@id, "Version")]')
    version = [t.get('value') for t in temp][0]


lst = ['tic', 'tac', 'toe']
for i, v in enumerate([lst]):
    print(i, v)

print(name_list)
