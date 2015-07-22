''' This module handles the customized parsing for the data
coming back from ALU 7705 and 6450 pulls. 

For now we'll keep vendor specific code isolated to 
modules until I can come up with a more elegant way to do it. 

'''

# Standard Library imports
import re
import time
import datetime
import os
import sys
import getopt
import operator
import pickle
import logging
import inspect
import gc
import getpass
import copy

import xml.etree.ElementTree as ET

# internal imports
from nwClasses import werd # super important that this is first
import nwConfig
import nwClasses

# import the basic NetworkElement class from the NetWalk mothership
#baseNEclass = __import__('nwClasses.NetworkElement')
from nwClasses import NetworkElement as baseNEclass



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

# the minimum length of discovery output, anything less means pull hiccupped
minimum_discoveryoutputlength = 400

# list of type identifer dictionaries which have key-value
#  pairs. This directory will be used to generate regexes
#  for type determination of NE.
typeIdentifiers = [
    {   'type':             'scs',
        'indicatorstring':  'Omniswitch',
        'variant':          ''
        },
    {   'type':             'scs',
        'indicatorstring':  'Omniswitch 6450',
        'variant':          ''
        },
    {   'type':             'scs',
        'indicatorstring':  'OS6450-P10',
        'variant':          'p10'
        },
    {   'type':             'scs',
        'indicatorstring':  '6450 10',
        'variant':          'p10'
        },
    {   'type':             'scs',
        'indicatorstring':  'OS6450-U24',
        'variant':          'u24'
        },
    {   'type':             'scs',
        'indicatorstring':  'OS6450-P24',
        'variant':          'p24'
        },
    {   'type':             'scs',
        'indicatorstring':  '6450 24 PORT',
        'variant':          'u24'
        },
    {   'type':             'scr',
        'indicatorstring':  '7705 SAR-H',
        'variant':          'sarh'
        },
    {   'type':             'scr',
        'indicatorstring':  '7705',
        'variant':          ''
        },
    # in the future, if more indicators are discovered, add them here
    #
    #
    ]

''' List of identifer dictionairies for finding 
the hostname of the NE in the primerOutput. Indicatorstrings
are ready for regex compilation. 

The group names are hard coded (e.g., (?P<indicator>)(?P<value>) so please use
same syntax for additional indicators
'''
# Example of grouped regex string: (?P<prefix7>^7\+)(?P<index>\d*)
hostnameIdentifiers = [
    {   'type':             'scs',
        # for SCS P10 and U24, the name comes from a block that looks like this
        'indicatorstring':  '(?P<indicator>  Name:         )(?P<value>.*)',
        },
    {   'type':             'scr',
        # for SCR SAR-H, the name comes from a block that looks like this
        'indicatorstring':  '(?P<indicator>System Name            : )(?P<value>.*)',
        },
    # in the future, if more indicators are discovered, add them here
    #
    #
    ]



loo_typeIdentifiers = []
uniqueTypes = []
loo_hostnameIdentifiers = []

'''=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-'''
'''                    EXPECT SCRIPT DEFINITIONS                       '''
'''=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-'''

''' define the primer script for the inital data pull for 
    ALU we can have a single hard coded primer that can pull
    model information for the 7705 SAR, 6450 P10 switch, and
    6450 U24 switch. 
'''
primerScript_hop0 = 'primer-ALU-7705-6450.exp'
primerScript_hop1 = 'primer-hop1-ALU-7705-6450.exp'
primerScript_hop2 = 'primer-hop2-ALU-7705-6450.exp'
# this is the timeout value appended to the end of the expect script parameters
primerExpectTimeout = '8'
# this is the string that will come back from an expect script that timed out. 
primerExpectTimeoutString = "Timed Out!"
primerExpectWaitString = "Need to wait."
primerExpectBadHostname = "ssh: Could not resolve hostname"

# define the prefixes/trailers used for various levels of expect hops
class ExpectWrapper():
    ''' Object to hold expect prefix/trailer and hop level.
    '''
    def __init__(self):
        self.expectPrefix = """"""
        self.expectTrailer = """"""
        self.hopcount = 0
        self.primerscript = ''

loo_expectwrappers = []


expectPrefix_hop0 = """
#!/usr/bin/expect

set CTRL_C     \\x03       ;# http://wiki.tcl.tk/3038


set ipaddr [lindex $argv 0]
set port [lindex $argv 1]
set username [lindex $argv 2]
set password [lindex $argv 3]
set timeout [lindex $argv 4]
set timeout 15

spawn ssh "$username@$ipaddr"
expect { 
    "yes/no" {send "yes\\r"
            expect "*?assword" { send $password\\r }
            }
    "*?assword" { send $password\\r }
    "Connection closed by remote host" {puts "Need to wait."; exit 1}
    "Packet corrupt" {puts "Need to wait." ; exit 1}
    "Connection refused" {puts "Timed Out!"; exit 1}
    timeout {send $CTRL_C; puts "Timed Out!"; exit 1}
}

expect {
    ">" { send "\\r"
"""

expectTrailer_hop0 = """
    }
    timeout {send $CTRL_C; puts "Timed Out!"; exit 1}
    }

exit 0
"""
ew = ExpectWrapper()
ew.expectPrefix = expectPrefix_hop0
ew.expectTrailer = expectTrailer_hop0
ew.hopcount = 0
ew.primerscript = primerScript_hop0
loo_expectwrappers.append(ew)

expectPrefix_hop1 = """
#!/usr/bin/expect

set CTRL_C     \x03       ;# http://wiki.tcl.tk/3038


set ipaddr [lindex $argv 0]
set port [lindex $argv 1]
set username [lindex $argv 2]
set password [lindex $argv 3]
set timeout [lindex $argv 4]

set ipaddr_1 [lindex $argv 5]
set port_1 [lindex $argv 6]
set username_1 [lindex $argv 7]
set password_1 [lindex $argv 8]
set timeout_1 [lindex $argv 9]

#set timeout 

spawn ssh "$username@$ipaddr"
expect { 
    "yes/no" {send "yes\\r"
            expect "*?assword" { send $password\\r }
            }
    "*?assword" { send $password\\r }
    "Connection closed by remote host" {puts "Need to wait."; exit 1}
    "Packet corrupt" {puts "Need to wait." ; exit 1}
    "Connection refused" {puts "Timed Out!"; exit 1}
    timeout {send $CTRL_C; puts "Timed Out!"; exit 1}
}

expect {
    ">" {send "ssh $ipaddr_1\\r"
        expect ":" {send "$username_1\\r"
            expect { 
                "yes/no" {send "yes\\r"
                        expect "*?assword" { send $password_1\\r }
                        }
                "*?assword" { send $password_1\\r }
                "Connection closed by remote host" {puts "Need to wait."; exit 1}
                "Packet corrupt" {puts "Need to wait." ; exit 1}
                "Connection refused" {puts "Timed Out!"; exit 1}
                timeout {send $CTRL_C; puts "Timed Out!"; exit 1}
                }
            expect {
                ">" {send "\\r"
"""

