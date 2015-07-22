'''
Runs NETWALK input XML files through the crawler in bulk
for testing/automation.
'''

import os
import re
import datetime
import getpass
import xml.etree.ElementTree as ET

#workdir = "c:\\Russ\\NETWALK\\inputfiles\\"
workdir = "./"
app_fname = 'nw.py'
app_options = '-d -1 -p'
addtl_output_filename_postfix = ''
addtl_output_filename_midfix = ''
addtl_output_filename_prefix = ''

files_all = os.listdir(workdir)
entries = []


re_desc = re.compile('(nwinput-)(?P<desc>.*)(--)')
for f in files_all:
    if 'nwinput' in f:
        re_desc_match = re.search(re_desc,f)
        if re_desc_match:
            desc = re_desc_match.group('desc')
            desc = desc.replace(' ','_')
            entry = {'filename':f,'desc':desc}
            entries.append(entry)

class AuthEntry():
    def __init__(self):
        self.username = ''
        self.password = ''
        self.id = ''
        self.tomod = None
    def __eq__(self, other):
        return self.username==other.username
    def __hash__(self):
        return hash(('username', self.username))

scsadmin = AuthEntry()
scradmin = AuthEntry()
admin1 = AuthEntry()
admin2 = AuthEntry()

scsadmin.username = 'admin'
scsadmin.password = 'password'

scradmin.username = 'admin'
scradmin.password = 'password2'

admin1.username = 'admin'
admin1.password = 'password3'

admin2.username = 'admin'
admin2.password = 'password4'

jelly = []
jelly.append(scsadmin)
jelly.append(scradmin)
jelly.append(admin1)
jelly.append(admin2)


def modifyXMLpasswords(fileXMLInput):
    ''' This function takes the input XML and parses it into
    then changes the password fields.

    '''
    auth = []
    # first try and open the XML file
    fname = workdir + fileXMLInput
    '''
    with open(fname,'rb') as f:
        xml_list = f.readlines()
    xml_string = ''.join(xml_list)
    '''
    done = []
    try:
        tree = ET.parse(fname)
        root = tree.getroot()
        xml_tag_possibilities = root.findall("./target/auth/possibility")
        for xml_tag in xml_tag_possibilities:
            string_uname = xml_tag.find('username').text
            #print "Working on tag: " + string_uname
            for authobj in jelly:
                #print("\tauthobj.id:" + authobj.id )
                if authobj.username == string_uname:
                    xml_tag_password = xml_tag.find('password')
                    if authobj.id == '':
                        authobj.id = xml_tag.attrib.get('id')
                        #print("\t\t\tCurrent authobj.id = "+authobj.id+" Updating: " + xml_tag.attrib.get('id') + " " + xml_tag.find('username').text + " with password: " + authobj.password)
                        xml_tag_password.text = authobj.password
                        break
                    

        # now rewrite the file
        tree.write(fname)
    except Exception as e:
        print(str(e))

def validate_outputfile(filename):
    ''' Examines output xml and returns 
    True if file looks good or False otherwise
    '''
    with open(filename,'rb') as f:
        filelist = f.readlines()
    returnvalue = True
    if len(filelist) < 2:
        returnvalue = False
    else:
        returnvalue = True
    return(returnvalue)

def zip_and_delete(descriptor,timestamp,expected_outputfile):
    # try and validate data in outputfile
    if not validate_outputfile(expected_outputfile):
        addtl_output_filename_midfix = 'FAILED-'
    else:
        addtl_output_filename_midfix = 'SUCCESS-'
    rundirlist = os.listdir(os.getcwd())
    t_filelist = []
    for filer in rundirlist:
        if '.log' in filer or '.sh' in filer:
            t_filelist.append(filer)
    # now zip up the files
    import zipfile
    compression = zipfile.ZIP_DEFLATED
    extension = '.zip'
    zipfilename = "{0}{1}-{2}{3}{4}{5}".format(
                                addtl_output_filename_prefix,
                                timestamp,
                                addtl_output_filename_midfix,
                                descriptor,
                                addtl_output_filename_postfix,
                                extension,
                                )
    try:
        zf = zipfile.ZipFile(zipfilename,mode='w')
        for f in t_filelist:
            zf.write(f,compress_type=compression)
        zf.close()
        print("Wrote the following zipfile: " + zipfilename)
    except Exception as ee:
        print(str(ee))
    # now delete the raw syslogs to save space
    try:
        for f in t_filelist:
            os.remove(f)
    except Exception as ee:
        print("Exception trying to delete raw data txt files: "+ str(ee))

    try:
        env_abspath = os.path.abspath(zipfilename)
        # append zip file to file log
    except Exception as ee:
        print("Exception pulling filename absolute path: " + str(ee))

def buildcommand(entry,timestamp):
    filename_input = entry.get('filename')
    descriptor = entry.get('desc')
    def dofilename(extension):
        filename_output = "{0}{1}-{2}{3}{4}{5}".format(
                                addtl_output_filename_prefix,
                                timestamp,
                                addtl_output_filename_midfix,
                                descriptor,
                                addtl_output_filename_postfix,
                                extension,
                                )
        return filename_output
    filename_output = dofilename(".xml")
    filename_log_output = dofilename(".log")
    logging_filename_option = "-l " + filename_log_output
    command = 'python {0} -i {1} -o {2} {3} {4}'.format(
                            app_fname,
                            filename_input,
                            filename_output,
                            app_options,
                            logging_filename_option,
                            )
    return(command,filename_output)


for e in entries:
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    modifyXMLpasswords(e.get('filename'))
    command,expected_outputfile = buildcommand(e,timestamp)
    # run command
    try:
        print command
        os.system(command)
    except Exception as ex_run:
        print("Exception running command: " + str(ex_run))
    # zip and delete all log and sh files
    zip_and_delete(e.get('desc'),timestamp,expected_outputfile)
