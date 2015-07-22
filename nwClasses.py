'''
This file contains all of th custom classes used by the 
NetWalk application. 

'''

import time
import datetime
import logging
import pickle
import xml.etree.ElementTree as ET


# internal imports
import nwConfig

class Counter(object):
    ''' This is a counter object to be created when
    new classes of type target, etc. are created.
    A counter will be generated for each object type.
    The counter can be increased or reset depending
    on need. Also can be called upon to create 
    unique identifiers as needed.

    '''
    def __init__(self,name):
        self.name = name
        self.value = 1
    def increase(self):
        self.value += 1
    def decrease(self):
        if self.value >= 2:
            self.value -= 1
        else:
            self.value = 1
    def reset(self):
        self.value = 1
    def read(self):
        return str(self.value)

class EventLog(list):
    ''' Inherited from list type to hold
    Event() objects. Primarily set up to 
    create methods for dumping the event log
    or attaching it to XML.

    '''
    def __init__(self):
        self.type = "EventLog"
    def dumpdata(self):
        msgtext = ("EVENT LOG: \n")
        for line in self:
            msgtext += ("\t" + str(line) + '\n')
        return msgtext

class Cfg(object):
    ''' This class is the configuration defines
    a configuration object that the program can 
    use to pass configuration settings around between
    various functions. This lets us avoid using
    global variables. 

    '''
    def __init__(self):
        ''' we'll create a list for log messages
        so we can return an event log with the XML
        in the case of failure.
        '''
        self.messagelog = EventLog()
        self.fileXMLInput = ''
        self.fileXMLOutput = ''
        self.loo_targets = []
        self.loo_members = []
        # create an exit flag in case we want to bail
        self.exitflag = False
        # the current NE id number, used as a sort of global police to
        #   make sure we don't duplicate ID numbers
        self.currentNEidNumber = 1
        self.currentUID = 1
        self.fromfile = ''
        self.fromfile_bool = False
    def dumpdata(self):
        msgtext = ("TYPE: Cfg" + '\r\n' +
            "TARGETS: " + str(len(self.loo_targets)) + '\r\n' +
            "INPUT XML: " + self.fileXMLInput + '\r\n' +
            "OUTPUT XML: " + self.fileXMLOutput + '\r\n' + 
            "MESSAGES: " + str(len(self.messagelog)) + '\r\n'
            "FROMFILE_BOOL: " + str(self.fromfile_bool) + '\r\n'
            "FROMFILE: " + str(self.fromfile) + '\r\n'
            )
        if len(self.messagelog) >= 1:
            msgtext += self.messagelog.dumpdata()
        return msgtext
    def neIdRequest(self):
        ''' Returns the currentNEidNumber + 1 as a string
        '''
        self.currentNEidNumber+=1
        logging.debug("Cfg().neIdRequest(): currentNEidNumber = " + str(self.currentNEidNumber))
        return(str(self.currentNEidNumber))
    def genUID(self):
        ''' returns an incrementing number, useful for making sure
        element ID numbers are always unique. 
        '''
        self.currentUID += 1
        #logging.debug("Cfg().genUID(): currentUID = " + str(self.currentUID))
        return(str(self.currentUID))
    def randomNumberBlock(self):
        ''' Generates a random 5 digit number string and returns it. 
        Useful for creating filenames on disk, etc.
        '''
        import random
        blocksize = 5
        stringer = ''
        for i in range(0,blocksize):
            stringer += str(random.randrange(1,10))
        return stringer

'''create a configuration (Cfg) object to hold options instead of 
using global vars. Then we can just pass the options 
around into each function'''
werd = Cfg() #we'll call it something unique since we'll use it everywhere

class Event(object):
    ''' Let's create an event object so we can send log messages
    with timestamps back through the output XML.

    Timestamp must be a datetime object.
    '''
    def __init__(self,messagetext,funcname=None,printnow=None,lognow=None):
        if funcname == None:
            funcname = "UNKNOWN FUNCTION SOURCE"
        if printnow == None:
            printnow = False
        if lognow == None:
            lognow = False
        self.messagetext = messagetext
        self.timestamp = datetime.datetime.now()
        self.funcname = funcname
        self.printnow = printnow
        self.lognow = lognow
        if printnow:
            print(self)
        if lognow:
            logging.info(self)
        werd.messagelog.append(self)
    def __repr__(self):
        return(str(self.timestamp) + ":::" + self.funcname + ":::" + self.messagetext)
    def dump(self):
        return(str(self.timestamp) + ":::" + self.funcname + ":::" + self.messagetext)