expectTrailer_hop1 = """
                    }
                    }
                }
        }
        }
    timeout {send $CTRL_C; puts "Timed Out!"; exit 1}
    }

exit 0
"""
ew = ExpectWrapper()
ew.expectPrefix = expectPrefix_hop1
ew.expectTrailer = expectTrailer_hop1
ew.hopcount = 1
ew.primerscript = primerScript_hop1
loo_expectwrappers.append(ew)




expectPrefix_hop2 = """
#!/usr/bin/expect

set CTRL_C     \x03       ;# http://wiki.tcl.tk/3038


set ipaddr [lindex $argv 0]
set port [lindex $argv 1]
set username [lindex $argv 2]
set password [lindex $argv 3]
set timeout [lindex $argv 4]

set ipaddr_1 [lindex $argv 5]
set port_1 [lindex $argv 6]
set username_1 [lindex $argv 7]
set password_1 [lindex $argv 8]
set timeout_1 [lindex $argv 9]

set ipaddr_2 [lindex $argv 10]
set port_2 [lindex $argv 11]
set username_2 [lindex $argv 12]
set password_2 [lindex $argv 13]
set timeout_2 [lindex $argv 14]

#set timeout 

spawn ssh "$username@$ipaddr"
expect { 
    "yes/no" {send "yes\\r"
            expect "*?assword" { send $password\\r }
            }
    "*?assword" { send $password\\r }
    "Connection closed by remote host" {puts "Need to wait."; exit 1}
    "Packet corrupt" {puts "Need to wait." ; exit 1}
    "Connection refused" {puts "Timed Out!"; exit 1}
    timeout {send $CTRL_C; puts "Timed Out!"; exit 1}
}

expect {
    ">" {send "ssh $ipaddr_1\\r"
        expect ":" {send "$username_1\\r"
            expect { 
                "yes/no" {send "yes\\r"
                        expect "*?assword" { send $password_1\\r }
                        }
                "*?assword" { send $password_1\\r }
                "Connection closed by remote host" {puts "Need to wait."; exit 1}
                "Packet corrupt" {puts "Need to wait." ; exit 1}
                "Connection refused" {puts "Timed Out!"; exit 1}
                timeout {send $CTRL_C; puts "Timed Out!"; exit 1}
                }
            expect {
                ">" {send "ssh $ipaddr_2\\r"
                    expect ":" {send "$username_2\\r"
                        expect { 
                            "yes/no" {send "yes\\r"
                                    expect "*?assword" { send $password_2\\r }
                                    }
                            "*?assword" { send $password_2\\r }
                            "Connection closed by remote host" {puts "Need to wait."; exit 1}
                            "Packet corrupt" {puts "Need to wait." ; exit 1}
                            "Connection refused" {puts "Timed Out!"; exit 1}
                            timeout {send $CTRL_C; puts "Timed Out!"; exit 1}
                            }
                        expect {
                            ">" {send "\\r"
"""

expectTrailer_hop2 = """
                                }
                                }
                            }
                    }
                    }
                }
        }
        }
    timeout {send $CTRL_C; puts "Timed Out!"; exit 1}
    }

exit 0
"""
ew = ExpectWrapper()
ew.expectPrefix = expectPrefix_hop2
ew.expectTrailer = expectTrailer_hop2
ew.hopcount = 2
ew.primerscript = primerScript_hop2
loo_expectwrappers.append(ew)





'''=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-'''
'''               END EXPECT SCRIPT DEFINITIONS                        '''
'''=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-'''

# custom NE equipment types
# already imported at top of file
#from nw_NE_Type_SCS_6450 import TypeContainer_ALU_SCS
# TypeContainer_ALU_SCS()




class Type_Identifier():
    ''' class used to store type identifiers primarily for 
        the purposes of holding the generated regexes.
    '''
    def __init__(self,typekeyword,indicatorstring,variant):
        self.type = typekeyword
        self.indicatorstring = indicatorstring
        self.variant = variant
        self.regex = self.genregex()
    def genregex(self):
        return(re.compile(self.indicatorstring))
    def check_match(self,linestring):
        ''' Takes a line of data as input and returns
        true if a match was found.
        '''
        match = re.search(self.regex,linestring)
        if match:
            return True
        else:
            return False

class Hostname_Identifier():
    ''' class used to store hostname identifiers primarily for 
        the purposes of holding the generated regexes.
    '''
    def __init__(self,typekeyword,indicatorstring):
        self.type = typekeyword
        self.indicatorstring = indicatorstring
        self.regex = self.genregex()
    def genregex(self):
        return(re.compile(self.indicatorstring))
    def check_match(self,linestring):
        ''' Takes a line of data as input and returns
        true if a match was found.
        '''
        match = re.search(self.regex,linestring)
        if match:
            return True
        else:
            return False
    def give_group_value(self,linestring):
        ''' takes a line of data as input and returns
        the contents of the 'value' ?P group
        '''
        match = re.search(self.regex,linestring)
        if match:
            value = match.group('value')
            # strip out unwanted chars
            value = value.rstrip(',\n\r') 
            return value
        else:
            return("NO MATCH!")

def genExpect_Discovery(ne_with_type):
    ''' Takes a network element object that 
    already has the 'type' section specified
    and then takes the expect body from that 
    object and wraps it with the expect prefix
    and trailer.

    '''
    myfunc = str(giveupthefunc())
    expectbody = ''
    hopcount = 0
    alreadygenerated = False
    # first check to see if we're on a hop 1
    try:
        if not alreadygenerated:
            #if ne_with_type.sourceEntryObj.learnedfromEntryObj.learnedfromEntryObj != None:
            if ne_with_type.sourceEntryObj.hopcount == 2:
                logging.debug(myfunc + '\t' + 
                    "Succesfully queried 'ne_with_type.sourceEntryObj.learnedfromEntryObj.learnedfromEntryObj', Setting hopcount=2")
                hopcount = 2
                alreadygenerated = True
    except Exception as r:
        logging.debug(myfunc + '\t' +
            "Exception attempting to query 'ne_with_type.sourceEntryObj.learnedfromEntryObj.learnedfromEntryObj' : " +
            str(r))
    try:
        if not alreadygenerated:
            #if ne_with_type.sourceEntryObj.learnedfromEntryObj != None:
            if ne_with_type.sourceEntryObj.hopcount == 1:
                logging.debug(myfunc + '\t' + 
                    "Succesfully queried 'ne_with_type.sourceEntryObj.learnedfromEntryObj', Setting hopcount=1")
                hopcount = 1 # assume for now
                alreadygenerated = True
    except Exception as e:
        logging.debug(myfunc + '\t' + 
            "Exception attempting to query 'ne_with_type.sourceEntryObj.learnedfromEntryObj' : " +
            str(e) + ". Setting hopcount=0")
        hopcount = 0
        alreadygenerated = True
    for ew in loo_expectwrappers:
            if ew.hopcount == hopcount:
                expectbody =(ew.expectPrefix + 
                            ne_with_type.type.nox_expectbody + 
                            ew.expectTrailer)
    return(expectbody)

