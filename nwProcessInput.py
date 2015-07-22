'''
This module contains all of the input processing
functions for the NetWalk application.

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

def parseXMLInput():
    ''' This function takes the input XML and parses it into
    various objects.

    '''
    myfunc = str(giveupthefunc())
    # first try and open the XML file
    logging.debug(myfunc + '\t' +
        "Attempting to open XML file for parsing...")
    with open(werd.fileXMLInput,'rb') as f:
        xml_list = f.readlines()
    xml_string = ''.join(xml_list)
    try:
        tree = ET.fromstring(xml_string)
    except Exception as e:
        xmlprocstring = (myfunc + '\t' +
            "Exception from ElementTree building tree from string: " + 
            str(e) + ". Exiting now...")
        dingding = nwClasses.Event(xmlprocstring,myfunc,True,True)
        werd.exitflag = True
    warningcount = 0
    if not werd.exitflag:
        for i,target in enumerate(tree._children):
            # this is the target id level
            try:
                t_targetId = target.attrib['id']
            except:
                pass
            logging.debug(myfunc + "\t" + 
                "t_targetId = " + t_targetId)
            logging.debug(myfunc + "\t" + 
                str(target._children))
            t_list_entrypoint = []
            t_list_auth = []
            t_list_member = []
            # now there are three possibilities for second level tags
            for secondlevel in target:
                if secondlevel.tag == "entrypoint":
                    # set up temp list to hold entrypoints
                    t_entrypointId = secondlevel.attrib["id"]
                    logging.debug(myfunc + "\t" + 
                        "\tENTRYPOINT ID = " + t_entrypointId)
                    for attribute in secondlevel:
                        for element in attribute:
                            try:
                                logging.debug(myfunc + "\t" + 
                                    "\t\t" + element.tag + " = " + element.text)
                            except:
                                logging.debug(myfunc + "\t" + 
                                    "\t\t" + element.tag + " = ")
                            # identify IP for entrypoint so we can create object
                            if element.tag == 'ipaddr':
                                if element.text != None:
                                    t_entrypointIp = element.text.rstrip('\t ')
                                    # now have enough info to create object
                                    t_cEntrypoint = nwClasses.Entrypoint(t_entrypointId,t_entrypointIp)
                                else:
                                    # need to bail since entrypoint requires IP
                                    exitmsg = ("No IP detected associated with entrypoint: '" +
                                        t_entrypointId + 
                                        "'. IP is required for entrypoints and therefore program will "
                                        "now exit.")
                                    dingding = nwClasses.Event(exitmsg,myfunc,True,True)
                                    werd.exitflag = True
                            # now check to see if a custom port is defined
                            if not werd.exitflag:
                                if element.tag == 'port' and element.text != None:
                                    t_cEntrypoint.port = element.text
                                else:
                                    pass
                                # now check to see if a custom hostname is defined
                                if element.tag == 'hostname' and element.text != None:
                                    t_cEntrypoint.hostname = element.text.rstrip('>< ')
                                else:
                                    pass
                    # now should have enough info to add entrypoint to temp list
                    if not werd.exitflag:
                        t_list_entrypoint.append(t_cEntrypoint)

                # now process auth and auth possibilities
                if secondlevel.tag == "auth":
                    logging.debug(myfunc + "\t" 
                        + "\tAUTH")
                    # this next level will be the <possibility> tags
                    for poss in secondlevel:
                        logging.debug(myfunc + "\t" + 
                            "\t\t" + poss.tag + " = " + poss.attrib["id"])
                        # assign possibility id to temp var
                        tPossibility_id = poss.attrib["id"]
                        # next level is the possibility attributes
                        for attrib in poss:
                            if attrib.text != None:
                                logging.debug(myfunc + "\t" + 
                                    "\t\t\t" + attrib.tag + " = " + attrib.text)
                            if attrib.tag == 'username':
                                if attrib.text != None:
                                    tPossibility_username = attrib.text
                                else:
                                    exitmsg = ("No username detected with auth possibility: '" +
                                        tPossibility_id + 
                                        "'. Username is an auth possibility requirement. Exiting "
                                        "now. ")
                                    dingding = nwClasses.Event(exitmsg,myfunc,True,True)
                                    werd.exitflag = True
                            if attrib.tag == 'password':
                                if attrib.text != None:
                                    tPossibility_password = attrib.text
                                else:
                                    exitmsg = ("No password detected with auth possibility: '" +
                                        tPossibility_id +
                                        "'. Password is an auth possibility requirement. Exiting "
                                        "now. ")
                                    dingding = nwClasses.Event(exitmsg,myfunc,True,True)
                                    werd.exitflag = True
                        if not werd.exitflag:
                            tPossibility = nwClasses.AuthPossibility(tPossibility_id,tPossibility_username,tPossibility_password)
                            t_list_auth.append(tPossibility)

                if secondlevel.tag == "members":
                    logging.debug(myfunc + "\t" + 
                        "\tMEMBERS")
                    tMember_id = ''
                    tMember_hostname = ''
                    tMember_ipaddr = ''
                    tMember_netmask = ''
                    tMember_defaultroute = ''
                    tMember_dhcps = ''
                    tMember_mac = ''
                    tMember_typestring = ''
                    for memberselement in secondlevel:
                        tMember_id = memberselement.attrib["id"]
                        logging.debug(myfunc + "\t" + 
                            "\t\t" + memberselement.tag + " = " + memberselement.attrib["id"])
                        for member in memberselement:
                            if member.tag == 'hostname':
                                if member.text == None:
                                    tMember_hostname = ''
                                else:
                                    tMember_hostname = member.text
                            elif member.tag == 'ipaddr':
                                if member.text == None:
                                    tMember_ipaddr = ''
                                else:
                                    tMember_ipaddr = member.text
                            elif member.tag == 'defaultroute':
                                if member.text == None:
                                    tMember_defaultroute = ''
                                else:
                                    tMember_defaultroute = member.text
                            elif member.tag == 'dhcps':
                                if member.text == None:
                                    tMember_dhcps = ''
                                else:
                                    tMember_dhcps = member.text
                            elif member.tag == 'mac':
                                if member.text == None:
                                    tMember_mac = ''
                                else:
                                    tMember_mac = member.text.lower()
                            try:
                                logging.debug(myfunc + "\t" + 
                                    "\t\t\t" + member.tag + " = " + member.text)
                            except:
                                logging.debug(myfunc + "\t" + 
                                    "\t\t\t" + member.tag + " = ")
                            try:
                                if member.tag == 'custom':
                                    tMember_typestring = member.attrib['tag']
                            except Exception as ex_custtag:
                                logging.debug(myfunc + '\t' +
                                        "Exception pulling member.tag.attrib 'tag': " + str(ex_custtag))
                            for custom in member:
                                try:
                                    logging.debug(myfunc + "\t" + 
                                        "\t\t\t\t" + custom.tag + " = " + custom.text)
                                except Exception as ex_cust:
                                    logging.debug(myfunc + '\t' +
                                        "Exception pulling custom tags: " + str(ex_cust))
                                    logging.debug(myfunc + "\t" + 
                                        "\t\t\t\t" + custom.tag + " = ")
                        tMember = nwClasses.Member(tMember_id)
                        tMember.hostname = tMember_hostname
                        tMember.ipaddr = tMember_ipaddr
                        tMember.netmask = tMember_netmask
                        tMember.defaultroute = tMember_defaultroute
                        tMember.dhcps = tMember_dhcps
                        tMember.mac = tMember_mac
                        tMember.typestring = tMember_typestring
                        werd.loo_members.append(tMember)

                elif(secondlevel.tag != "entrypoint" and 
                    secondlevel.tag != "auth" and 
                    secondlevel.tag != "members"):
                        warningcount += 1
                        msgtext = ("Warning, tags detected other than "
                            "ENTRYPOINT, AUTH, and MEMBERS. Suspect bad XML" )
                        dingding = nwClasses.Event(msgtext,myfunc,False,True)
                if warningcount > 1:
                    werd.exitflag = True
            # now we should have enough to create our target
            if not werd.exitflag:
                tTarget = nwClasses.Target(t_targetId,
                                            t_list_entrypoint,
                                            t_list_auth)
                tTarget.hopdepth = 0
                werd.loo_targets.append(tTarget)