class Target(object):
    ''' This defines the input target object. Major child objects
    are entrypoints, authentication, and members.

    At a bare minimum, a Target object must have at least one
    Entrypoint and one auth possibility.

    '''
    def __init__(self,identifier,entrypointlist,authlist):
        self.id = identifier
        # list of Entrypoint objects
        self.entrypointlist = entrypointlist
        # list of AuthPossibility objects
        self.authlist = authlist
        self.memberlist = []
        self.entrypoint_counter = Counter("Counter_Target_Entrypoint")
        ''' Incrementor for depth concept. Based on hopdepth the functions know whether
        or not to generate hop scripts rather than trying to reach the node directly. 
        '''
        self.hopdepth = 0
    def dumpdata(self,rowentry=None):
        if rowentry == None:
            rowentry = False
        msgtext = ("\n\rTYPE: Target \n\r")
        msgtext += ("\t" + "ID: " + self.id + '\n\r')
        msgtext += ("\t" + "ENTRYPOINTS: " + str(len(self.entrypointlist)) + '\n\r')
        for e in self.entrypointlist:
            if not rowentry:
                msgtext += (e.dumpdata() + '\n\r')
            else:
                msgtext += (e.dump_rowformat() + '\n\r')
        msgtext += ("\t" + "AUTHLIST: " + str(len(self.authlist)) + '\n\r')
        msgtext += ("\t" + "HOPDEPTH: " + str(self.hopdepth) + '\n\r')
        for e in self.authlist:
            msgtext += (e.dumpdata() + '\n\r')
        return msgtext




class Entrypoint(object):
    ''' This defines an entrypoint object. Its primary properties
    are an IP address and port number (default 22) for SSH attempt.

    '''
    def __init__(self,identifier,ip):
        self.id = identifier
        self.ip = ip
        # the SSH Port (IGNORED / NOT SUPPORTED DUE TO EXPECT LIMITATIONS)
        self.port = nwConfig.defaultSSHPort
        self.hostname = ''
        # the authPossibility identifier that worked for this entrypoint
        # by default will be 1 and will change if 1 doesn't work
        self.auth = '1'
        self.authobj = None
        # list of authpossibilities that failed
        self.authfailed = []
        # placeholder for primer OS command
        self.primercommand = ''
        # list to hold output from primer command
        self.primeroutput = []
        # flag to show primer success, False by default
        self.primersuccess = False
        # flag if entrypoint is reachable, True by default
        self.reachable = True
        # holder for the NE that this was learned through
        self.learnedfromNEid = 0
        self.learnedfromEntryObj = None
        self.learnedfromAuthObj = None
        self.hopcount = 0
        self.hopcount_saved = 0
        self.directfailed = False
    def dumpdata_singleline(self):
        msg = ''
        msg += ("TYPE: Entrypoint, ID: " + self.id + ", IP: " + self.ip + ", HOSTNAME: " + self.hostname)
        return(msg)
    def dumpdata(self):
        msgtext = ('\t\t' + "TYPE: Entrypoint" + '\n\r' +
            '\t\t\t' + "ID:\t\t\t" + self.id + '\n\r' +
            '\t\t\t' + "IP:\t\t\t" + self.ip + '\n\r' +
            '\t\t\t' + "PORT:\t\t\t" + self.port + '\n\r' +
            '\t\t\t' + "HOSTNAME:\t\t" + self.hostname + '\n\r' + 
            '\t\t\t' + "MEMID:\t\t\t" + str(id(self)) + '\n\r' + 
            '\t\t\t' + "LEARNEDFROMNEID:\t" + str(self.learnedfromNEid) + '\n\r')
        try:
            msgtext += ('\t\t\t' + "LEARNEDFROMENTRYOBJ:\t" + str(self.learnedfromEntryObj.id) + '\n\r' +
                        '\t\t\t' + "LEARNEDFROMAUTHOBJ:\t" + str(self.learnedfromAuthObj.id) + '\n\r' )
        except:
            msgtext += ('\t\t\t' + "LEARNEDFROMENTRYOBJ:\t" + "NONE" + '\n\r' +
                        '\t\t\t' + "LEARNEDFROMAUTHOBJ:\t" + "NONE" + '\n\r' )
        msgtext += ('\t\t\t' + "AUTH:\t\t\t" + self.auth + '\n\r' + 
            '\t\t\t' + "AUTHFAILED:\t\t" + str(self.authfailed) + '\n\r' + 
            '\t\t\t' + "PRIMERSUCCESS:\t\t" + str(self.primersuccess) + '\n\r' + 
            '\t\t\t' + "REACHABLE:\t\t" + str(self.reachable) + '\n\r'
            '\t\t\t' + "HOPCOUNT:\t\t" + str(self.hopcount) + '\n\r' +
            '\t\t\t' + "DIRECTFAILED:\t\t" + str(self.directfailed) + '\n\r'
            )
        return msgtext
    def dump_rowformat(self):    
        row = []
        row.append(self.id)
        row.append(self.ip)
        row.append(self.port)
        row.append(self.hostname)
        row.append(str(self.learnedfromNEid))
        try:
            row.append(str(self.learnedfromEntryObj.id)[:24])
            row.append(str(self.learnedfromAuthObj.id)[:24])
        except:
            row.append('NONE')
            row.append('NONE')
        row.append(str(self.hopcount))
        msg = nwConfig.ep_fmt.format(*row)
        return(msg)