def appendTypeToNE(ne_without_type):
    ''' Takes a base NE that has no type
    yet and appends the specific type object
    in the type section. 
    '''
    myfunc = str(giveupthefunc())
    if ne_without_type.typestring == 'scs':
        ne_without_type.type = TypeContainer_ALU_SCS()
    elif ne_without_type.typestring == 'scr':
        logging.debug(myfunc + '\t' + 
            "Typestring detected as 'scr' but that Type() module has not been written yet.")
    else:
        logging.debug(myfunc + '\t' + 
            "Typestring detected as '" + ne_without_type.typestring + "' but that Type() module has not been written yet.")
    return ne_without_type

def giveupthefunc():
    #This function grabs the name of the current function
    # this is used in most of the debugging/info/warning messages
    # so I know where an operation failed
    '''This code block comes from user "KindAll" on StackOverflow
    http://stackoverflow.com/a/4506081'''
    frame = inspect.currentframe(1)
    code  = frame.f_code
    globs = frame.f_globals
    functype = type(lambda: 0)
    funcs = []
    for func in gc.get_referrers(code):
        if type(func) is functype:
            if getattr(func, "func_code", None) is code:
                if getattr(func, "func_globals", None) is globs:
                    funcs.append(func)
                    if len(funcs) > 1:
                        return None
    return funcs[0] if funcs else None

def genTypeIdentifiers(list_of_dictionaries):
    ''' Takes a list of dictionary type identifiers and 
    builds Type_Identifer() objects.
    '''
    myfunc = str(giveupthefunc())
    loo = []
    for i in list_of_dictionaries:
        tmpidentifer = Type_Identifier(
                    i.get('type'),
                    i.get('indicatorstring'),
                    i.get('variant'),
                    )
        loo.append(tmpidentifer)
    ''' DONT TRY TO LOG ANYTHING IN HERE, RUNS ON IMPORT AND
     LOG FACILITY  ISNT READY YET'''
    #logging.debug(myfunc + '\t' + 
        #"Generated list of TypeIdentifiers of length: " + str(len(loo)))
    return(loo)

def genHostnameIdentifiers(list_of_dictionaries):
    ''' Takes a list of dictionary hostname identifiers and 
    builds Hostname_Identifer() objects.
    '''
    loo = []
    for i in list_of_dictionaries:
        tmpidentifer = Hostname_Identifier(
                    i.get('type'),
                    i.get('indicatorstring'),
                    )
        loo.append(tmpidentifer)
    return(loo)

def genUniqueTypes(loo_typeIdentifiers):
    ''' Takes list Type_Identifer objects 
    and examines to determine number of unique types.
    Populates local-global uniqueTypes list.
    '''
    myfunc = str(giveupthefunc())
    listoftypes = []
    for tid in loo_typeIdentifiers:
        if len(listoftypes) == 0:
            listoftypes.append(tid.type)
            continue
        elif len(listoftypes) > 0:
            foundflag = False
            for t in listoftypes:
                if tid.type == t:
                    foundflag = True
                    break
            if not foundflag:
                listoftypes.append(tid.type)
    return listoftypes
            

def outputInspector(textlist):
    ''' This function lives inside the custom schemaModule since output from
    various vendors will be somewhat customized.

    This function examines the data that came back from the primer and discovery
    script and determines whether or not the command worked to pull the 
    data. It returns three booleans: "reachable", "authsuccess", and
    "sleepandtryagain". That will tell the generic crawler how to flag the attempt.

    '''
    myfunc = str(giveupthefunc)
    re_timeout_string = primerExpectTimeoutString
    re_timeout_regex = re.compile(re_timeout_string)
    
    re_wait_string = primerExpectWaitString
    re_wait_regex = re.compile(re_wait_string)

    re_badhost_string = primerExpectBadHostname
    re_badhost_regex = re.compile(re_badhost_string)

    re_badkeys_regex = re.compile('DOING SOMETHING NASTY')

    reachable = False
    authsuccess = False
    sleepandtryagain = False
    deletesshkeys = False
    # loop through the lines in the primer output
    for line in textlist:
        re_timeout_match = re.search(re_timeout_regex,line)
        re_wait_match = re.search(re_wait_regex,line)
        re_badhost_match = re.search(re_badhost_regex,line)
        re_badkeys_match = re.search(re_badkeys_regex,line)
        # timeout match could mean bad IP or bad password
        if re_timeout_match:
            # less than a few lines means bad IP
            if len(textlist) < 4:
                reachable = False
            # more than a few lines means bad auth
            elif len(textlist) > 4:
                authsuccess = False
        elif re_wait_match:
            sleepandtryagain = True
            authsuccess = True
            reachable = True
        elif re_badhost_match:
            sleepandtryagain = False
            authsuccess = False
            reachable = False
        elif re_badkeys_match:
            sleepandtryagain = True
            authsuccess = False
            reachable = True
            deletesshkeys = True
        else:
            reachable = True
            authsuccess = True
            sleepandtryagain = False
    return(reachable,authsuccess,sleepandtryagain,deletesshkeys)


def detectNEtype(entryPrimerOutput,entry):
    ''' takes entryPrimerOutput and tries to
    determine what type of NE we're looking at.

    '''
    myfunc = str(giveupthefunc())
    logging.debug(myfunc + '\t' + 
        "Working on Entry:::::::" + entry.dumpdata_singleline())
    class TypeCounter():
        ''' Sets up a counter for a specific type
        '''
        def __init__(self,typer):
            self.type = typer
            self.count = 0    

    class TypePoll():
        ''' Holder for all TypeCounters. Has methods
        to sort based on highest count.
        '''
        def __init__(self):
            self.counterlist = []
        def highest_count_type(self):
            winner = ''
            # first check to see if all zero
            notzeroflag = False
            for o in self.counterlist:
                if o.count > 0:
                    notzeroflag = True
            if notzeroflag:
                self.counterlist.sort(key=operator.attrgetter('count'))
                # pop the object
                w = self.counterlist.pop()
                # convert object to string
                winner = w.type
            else:
                logging.debug("TypePoll: Unable to determine winner.")
                winner = "UNDETERMINED"
            return winner

    tpoll = TypePoll()
    # initiate TypePoll based on uniqueTypes
    for typ in uniqueTypes:
        typo = TypeCounter(typ)
        tpoll.counterlist.append(typo)

    resultstring = ''
    msg = ''
    # scans through input and sends data to type identifiers for match
    for i,line in enumerate(entryPrimerOutput):
        for tid in loo_typeIdentifiers:
            if tid.check_match(line):
                msg = ("\t\t\tmatched '" + 
                    tid.indicatorstring +
                    "' on line " + str(i) + '\n')
                resultstring += msg
                # find the corresponding TypeCounter and add value
                for typo in tpoll.counterlist:
                    if typo.type == tid.type:
                        typo.count += 1
    # log the results
    logging.debug(myfunc + '\t' + 
        "resultstring from TypePoll: \n" + msg)
    winner = tpoll.highest_count_type()
    logging.debug(myfunc + '\t' + 
        "Winner of TypePoll is '" + winner + "'!")
    return winner

