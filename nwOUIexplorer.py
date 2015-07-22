''' Provides a class for parsing a text based IEEE
OUI database for the purpose of looking up the 
manufacturer for a provided MAC address. 

Written by Russell Endicott (rendicott@gmail.com)
'''

import re

''' Offline database sourced from IEEE: 
    http://standards-oui.ieee.org/oui.txt
'''
ouidatabasetextfile = 'oui-database.txt'

try:
    with open(ouidatabasetextfile,'rb') as f:
        ouidatabaselist = f.readlines()
except Exception as ex_ouiload:
    raise Exception_Dataload_OUI_Database(
        "Exception reading ouidatabasetextfile: '" + 
        ouidatabasetextfile + "' : " + str(ex_ouiload))

class Oui():
    ''' Holds properties and methods
    for a parsed OUI
    '''
    def __init__(self):
        pass

class Exception_Dataload_OUI_Database(Exception): pass
class Exception_Constructor_Locator_MacString(Exception): pass
class Exception_Constructor_Locator_MacString_Validation_Short(Exception): pass

class Oui_Locator():
    ''' Locates a particular OUI based
    on MAC address and holds the OUI
    as an object so that properties and
    methods can be called.
    '''
    ouidatabase = ouidatabaselist
    def __init__(self,macstring=None):
        self.maclist = []
        self.oui = '' # First 3 octets of mac sep by dash
        self.manufacturer = None
        self.combo = None
        if macstring != None:
            self.macstring = macstring
            if self.valid_macstring():
                self.normalize_macstring()
                self.make_oui()
                self.manufacturer = self.oui_lookup()
        else:
            raise Exception_Constructor_Locator_MacString(
                'Must provide mac address string as input parameter to Oui_Locator constructor.')
            self.macstring = '00:00:00:00:00:00'
    def normalize_macstring(self):
        ''' takes the mac in whatever format
        and converts to list of two char strings.
        supports: 00-00-00-00-00-00
        supports: 00:00:00:00:00:00
        supports: 0000-0000-0000
        supports: 000000000000
        '''
        tempstring = self.macstring.replace('-','')
        tempstring = tempstring.replace(':','')
        tempstring = tempstring.replace('.','')
        tempstring = tempstring.lower()
        for i in range(0,len(tempstring),2):
            self.maclist.append(tempstring[i:i+2])
    def valid_macstring(self):
        ''' returns true if string looks like
        it might be a mac address
        '''
        valid = True
        re_highletters = re.compile('([g-zG-Z])')
        match_highletters = re.search(re_highletters,self.macstring)
        if len(self.macstring) <= 11:
            raise Exception_Constructor_Locator_MacString_Validation_Short(
                    'Length of provided macstring is <= 11 characters. Must not be MAC.')
            valid = False
        elif match_highletters:
            raise Exception_Constructor_Locator_MacString_Validation_Short(
                    'Provided macstring has chars g-z. Must not be MAC.')
            valid = False
        else:
            valid = True
        return valid
    def make_oui(self):
        ''' Takes the maclist and turns into 
        OUI string which is first three octets
        separated by dash
        '''
        tempstring = '-'.join(self.maclist)
        self.oui = tempstring[0:8]
    def oui_lookup(self):
        ''' Searches through the ouidatabaselist for the given
        mac address. Returns the full manufacturer string. 
        '''
        manu = ''
        searchstring = self.oui.upper()
        for idx,line in enumerate(ouidatabaselist):
            if searchstring in line:
                manu = (line.split('\t'))[2].rstrip('\n ')
                break
        manu = manu.replace('&','')
        manu = manu.replace(',','')
        manu = manu.replace('.','')
        manu = manu.replace('(','-')
        manu = manu.replace(')','-')
        manu = manu.replace(' ','_')
        self.manufacturer = manu
        return(manu)
    def return_combo(self):
        ''' Takes the manufacturer string and 
        appends it to end of mac address in 
        parenthesis.
        '''
        if self.manufacturer == None:
            self.oui_lookup()
        manus = self.manufacturer[:14]
        mactail = ':'.join(self.maclist)
        self.combo = mactail + "("+manus+")"
        return(self.combo)
        
    def __repr__(self):
        return(str(self.maclist))

sampleset = [   "FC-DC-4A-6C-71-6B",
                "00:00:5e:00:01:01",
                "00-00-21-7C-6D-C7",
                "00:30:ab:2b:ec:b2",
                "00:04:96:1e:cf:f0",
                "00d0.062d.d524",
                "0000.5E00.0101",
                "0008.e3ff.ff1c",
                "00:04:96:37:2a:7b",
                "70-5a-b6-b4-b6-a8",
                "E8:CE:06:79:4C:77",
                "A0:5D:C1:1a:8c:2a",
            ]

# section for testing generators
'''
macs = map(lambda x: Oui_Locator(x),sampleset)

for chunk in map((lambda x: x.return_combo()),macs):
    print chunk
'''

#print loc.oui_lookup()
#print loc4.oui