class AuthPossibility(object):
    ''' This defines an authentication possibility object.
    These will be attached to Target objects so that 
    auth possibilities can be cycled through during 
    login attempts.

    '''
    def __init__(self,identifier,username,password):
        self.id = identifier
        self.username = username
        self.password = password
        # we'll create a scoring system so that auth possibilities
        # that work get graded higher.
        self.score = 1
    def dumpdata(self):
        msgtext = ('\t\t' + "TYPE: AuthPossibility" + '\n\r' +
            '\t\t\t' + "ID: " + self.id + '\n\r' +
            '\t\t\t' + "USERNAME: " + self.username + '\n\r' +
            '\t\t\t' + "PASSWORD: " + self.password + '\n\r')
        return msgtext

class Member(object):
    ''' This defines a member object to be used as a child
    of a Target object. At a bare minimum a member object
    needs a unique identifier. 

    '''
    def __init__(self,identifier):
        self.id = identifier
        # holder for an NE hostname
        self.hostname = ''
        # holder for IP address of member element
        self.ip = ''
        # holder for netmask of member element
        self.netmask = ''
        # holder for DHCP server IP
        self.dhcps = ''
        # holder for known default route
        self.defaultroute = ''
        # holder for NE MAC address
        self.mac = ''
        # add support for attaching a custom enhancement object
        self.custom = None
        # just do a typestring without messing with custom
        self.typestring = ''
    def dump(self):
        prefix = "#########   "
        msgtext = (prefix + '\t' + "TYPE: Member" + '\n\r')
        msgtext += prefix + '\t\t' + "ID: " + self.id + '\n\r'
        msgtext += prefix + '\t\t' + "HOSTNAME: " + self.hostname + '\n\r'
        msgtext += prefix + '\t\t' + "MAC: " + self.mac + '\n\r'
        msgtext += prefix + '\t\t' + "IP: " + self.ip + '\n\r'
        msgtext += prefix + '\t\t' + "NETMASK: " + self.netmask + '\n\r'
        msgtext += prefix + '\t\t' + "DHCPS: " + self.dhcps + '\n\r'
        msgtext += prefix + '\t\t' + "DEFAULTROUTE: " + self.defaultroute + '\n\r'
        msgtext += prefix + '\t\t' + "TYPESTRING: " + self.typestring + '\n\r'
        return(msgtext)

class MemberEnhancement(object):
    '''
    A flexible object that can be attached to a Member with 
    various additional information. If the member is discovered
    this information will be passed on directly into the output 
    XML associated with the discovered network element. An 
    example of how this could be used is when you know the 
    hostname of an element and want to display that hostname
    in the output topology associated with the discovered object.

    The tag element will be parsed to potentially use to 
    alter the crawler's behavior in the future. The 'tag' property 
    is required upon instantiation of a MemberEnhancement. 

    '''
    def __init__(self,tag):
        self.tag = tag
        # right now the only custom enhancment I can think of
        # would be the firstPublicIPinPath property of a metrocell
        self.fpip = ''