def detectNEhostname(entryPrimerOutput):
    ''' takes entryPrimerOutput and tries to
    determine hostname based on type.
    '''
    myfunc = str(giveupthefunc())
    class HostnameCounter():
        ''' Sets up a counter for a specific hostname
        '''
        def __init__(self,typer):
            self.type = typer
            self.count = 0
            self.hname = ''

    class HostnamePoll():
        ''' Holder for all HostnameCounters. Has methods
        to sort based on highest count.
        '''
        def __init__(self):
            self.counterlist = []
        def highest_count_type(self):
            winner = ''
            # first check to see if all zero
            notzeroflag = False
            for o in self.counterlist:
                if o.count > 0:
                    notzeroflag = True
            if notzeroflag:
                self.counterlist.sort(key=operator.attrgetter('count'))
                # pop the object
                w = self.counterlist.pop()
                # convert object to string
                winner = w.hname
            else:
                logging.debug("TypePoll: Unable to determine winner.")
                winner = "UNDETERMINED"
            return winner
    hpoll = HostnamePoll()
    # initiate HostnamePoll based on uniqueTypes
    for hyp in uniqueTypes:
        hypo = HostnameCounter(hyp)
        hpoll.counterlist.append(hypo)

    resultstring = ''
    msg = 'UNDETERMINED'
    # scans through input and sends data to hostname identifiers for match
    for i,line in enumerate(entryPrimerOutput):
        for hid in loo_hostnameIdentifiers:
            hname = ''
            if hid.check_match(line):
                hname = hid.give_group_value(line)
                msg = ("\t\t\tmatched '" + 
                    hid.indicatorstring +
                    "' on line " + str(i) + 
                    " with hostname of '" + hname + "'\n")
                resultstring += msg
                # find the corresponding HostnameCounter and add value
                for hypo in hpoll.counterlist:
                    if hypo.type == hid.type:
                        hypo.count += 1
                        hypo.hname = hname
    # log the results
    logging.debug(myfunc + '\t' + 
        "resultstring from HostnamePoll: \n" + msg)
    winner = hpoll.highest_count_type()
    logging.debug(myfunc + '\t' + 
        "Winner of HostnamePoll is '" + winner + "'!")
    # strip bogus characters off winner
    winner = winner.rstrip(',\r\n')
    return winner

def fetchBaseNEdata(entryPrimerOutput,entry):
    ''' Returns the four basic things we can get from 
    the primerOutput that came back from primer.

    Things we can get from primeroutput:
    hostname [string]
    typestring [string]

    '''
    myfunc = str(giveupthefunc())
    # first need to detect type
    typestring = detectNEtype(entryPrimerOutput,entry)
    hname = detectNEhostname(entryPrimerOutput)
    return(typestring,hname)

def chunkdata_alldiscovery_SCS(ne):
    ''' Dig into the discoveryoutput and pull the sections of output that
    correspond to the various commands. Creates CommandOutput() objects 
    that contain the relevant output data for that command
    '''
    myfunc = str(giveupthefunc())
    logging.debug(myfunc + '\t' + 
        "Examining NE: " + ne.dump_basic_singleline())
    # first build a list of commands from typeModule.discoveryCommands
    commandlist = []
    for chunk in discoveryCommands:
        if chunk.get('type') == ne.typestring:
            commandlist = chunk.get('commands')
    # now that that list of commands and build typeModule.CommandOutput() command objects
    loo_commandlist = []
    for c in commandlist:
        tc = CommandOutput(c)
        loo_commandlist.append(tc)

    matchcount = 0
    for r,c in enumerate(loo_commandlist):
        for i,line in enumerate(ne.type.nox_discoveryoutput):
            if c.check_match(line):
                matchcount += 1
                linefound = i
                c.linefound.append(linefound)
    # check to see if there are any multiline matches
    for c in loo_commandlist:
        if len(c.linefound) > 0:
                c.startline = c.linefound[0]
        if len(c.linefound) > 1:
            logging.debug(myfunc + '\t' + 
                "Uh oh, found multiline matches for '" + c.commandstring + "' : " + str(c.linefound))
    # now go through loo_commandlist again now that we know the lines
    #  set stop blocks based on location of next command
    successcount = 0
    for r,c in enumerate(loo_commandlist):
        # make sure there was a match
        if len(c.linefound) > 0:
            c.startline = c.linefound[0]
            # now check location of startline of next command
            indexofnextcommandinlist = r+1
            try:
                c.stopline = loo_commandlist[indexofnextcommandinlist].startline
                # add some end of list protection
                if r == len(loo_commandlist)-2 and c.stopline == None:
                    c.stopline = len(ne.type.nox_discoveryoutput)
                for linenumber in range(c.startline+1,c.stopline):
                    c.sectionoutput.append(ne.type.nox_discoveryoutput[linenumber])
                logging.debug(myfunc + '\t' + 
                    "For '" + c.commandstring + "'. Grabbed lines = " + str(len(c.sectionoutput)))
                successcount += 1
            except Exception as e:
                logging.debug(myfunc + '\t' + 
                    "Exception pulling startline of nextcommandinlist: " + str(e))
        else:
            continue
    logging.debug(myfunc + '\t' +
        "At end of parsing successcount = " + str(successcount))
    if successcount < len(loo_commandlist)-1:
        ne.badpull = True
        logging.debug("Successcount is less than len(loo_commandlist) of " + str(len(loo_commandlist)) +
            ". Setting ne.badpull = True for resubmission")
    # now we have a list of commands and their output sections
    return(loo_commandlist)

