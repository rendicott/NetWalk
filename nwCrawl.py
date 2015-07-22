''' This module orechestrates the network crawl
by taking the input data and kicking off the various
crawler scripts. It then process the data based on the 
customized schemaModule.

Will try to keep this as generic as possible and do most
of the custom work inside the schemaModules.

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


# now test to see if we can load a schemaModule for vendor specific parsing
# try to open the schemaModule that will define how we vendor parse
try:
    schemaModule = __import__(nwConfig.schemaModule)
except Exception as e:
    msgtext = ("Unable to load schemaModule specified in nwConfig: " + str(e))
    dingding = nwClasses.Event(msgtext,"top of nwCrawl",True,True)
    msgtext = ("Program unable to continue without schemaModule. Exiting now...")
    dingding = nwClasses.Event(msgtext,"top of nwCrawl",True,True)
    sys.exit()




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

def runoscommand(commandstringraw,subool=None):
    funcname = str(giveupthefunc())
    if subool == None:
        subool = False
    logging.info(funcname + '\t' + nwConfig.rob + commandstringraw)
    if subool:
        commandlist = commandstringraw.split(' ')
        command = subprocess.Popen(commandlist,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
        outputstr, errors = command.communicate()
        logging.debug(funcname + '\t' +
            "Done running command, now list interpretation...")
        outputlis = [x for x in outputstr.split('\n')]
        return outputlis
    else:
        # make sure we're returning a list
        return os.popen(commandstringraw).readlines()
'''
def buildExpectCommand(ne):
    # Takes an NE and builds the expect script launch
    #  command based on the data stored in the object.


    myfunc = str(giveupthefunc())
    filename = ne.type.nox_discoveryexpectscript
    ipaddr = ne.sourceEntryObj.ip
    port = ne.sourceEntryObj.port
    username = ne.authobj.username
    password = ne.authobj.password
    timeout = schemaModule.primerExpectTimeout

    commandList = [nwConfig.expectPrefix,
                    filename,
                    ipaddr,
                    port,
                    username,
                    password,
                    timeout,
                    ]
    # join the commandlist and add spaces
    command = ' '.join(commandList)
    logging.debug(myfunc + '\t' +
        "Built OS command: " + command)
    return command