''' Define a short version on an NE that we can attach to the parent/child lists
of a full NE object.  
'''
class Assoc_NE():
    class Port():
        def __init__(self):
            self.xmldesc = 'port'
            self.portid = ''
            self.slotport = ''
    def __init__(self,id):
        self.xmldesc = 'ne'
        self.id = id
        self.typestring = ''
        self.hostname = ''
        self.port = self.Port()
    def dump(self):
        msg = "=========================\n\r"
        msg += "Assoc_NE():\n\r"
        msg += "\tID:\t\t\t" + str(self.id) + "\n\r"
        msg += "\tTYPESTRING:\t\t" + str(self.typestring) + "\n\r"
        msg += "\tHOSTNAME:\t\t" + str(self.hostname) + "\n\r"
        msg += "\tLOCAL_PORTID:\t\t" + str(self.port.portid) + "\n\r"
        msg += "\tLOCAL_SLOTPORT:\t\t" + str(self.port.slotport) + "\n\r"
        msg += "=========================\n\r"
        return(msg)

class NetworkElement(object):
    ''' Class to define a basic network element with basic
    generic properties. A more advanced 'Type' object can be
    attached to the basic NE. 

    '''
    class Parents_List():
        def __init__(self):
            self.xmldesc = 'parents'
            self.parentlist = []
            # parentlist.append(Assoc_NE('1')
    class Children_List():
        def __init__(self):
            self.xmldesc = 'children'
            self.childrenlist = []
            # childrenlist.append(Assoc_NE('1')
    class Macs_List():
        class Mac():
            def __init__(self):
                self.xmldesc = 'mac'
                self.value = ''
            def __repr__(self):
                return(self.value)
        def __init__(self):
            self.xmldesc = 'macs'
            self.macslist = []
            # macslist.append(Mac())
    class Ips_List():
        class Ip():
            class Address():
                def __init__(self):
                    self.xmldesc = 'address'
                    self.value = ''
                def __repr__(self):
                    return(self.value)
            class Mask():
                def __init__(self):
                    self.xmldesc = 'mask'
                    self.value = ''
                def __repr__(self):
                    return(self.value)
            def __init__(self):
                self.xmldesc = 'ip'
                self.address = self.Address()
                self.mask = self.Mask()
            def __repr__(self):
                return(self.address.value)
        def __init__(self):
            self.xmldesc = 'ips'
            self.iplist = []
    class PullTimeStamp():
        def __init__(self):
            self.xmldesc = 'pulltimestamp'
            self.value = datetime.datetime.now()
    class Hostname():
        def __init__(self):
            self.xmldesc = 'hostname'
            self.value = ''
    class SourceEntryId():
        def __init__(self):
            self.xmldesc = 'sourceentryid'
            self.value = ''
    # define an __eq__ and __hash__ method so we can remove duplicates with set()
    def __eq__(self, other):
        return self.macs.macslist[0].value==other.macs.macslist[0].value
    def __hash__(self):
        return hash(('mac', self.macs.macslist[0].value))
    def __init__(self,identifier):
        # the only property required on init is an id number
        self.id = identifier
         # the typestring is more human readable, should derive
        #  from the type class attached.
        self.typestring = ''
        self.xmldesc = 'ne'
        self.xmlparent = ''
        # optional hostname of NE
        self.hostname = self.Hostname()
        # placeholder for immediate parents
        self.parents = self.Parents_List()
        # placeholder for immediate children
        self.children = self.Children_List()
        # placeholder for mac addresses associated with NE
        self.macs = self.Macs_List()
        # placeholder for ip addresses associated with NE
        self.ips = self.Ips_List()
        # datetime object of when NE was created
        self.pulltimestamp = self.PullTimeStamp()
        # the type will eventually be an attached class
        self.type = None
        # if NE was created from an entrypoint it's nice to track that source
        self.sourceEntryId = self.SourceEntryId()
        # flag to determine if the NE has been type crawled yet
        self.typecrawled = False
        # make a flag to catch incomplete data pulls
        self.badpull = False
        self.hopcount = 0
        ##### Section to hold parent/child relationship discovery flags #######
        self.islowestchild = False
        self.isaparent = False
        self.isroot = False
        self.defaultrouteip = ''
        self.rootupMAC = ''
        self.rootNEmac = '' # MAC of top root element
        self.realroot = False
        self.upstreamPort = None # port object of upstream port
        self.upstreamSlotport = '' # slotport descriptor of upstream port
        self.loo_children = []
        self.child_ids = []
        self.loo_parents = []
        self.parent_ids = []
        # flag to indicate whether or not we've crawled mac-address-table
        self.macattack = False 
        self.removalflag = False # to indicate when this NE should be removed from some list
        self.parentport = '' # quick and dirty place to store the parent's slotport
        self.parentportid = '' # quick and dirty place to store parent's port ID
        self.parenthostname = '' # quick and dirty place to store the parent's hostname
    # placeholder to append the auth possibility object for future authentications
    authobj = None
    sourceEntryObj = None
    def dump_basic_multiline(self):
        ''' Returns the basic object properties for NE.
        Does not dump all specific type data. Primarily used
        to pull for logging updates.
        '''
        msgtext = ("\n\tObject Class: NetworkElement: {\n\r")
        msgtext += ("\t\t ID:\t\t\t" + self.id + "\n\r")
        msgtext += ("\t\t HOSTNAME:\t\t" + self.hostname.value + "\n\r")
        msgtext += ("\t\t TYPESTRING:\t\t" + self.typestring + "\n\r")
        msgtext += ("\t\t PARENTS:\t\t" + str(self.parents.parentlist) + "\n\r")
        msgtext += ("\t\t CHILDREN:\t\t" + str(self.children.childrenlist) + "\n\r")
        msgtext += ("\t\t MACS:\t\t\t" + str(self.macs.macslist) + "\n\r")
        msgtext += ("\t\t IPS:\t\t\t" + str(self.ips.iplist) + "\n\r")
        msgtext += ("\t\t PULLTIMESTAMP:\t\t" + str(self.pulltimestamp.value) + "\n\r")
        msgtext += ("\t\t TYPE:\t\t\t" + str(self.type) + "\n\r")
        msgtext += ("\t\t TYPECRAWLED:\t\t" + str(self.typecrawled) + "\n\r")
        msgtext += ("\t\t HOPCOUNT:\t\t" + str(self.hopcount) + "\n\r")
        msgtext += ("\t\t DEFAULTROUTEIP:\t\t" + str(self.defaultrouteip) + "\n\r")
        msgtext += ("\t\t UPSTREAMSLOTPORT:\t\t" + str(self.upstreamSlotport) + "\n\r")
        try:
            msgtext += ("\t\t SOURCEENRYOBJ:\t\t" + str(self.sourceEntryObj.id) + "\n\r")
        except:
            msgtext += ("\t\t SOURCEENRYOBJ:\t\t" + "NONE" + "\n\r")
        msgtext += ("\t\t SOURCEENTRYID:\t\t " + str(self.sourceEntryId.value) + "\n\r")
        msgtext += ("\t}")
        return msgtext
    def dump_rowformat(self):
        row = []
        row.append(self.id)
        nhostname = self.hostname.value[:25]
        row.append(nhostname.rstrip('\r\n '))
        row.append(self.typestring)
        try:
            row.append(str(self.macs.macslist[0].value))
        except:
            row.append('NA')
        try:
            row.append(str(self.ips.iplist[0].value))
        except:
            row.append('NA')
        try:
            row.append(str(len(self.type.amap.amaplist)))
        except:
            row.append('NA')
        row.append(str(self.type)[0:10])
        row.append(str(self.typecrawled))
        row.append(str(self.hopcount))
        row.append(str(self.defaultrouteip))
        try:
            row.append(str(self.sourceEntryObj.id))
        except:
            row.append('NONE')
        row.append(str(self.sourceEntryId.value))
        row.append(str(self.upstreamSlotport))
        row.append(str(self.parentport))
        row.append(str(self.parenthostname))
        row.append(str(self.removalflag))
        msg = nwConfig.ne_fmt.format(*row)
        return(msg)
    def dump_basic_singleline(self):
        ''' Returns the basic object properties of the NE.
        Does not dump things like macs or timestamp. Primarily
        used for creating Event() oneliners with basic object properties. 
        '''
        msgtext = ("NE ID: '" + self.id + "'" +
            ", NE Type: '" + self.typestring + "'" +
            ", NE Hostname: '" + self.hostname.value + "'" +
            "::: from source Entry ID: '" + self.sourceEntryId.value + "'")
        return msgtext
    def pickleMeElmo(self):
        ''' Pickles the network element to random filename.
        !!!!!!!! DOES NOT WORK !!!!!!!!!!!
        '''
        filename = 'ne_' + werd.randomNumberBlock() + '.pkl'
        with open(filename,'wb') as f:
            pickle.dump(self,f)
    def genxml(self):
        ''' Returns the NetworkElement serialized as XML
        '''
        x_ne = ET.Element(self.xmldesc,attrib={'id':self.id,'type':self.typestring})
        x_ne_hostname = ET.SubElement(x_ne,self.hostname.xmldesc)
        x_ne_hostname.text = self.hostname.value

        x_ne_parents = ET.SubElement(x_ne,self.parents.xmldesc)
        for parent in self.parents.parentlist:
            x_ne_parents_parent = ET.SubElement(x_ne_parents,
                                                parent.xmldesc,
                                                attrib={'id':parent.id,
                                                        'type':parent.typestring,
                                                        'hostname':parent.hostname,})
            x_ne_parents_parent_port = ET.SubElement(x_ne_parents_parent,
                                                    parent.port.xmldesc,
                                                    attrib={'local_portid':parent.port.portid,
                                                            'local_slotport':parent.port.slotport,})

        x_ne_children = ET.SubElement(x_ne,self.children.xmldesc)
        for child in self.children.childrenlist:
            x_ne_children_child = ET.SubElement(x_ne_children,
                                                child.xmldesc,
                                                attrib={'id':child.id,
                                                        'type':child.typestring,
                                                        'hostname':child.hostname,})
            x_ne_children_child_port = ET.SubElement(x_ne_children_child,
                                                    child.port.xmldesc,
                                                    attrib={'local_portid':child.port.portid,
                                                            'local_slotport':child.port.slotport,})
        
        x_ne_macs = ET.SubElement(x_ne,self.macs.xmldesc)
        for mac in self.macs.macslist:
            x_ne_macs_mac = ET.SubElement(x_ne_macs,mac.xmldesc)
            x_ne_macs_mac.text = mac.value

        x_ne_ips = ET.SubElement(x_ne,self.ips.xmldesc)
        for ip in self.ips.iplist:
            x_ne_ips_ip = ET.SubElement(x_ne_ips,ip.xmldesc)
            x_ne_ips_ip_address = ET.SubElement(x_ne_ips_ip,ip.address.xmldesc)
            x_ne_ips_ip_address.text = ip.address.value
            x_ne_ips_ip_mask = ET.SubElement(x_ne_ips_ip,ip.mask.xmldesc)
            x_ne_ips_ip_mask.text = ip.mask.value
        # now append the XML from the type object
        if self.type != None:
            # the type.genxml() func returns ET xml object (not string)
            logging.debug("NE.GENXML(): Attempting to generate Type() XML...")
            try:
                x_ne.append(self.type.genxml())
            except Exception as eel:
                logging.debug("NE.GENXML(): Exception generating Type() XML: " + str(eel))
        
        return(x_ne)