def parseData_SCS(ne):
    ''' orchestrates the parsing functions and classes
    '''
    myfunc = str(giveupthefunc())
    logging.debug(myfunc + '\t' + 
        "Length of generated list of typeIdentifiers: " + str(len(loo_typeIdentifiers)))
    # break up the discovery output into chunks and the relevant sections to CommandOutput() objects
    loo_commandlist = chunkdata_alldiscovery_SCS(ne)
    '''Now do some data validation to make sure we didn't get a bad data pull'''
    logging.debug(myfunc + '\t' + 
        "Length of loo_commandlist: " + str(len(loo_commandlist)))
    # find the command list for this type of ne
    complist = []
    try:
        for typecommands in discoveryCommands:
            if typecommands.get('type') == ne.typestring:
                complist = typecommands.get('commands')
    except:
        pass
    logging.debug(myfunc + '\t' +
        "Length of discoveryCommands.commands[]: " + str(len(complist)))
    if len(loo_commandlist)+2 < len(complist):
        ne.badpull = True
    if not ne.badpull:
        '''-----------------------------------------------------'''
        # initialize the Parser for Port info. Most of the heavy lifting happens during initialization.
        parsedports = Parser_Port(loo_commandlist)
        # within the parsedports object all of the data we want has been processed
        # now take the parsed ports object and build a port generator
        pg = PortGenerator_TypeContainer_ALU_SCS(parsedports)
        # within the port generator it as real type ports for the SCS structured type
        ne.type.ports.portlist = pg.portlist
        '''-----------------------------------------------------'''
        ints = TableParser_ShowIpInterface(loo_commandlist)
        ig = InterfaceGenerator_TypeContainer_ALU_SCS(ints)
        ne.type.interfaces.interfacelist = ig.intlist
        '''-----------------------------------------------------'''
        pchas = SectionParser_ShowChassis(loo_commandlist)
        chas = ChassisGenerator_TypeContainer_ALU_SCS(pchas)
        ne.type.chassis = chas.chassis
        '''-----------------------------------------------------'''
        '''Now the modules/gbics section'''
        mod = Parser_Module(loo_commandlist)
        mg = ModuleGenerator_TypeContainer_ALU_SCS(mod)
        ne.type.modules.modulelist = mg.modulelist
        '''-----------------------------------------------------'''
        '''Now the Vlans'''
        v = TableParser_ShowVlan(loo_commandlist)
        vg = VlanGenerator_TypeContainer_ALU_SCS(v)
        ne.type.vlans.vlanlist = vg.vlanlist
        '''-----------------------------------------------------'''
        ''' now the routes'''
        r = TableParser_ShowIpRouterDatabase(loo_commandlist)
        rg = RouteGenerator_TypeContainer_ALU_SCS(r)
        ne.type.routes.routelist = rg.routelist
        '''-----------------------------------------------------'''
        ''' now the DHCP'''
        d = Parser_Dhcp(loo_commandlist)
        dg = DhcpGenerator_TypeContainer_ALU_SCS(d)
        ne.type.dhcp = dg.dhcpcontainer
        '''-----------------------------------------------------'''
        ''' now the config '''
        c = SectionParser_ShowConfigurationSnapshot(loo_commandlist)
        cg = ConfigurationGenerator_TypeContainer_ALU_SCS(c)
        ne.type.configuration = cg.configurationcontainer
        '''-----------------------------------------------------'''
        ''' now the arp '''
        a = TableParser_ShowArp(loo_commandlist)
        ag = ArpGenerator_TypeContainer_ALU_SCS(a)
        ne.type.arptable.arplist = ag.arplist
        '''-----------------------------------------------------'''
        ''' now the amap '''
        am = SectionParser_ShowAmap_RemoteHosts(loo_commandlist)
        #logging.debug(myfunc + '\t' + am.dump())
        amg = AmapGenerator_TypeContainer_ALU_SCS(am)
        ne.type.amap = amg.amap

        # now flag the NE that it's been type crawled so it doesn't happen twice
        ne.typecrawled = True
        # now append the type.chassis mac to the NE maclist
        m = ne.macs.Mac()
        m.value = ne.type.chassis.mac.value
        if len(m.value) < 12:
            m.value = 'NA'
        ne.macs.macslist.append(m)
    return(ne)

def link_amaps_to_ne(crawl):
    ''' Loops through the AMAPLists of all NE.type's and links 
    NE id to remotehost. Used to determine if a remotehost
    has already been crawled. Returns a list of uncrawled remotehost objects
    '''
    myfunc = str(giveupthefunc())
    rhosts = []
    for ne in crawl.loo_ne:
        try:
            for rhost in ne.type.amap.amaplist:
                rhost.nox_learnedfromNEid = ne.id
                rhost.nox_learnedfromEntryid = ne.sourceEntryId.value
                rhost.nox_learnedfromEntryObj = ne.sourceEntryObj
                rhost.nox_learnedfromAuthObj = ne.authobj
                rhosts.append(rhost)
        except Exception as ex_rhostcrawl:
            logging.debug(myfunc + '\t' +
            "Exception looking for rhosts in ne.type.amap. May not be SCS")
            pass
    for rh in rhosts:
        for ne in crawl.loo_ne:
            try:
                mac = ne.macs.macslist[0].value
                #logging.debug("Examining ne mac: '" + mac + "' with rh mac: '" + rh.remotemac.value + "'")
                if rh.remotemac.value in mac:
                    rh.nox_linkedNEid = ne.id
            except Exception as ex_maccompare:
                logging.debug(myfunc + '\t' + 
                    "Exception comparing NE mac with RH mac. NE hostname is '" + 
                    ne.hostname.value + "'..." + str(ex_maccompare))

    logging.debug(myfunc + "\t" + nwConfig.remotehost_fmt.format(*nwConfig.remotehost_hdr))
    for rh in rhosts:
        logging.debug(myfunc + "\t" + rh.dump_rowformat())
    logging.debug(myfunc + "\t---------------------------------")
    logging.debug(myfunc + "\t" + nwConfig.ne_fmt.format(*nwConfig.ne_hdr))
    for ne in crawl.loo_ne:
        logging.debug(myfunc + "\t" + ne.dump_rowformat())
    return rhosts
    
    theone = []
    for rh in uncrawledremotehosts_unique:
        if rh.nox_linkedNEid == 0:
            theone.append(rh)
        logging.debug(myfunc + '\t' + "DUMP OF REMOTEHOSTS AFTER FINAL SCRUB: ")
    for rh in theone:
        logging.debug(rh.dump())
    logging.debug(myfunc + '\t' + 
        "Length of uncrawledremotehosts_unique after removing final scrub: " + str(len(theone)))
    return(theone)

def convert_loo_remotehosts_to_loo_entrypoints(loo_remothosts):
    ''' Takes a list of objects of Remotehosts and converts them 
    to Entrypoint objects. Returns list of objects of Entrypoints.
    '''
    myfunc = str(giveupthefunc())
    loo_entrypoints = []
    # for every remotehost in the list
    for rh in loo_remothosts:
        # and for the multiple IP's per remotehost
        if rh.nox_linkedNEid == 0:
            try:
                rh.remoteips.riplist[0]
                for rhip in rh.remoteips.riplist:
                    uid = werd.genUID()
                    t_rhip = rhip.value
                    ep = nwClasses.Entrypoint(uid,t_rhip)
                    ep.hostname = rh.remotehostname.value
                    # track where we learned about this from
                    ep.learnedfromNEid = rh.nox_learnedfromNEid
                    ep.learnedfromEntryid = rh.nox_learnedfromEntryid
                    ep.learnedfromEntryObj = rh.nox_learnedfromEntryObj
                    try:
                        ep.hopcount = ep.learnedfromEntryObj.hopcount + 1
                    except:
                        ep.hopcount += 1
                    ep.learnedfromAuthObj = rh.nox_learnedfromAuthObj
                    loo_entrypoints.append(ep)
            except Exception as ex_riplist:
                logging.debug(myfunc + '\t' +
                    "Exception referencing RIP of RH: " + str(ex_riplist))
            
    logging.debug(myfunc + "\t" + "At end of conversion we have loo_entrypoints of length: " + str(len(loo_entrypoints)))
    return(loo_entrypoints)




