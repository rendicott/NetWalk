
usagedesc = """
nw_offline -- This script copies the NetWalk code from the 'source' directory and then
scans the current directory for .log files and attempts to process them
using the same parser modules and relationship logic imported from the main
NetWalk imported modules. 

This is intended to be able to test code using the output logs from previously 
successful crawls. The log files are the outputs from the auto-generated shell 
scripts (e.g., expect---51183---Quantum_IDFP10-4.sh-output.log)
"""


import os
import random
import re
import logging
import sys
import shutil
import copy 

destination = os.getcwd()
source = 'c:\\Russ\\NETWALK\\nw'
# source = os.path.abspath('..')
extension = '.py'


copycount_new = 0
filecount = 0
for root, dirs, files in os.walk(source):
    for file in files:
        if file.lower().endswith(extension):
            file_path = os.path.realpath(os.path.join(root, file))
            if 'nw_offline' not in file.lower():
                shutil.copy2(file_path, destination)
                copycount_new += 1

print("Copied " + str(copycount_new) + " of " + str(filecount) + " files.")

import nwClasses
import nwParser_ALU_7705_6450 as schemaModule
import nwConfig
import nwCrawl
import nwOUIexplorer

# Import the stuff we need from the Type module
from nw_NE_Type_SCS_6450 import TypeContainer_ALU_SCS
from nw_NE_Type_SCS_6450 import discoveryCommands
from nw_NE_Type_SCS_6450 import CommandOutput
# from the Type module we want all of our parser classes
from nw_NE_Type_SCS_6450 import Parser_Port
from nw_NE_Type_SCS_6450 import PortGenerator_TypeContainer_ALU_SCS

from nw_NE_Type_SCS_6450 import TableParser_ShowIpInterface
from nw_NE_Type_SCS_6450 import InterfaceGenerator_TypeContainer_ALU_SCS

from nw_NE_Type_SCS_6450 import SectionParser_ShowChassis
from nw_NE_Type_SCS_6450 import ChassisGenerator_TypeContainer_ALU_SCS

from nw_NE_Type_SCS_6450 import Parser_Module
from nw_NE_Type_SCS_6450 import ModuleGenerator_TypeContainer_ALU_SCS

from nw_NE_Type_SCS_6450 import TableParser_ShowVlan
from nw_NE_Type_SCS_6450 import VlanGenerator_TypeContainer_ALU_SCS

from nw_NE_Type_SCS_6450 import TableParser_ShowIpRouterDatabase
from nw_NE_Type_SCS_6450 import RouteGenerator_TypeContainer_ALU_SCS

from nw_NE_Type_SCS_6450 import Parser_Dhcp
from nw_NE_Type_SCS_6450 import DhcpGenerator_TypeContainer_ALU_SCS

from nw_NE_Type_SCS_6450 import SectionParser_ShowConfigurationSnapshot
from nw_NE_Type_SCS_6450 import ConfigurationGenerator_TypeContainer_ALU_SCS

from nw_NE_Type_SCS_6450 import TableParser_ShowArp
from nw_NE_Type_SCS_6450 import ArpGenerator_TypeContainer_ALU_SCS

from nw_NE_Type_SCS_6450 import SectionParser_ShowAmap_RemoteHosts
from nw_NE_Type_SCS_6450 import AmapGenerator_TypeContainer_ALU_SCS

werd = nwClasses.Cfg()

default_logfilename = 'scanning.txt'

def setuplogging(loglevel,printtostdout,logfile):
    #pretty self explanatory. Takes options and sets up logging.
    print "starting up with loglevel",loglevel,logging.getLevelName(loglevel)
    logging.basicConfig(filename=logfile,
                        filemode='w',level=loglevel, 
                        format='%(asctime)s:%(levelname)s:%(message)s')
    if printtostdout:
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(loglevel)
        logger = logging.getLogger()
        logger.addHandler(soh)

def get_random_word(wordLen):
    word = ''
    for i in range(wordLen):
        word += random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
    return word

def get_random_number(wordLen):
    word = ''
    for i in range(wordLen):
        word += random.choice('0123456789')
    return word

