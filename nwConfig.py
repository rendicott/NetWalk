'''
This is the primary configuration for the application
kicked off with nw.py.

It contains static configuration values for use with
the application in order to keep static assignments
out of the working code.

'''

# the overall NetWalk application current version
sVersion = '0.5'

# the default filename of the output XML if no
# filename is specified in the input parameters
defaultOutputXMLFilename = 'output.xml'

# the default filename of the output log file
# for standard logging or debugging purposes unless
# a different filename is specified in the input
# parameters.
defaultlogfilename = 'nw.log'

# working directory for output expect logs and scripts
#workdir = './working/'

# default port for SSH attempts
defaultSSHPort = '22'

# LOCAL OS PATH SUPPORT
expectPrefix = '/usr/bin/expect'

#define a long banner string when we run an OS command
#declaring here saves space in the rest of the code
rob = "=-=-=-=-=- RUNNING OS COMMAND =-=-=-=-=-: "

# define sleep time in seconds between expect SSH attempts
expectSleep = 20

# MODULE SUPORT
''' schemaModule defines which python module we'll use to parse
vendor specific data coming back from the pulls. If the file
is named "whatever.py" then the value for schemaModule would be
"whatever" without the .py
'''
schemaModule = 'nwParser_ALU_7705_6450'

# maximum depth to crawl
maxcrawldepth = 3
''' When adding hopdepth support the following functions need to be modified:
nwConfig.maxcrawldepth = 
nwCrawl.buildExpectCommand()
nwCrawl.buildExpectScript()
schemaModule.expectPrefix_X = """ """
schemaModule.genExpect_Discovery()
'''
'''The max number of attempts on an NE returning incomplete data
before abandoning'''
maxpullattempts = 4

# default file to dump pickled crawl results
defaultcrawlresultspicklefile = 'crawlresults.pkl'



''' Define the various rowformat headers and spacing for debugging tables '''
remotehost_hdr = [ 
                        'id',                       # {0
                        'lclsltprt',                # {1
                        'remotehostname',           # {2
                        'remotedevice',             # {3
                        'remotemac',                # {4
                        'remoteslotport',           # {5
                        'remoteips',                # {6
                        'nox_linkedNEid',           # {7
                        'nox_learnedfromNEid',      # {8
                        'nox_learnedfromEntryid',   # {9
                        'nox_learnedfromEntryObj',  # {10
                        'nox_learnedfromAuthObj',   # {11
                        'lclvlan',                  # {12
                        'remotevlan',               # {13
                    ]

remotehost_fmt = (      '{0:8}'         # id
                        '{1:10}'        # localslotport
                        '{2:30}'        # remotehostname
                        '{3:13}'        # remotedevice
                        '{4:18}'        # remotemac
                        '{5:15}'        # remoteslotport
                        '{6:16}'        # remoteips
                        '{7:16}'        # nox_linkedNEid
                        '{8:20}'        # nox_learnedfromNEid
                        '{9:23}'        # nox_learnedfromEntryid
                        '{10:24}'       # nox_learnedfromEntryObj
                        '{11:24}'       # nox_learnedfromAuthObj
                        '{12:8}'        # localvlan
                        '{13:11}'       # remotevlan
                    )

ne_hdr = [          'id',               # {0:}
                    'hostname',         # {1:}
                    'typestring',       # {2:}
                    'macs',             # {3:}
                    'ips',              # {4:}
                    'amaps',            # {5:}
                    'typestring',       # {6:}
                    'type',             # {7:}
                    'hopcount',         # {8:}
                    'dfltrtip',         # {9:}
                    'sourceEntryObj',   # {10:}
                    'sourceEntryId',    # {11:}
                    'upstreamSlotport', # {12:}
                    'parentport',       # {13:}
                    'parenthostname',   # {14:}
                    'rmvlflag',      # {15:}
        ]
ne_fmt = (          '{0:6}'             # id
                    '{1:30}'            # hostname
                    '{2:11}'            # typestring
                    '{3:18}'            # macs
                    '{4:16}'            # ips
                    '{5:6}'             # amaps
                    '{6:12}'            # type
                    '{7:12}'            # typecrawled
                    '{8:9}'             # hopcount
                    '{9:17}'            # defaultrouteip
                    '{10:30}'           # sourceEntryObj
                    '{11:15}'           # sourceEnryId
                    '{12:17}'           # upstreamSlotport
                    '{13:11}'           # parentport
                    '{14:25}'           # parenthostname
                    '{15:8}'            # rmvlflag
            )

ep_hdr = [
                    'id',                   # 0
                    'ip',                   # 1
                    'port',                 # 2
                    'hostname',             # 3
                    'learnedfromNEid',      # 4
                    'learnedfromEntryObj',  # 5
                    'learnedfromAuthObj',   # 6
                    'hopcount',             # 7
        ]
ep_fmt = (
                    '{0:6}'                 # id
                    '{1:16}'                # ip
                    '{2:22}'                # port
                    '{3:22}'                # hostname
                    '{4:23}'                # learnedfromNEid
                    '{5:23}'                # learnedfromEntryObj
                    '{6:23}'                # learnedfromAuthObj
                    '{7:9}'                 # hopcount
         )