def gen_next_target(target,currentCrawl):
    ''' takes a previous target and currentCrawl and generates a new
    target with depth.
    '''
    myfunc = str(giveupthefunc())
    # first we need to link amap remotehosts to list of currentCrawl NE's
    # now go through and create a new target based on AMAP list
    ''' 
    t_cEntrypoint = nwClasses.Entrypoint(t_entrypointId,t_entrypointIp)
    tTarget = nwClasses.Target(t_targetId,
                                            t_list_entrypoint,
                                            t_list_auth)
    '''
    # first we need to conver the list of remotehosts into entrypoints
    
    loo_rhosts = link_amaps_to_ne(currentCrawl)
    ''' Now build loo_entrypoints based on rhosts that have linkedNEid of 0 '''
    loo_entrypoints = convert_loo_remotehosts_to_loo_entrypoints(loo_rhosts)
    logging.debug(myfunc + '\t' + "--------------------------------")
    logging.debug(myfunc + '\t' + "          ENTRYPOINTS           ")
    logging.debug(myfunc + '\t' + "--------------------------------")
    logging.debug(myfunc + '\t' + nwConfig.ep_fmt.format(*nwConfig.ep_hdr))
    for ep in loo_entrypoints:
        logging.debug(myfunc + '\t' + ep.dump_rowformat())

    # create a new target stealing the auth from the original netwalk target
    tid = werd.genUID()
    ntarget = nwClasses.Target(tid,loo_entrypoints,target.authlist)
    # take the previous hopdepth and increment by 1
    ntarget.hopdepth = target.hopdepth + 1
    # dump the tgt object to debug
    bool_eprowformat = True
    msg = ntarget.dumpdata(bool_eprowformat)
    logging.debug(myfunc + '\t' + msg)
    return(ntarget)
    # now we have a new target with more entrypoints. Now we need to figure out how to reach those entrypoints

def peanut_gallery(crawl):
    ''' Cycle through the current crawl's mac-address-tables
    and create really basic NE's for the Macs detected on the 
    switch links.
    '''
    import nwOUIexplorer
    def map_cid_to_ne(ne):
        ''' Search the member list for the mac addres of the 
        Unknown NE and return additional details
        '''
        for member in werd.loo_members:
            if member.mac.lower() == newne.macs.macslist[0].value.lower():
                ne.hostname.value = member.hostname
                ne.typestring = member.typestring
        return(ne)

    myfunc = 'peanut_gallery()'
    temp_loo_ne = []
    for ne in crawl.loo_ne:
        try:
            for port in ne.type.ports.portlist:
                # determine if the slotport is used in amap, if so, ignore maclist
                for rhost in ne.type.amap.amaplist:
                    if port.slotport.value == rhost.localslotport.value:
                        try:
                            # if the riplist is blank, it's a bad rhost entry and we shouldn't 
                            #  ignore the port for macattack
                            rhost.remoteips.riplist[0].value
                            port.nox_macattack = True
                        except Exception as ex_macattack:
                            logging.debug(myfunc + '\t' +
                                "Exception setting nox_macattack for rhost: " + str(ex_macattack))
                
                for mac in port.associatedmacs.maclist:
                    #logging.debug("()()()()()()()()()   MAC.MAC.VALUE = " + str(mac.mac.value) + "     ()()()()()()()()()")
                    # create the new child NE and build parent
                    newne = nwClasses.NetworkElement(werd.genUID())
                    newne.macs.macslist.append(newne.macs.Mac())
                    newne.macs.macslist[0].value = mac.mac.value
                    newne.parentport = port.slotport.value
                    newne.parentportid = port.id
                    newne.parenthostname = ne.hostname.value

                    # this ANE is for the parent, probably SCS that we know about already
                    ane = nwClasses.Assoc_NE(ne.id)
                    ane.typestring = ne.typestring
                    ane.port.portid = 'NA' # nothing for local port on member
                    ane.port.slotport = 'NA' # nothing for slotport on member
                    ane.hostname = ne.hostname.value
                    

                    newne.typestring = "UNKNOWN"
                    try:
                        newne.hostname.value = newne.macs.macslist[0].value
                        ouifinder = nwOUIexplorer.Oui_Locator(newne.hostname.value)
                        newne.hostname.value = ouifinder.return_combo()
                    except Exception as ex_ouifinder:
                        logging.debug(myfunc + '\t' + 
                            "Exception doing ouilookup on mac: " + str(ex_ouifinder))
                        newne.hostname.value = 'UNKNOWN'
                    # try and get more info about the NE
                    newne = map_cid_to_ne(newne)

                    newne.parents.parentlist.append(ane)
                    # for now just set the hostname to the mac address

                    ''' no matter what, add the NE to loo_scratchpad. We want this later
                    so we can account for NE's that fell through the logic cracks.
                    '''
                    crawl.loo_scratchpad.append(newne)

                    # only add to currentcrawl.loo_ne if this is not an rhost port (i.e., nox_macattack)
                    if port.operstatus.value == 'up' and not port.nox_macattack:
                        temp_loo_ne.append(newne)

                        # create the child ANE and append to parent's children list
                        anep = nwClasses.Assoc_NE(newne.id)
                        anep.typestring = newne.typestring
                        anep.hostname = newne.hostname.value
                        anep.port.portid = port.id
                        anep.port.slotport = port.slotport.value
                        ne.children.childrenlist.append(anep)

                        # flag that we've crawled mac-address-table
                        ne.macattack = True
                    logging.debug(myfunc + '\t' + 
                            "Successfully ran macattack for '" + ne.hostname.value + 
                            "'. SlotPort= " + port.slotport.value + 
                            ". Length of associatedmacs.maclist = " + 
                            str(len(port.associatedmacs.maclist)))
        except Exception as exe:
            logging.debug(myfunc + '\t' + 
                "Exception pulling ne.type.ports.portlist for NE hostname: '" + ne.hostname.value + "' : " + str(exe))
            ne.macattack = True

    logging.debug(myfunc + '\t' + 
        "Before removing duplicates we have " + str(len(temp_loo_ne)) + " new NEs.")
    temp_loo_ne_unique = list(set(temp_loo_ne))
    logging.debug(myfunc + '\t' + 
        "After removing duplicates we have " + str(len(temp_loo_ne_unique)) + " new NEs.")

    for ne in temp_loo_ne_unique:
        crawl.loo_ne.append(ne)

    counter_nomacattacks = 0
    for ne in crawl.loo_ne:
        if ne.macattack:
            counter_nomacattacks += 1
    logging.debug(myfunc + '\t' +
        "macattack performed on " + str(counter_nomacattacks) + " of " + str(len(crawl.loo_ne)) + " network elements.") 

def lookup_ne_by_id(i,loo_ne):
    ''' Returns the NE object with id == i
    '''
    for ne in loo_ne:
        if ne.id == i:
            return ne

def lookup_portobj_by_slotport(s,ne):
    ''' Returns the port object that matches
    the supplied slotport string. 
    '''
    for port in ne.type.ports.portlist:
        if port.slotport.value == s:
            return port