class CrawlResults(object):
    ''' Used to store the results of a crawl. Eventually will have a
    dump to XML method that creates the output XML.
    '''
    def __init__(self,sourceTargetId):
        ''' Not sure if I want to split the crawls up into crawls per target
        or not yet. For now I'll put source targets in a list.'''
        self.idOfSourceTarget = []
        self.idOfSourceTarget.append(sourceTargetId)
        self.creationTimestamp = datetime.datetime.now()
        # holder for list of object NE's found in crawl
        self.loo_ne = []
        self.loo_members = []
        self.loo_scratchpad = []
        self.realrootmac = ''
        self.textmap = [] # holds lines from the map view so it can be logged
    def genxml(self):
        x_root = ET.Element('root')
        for ne in self.loo_ne:
            try:
                logging.debug("CrawlResults():\t\t Attempting .genxml() on NE with ID: " + ne.id)
                x_root.append(ne.genxml())
            except Exception as e:
                logging.debug("CrawlResults():\t\t Exception serializing xml for NE: " + str(e))
        # now add the event log to end of XML:
        x_root_eventlog = ET.SubElement(x_root,'eventlog')
        for index,message in enumerate(werd.messagelog):
            orderid = str(index+1)
            x_root_eventlog_event = ET.SubElement(x_root_eventlog,'event',attrib={'id':orderid})
            x_root_eventlog_event.text = message.dump()
        #xmlstring = ET.dump(x_root)
        return(ET.tostring(x_root))


class ExpectGenerator(object):
    ''' used to build an expect script based on inputs
    needs the following to build one:
    --ip address
    --port
    --username/password
    --timeout
    --list of commands to run
    '''
    def __init__(self):
        self.typestring = typestring