def is_logfile(filename):
    if 'nw.log' in filename:
        return False
    elif '.log' in filename:
        return True
    else:
        return False

def build_NEs(filename):
    ne = nwClasses.NetworkElement(get_random_number(5))
    ne.hostname.value = get_random_word(10)
    try:
        #ne.ips.iplist.append('192.168.1.5')
        ne.pulltimestamp.value = '2015-03-18 16:07:20.896777'
        ne.typestring = 'scs'
        ne.type = schemaModule.TypeContainer_ALU_SCS()

        #append the output text to the ne.type.nox_discoveryoutput list
        with open(filename,'rb') as f:
            for line in f:
                ne.type.nox_discoveryoutput.append(line)

        loo_commandlist = schemaModule.chunkdata_alldiscovery_SCS(ne) 

        ''' Build the TYPE section of the NE from the parsers '''
            # initialize the Parser for Port info. Most of the heavy lifting happens during initialization.
        '''start with the ports'''
        p = Parser_Port(loo_commandlist)
        pg = PortGenerator_TypeContainer_ALU_SCS(p)
        ne.type.ports.portlist = pg.portlist
        '''Now the interfaces'''
        ints = None
        ints = TableParser_ShowIpInterface(loo_commandlist)
        ig = InterfaceGenerator_TypeContainer_ALU_SCS(ints)
        ne.type.interfaces.interfacelist = ig.intlist
        '''now the simple chassis section'''
        pchas = SectionParser_ShowChassis(loo_commandlist)
        chas = ChassisGenerator_TypeContainer_ALU_SCS(pchas)
        ne.type.chassis = chas.chassis
        '''Now the modules/gbics section'''
        mod = Parser_Module(loo_commandlist)
        #print(mod.module_long.dump())
        #print(mod.module.dump())
        #print(mod.module_status.dump())
        #print(mod.dump())
        mg = ModuleGenerator_TypeContainer_ALU_SCS(mod)
        #print(mg.dump())
        ne.type.modules.modulelist = mg.modulelist
        ''' Now the vlans'''
        v = TableParser_ShowVlan(loo_commandlist)
        #print(v.dump())
        vg = VlanGenerator_TypeContainer_ALU_SCS(v)
        ne.type.vlans.vlanlist = vg.vlanlist
        ''' now the routes'''
        r = TableParser_ShowIpRouterDatabase(loo_commandlist)
        #print(r.dump())
        rg = RouteGenerator_TypeContainer_ALU_SCS(r)
        ne.type.routes.routelist = rg.routelist
        ''' now the DHCP'''
        d = Parser_Dhcp(loo_commandlist)
        #print(d.dump())
        dg = DhcpGenerator_TypeContainer_ALU_SCS(d)
        ne.type.dhcp = dg.dhcpcontainer
        ''' now the config '''
        c = SectionParser_ShowConfigurationSnapshot(loo_commandlist)
        #print(c.dump())
        cg = ConfigurationGenerator_TypeContainer_ALU_SCS(c)
        ne.type.configuration = cg.configurationcontainer
        ''' now the arp '''
        a = TableParser_ShowArp(loo_commandlist)
        #print(a.dump())
        ag = ArpGenerator_TypeContainer_ALU_SCS(a)
        ne.type.arptable.arplist = ag.arplist
        ''' now the amap '''
        am = SectionParser_ShowAmap_RemoteHosts(loo_commandlist)
        #print(am.dump())
        amg = AmapGenerator_TypeContainer_ALU_SCS(am)
        ne.type.amap = amg.amap


        ''' find the system name from config text '''
        #print("LENGTH OF CONFIG: " + str(len(ne.type.configuration.text.value)))
        regex_systemname = re.compile('(system name )(?P<hostname>.*)')
        regex_systemname_match = re.search(regex_systemname,ne.type.configuration.text.value)
        if regex_systemname_match:
            ne.hostname.value = regex_systemname_match.group('hostname')
            ne.hostname.value = ne.hostname.value.replace('\r','')
            ne.hostname.value = ne.hostname.value.replace('\n','')

        ''' find the type.chassis mac address and append to ne '''
        mmm = ne.macs.Mac()
        mmm.value = ne.type.chassis.mac.value
        ne.macs.macslist.append(mmm)
        if ne.typestring == 'scs':
            ne.typecrawled = True
    except Exception as ex_makene:
        logging.debug("build_NEs(): Exception creating NE: " + str(ex_makene))

    return(ne)
    # print(ne.dump_basic_multiline())