def family_matters(crawl):
    ''' Establishes the parent/child relationships between
    network elements. 
    '''
    myfunc = str(giveupthefunc())
    '''
    # first, we need to remove any duplicates (*cough* Classic Residence *cough*)
    try:
        tempset = set(crawl.loo_ne)
        # blank out the main list and recreate from the set
        crawl.loo_ne = []
        for thing in tempset:
            crawl.loo_ne.append(thing)
    except Exception as ex_dupremove:
        logging.debug(myfunc + '\t' +
            "Exception attempting to remove duplicates from crawl.loo_ne with set(): " + str(ex_dupremove))
    '''
   

    # now identify roots, this breaks if multiple sites in one crawl
    rootmac = ''
    for ne in crawl.loo_ne:
        try:
            for route in ne.type.routes.routelist:
                    if route.destination.value == '0.0.0.0/0':
                        ne.defaultrouteip = route.gateway.value
                        break
        except Exception as ex_drt:
            logging.debug(myfunc + '\t' +
                "Exception attempting to pull default route: " + str(ex_drt))
        int_ip_found_in_crawl = False
        try:
            for ne_ in crawl.loo_ne:
                for interface in ne_.type.interfaces.interfacelist:
                    if interface.address.value == ne.defaultrouteip:
                        int_ip_found_in_crawl = True
            # have to make sure typecrawled is true otherwise it tries to make
            #  NE's with failed pulls into roots.
            ''' 20150604_russ-Also hit a bug where the absence of a default route would flag a
            switch as .isroot. In this case there was no default route on the switch so it obviously
            wasn't finding that IP in the rest of the NE's interfaces so it was improperly flagging 
            that switch as .isroot.
            '''
            if not int_ip_found_in_crawl and ne.typecrawled and ne.defaultrouteip != '':
                ne.isroot = True
                ne.isaparent = True # of course if it's a root then it's also a parent
                try:
                    rootmac = ne.macs.macslist[0].value
                    logging.debug(myfunc + '\t' + 
                        "For '" + ne.hostname.value + 
                        "' found 'rootmac' of '" + rootmac + "'")
                except Exception as ex_rootmac:
                    logging.debug(myfunc + '\t' +
                        "Exception proccessing mac of suspected root NE: " + 
                        str(ex_rootmac))
        except Exception as ex_idroot:
            logging.debug(myfunc + '\t' + 
                "Exception identifying roots: " + str(ex_idroot))
            ne.isroot = False


    '''Now we can identify the upstream port on each NE
    The upstream port on each NE will always have the root NE's MAC
    address listed in it's mac-address-table'''
    for ne in crawl.loo_ne:
        try:
            ne.rootNEmac = rootmac
            for port in ne.type.ports.portlist:
                for mac in port.associatedmacs.maclist:
                    if ne.rootNEmac in mac.mac.value:
                        ne.upstreamSlotport = port.slotport.value
                        ne.upstreamPort = port # the whole object
                        logging.debug(myfunc + '\t' +
                            "For '" + ne.hostname.value +
                            "' found upstreamSlotport of '" + ne.upstreamSlotport + "'")
        except Exception as ex_upstream:
            logging.debug(myfunc + '\t' +
                "Exception processing upstream port: " + str(ex_upstream))

    ''' Let's try and identify the upstream port of the root NE based
    on the default gateway IP and the ARP table.
    '''
    
    for ne in crawl.loo_ne:
        try:
            if ne.isroot:
                for arpentry in ne.type.arptable.arplist:
                    if arpentry.ip.value == ne.defaultrouteip:
                        ne.upstreamSlotport = arpentry.slotport.value
                        ne.upstreamPort = lookup_portobj_by_slotport(
                                                ne.upstreamSlotport,
                                                ne)
                        ne.rootupMAC = arpentry.mac.value
                        crawl.realrootmac = ne.rootupMAC
        except Exception as ex_rootup:
            logging.debug(myfunc + '\t' +
                "Exception attempting to find upstream port of root NE: " + str(ex_rootup))
    logging.debug(myfunc + '\t' + 
        "Discovered crawl.realrootmac: " + str(crawl.realrootmac))

     # identify lowest children
    for ne in crawl.loo_ne:
        ne.hostname.value = ne.hostname.value.rstrip('\r\n ')
        try:
            if len(ne.type.amap.amaplist) < 2:
                # needed to add this logic to make sure didn't fail when only two switches chained together.
                for amap in ne.type.amap.amaplist:
                    if ne.upstreamSlotport == amap.localslotport.value:
                        ne.islowestchild = True
                    else:
                        # if you've got ONE amap but it's not on the upstream, you've got to be a parent
                        ne.isaparent = True
            else:
                ne.isaparent = True
            
        except Exception as ex_lowchild:
            logging.debug(myfunc + '\t' +
                "Exception processing lowest child. May not be SCS.: " + str(ex_lowchild))
            ne.isaparent = False
            ne.islowestchild = False

    # now find direct children
    for ne in crawl.loo_ne:
        try:
            logging.debug(myfunc + '\t' +
                ": isroot?: " + str(ne.isroot) + ", isaparent?: " + str(ne.isaparent) + ", .islowestchild?: " + str(ne.islowestchild) + ": " + ne.hostname.value )
        except:
            logging.debug(myfunc + '\t' +
                "Exception processing NE: " + str(ne.id))
        if ne.isaparent:
            try:
                for rhost in ne.type.amap.amaplist:
                    try:
                        rhost_ne = lookup_ne_by_id(rhost.nox_linkedNEid,crawl.loo_ne)
                        # as long as the rhost_ne isn't the root and isn't on the upstream port
                        # if not rhost_ne.isroot and rhost.localslotport.value != ne.upstreamPort.slotport.value:
                        dbg_msg = [str(rhost_ne.isroot),rhost.localslotport.value,ne.upstreamSlotport,ne.hostname.value]
                        logging.debug(myfunc + '\t' + 
                            "rhost_ne.isroot?: {0}, rhost.localslotport.value: {1}, ne.upstreamSlotport: {2}, NE hostname: {3}".format(*dbg_msg))
                        # if not rhost_ne.isroot and rhost.localslotport.value != ne.upstreamSlotport:
                        if rhost.localslotport.value != ne.upstreamSlotport:
                            # assume it's a child
                            rhost_ne.loo_parents.append(ne)
                            ne.loo_children.append(rhost_ne)
                    except:
                        pass
            except Exception as ex_children:
                logging.debug(myfunc + '\t' + 
                    "Exception identifying children based on upstream port: " + str(ex_children))
                #ne.child_ids.append(rhost.nox_linkedNEid)
            #logging.debug("CHILD IDS FOR '%s': %s",ne.hostname.value,str(ne.child_ids))
            '''
            for ne_ in crawl.loo_ne:
                if ne_.id in ne.child_ids and not ne_.isroot:
                    ne_.loo_parents.append(ne)
                    ne.loo_children.append(ne_)
            '''


    # now summarize for child/parent list association and attach
    for ne in crawl.loo_ne:
        for ne_child in ne.loo_children:
            # find ne_child in ne.amap
            for amap in ne.type.amap.amaplist:
                if amap.remotemac.value == ne_child.macs.macslist[0].value:
                    # build a new associated NE with same id as child NE
                    ane = nwClasses.Assoc_NE(ne_child.id)
                    #ane.port = ane.Port()
                    ane.port.slotport = amap.localslotport.value
                    ane.hostname = ne_child.hostname.value
                    ane.typestring = ne_child.typestring
                    for port in ne.type.ports.portlist:
                        if port.slotport.value == ane.port.slotport:
                            ane.port.portid = port.id
                    ne.children.childrenlist.append(ane)
        logging.debug(myfunc + '\t' + 
            "///////////////////////////////////////////")
        logging.debug(myfunc + '\t' +
            "CHILDREN FOR NE: " + ne.hostname.value)
        for chillen in ne.children.childrenlist:
            logging.debug(myfunc + '\t' + chillen.dump())
        logging.debug(myfunc + '\t' +
            "///////////////////////////////////////////")
        for ne_parent in ne.loo_parents:
            # find ne_child in ne.amap
            for amap in ne.type.amap.amaplist:
                if amap.remotemac.value == ne_parent.macs.macslist[0].value:
                    # build a new associated NE with same id as child NE
                    ane = nwClasses.Assoc_NE(ne_parent.id)
                    #ane.port = ane.Port()
                    ane.port.slotport = amap.localslotport.value
                    ane.hostname = ne_parent.hostname.value
                    ane.typestring = ne_parent.typestring
                    for port in ne.type.ports.portlist:
                        if port.slotport.value == ane.port.slotport:
                            ane.port.portid = port.id
                    ne.parents.parentlist.append(ane)