'''

def buildExpectCommand(entry,bool_useprimer=None,ne=None):
    ''' This function takes data from the Cfg()
    object built in the nwProcessInput module
    and obtains the info needed to launch the OS
    expect scripts.

    It chooses auth data from the EntryPoint.auth
    property pre-existing in the EntryPoint object. 

    '''
    myfunc = str(giveupthefunc())
    if bool_useprimer == None:
        bool_useprimer = True
    elif bool_useprimer == False:
        # must have ne
        try:
            ne.id
        except Exception as yt:
            logging.debug(myfunc + '\t' +
                "If not using primer, must send NE: " + str(yt))
    logging.debug(myfunc + '\t' +
        "Entering buildExpectCommand we have entry ID: " + 
        entry.id + ", with auth ID: " + entry.auth)
    entrid = entry.id
    ipaddr = entry.ip
    port = entry.port
    username = ''
    password = ''
    timeout = schemaModule.primerExpectTimeout
    authid = ''
    ''' cycle through authPossibilities until find the
    one with the entry.auth identifier. 
    '''
    username = entry.authobj.username
    password = entry.authobj.password
    authid = entry.auth

    # first we'll try and bypass hopcount to go direct as long as
    #  direct hasn't failed already
    if not entry.directfailed:
        logging.debug(myfunc + '\t' + 
            "Setting hopcount = 0 since entry.directfailed = " + str(entry.directfailed))
        entry.hopcount_saved = entry.hopcount
        entry.hopcount = 0
    elif entry.directfailed:
        logging.debug(myfunc + '\t' + 
        "Setting hopcount = hopcount_saved since entry.directfailed = " + str(entry.directfailed) +
        ". entry.hopcount_saved = " + str(entry.hopcount_saved))
        entry.hopcount = entry.hopcount_saved


    # pick the primerscript filename based on hopcount
    filename = ''
    if bool_useprimer:
        for ew in schemaModule.loo_expectwrappers:
            if ew.hopcount == entry.hopcount:
                filename = ew.primerscript
    else:
        filename = ne.type.nox_discoveryexpectscript
    
    # now build the command
    # starting with if we're a hopcount 0
    commandList = []
    if entry.hopcount == 0:
        commandList = [nwConfig.expectPrefix,
                        filename,
                        ipaddr,
                        port,
                        username,
                        password,
                        timeout,
                        ]    
    elif entry.hopcount == 1:
        # in a hopcount 1 scenario, first set of parameters belongs
        #  to the learnedFromEntryId
        ipaddr = entry.learnedfromEntryObj.ip
        port = entry.learnedfromEntryObj.port
        username_0 = entry.learnedfromAuthObj.username
        password_0 = entry.learnedfromAuthObj.password
        timeout = schemaModule.primerExpectTimeout
        commandList = [nwConfig.expectPrefix,
                        filename, # filename is the same
                        ipaddr,
                        port,
                        username_0,
                        password_0,
                        timeout,
                        ]
        # now for the second hop entrypoint
        ipaddr_1 = entry.ip
        port_1 = entry.port
        username_1 = username
        password_1 = password
        commandList_1 = [ipaddr_1,
                        port_1,
                        username_1,
                        password_1,
                        timeout]
        commandList += commandList_1
    elif entry.hopcount == 2:
        # in a hopcount 2 scenario, first set of parameters belongs
        #  to the learnedFromEntryId.learnedFromEntryId
        ipaddr = entry.learnedfromEntryObj.learnedfromEntryObj.ip
        port = entry.learnedfromEntryObj.learnedfromEntryObj.port
        username_0 = entry.learnedfromEntryObj.learnedfromAuthObj.username
        password_0 = entry.learnedfromEntryObj.learnedfromAuthObj.password
        timeout = schemaModule.primerExpectTimeout
        commandList = [nwConfig.expectPrefix,
                        filename, # filename is the same
                        ipaddr,
                        port,
                        username_0,
                        password_0,
                        timeout,
                        ]
        # second set of parameters belongs
        #  to the learnedFromEntryId
        ipaddr_1 = entry.learnedfromEntryObj.ip
        port_1 = entry.learnedfromEntryObj.port
        username_1 = entry.learnedfromAuthObj.username
        password_1 = entry.learnedfromAuthObj.password
        commandList_1 = [
                        ipaddr_1,
                        port_1,
                        username_1,
                        password_1,
                        timeout,
                        ]
        # now for the last hop entrypoint
        ipaddr_2 = entry.ip
        port_2 = entry.port
        username_2 = username
        password_2 = password
        commandList_2 = [ipaddr_2,
                        port_2,
                        username_2,
                        password_2,
                        timeout]
        commandList += commandList_1 + commandList_2
    # join the commandlist and add spaces
    command = ' '.join(commandList)
    logging.debug(myfunc + '\t' +
        "Built OS command: " + command)
    if bool_useprimer:
        entry.primercommand = command
    else:
        # not doing primer, return the prefix stuff to the buildAdvancedNE() function
        return(command)

def adjustAuth(target,entry,purgecurrent):
    ''' takes list of auth possibilities and sort
    by score. If 'purgecurrent' is set then the current
    auth entry is removed from the pool. Then the highest
    scored authpossibility is set as the current entry.auth 
    '''
    myfunc = str(giveupthefunc())
    def sortbyweight(listofauthidstrings):
        ''' Takes list of authid strings and resorts them
        based on their corresponding object's score. Returns
        sorted list of auth id strings.
        '''
        # take remaining allauths and build list of objects of real auths
        loo_auths = []
        for o in listofauthidstrings:
            for i in target.authlist:
                if o == i.id:
                    loo_auths.append(i)
        # give 1 extra weight to 'admin' if this is first round
        #  this will mess with scoring flow if 'admin' is naturally
        #  decremented to 1 by the scoring system.
        for o in loo_auths:
            if o.username == 'admin' and o.score == 1:
                o.score += 1
        # now sort based on score value
        loo_auths.sort(key=operator.attrgetter('score'))
        # now copy back to string list
        sortmsg = (myfunc + '\t\t\t' + "New auth sort order: \n")
        allauths = []
        for o in loo_auths:
            allauths.append(o.id)
            sortmsg += ("\t\t\t\tAuth ID: " + o.id + 
                ", Score: " + str(o.score) + 
                ", Uname: " + str(o.username) + '\n')
        logging.debug(sortmsg)
        return allauths

    # if instructed to purge current, append current auth to authfailed list
    if purgecurrent:
        entry.authfailed.append(entry.auth)
    logging.debug(myfunc + '\t' + 
        "starting adjustAuth alorigthm for Entry with ID: "+ entry.id + 
        ". Old auth id = " + entry.auth)
    allauths = []
    # first build list of authpossibilities
    for authposs in target.authlist:
        allauths.append(authposs.id)
    # now take list of all auths and sort by score
    allauths = sortbyweight(allauths)
    numtotalauths = str(len(allauths))
    logging.debug(myfunc + '\t' +
        "have list of auth possibilities length: " + numtotalauths)
    # now clean out all auths from authlist that have previously failed 
    if len(entry.authfailed) > 0:
        for failed in entry.authfailed:
            try:
                allauths.remove(failed)
            except:
                logging.debug(myfunc + '\t' + "Could not find: " + failed)
    try:
        logging.debug(myfunc + '\t' + "Now have allauths content of: " +
            str(allauths))
    except:
        logging.debug(myfunc + '\t' + "Failure pulling allauths contents, may be empty...")
    # check to see if there are any entries left in allauths
    if len(allauths) >= 1:
        # now pop the auth off the end of the list since it's the highest weighted
        entry.auth = allauths.pop()
        for o in target.authlist:
            if o.id == entry.auth:
                logging.debug(myfunc + '\t' +
                    "Choosing new auth ID: " + o.id + ", with Score: " + str(o.score))
        # now that allauths is clean from known-bad auths, reverse list and pop first entry
        logging.debug(myfunc + '\t' +
            "New auth ID = " + entry.auth)
    else:
        # need to log an xml error to notify user that we ran out of authpossibilities
        msgtext = ("Cycled through " + numtotalauths + " auth possibilities and found none " +
            "that work for Entry with ID: " + entry.id + ", IP: " + entry.ip)
        dingding = nwClasses.Event(msgtext,myfunc,False,True)
        # also flag entry as totally unreachable
        entry.reachable = False
    # finally, append the actual authobj to the entrypoint
    for auth in target.authlist:
        if auth.id == entry.auth:
            entry.authobj = auth
    return entry

def adjustAuthScore(target,entry,successbool):
    ''' Takes an entry's successful authentication method
    and adjusts the score of the auth possibility up or down
    based on successbool.

    '''
    myfunc = str(giveupthefunc())
    logging.debug("adjustAuthScore:: Adjusting Entry ID: " + entry.id + ", Auth ID: " + entry.auth)
    for authposs in target.authlist:
        if authposs.id == entry.auth:
            if successbool:
                authposs.score += 1
                logging.debug("adjustAuthScore:: Increasing authposs score. New Value: " + str(authposs.score))
            elif not successbool:
                authposs.score -= 1
                logging.debug("adjustAuthScore:: Decreasing authposs score. New Value: " + str(authposs.score))
        logging.debug("adjustAuthScore::" + '\t\t' + "Auth ID: " + authposs.id + ", Score: " + str(authposs.score))

def sleeper():
    ''' Sleeps for time specified in nwConfig.expectSleep then
    resubmits same Entry back to primerDriver
    '''
    myfunc = str(giveupthefunc())
    sleeptime = nwConfig.expectSleep
    logging.debug(myfunc + '\t' +
        "Sleeping " + str(sleeptime) + " seconds...")
    time.sleep(sleeptime)
    #logging.debug(myfunc + '\t' + 
        #"Resubmitting Entry ID " + entry.id + " back to primerDriver...")
    #primerDriver(target,entry)

def delete_ssh_keys():
    ''' Deletes the current profile's ~/.ssh/known_hosts keys
    to fix problems when they get out of synch.
    '''
    myfunc = str(giveupthefunc())
    logging.debug(myfunc + '\t' +
        "Attempting to delete known_hosts file...")
    try:
        knownhostscommand = 'rm $HOME/.ssh/known_hosts'
        results = runoscommand(knownhostscommand)
        logging.debug(myfunc + '\t' +
            "Results from knownhostscommand: ")
        for line in results:
            logging.debug(myfunc + '\t\t' + line)
    except Exception as ex_kh:
        logging.debug(myfunc + '\t' +
            "Exception deleting known_hosts file: " + str(ex_kh))

def primerDriver(target,entry):
    ''' This function takes the primer commands and runs them.
    If they fail for timeouts or bad passwords it handles
    all of that tweaking until the primer commands work. 
    '''
    myfunc = str(giveupthefunc())
    logging.debug(myfunc + '\t' + 
        "Entering primerDriver function...about to build and run oscommands")
    # first check to see if entry is reachable
    # also check to make sure not re-running if primer was successful
    counter = 0
    ####################while not entry.primersuccess:
    failed = False
    while not entry.primersuccess:
        # put a little saftey in there
        counter += 1
        if counter > 5:
            break
        # keep running until primersuccess
        if entry.reachable or entry.primersuccess or entry.directfailed:
            # first run adjust auth to see choose best auth
            purgecurrentbool = False
            entry = adjustAuth(target,entry,purgecurrentbool)
            # build expect command knowing we want the primer
            bool_useprimer = True
            buildExpectCommand(entry,bool_useprimer)
            entry.primeroutput = runoscommand(entry.primercommand)
            sleepandtryagain = False
            poutput = ''.join(entry.primeroutput)

            # add a flag so we know if we should watch out for direct failing
            #   when querying entrypoints that we learned through another NE
            directmightfail = False
            try:
                # if the entry has a learnedfromEntryObj then it was discovered
                #  through another object. In this case we know that direct access
                #  may fail. 
                logging.debug(myfunc + '\t' + 
                    "Entry ID: " + str(entry.id) + " was learned from " + 
                    str(entry.learnedfromEntryObj.id) + ". Setting DIRECTMIGHTFAIL = TRUE")
                directmightfail = True
            except:
                # means that this was not learned through another. Hence it's 
                #  probably only reachable direct meaning we don't need to flag 
                #  a direct failure. 
                pass

            # dump the output that's coming back to debug log
            logging.debug(myfunc + "\tEntry.primeroutput: \n\r" + poutput)
            ''' send each entry to the schemaModule.outputInspector()
            to determine whether or not the primer command was a success.
            If not, need to adjust auth or abandon that entry.'''
            (entry.reachable,
                authsuccess,
                sleepandtryagain,
                deletesshkeys) = schemaModule.outputInspector(entry.primeroutput)
            oi_msg = ("\tComing back from outputInspector we have:\n\r")
            oi_msg += ("\t\tentry.reachable = " + str(entry.reachable) + "\n\r")
            oi_msg += ("\t\tauthsuccess = " + str(authsuccess) + "\n\r")
            oi_msg += ("\t\tsleepandtryagain = " + str(sleepandtryagain))
            oi_msg += ("\t\tdeletesshkeys = " + str(deletesshkeys))
            logging.debug(myfunc + '\t' + oi_msg)
            if deletesshkeys:
                msgtext = "Bad SSH hostkeys detected, deleting known_hosts..."
                dingding = nwClasses.Event(msgtext,myfunc,False,True)
                delete_ssh_keys()
            elif not entry.reachable:
                if directmightfail:
                    entry.directfailed = True
                else:
                    msgtext = ("Entrypoint IP Unreachable: ( ID: " + entry.id +
                                ", IP: " + entry.ip + ", PORT: " + entry.port + 
                                ", AUTHattemptID: " + entry.auth + ") No further "
                                "attempts will be made on this entrypoint.")
                    dingding = nwClasses.Event(msgtext,myfunc,False,True)
                    entry.primersuccess = False
            elif not authsuccess:
                # need to adjust auth possibility and try again
                for authposs in target.authlist:
                    if authposs.id == entry.auth:
                        # log to event log with masked password
                        msgtext = ("Auth for entrypoint failed: ENTRY( ID: " + entry.id +
                            ", IP: " + entry.ip + ", PORT: " + entry.port + 
                            ", AUTHattemptID: " + entry.auth + ") with AUTH( USERNAME: " +
                            authposs.username + ", PASS: *********" 
                            )
                        dingding = nwClasses.Event(msgtext,myfunc,False,False)
                        # log to debug with clear password
                        logging.debug(myfunc + '\t' + msgtext + " -- [CLEAR PASSWORD: " + 
                            authposs.password + "]")
                # first adjust auth score based on failure
                adjustAuthScore(target,entry,False)
                # now adjust the authentication
                purgecurrentbool = True
                entry = adjustAuth(target,entry,purgecurrentbool)
            elif sleepandtryagain:
                msgtext = ("NE not ready. Sleeping " + str(nwConfig.expectSleep) +
                    " seconds.")
                dingding = nwClasses.Event(msgtext,myfunc,False,True)
                sleeper()
            elif entry.reachable and authsuccess:
                # must mean primer was successful
                entry.primersuccess = True
                # adjust authpossibility score based on auth success
                adjustAuthScore(target,entry,True)
                for authposs in target.authlist:
                    if authposs.id == entry.auth:
                        msgtext = ("Auth for entrypoint Succeeded: ENTRY( ID: " + entry.id +
                                    ", IP: " + entry.ip + ", PORT: " + entry.port + 
                                    ", AUTHattemptID: " + entry.auth + ") with AUTH( USERNAME: " +
                                    authposs.username + ", PASS: *********" 
                                    )
                        dingding = nwClasses.Event(msgtext,myfunc,False,True)
        # not reachable or primer success means no need to attempt again.
        else:
            pass
    logging.debug(myfunc + '\t' +
        "Leaving primerDriver with Entry ID: " + entry.id +
        ", Auth ID: " + entry.auth)
    return entry

def primerBrain(target):
    ''' This function orchestrates the functions of the
    initial primer functions. It cycles through the 
    entrypoints and kicks off the primer and learns the
    best authentication to use. 
    '''
    myfunc = str(giveupthefunc())
    for idx,entry in enumerate(target.entrypointlist):
        # create a flag to let the loop know when to stop
        #  working on the entry
        logging.debug(myfunc + '\t' +
            "\t\t\t\t\t\t{}{}{}{}{}{}{}{}{}  PRIMERBRAIN WORKING ON ENTRYPOINT " + 
            str(idx+1) + " of " + str(len(target.entrypointlist)) + 
            "   {}{}{}{}{}{}{}{}{}")
        entryfinished = False
        while not entryfinished:
            logging.debug(myfunc + '\t' +
                "At start of burrow while loop: \n" + entry.dumpdata())
            # cycle through primerDriver until get a reachable false or primersuccess true
            if entry.reachable:
                entry = primerDriver(target,entry)
            if not entry.reachable and entry.directfailed:
                entry = primerDriver(target,entry)
            if entry.primersuccess == False and entry.reachable == True:
                entryfinished = False
            elif entry.primersuccess == True and entry.reachable == True:
                entryfinished = True
            elif entry.primersuccess == False and entry.reachable == False:
                if entry.directfailed:
                    entryfinished = False
                else:
                    entryfinished = True
            logging.debug(myfunc + '\t' +
                "At end of burrow while loop: \n" + entry.dumpdata())
            time.sleep(2)



def createBaseNE(target,entry):
    ''' Parse the primeroutput and send data to 
    schemaModule's createBaseNE function. Will pass
    the NetworkElement class down to schemaModule
    so schemaModule can inherit. 

    All NE's--regardless of type--will have the basic
    properties defined in the NetworkElement class.
    '''
    myfunc = str(giveupthefunc())
    # create a temp network element with id from Cfg() method
    temp_ne = nwClasses.NetworkElement(werd.neIdRequest())
    # send the entry.primeroutput to schemaModule to parse what we want
    logging.debug(myfunc + '\t' + 
        "Examining primerOutput for Entry ID: " + entry.id)
    (typestring,
        hname) = schemaModule.fetchBaseNEdata(entry.primeroutput,entry)
    # now we have enough to build a basic NE
    temp_ne.hostname.value = hname
    temp_ne.typestring = typestring
    # we can go ahead and pull the NE IP from the entry IP
    # need to create this as an object then append to the NE's iplist
    ipobj = temp_ne.ips.Ip()
    ipobj.address.value = entry.ip
    temp_ne.ips.iplist.append(ipobj)
    # also, since we know this NE came from an entrypoint, set that property
    temp_ne.sourceEntryId.value = entry.id
    temp_ne.sourceEntryObj = entry
    for auth in target.authlist:
        if auth.id == entry.auth:
            # appends the auth possibility object to the NE
            temp_ne.authobj = auth
    msgtext = ("Entry ID: " + entry.id + 
        " with Entry IP: " + entry.ip + 
        ": Detected as type '" + typestring + "', hostname: '" +
        hname + "'")
    dingding = nwClasses.Event(msgtext,myfunc,False,True)
    msgtext = ("Created NE object:::" + temp_ne.dump_basic_singleline())
    dingding = nwClasses.Event(msgtext,myfunc,False,True)
    logging.debug(myfunc + "\t" + temp_ne.dump_basic_multiline())
    return temp_ne

def buildExpectScript(ne):
    ''' takes a block of body text and generates a .sh file
    storing it in current directory. Returns the filename 
    of the expect script.
    '''
    myfunc = str(giveupthefunc())
    alreadygeneratedfilename = False
    try:
        filename = 'expect---' + werd.randomNumberBlock() + "---" + ne.hostname.value + '.sh'
        try:
            if not alreadygeneratedfilename:
                #if ne.sourceEntryObj.learnedfromEntryObj.learnedfromEntryObj.hostname != None:
                if ne.sourceEntryObj.hopcount == 2:
                    filename = ('expect---' + 
                            werd.randomNumberBlock() + "---" + 
                            ne.sourceEntryObj.learnedfromEntryObj.learnedfromEntryObj.hostname + "---" +
                            ne.sourceEntryObj.learnedfromEntryObj.hostname + "---" +
                            ne.hostname.value + '.sh')
                    alreadygeneratedfilename = True
        except Exception as eee:
            logging.debug(myfunc + '\t' +
                "Exception building hop 2 filename: " + str(eee))
        try:
            if not alreadygeneratedfilename:
                #if ne.sourceEntryObj.learnedfromEntryObj.hostname != None:
                if ne.sourceEntryObj.hopcount == 1:
                    filename = ('expect---' + 
                            werd.randomNumberBlock() + "---" + 
                            ne.sourceEntryObj.learnedfromEntryObj.hostname + "---" +
                            ne.hostname.value + '.sh')
                    alreadygeneratedfilename = True
        except Exception as eee:
            logging.debug(myfunc + '\t' +
                "Exception building hop 1 filename: " + str(eee))
    except Exception as e:
        logging.debug(myfunc + '\t' + "Exception building filename: " + str(e))
        if not alreadygeneratedfilename:
            filename = 'expect---' + werd.randomNumberBlock() + '---UNKNOWNHOST.sh'
            alreadygeneratedfilename = True
    body = schemaModule.genExpect_Discovery(ne)

    logging.debug(myfunc + '\t' +
        "Attempting to open filename: " + filename + ". For writing...")
    with open(filename,'wb') as f:
        f.write(body)
    return filename

def buildAdvancedNE(basic_ne):
    ''' Takes a base NE and orchestrates the functions required
    to add more advanced data. 
    '''
    myfunc = str(giveupthefunc())
    def dataGrabber(ne):
        finished = False
        counter = 0
        maxattempts = 7
        while not finished:
            counter += 1
            if counter > maxattempts:
                logging.debug("dataGrabber(): Maxattempts of "+str(maxattempts)+" reached")
                break
            logging.debug(myfunc + '\t' + "attempting to run temp_ne discovery expect script...")
            ne.type.nox_discoveryoutput = runoscommand(ne.type.nox_discoveryexpectcommand)
            
            (reachable,
                authsuccess,
                sleepandtryagain,
                deletesshkeys) = schemaModule.outputInspector(ne.type.nox_discoveryoutput)
            if deletesshkeys:
                msgtext = "Bad SSH hostkeys detected, deleting known_hosts..."
                dingding = nwClasses.Event(msgtext,myfunc,False,True)
                delete_ssh_keys()
            elif sleepandtryagain:
                msgtext = ("NE not ready. Sleeping " + str(nwConfig.expectSleep) +
                    " seconds.")    
                dingding = nwClasses.Event(msgtext,myfunc,False,True)
                sleeper()
            elif len(ne.type.nox_discoveryoutput) < schemaModule.minimum_discoveryoutputlength:
                logging.debug(myfunc + '\t' +
                    "Length of nox_discoveryoutput: '" + str(len(ne.type.nox_discoveryoutput)) + 
                    "' which is less than 'schemaMoodule.minimum_discoveryoutputlength' of '" + 
                    str(schemaModule.minimum_discoveryoutputlength) + "'. Sleeping and trying again.")
                sleeper()
            else:
                finished = True
        return(ne)
    # take the base NE and based on type, append
    #  the specific type object from the schemaModule
    basic_ne = schemaModule.appendTypeToNE(basic_ne)
    if basic_ne.type != None:
        counter = 0
        counter_maxattempts = nwConfig.maxpullattempts
        finished = False
        while not finished:
            logging.debug(myfunc + '\t' +
                "At end of while loop, basic_ne.badpull = " + str(basic_ne.badpull))
            counter += 1
            # first thing we want to do is build the expect script to do discovery
            bool_useprimer = False
            logging.debug(myfunc + '\t' + "attempting to build temp_ne discovery expect script from body...")
            basic_ne.type.nox_discoveryexpectscript = buildExpectScript(basic_ne)
            logging.debug(myfunc + '\t' + "attempting to build temp_ne discovery expect command from NE info...")
            basic_ne.type.nox_discoveryexpectcommand = buildExpectCommand(basic_ne.sourceEntryObj,bool_useprimer,basic_ne)
            # now we want to run the discovery and append results to object
            basic_ne = dataGrabber(basic_ne)

            logging.debug(myfunc + '\t' + 
                "now have 'basic_ne.type.nox_discoveryoutput' of len: " + str(len(basic_ne.type.nox_discoveryoutput)))
            # dump the output to file for testing purposes.
            logging.debug(myfunc + '\t' + 
                "Attempting to write 'basic_ne.type.nox_discoveryoutput' to file...")
            basic_ne.type.dumpDiscoveryOutputToFile()
            # dump the Network Element object to pickle file for testing purposes.
            #logging.debug(myfunc + '\t' + "Attempting to write 'basic_ne' to pickle file...")
            #basic_ne.pickleMeElmo()

            # now parse and create the Ports section of the ne.type
            #if basic_ne.typestring == 'scs' and not basic_ne.badpull:
            ''' First set badpull back to false and let parseData_SCS determine again'''
            basic_ne.badpull = False
            if basic_ne.typestring == 'scs':
                basic_ne = schemaModule.parseData_SCS(basic_ne)
                if not basic_ne.badpull:
                    finished = True
                    break
            if counter >= counter_maxattempts:
                msg = "Tried " + str(counter) + " times and still couldn't "
                msg += "get a good data pull. Abandoning."
                dingding = nwClasses.Event(msg,myfunc,False,True)
                finished = True
                break
            logging.debug(myfunc + '\t' +
                "At end of while loop, basic_ne.badpull = " + str(basic_ne.badpull))
    else:
        logging.debug(myfunc + '\t' + 
            "No ne type class detected. Should process as generic.")
    return(basic_ne)

def inititialzeNetworkElements(target,currentCrawl):
    ''' Takes a target and loops through the valid 
    entrypoints and builds the network element objects
    based on class. 
    '''
    myfunc = str(giveupthefunc())
    for idx,entry in enumerate(target.entrypointlist):
        if entry.primersuccess:
            logging.debug(myfunc + '\t' +
                "Working on Entry ID: " + entry.id + 
                ", with IP of " + entry.ip)
            # create the base NE from primeroutput data
            temp_ne = createBaseNE(target,entry)
            # now that we have the base we can run another pull for more specific data
            logging.debug(myfunc + '\t' +
                "\t\t\t\t\t\t-=-=-=-==-=-=-=-=-=-=-=-=-=-=-  INITNTWELEMENTS WORKING ON ENTRYPOINT " + 
                str(idx+1) + " of " + str(len(target.entrypointlist)) + 
                "   -=-=-=-==-=-=-=-=-=-=-=-=-=-=-")
            temp_ne = buildAdvancedNE(temp_ne)
            # append it to current crawl results list of objects network elements
            currentCrawl.loo_ne.append(temp_ne)
            msgtext = ("Crawled NE object:::" + temp_ne.dump_basic_singleline())
            dingding = nwClasses.Event(msgtext,myfunc,False,True)
            logging.debug(myfunc + '\t' + 
                "AFTER COMPLETING CRAWL: \n\r" + temp_ne.dump_basic_multiline())

def find_more_targets(target,currentCrawl):
    ''' takes the currentCrawl and analyzes the NE's to discover 
    possible relationships most of the work is done in the schemaModule's 
    routines but this is a global orchestrator. 
    '''
    myfunc = str(giveupthefunc())
    # first run the peckingOrder from the schema module
    ntarget = schemaModule.gen_next_target(target,currentCrawl)
    msgtext = (myfunc + '\t' + "Examined relationships and generated new target with hopdepth = " + str(ntarget.hopdepth) + 
        ". Number of new Entrypoints = " + str(len(ntarget.entrypointlist)))
    dingding = nwClasses.Event(msgtext,myfunc,False,True)
    return(ntarget)
    # do we need to do anything else before returning to burrow?

def lookup_ne_by_id(i,loo_ne):
    ''' Returns the NE object with id == i
    '''
    for ne in loo_ne:
        if ne.id == i:
            return ne

def map_view(crawl):
    templist = []
    _t = '----' # define a char tab since not all xml viewers like tabs
    templist.append("(((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((")
    for ne in crawl.loo_ne:
        if ne.realroot:
            templist.append(ne.id + " :: " + ne.typestring + " :: " + ne.hostname.value)
    for ne in crawl.loo_ne:
        if ne.isroot:
            templist.append(_t*1 + ne.id + " :: " + ne.typestring + " :: " + ne.hostname.value)
            for child in ne.children.childrenlist:
                working = lookup_ne_by_id(child.id,crawl.loo_ne)
                templist.append(_t*2 + child.port.slotport + " :: " + child.typestring + " :: " + child.hostname)
                try:
                    for child1 in working.children.childrenlist:
                        templist.append(_t*3 + child1.port.slotport + " :: " + child1.typestring + " :: " + child1.hostname)
                        try:
                            working1 = lookup_ne_by_id(child1.id,crawl.loo_ne)
                            #print("\t\t\t\t\tSearching children for working1: " + working1.hostname.value)
                            for child2 in working1.children.childrenlist:
                                templist.append(_t*4 + child2.port.slotport + " :: " + child2.typestring + " :: " + child2.hostname)
                                try:
                                    working2 = lookup_ne_by_id(child2.id,crawl.loo_ne)
                                    #print("\t\t\t\t\tSearching children for working1: " + working1.hostname.value)
                                    for child3 in working2.children.childrenlist:
                                        templist.append(_t*5 + child3.port.slotport + " :: " + child3.typestring + " :: " + child3.hostname)
                                except Exception as e:
                                    templist.append((_t*7 + "EXCEPTION: " + str(e)))
                        except Exception as e:
                            templist.append((_t*6 + "EXCEPTION: " + str(e)))
                except Exception as ex_mapper:
                    templist.append((_t*5 + "EXCEPTION: " + str(ex_mapper)))

    templist.append("----------------------")
    templist.append("Number of SCS: " + str(len(filter((lambda x: 'scs' in x.typestring),crawl.loo_ne))))
    templist.append("Number of metrocell: " + str(len(filter((lambda x: 'metrocell' in x.typestring),crawl.loo_ne))))
    templist.append("Number of UNKNOWN: " + str(len(filter((lambda x: 'UNKNOWN' in x.typestring),crawl.loo_ne))))
    templist.append(")))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))")
    crawl.textmap = templist

    for line in crawl.textmap:
        dingding = nwClasses.Event(line,'map_view(): ',False,True)


def link_members_to_ne(crawl):
    ''' Takes members inputted from xml and tries
    to map them to discovered NE's
    '''
    pass

def stats_view(crawl):
    # dump some statistics
    myfunc = str(giveupthefunc())
    logging.debug(myfunc + '\t' + "--------------------------------")
    logging.debug(myfunc + '\t' + "       FAMILY MATTERS           ")
    logging.debug(myfunc + '\t' + "--------------------------------")
    logging.debug(myfunc + '\t' + "")
    count = 0
    logging.debug(myfunc + '\t' + "LOWEST CHILDREN")
    logging.debug(myfunc + '\t' +"\t" + nwConfig.ne_fmt.format(*nwConfig.ne_hdr))
    for ne in crawl.loo_ne:
        if ne.islowestchild:
            count += 1
            logging.debug(myfunc + '\t' + "\t" + ne.dump_rowformat())
    logging.debug(myfunc + '\t' + "%s of %s are lowestchild",str(count),str(len(crawl.loo_ne)))

    count = 0
    logging.debug(myfunc + '\t' + "PARENTS")
    logging.debug(myfunc + '\t' + "\t" + nwConfig.ne_fmt.format(*nwConfig.ne_hdr))
    for ne in crawl.loo_ne:
        if ne.isaparent:
            count += 1
            logging.debug(myfunc + '\t' + "\t" + ne.dump_rowformat())
    logging.debug(myfunc + '\t' + "%s of %s are isaparent",str(count),str(len(crawl.loo_ne)))

    count = 0
    logging.debug("ROOTS")
    logging.debug(myfunc + '\t' + "\t" + nwConfig.ne_fmt.format(*nwConfig.ne_hdr))
    for ne in crawl.loo_ne:
        if ne.isroot:
            count += 1
            logging.debug(myfunc + '\t' + "\t" + ne.dump_rowformat())
    logging.debug(myfunc + '\t' + "%s of %s are isroot",str(count),str(len(crawl.loo_ne)))

    logging.debug(myfunc + '\t' + "CHILDREN")
    logging.debug(myfunc + '\t' + "\t" + nwConfig.ne_fmt.format(*nwConfig.ne_hdr))
    for ne in crawl.loo_ne:
        logging.debug(myfunc + '\t' + "*******************************************************")
        logging.debug(myfunc + '\t' + "DIRECT CHILDREN OF '%s'",ne.hostname.value)
        for child in ne.children.childrenlist:
            working = lookup_ne_by_id(child.id,crawl.loo_ne)
            try:
                logging.debug(myfunc + '\t' + "\t\t" + working.dump_rowformat())
            except Exception as ex_childrenlist:
                logging.debug(myfunc + '\t' + "\t\t" + "EXCEPTION WITH DIRECT CHILD: " + str(ex_childrenlist))
    logging.debug(myfunc + '\t' + "")
    logging.debug(myfunc + '\t' + "\t-----------------------")
    logging.debug(myfunc + '\t' + "\tPARENTAL RELATIONSHIPS")
    logging.debug(myfunc + '\t' + "\t-----------------------")
    for ne in crawl.loo_ne:
        logging.debug(myfunc + '\t' + "\t\t_____________________________________________________")
        logging.debug(myfunc + '\t' + "\t\tPARENTS OF " + ne.hostname.value)
        logging.debug(myfunc + '\t' + "\t\t" + nwConfig.ne_fmt.format(*nwConfig.ne_hdr))
        for parent in filter((lambda x: x.id in map((lambda y: y.id),ne.parents.parentlist)),crawl.loo_ne):
            logging.debug(myfunc + '\t' + "\t\t" + parent.dump_rowformat())
        logging.debug(myfunc + '\t' + "\t\t_____________________________________________________")
        logging.debug(myfunc + '\t' + "")
        logging.debug(myfunc + '\t' + "")

def oui_converter(currentCrawl):
    ''' Go through the NE's in the current crawl. If the hostname
    is set to a mac address, append the manufacturer to the end 
    of the hostname using the nwOUIExplorer classes.
    '''
    myfunc = str(giveupthefunc())
    import nwOUIexplorer
    for ne in currentCrawl.loo_ne:
        if ":" in ne.hostname.value: # quick and dirty mac detection
            try:
                ouifinder = nwOUIexplorer.Oui_Locator(ne.hostname.value)
                ne.hostname.value = ouifinder.return_combo()
                try:
                    for macstring in ne.macs.macslist:
                        tmac = nwOUIexplorer.Oui_Locator(macstring.value)
                        macstring.value = tmac.return_combo()
                except Exception as ex_maclist:
                    logging.debug(myfunc + '\t' +
                        "Exception converting ne.macs.macslist values to oui combo: " + 
                        str(ex_maclist))
            except Exception as ex_ouilookup:
                logging.debug(myfunc + '\t' + 
                    "Exception doing OUI lookup from NE hostname mac: " + str(ex_ouilookup))

def clean_dupes(currentCrawl):
    ''' Clean up some of the duplicate NE's that show up when there are a lot of
    badpull re-runs. 
    '''
    myfunc = str(giveupthefunc())       

    for idx,ne in enumerate(currentCrawl.loo_ne):
        try:
            if len(ne.macs.macslist) < 1:
                ne.removalflag = True
            elif len(ne.parents.parentlist)<1 and len(ne.children.childrenlist)<1:
                ne.removalflag = True
        except Exception as ex_dupes:
            logging.debug(myfunc + '\t' +
                "Exception processing macslist,parentlist, or childrenlist for dupe removal: " + str(ex_dupes))
            # go ahead and flag it for removal anyway
            ne.removalflag = True
    for ne in currentCrawl.loo_ne:
        if ne.removalflag:
            msgtext = ("Removing NE with partial data: '" + ne.hostname.value + "'...")
            dingding = nwClasses.Event(msgtext,"mod_ne_flag_delete(): ",True,True)
    currentCrawl.loo_ne = [x for x in currentCrawl.loo_ne if not ne.removalflag]

def ne_audit(currentCrawl):
    ''' After the crawl is completed, go through and try to find
    associated macs on ports that have no NE in the current crawl.
    Then make an attempt to create NE's out of the missing information.
    '''
    myfunc = str(giveupthefunc())
    # first query the schemaModule for all associated macs in a single table
    logging.debug(myfunc + '\t' +
        "Before removing duplicates from loo_scratchpad: " + str(len(currentCrawl.loo_scratchpad)))
    # first we need to go through and give dummy macs to NE's without macs
    for ne in currentCrawl.loo_scratchpad:
        try:
            ne.macs.macslist[0].value
        except:
            logging.debug(myfunc + '\t' +
                "Exception processing MAC for loo_scratchpad NE '" + ne.hostname.value + "'. Setting to 00:00:00:00:00:00")
            ne.macs = ne.Macs_List()
            tmac = ne.macs.Mac()
            tmac.value = '00:00:00:00:00:00'
            ne.macs.macslist.append(tmac)
    for ne in currentCrawl.loo_ne:
        try:
            ne.macs.macslist[0].value
        except:
            logging.debug(myfunc + '\t' +
                "Exception processing MAC for loo_ne NE '" + ne.hostname.value + "'. Setting to 00:00:00:00:00:00")
            ne.macs = ne.Macs_List()
            tmac = ne.macs.Mac()
            tmac.value = '00:00:00:00:00:00'
            ne.macs.macslist.append(tmac)
    # now remove dupes from loo_ne
    logging.debug(myfunc + '\t' +
        "Before removing duplicates from loo_ne: " + str(len(currentCrawl.loo_ne)))
    temp_loo_ne = set(currentCrawl.loo_ne)
    currentCrawl.loo_ne = []
    currentCrawl.loo_ne = [x for x in temp_loo_ne if not x.removalflag]
    logging.debug(myfunc + '\t' +
        "After removing duplicates from loo_ne: " + str(len(currentCrawl.loo_ne)))

    stripped = [item for item in currentCrawl.loo_scratchpad if item not in currentCrawl.loo_ne]
    '''
    stripped = set(currentCrawl.loo_ne)
    for ne in currentCrawl.loo_ne:
        for _ne in stripped:
            if ne == _ne:
                _ne.removalflag = True
    for _ne in currentCrawl.loo_scratchpad:
        if _ne.removalflag:
            try:
                currentCrawl.loo_scratchpad.remove(_ne)
            except Exception as ex_removescratch:
                logging.debug(myfunc + '\t' + 
                    "Exception deleting dupe NE: " + str(ex_removescratch))
    '''
    logging.debug(myfunc + '\t' +
        "After removing duplicates from loo_scratchpad(stripped): " + str(len(stripped)))
    # now we need to figure out how to get rid of these NE's that are actually port macs of other NEs
    portmacs = []
    for ne in currentCrawl.loo_ne:
        try:
            for port in ne.type.ports.portlist:
                portmacs.append(port.mac.value)
        except:
            pass
    # now go through and flag NEs that are really just port macs
    for ne in stripped:
        for portmac in portmacs:
            try:
                if ne.macs.macslist[0].value == portmac:
                    ne.removalflag = True
            except:
                pass
    unidentified = [x for x in stripped if not x.removalflag]
    logging.debug(myfunc + '\t' +
        "After removing known portmacs from stripped, unidentified): " + str(len(unidentified)))
    final = set(unidentified)
    logging.debug(myfunc + '\t' +
        "After removing duplicates from unidentified, final): " + str(len(final)))
    logging.debug(myfunc + '\t\t' + nwConfig.ne_fmt.format(*nwConfig.ne_hdr))
    for ne in final:
        logging.debug(myfunc + '\t\t' + ne.dump_rowformat())

    # now need to take the leftover NE's and place them into the loo_ne hierarchy
    for ne in final:
        # the parent of the unidentified element already exists, now just need
        #  to locate that parent and add this unidentified NE to it's children.
        for parent in ne.parents.parentlist:
            parentneobj = lookup_ne_by_id(parent.id,currentCrawl.loo_ne)
            # create the child ANE and append to parent's children list
            anep = nwClasses.Assoc_NE(ne.id)
            anep.typestring = ne.typestring
            anep.hostname = ne.hostname.value
            anep.port.portid = ne.parentportid
            anep.port.slotport = ne.parentport
            parentneobj.children.childrenlist.append(anep)
        # to make these strange ones easier to identify, prepend the hostname with '!'
        ne.hostname.value = "!!-" + ne.hostname.value
        currentCrawl.loo_ne.append(ne)



def peckingOrder(currentCrawl):
    ''' Sends currentCrawl to the schemaModule to attempt to establish
    parent/child relationships between NE's.
    '''
    myfunc = str(giveupthefunc())
    # run the schemaModules' pecking order which does family_matters and peanut_gallery
    schemaModule.peckingOrder(currentCrawl)
    # remove incomplete NE's
    clean_dupes(currentCrawl)
    # replace unknown NE's mac addy hostnames with manufacturer lookup
    oui_converter(currentCrawl)
    # audit learned NE's to see if we missed any
    ne_audit(currentCrawl)
    # log some stats for debug
    stats_view(currentCrawl)
    # generate a map view
    map_view(currentCrawl)



def burrow(target,currentCrawl=None):
    ''' This is the main runtime function of the crawler.
    This function should be initiated inside the main()
    block of nw.py. This burrow() function will orechestrate
    the other crawler actions within this nwCrawl module
    as well as the schemaModule.

    Returns the currentCrawl results as an object
    '''
    myfunc = str(giveupthefunc())
    # as long as we're under crawl depth
    finished = False
    count = 0
    while not finished:
        count += 1
        if count > 10:
            break
        elif target.hopdepth <= nwConfig.maxcrawldepth:
            # first kick off the primerBrain to get things started
            primerBrain(target)
            ''' Now we know several things: 
                    -which Entrypoints are valid
                    -which authentication to use for each EntryPoint
                    -the show system/chassis info for each
            '''
            # for now let's create a crawl per target here in nwCrawl
            if currentCrawl == None:
                currentCrawl = nwClasses.CrawlResults(target.id)
            # now kick off the initialization of the NEs
            inititialzeNetworkElements(target,currentCrawl)
            # decide what to crawl next
            ''' Insert next target decision code here'''
            # Take all discovered NE's and build relationships.
            # first, check to make sure we're not past max depth
            target = find_more_targets(target,currentCrawl)
        elif len(target.entrypointlist) == 0:
            logging.debug(myfunc + '\t' + 
                "Latest target has no entrypoints. Stopping BURROW.")
            finished = True
        else:
            msg = ("Max crawl depth set at: " + str(nwConfig.maxcrawldepth) + 
                ", Current target hopdepth = " + str(target.hopdepth) +
                ". Now stopping BURROW.")
            logging.debug(myfunc + '\t' + msg)
            finished = True


    # now churn through NE's to try and establish parent child relationships
    peckingOrder(currentCrawl)
    msgtext = ("Created " + str(len(currentCrawl.loo_ne)) + 
        " Network Element Objects")
    dingding = nwClasses.Event(msgtext,myfunc,False,True)
    logging.debug("---------------------------------")
    logging.debug("\t" + nwConfig.ne_fmt.format(*nwConfig.ne_hdr))
    for ne in currentCrawl.loo_ne:
        logging.debug("\t" + ne.dump_rowformat())
    return(currentCrawl)



    
