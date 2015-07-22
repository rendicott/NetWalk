'''
---NetWalk-----
This program was created by Russell Endicott for 
the purpose of crawling remote switches and 
routers through an SSH interface in order to 
determine network topoplogy and various other
configurations of interest.

It's XML driven in that it expects an input XML
for targets to crawl and returns an XML based
toplogy. XML schema definitions can be found
in the README. 

Written by Russell Endicott (rendicott@gmail.com)

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
import nwProcessInput
import nwCrawl

    

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

def main():
    ''' This is the main runtime block of the NetWalk application.

    '''
    myfunc = str(giveupthefunc())
    # here we actually parse the input XML
    nwProcessInput.parseXMLInput()
    # kicking off a test of the Event() system
    for member in werd.loo_members:
        logging.debug(member.dump())
    msgtext = "Starting Event() facility..."
    dingding = nwClasses.Event(msgtext,myfunc,False,True)
    # testing the objectification of the target data
    logging.debug(myfunc + '\t' +
        "werd.exitflag value = " + str(werd.exitflag))
    if not werd.exitflag:
        for o in werd.loo_targets:
            logging.debug(myfunc + '\t' + o.dumpdata())
    print(' ')
    # pick one target and send to burrow
    for tgt in werd.loo_targets:
        # now kick off the burrow
        crawlresults = nwCrawl.burrow(tgt)
        logging.debug(myfunc + '\t' + 
            "Now have crawl results, attemping to serialize into XML")
        xml = crawlresults.genxml()
        # make a snippet for the debug log
        xmllogstring = xml[0:100] + '......'
        logging.debug(myfunc + '\t' + xmllogstring)
        # now we have the results so let's write it to the output file
        with open(werd.fileXMLOutput,'wb') as f:
            f.write(xml)
        break # just doing the first target for now
    # testing the objectification of the Cfg() data
    logging.debug(myfunc + '\t' + "Back in main...")
    logging.debug(myfunc + '\t' + werd.dumpdata())
    ''' Taking out this pickle section as it's struggling to pickle my custom 
    object structure for some reason.
    try:
        with open(nwConfig.defaultcrawlresultspicklefile,'wb') as f:
            #pickle.dump(crawlresults,f)
            pickle.dump(crawlresults, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as iu:
        logging.debug(myfunc + '\t' +
            "Tried dumping currentCrawl to pickle: " + str(iu))
    '''
    # now we're past the input parsing, time to prep for jump server


if __name__ == '__main__':
    ''' This is the initialization block of the NetWalk application.
    This section parses the input parameters, sets up logging, and
    then kicks off the main() function.

    '''
    # import the necessary Optionparsing libraries
    from optparse import OptionParser
    from optparse import OptionGroup
    usage = ("%prog [--help] [--debug] [--printtostdout] [--logfile] "
        "[--inputfile] [--outputfile]")
    parser = OptionParser(usage, version='%prog ' + nwConfig.sVersion)
    # set up a usage string.
    parser.add_option('-i','--inputfile', 
                    type='string',
                    metavar='FILE',
                    help=("This XML file contains the information needed "
                        "to kick off the crawler. Includes target IP's "
                        "and possible usernames/passwords. Refer to "
                        "'sample-input.xml' for example usage."
                        ),default=None)
    parser.add_option('-o','--outputfile', 
                    type='string',
                    metavar='FILE',
                    help=("This is the desired output filename that "
                        "will contain the output topology XML. "
                        "Default is '"+nwConfig.defaultOutputXMLFilename+"'"
                        ),default=nwConfig.defaultOutputXMLFilename)
    parser_debug = OptionGroup(parser,'Debug Options')
    parser_debug.add_option('-d','--debug',type='string',
            help=('Available levels are CRITICAL (3), ERROR (2), '
                    'WARNING (1), INFO (0), DEBUG (-1)'),
            default='CRITICAL')
    parser_debug.add_option('-p','--printtostdout',action='store_true',
            default=False,help='Print all log messages to stdout')
    parser_debug.add_option('-l','--logfile',type='string',metavar='FILE',
            help=('Desired filename of log file output. Default '
                    'is "'+nwConfig.defaultlogfilename+'"')
            ,default=nwConfig.defaultlogfilename)
    parser_debug.add_option('-f','--fromfile',
                        type='string',
                        metavar='FILE',
                        help='This adds option to load crawlResults from '
                        'file instead of doing an actual crawl. Useful for '
                        'testing relationship parsing. Default is "'
                        + nwConfig.defaultcrawlresultspicklefile + '"',
                        default=nwConfig.defaultcrawlresultspicklefile)
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
    logging.debug("__name__ == __main__ : NetWalk version: " + nwConfig.sVersion)
    # now parse and setup the input file options
    if options.inputfile != None:
        try:
            open(options.inputfile)
            werd.fileXMLInput = options.inputfile
            logging.info("Successfully opened input file: '" + werd.fileXMLInput + "'")
        except Exception as e:
            failedstring = ("Failed to open input file specified in "
                "the --inputfile parameter: '" + options.inputfile + "'. "
                "Exiting now.: " + str(e))
            print(failedstring)
            logging.info(failedstring)
            sys.exit()
    else:
        exitstring = ("You must provide an input file using the --inputfile "
            "parameter. Exiting now.")
        print(exitstring)
        logging.info(exitstring)
        sys.exit()
    # Now parse and setup the output file options
    if options.outputfile != None:
        try:
            logging.debug("Attempting to open parameter specified output file for "
                "writing...")
            open(options.outputfile,'w')
            werd.fileXMLOutput = options.outputfile
            logging.info("Successfully opened output file: '" + werd.fileXMLOutput + "'")
        except Exception as e:
            failedwritestring = ("Failed to open output file specified in "
                "the --outputfile parameter: '" + options.outputfile + "'. "
                "Reverting to default filename: " + nwConfig.defaultOutputXMLFilename)
            print(failedwritestring)
            logging.info(failedwritestring)
            werd.fileXMLOutput = nwConfig.defaultOutputXMLFilename
            try:
                open(werd.fileXMLOutput,'w')
            except Exception as ee:
                failedwritestring2 = ("Failed to open default output file "
                    "for writing. Exiting now.")
                print(failedwritestring2)
                logging.info(failedwritestring2)
                sys.exit()
    else:
        werd.fileXMLOutput = nwConfig.defaultOutputXMLFilename
    if options.fromfile != None:
        try:
            with open(options.fromfile,'rb') as f:
                logging.info("__main__ : Length of fromfile = " + str(len(f.readlines())))
            werd.fromfile_bool = True
            werd.fromfile = options.fromfile
        except Exception as exer:
            logging.info("__main__ : Exception attempting to open fromfile: " + str(exer))

    logging.debug('__main__ : werd.fileXMLInput = ' + werd.fileXMLInput)
    logging.debug('__main__ : werd.fileXMLOutput = ' + werd.fileXMLOutput)

    main()