def roto_rooter(crawl):
    ''' Does final cleanup to shuffle the root and real root around
    requires that peanut_gallery be run first.
    '''
    myfunc = str(giveupthefunc())
    # now go through and find the real root NE and strip parent
    logging.debug(myfunc + '\t' +
        "Discovering REAL root NE and stripping parent...")
    realroot_obj = None
    for ne in crawl.loo_ne:
        try:
            if ne.macs.macslist[0].value == crawl.realrootmac:
                logging.debug(myfunc + '\t' +
                    "Found REAL root NE with ID: " + str(ne.id))
                ne.realroot = True
                realroot_obj = ne
                # strip the parent
                ne.parents.parentlist = []
                # make the root switch as the child
                for ne_ in crawl.loo_ne:
                    if ne_.isroot:
                        logging.debug(myfunc + '\t' +
                            "Found ne_.isroot with ID: " + str(ne_.id))
                        # build a new associated NE with same id as child NE
                        ane = nwClasses.Assoc_NE(ne_.id)
                        #ane.port = ane.Port()
                        ane.port.slotport = 'NA'
                        ane.hostname = ne_.hostname.value
                        ane.typestring = ne_.typestring
                        ane.port.portid = 'NA'
                        ne.children.childrenlist.append(ane)
                    
        except Exception as ex_realroot:
            logging.debug(myfunc + '\t' + 
                "Exception finding realroot: " + str(ex_realroot))

    # now find the root and remove any children listed on the upstream port
    for ne in crawl.loo_ne:
        if ne.isroot:
            removallist = []
            for idx,anec in enumerate(ne.children.childrenlist):
                logging.debug(myfunc + '\t' +
                    "Comparing anec.port.slotport[" + anec.port.slotport + 
                    "] with ne.upstreamSlotport[" + ne.upstreamSlotport + "] ....(" +
                        str(idx) + " of " + str(len(ne.children.childrenlist)-1) + ")")
                if anec.port.slotport == ne.upstreamSlotport:
                    logging.debug(myfunc + '\t' + 
                        "Found an Assoc_NE on upstreamSlotport: " + str(ne.upstreamSlotport))
                    # lookup the ne object
                    oscar = lookup_ne_by_id(anec.id,crawl.loo_ne)
                    # if it's the real upstream NE then we move it to parent
                    try:
                        if oscar.macs.macslist[0].value == crawl.realrootmac:
                            logging.debug(myfunc + '\t' +
                                "Found REALROOT NE with ID: " + str(oscar.id))
                            ne.parents.parentlist.append(anec)
                        else:
                            # append the ne's mac to the realroot macslist
                            realroot_obj.macs.macslist.append(oscar.macs.macslist[0])
                            # and remove it from the crawl
                            crawl.loo_ne.remove(oscar)
                    except Exception as ex_oscar:
                        logging.debug(myfunc + '\t' + 
                            "Exception finding REALROOT NE: " + str(ex_oscar))
                    # either way add it to list of indices to be removed
                    removallist.append(idx)
            # now go through and blank out the children in the removallist
            removecount = 0
            for i in removallist:
                logging.debug(myfunc + '\t' +
                    "Removing ne.children.childrenlist["+str(i)+"]")
                removecount += 1
                ne.children.childrenlist[i] = 'NA'
            # now go through and actually delete those from the list
            for i in range(0,removecount):
                    logging.debug(myfunc + '\t' +
                        "Killing listing with 'NA'")
                    ne.children.childrenlist.remove('NA')
                    

def ne_audit_assocmacs(currentCrawl):
    ''' Scans through the currentCrawl NE's and 
    returns a list of associated mac addresses.
    '''
    myfunc = str(giveupthefunc())
    pass


def peckingOrder(currentCrawl):
    ''' Takes the currentCrawl and churns through NE's to determine
    parent/child relationships.
    '''
    myfunc = str(giveupthefunc())
    logging.debug(myfunc + '\t' + 
        "Length of currentCrawl.loo_ne: " + str(len(currentCrawl.loo_ne)))
    '''
    for ne in currentCrawl.loo_ne:
        # for now we'll work off of the AMAP until that breaks
        try:
            if ne.type != None and len(ne.type.amap.amaplist) > 0:
                # now loop through the amap remote hosts
                logging.debug(myfunc + '\t' + 
                        "REMOTEHOSTS FOR NE: " + ne.dump_basic_singleline() + '\n\r')
                for remotehost in ne.type.amap.amaplist:
                    additionalindent = '\t\t\t'
                    logging.debug(remotehost.dump(additionalindent))

            else:
                # not sure yet
                logging.debug(myfunc + '\t' + 
                    "No remote hosts in ne.amap.amaplist. No remotehost to NE id mapping performed.")
        except Exception as orrrr:
            logging.debug(myfunc + '\t' +
                "Exception checking ne.type.amap.amaplist, might not be SCS/SCR: " + str(orrrr))
    '''
    # for kicks, let's try an audit before running family matters
    from nwCrawl import ne_audit
    ne_audit(currentCrawl)
    family_matters(currentCrawl)
    peanut_gallery(currentCrawl)
    roto_rooter(currentCrawl)


# kick off the genTypeIdentifiers() function upon init
loo_typeIdentifiers = genTypeIdentifiers(typeIdentifiers)
# also process loo_typeIdentifiers to detect unique types
uniqueTypes = genUniqueTypes(loo_typeIdentifiers)
# now generate hostname identifiers
loo_hostnameIdentifiers = genHostnameIdentifiers(hostnameIdentifiers)