def main():
    myfunc = 'nw_offline(): main(): '
    directory = os.listdir(os.getcwd())
    loglist = (filter(is_logfile,directory))

    werd = nwClasses.Cfg()
    currentCrawl = nwClasses.CrawlResults('1')
    currentCrawl.loo_ne = list(map(build_NEs,loglist))

    print("Length of currentCrawl.loo_ne : " + str(len(currentCrawl.loo_ne)))



    loo_rhosts = schemaModule.link_amaps_to_ne(currentCrawl)
    ''' Now build loo_entrypoints based on rhosts that have linkedNEid of 0 '''
    loo_entrypoints = schemaModule.convert_loo_remotehosts_to_loo_entrypoints(loo_rhosts)
    logging.debug(myfunc + '\t' + "--------------------------------")
    logging.debug(myfunc + '\t' + "          ENTRYPOINTS           ")
    logging.debug(myfunc + '\t' + "--------------------------------")
    logging.debug(myfunc + '\t' + "\t" + nwConfig.ep_fmt.format(*nwConfig.ep_hdr))
    for ep in loo_entrypoints:
        logging.debug(myfunc + '\t' + "\t" + ep.dump_rowformat())
    logging.debug(myfunc + '\t' + "--------------------------------")
    logging.debug(myfunc + '\t' + "        NETWORK ELEMENTS        ")
    logging.debug(myfunc + '\t' + "--------------------------------")
    logging.debug(myfunc + '\t' + "\t" + nwConfig.ne_fmt.format(*nwConfig.ne_hdr))
    for ne in currentCrawl.loo_ne:
        logging.debug(myfunc + '\t' + "\t" + ne.dump_rowformat())
    '''
    nwCrawl.ne_audit(currentCrawl)
    schemaModule.family_matters(currentCrawl)
    schemaModule.peanut_gallery(currentCrawl)
    schemaModule.roto_rooter(currentCrawl)
    nwCrawl.ne_audit(currentCrawl)
    nwCrawl.stats_view(currentCrawl)
    nwCrawl.map_view(currentCrawl)
    '''
    nwCrawl.peckingOrder(currentCrawl)
    with open('output.xml','wb') as f:
        f.write(currentCrawl.genxml())













if __name__ == '__main__':
    from optparse import OptionParser
    from optparse import OptionGroup
    
    usage = (usagedesc + '%prog [--help] [--debug] [--printtostdout] [--logfile]')
    parser = OptionParser(usage, version='%prog ' + '0.1')

    parser_debug = OptionGroup(parser,'Debug Options')
    parser_debug.add_option('-d','--debug',type='string',
            help=('Available levels are CRITICAL (3), ERROR (2), '
                    'WARNING (1), INFO (0), DEBUG (-1)'),
            default='CRITICAL')
    parser_debug.add_option('-p','--printtostdout',action='store_true',
            default=False,help='Print all log messages to stdout')
    parser_debug.add_option('-l','--logfile',type='string',metavar='FILE',
            help=('Desired filename of log file output. Default '
                    'is "'+default_logfilename+'"')
            ,default=default_logfilename)
        #officially adds the debuggin option group
    parser.add_option_group(parser_debug) 
    options,args = parser.parse_args() #here's where the options get parsed

    try: #now try and get the debugging options
        loglevel = getattr(logging,options.debug)
    except AttributeError: #set the log level
        loglevel = {3:logging.CRITICAL,
                2:logging.ERROR,
                1:logging.WARNING,
                0:logging.INFO,
                -1:logging.DEBUG,
                }[int(options.debug)]

    try:
        open(options.logfile,'w') #try and open the default log file
    except:
        print "Unable to open log file '%s' for writing." % options.logfile
        logging.debug(
            "Unable to open log file '%s' for writing." % options.logfile)
        
    setuplogging(loglevel,options.printtostdout,options.logfile)
    main()


