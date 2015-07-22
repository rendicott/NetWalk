''' This module describes the class object structure for the
ALU Omniswitch 6450 SCS (Small Cell Switch)
'''

import datetime
import xml.etree.ElementTree as ET
import pickle
import re
import logging
import nwConfig

# internal imports
from nwClasses import werd # super important that this is first

''' list of dictionaries that contain the commands to run on the router/switch
to pull all of the data desired. Split up into a type identifier followed by a list
of commands.
'''
discoveryCommands = [
    {   'type':             'scs',
        'variant':          'p10',
        'commands':     [   'show lanpower 1',
                            'show interfaces',
                            'show interfaces port',
                            'show interfaces status',
                            'show hardware info',
                            'show microcode',
                            'show temperature',
                            'show system',
                            'show running directory',
                            'show ni',
                            'show module',
                            'show module status',
                            'show module long',
                            'show fan',
                            'show cmm',
                            'show chassis',
                            'show ip router database',
                            'show ip service',
                            'show ip interface',
                            'show ip http',
                            'show ip protocols',
                            'show ip route-pref',
                            'show dhcp-server statistics',
                            'show dhcp-server leases count',
                            'show dhcp-server leases',
                            'show lldp local-system',
                            'show lldp remote-system',
                            'show health',
                            'show arp',
                            'show arp summary',
                            'show amap',
                            'show spantree',
                            'show configuration snapshot',
                            'show vlan',
                            'show mac-address-table',
                            'show mac-address-table aging-time',
                            'show udld configuration',
                            # 'traceroute 8.8.8.8',
                        ],
        },
    {   'type':             'scr',
        'variant':          'sarh',
        'commands':     [   'show system information',
                            'show router arp',
                            'show service fdb-mac',
                            'show time',
                            'show version',
                        ],
        }

    ]

class BaseClass():
    ''' Basic class to hold basic properties
    for the purposes of inheritance.
    '''
    requiresId = False
    value = ''
    xmldesc = 'GENERIC'
    xmlparent = None
    def allprops(self):
        ''' Returns all properties of self
        '''
        return([x for x in dir(self) if not x.startswith('__') and not callable(getattr(self,x))])


class TypeContainer_ALU_SCS():
    ''' Class to define the properties, classes, 
    and methods specific to the ALU SCS (P10 and U24)
    '''
    typestring = 'scs'
    requiresId = False
    xmldesc = 'type'

    # all these classes will inherit BaseClass for things like
    #  the 'value' property. 
    class PortsContainer(BaseClass):
        xmldesc = 'ports'
        xmlparent = 'type'
        class Port(BaseClass):
            xmldesc = 'port'
            xmlparent = 'ports'
            requiresId = True
            class Slotport(BaseClass): 
                xmldesc = 'slotport'
            class OperStatus_Port(BaseClass): 
                xmldesc = 'operationalstatus'
            class Sfp(BaseClass): 
                xmldesc = 'sfp'
            class Mac_Port(BaseClass):
                xmldesc = 'mac'
            class Autonegotiate(BaseClass): 
                xmldesc = 'autonegotiate'
            class PortSpeed_Detected(BaseClass):
                xmldesc = 'detected'
                xmlparent = 'port'
                class Speed(BaseClass):
                    xmldesc = 'speed'
                    xmlparent = 'detected'
                class Duplex(BaseClass):
                    xmldesc = 'duplex'
                    xmlparent = 'detected'
                class Hybridtype(BaseClass):
                    xmldesc = 'hybridtype'
                    xmlparent = 'detected'
                def __init__(self):
                    self.speed = self.Speed()
                    self.duplex = self.Duplex()
                    self.hybridtype = self.Hybridtype()
            class PortSpeed_Configured(BaseClass): 
                xmldesc = 'configured'
                xmlparent = 'port'
                class Speed(BaseClass):
                    xmldesc = 'speed'
                    xmlparent = 'configured'
                class Duplex(BaseClass):
                    xmldesc = 'duplex'
                    xmlparent = 'configured'
                class Hybridtype(BaseClass):
                    xmldesc = 'hybridtype'
                    xmlparent = 'configured'
                def __init__(self):
                    self.speed = self.Speed()
                    self.duplex = self.Duplex()
                    self.hybridtype = self.Hybridtype()
            class AssociatedMacs():
                xmldesc = 'associatedmacs'
                xmlparent = 'port'
                class MacContainer(BaseClass):
                    xmldesc = 'mac'
                    xmlparent = 'associatedmacs'
                    requiresId = True
                    class AssocVlan(BaseClass):
                        xmldesc = 'vlan'
                        xmlparent = 'mac'
                    class MacAddy(BaseClass):
                        xmldesc = 'mac'
                        xmlparent = 'mac'
                        value = ''
                    class Type(BaseClass):
                        xmldesc = 'type'
                        xmlparent = 'mac'
                    def __init__(self,id):
                        self.id = id
                        self.vlan = self.AssocVlan()
                        self.mac = self.MacAddy()
                        self.typestring = self.Type()
                def __init__(self):
                    # list to hold MacContainers() within AssociatedMacs()
                    self.maclist = []
            def __init__(self,id):
                self.id = id
                self.slotport = self.Slotport()
                self.operstatus = self.OperStatus_Port()
                self.sfp = self.Sfp()
                self.mac = self.Mac_Port()
                self.autonegotiate = self.Autonegotiate()
                self.detected = self.PortSpeed_Detected()
                self.configured = self.PortSpeed_Configured()
                self.associatedmacs = self.AssociatedMacs()
                # if already mac-address-table crawled, set macattack true
                self.nox_macattack = False
        def __init__(self):
            self.portlist = []
    class VlanContainer(BaseClass):
        xmldesc = 'vlans'
        xmlparent = 'type'
        class Vlan(BaseClass):
            xmldesc = 'vlan'
            xmlparent = 'vlans'
            requiresId = True                
            class Name(BaseClass):
                xmldesc = 'name'
                xmlparent = 'vlan'
            class Ident(BaseClass):
                xmldesc = 'ident'
                xmlparent = 'vlan'
            class Description(BaseClass):
                xmldesc = 'description'
                xmlparent = 'vlan'
            class Type(BaseClass):
                xmldesc = 'type'
                xmlparent = 'vlan'
            class AdminStatus(BaseClass):
                xmldesc = 'adminstatus'
                xmlparent = 'vlan'
            class OperStatus(BaseClass):
                xmldesc = 'operstatus'
                xmlparent = 'vlan'
            class IpStatus(BaseClass):
                xmldesc = 'ipstatus'
                xmlparent = 'vlan'
            def __init__(self,id):
                self.id = id
                self.name = self.Name()
                self.ident = self.Ident()
                self.description = self.Description()
                self.typestring = self.Type()
                self.adminstatus = self.AdminStatus()
                self.operstatus = self.OperStatus()
                self.ipstatus = self.IpStatus()
        def __init__(self):
            self.vlanlist = []
    class ModuleContainer(BaseClass):
        xmldesc = 'modules'
        xmlparent = 'type'
        class Module(BaseClass):
            xmldesc = 'module'
            xmlparent = 'modules'
            class Slot(BaseClass):
                xmldesc = 'slot'
                xmlparent = 'modules'
            class Status(BaseClass):
                xmldesc = 'status'
                xmlparent = 'modules'
            class Description(BaseClass):
                xmldesc = 'description'
                xmlparent = 'modules'
            class PartNumber_Module(BaseClass):
                xmldesc = 'partnumber'
                xmlparent = 'modules'
            class Mac(BaseClass):
                xmldesc = 'mac'
                xmlparent = 'modules'
            class GbicContainer(BaseClass):
                xmldesc = 'gbics'
                xmlparent = 'modules'
                class Gbic(BaseClass):
                    xmldesc = 'gbic'
                    xmlparent = 'gbics'
                    requiresId = True
                    # we want gbics to have internal UID 
                    #  but also want to retain the ALU gbic number
                    class GbicIdent(BaseClass):
                        xmldesc = 'ident'
                        xmlparent = 'gbic'
                    class ModelName(BaseClass):
                        xmldesc = 'modelname'
                        xmlparent = 'gbic'
                    class PartNumber_Gbic(BaseClass):
                        xmldesc = 'partnumber'
                        xmlparent = 'gbic'
                    class Serial(BaseClass):
                        xmldesc = 'serial'
                        xmlparent = 'gbic'
                    class AdminStatus_Gbic(BaseClass):
                        xmldesc = 'adminstatus'
                        xmlparent = 'gbic'
                    class OperStatus_Gbic(BaseClass):
                        xmldesc = 'operstatus'
                        xmlparent = 'gbic'
                    class LaserWavelength(BaseClass):
                        xmldesc = 'laserwavelength'
                        xmlparent = 'gbic'
                    def __init__(self,id):
                        self.id = id
                        self.ident = self.GbicIdent()
                        self.modelname = self.ModelName()
                        self.partnumber = self.PartNumber_Gbic()
                        self.serial = self.Serial()
                        self.adminstatus = self.AdminStatus_Gbic()
                        self.operstatus = self.OperStatus_Gbic()
                        self.laserwavelength = self.LaserWavelength()
                def __init__(self):
                    self.gbiclist = []
            def __init__(self,id):
                self.id = id
                self.slot = self.Slot()
                self.status = self.Status()
                self.description = self.Description()
                self.partnumber = self.PartNumber_Module()
                self.mac = self.Mac()
                self.gbics = self.GbicContainer()
        def __init__(self):
            self.modulelist = []
    class ChassisContainer(BaseClass):
        xmldesc = 'chassis'
        xmlparent = 'type'
        class Model(BaseClass):
            xmldesc = 'model'
            xmlparent = 'chassis'
        class Description(BaseClass):
            xmldesc = 'description'
            xmlparent = 'chassis'
        class AdminStatus_Chassis(BaseClass):
            xmldesc = 'adminstatus'
            xmlparent = 'chassis'
        class OperStatus_Chassis(BaseClass):
            xmldesc = 'operstatus'
            xmlparent = 'chassis'
        class Mac_Chassis(BaseClass):
            xmldesc = 'mac'
            xmlparent = 'chassis'
        class Serial(BaseClass):
            xmldesc = 'serial'
            xmlparent = 'chassis'
        def __init__(self):
            self.model = self.Model()
            self.description = self.Description()
            self.adminstatus = self.AdminStatus_Chassis()
            self.operstatus = self.OperStatus_Chassis()
            self.mac = self.Mac_Chassis()
            self.serial = self.Serial()
    class RoutesContainer(BaseClass):
        xmldesc = 'routes'
        xmlparent = 'type'
        class Route(BaseClass):
            xmldesc = 'route'
            xmlparent = 'routes'
            requiresId = True
            class Destination(BaseClass):
                xmldesc = 'destination'
                xmlparent = 'route'
            class Gateway(BaseClass):
                xmldesc = 'gateway'
                xmlparent = 'route'
            class Interface(BaseClass):
                xmldesc = 'interface'
                xmlparent = 'route'
            class Metric(BaseClass):
                xmldesc = 'metric'
                xmlparent = 'route'
            class Type_Route(BaseClass):
                xmldesc = 'type'
                xmlparent = 'route'
            def __init__(self,id):
                self.id = id
                self.destination = self.Destination()
                self.gateway = self.Gateway()
                self.interface = self.Interface()
                self.metric = self.Metric()
                self.typestring = self.Type_Route()
        def __init__(self):
            self.routelist = []
    class InterfacesContainer(BaseClass):
        xmldesc = 'interfaces'
        xmlparent = 'type'
        class Interface(BaseClass):
            xmldesc = 'interface'
            xmlparent = 'interfaces'
            requiredId = True
            class Name_Int(BaseClass):
                xmldesc = 'name'
                xmlparent = 'interface'
            class Address(BaseClass):
                xmldesc = 'address'
                xmlparent = 'interface'
            class SubnetMask(BaseClass):
                xmldesc = 'subnetmask'
                xmlparent = 'interface'
            class Status_Int(BaseClass):
                xmldesc = 'status'
                xmlparent = 'interface'
            class Device(BaseClass):
                xmldesc = 'device'
                xmlparent = 'interface'
            def __init__(self,id):
                self.id = id
                self.name = self.Name_Int()
                self.address = self.Address()
                self.subnetmask = self.SubnetMask()
                self.status = self.Status_Int()
                self.device = self.Device()
        def __init__(self):
            self.interfacelist = []
    class AmapContainer(BaseClass):
        xmldesc = 'amap'
        xmlparent = 'type'
        class AmapStatus(BaseClass):
            xmldesc = 'amapstatus'
            xmlparent = 'amap'
            def __init__(self):
                self.value = ''
        class RemoteHost(BaseClass):
            xmldesc = 'remotehost'
            xmlparent = 'amap'
            requiredId = True
            class LSlotPort(BaseClass):
                xmldesc = 'localslotport'
                xmlparent = 'remotehost'
            class LVlan(BaseClass):
                xmldesc = 'localvlan'
                xmlparent = 'remotehost'
            class RHostname(BaseClass):
                xmldesc = 'remotehostname'
                xmlparent = 'remotehost'
            class RDevice(BaseClass):
                xmldesc = 'remotedevice'
                xmlparent = 'remotehost'
            class RMac(BaseClass):
                xmldesc = 'remotemac'
                xmlparent = 'remotehost'
            class RSlotPort(BaseClass):
                xmldesc = 'remoteslotport'
                xmlparent = 'remotehost'
            class RVlan(BaseClass):
                xmldesc = 'remotevlan'
                xmlparent = 'remotehost'
            class RIpList(BaseClass):
                xmldesc = 'remoteips'
                xmlparent = 'remotehost'
                class Rip(BaseClass):
                    xmldesc = 'remoteip'
                    xmlparent = 'remoteips'
                def __init__(self):
                    self.riplist = []
            # define an __eq__ and __hash__ method so we can remove duplicates with set()
            def __eq__(self, other):
                return self.remotemac==other.remotemac and self.remotehostname==other.remotehostname
            def __hash__(self):
                return hash(('remotemac', self.remotemac,
                    'remotehostname', self.remotehostname))
            def __init__(self,id):
                self.id = id
                self.localslotport = self.LSlotPort()
                self.localvlan = self.LVlan()
                self.remotehostname = self.RHostname()
                self.remotedevice = self.RDevice()
                self.remotemac = self.RMac()
                self.remoteslotport = self.RSlotPort()
                self.remotevlan = self.RVlan()
                self.remoteips = self.RIpList()
                # this one is for internal and links the remotehost to an NE id
                self.nox_linkedNEid = 0
                # holder to mark where we learned about this remotehost
                self.nox_learnedfromNEid = 0
                self.nox_learnedfromEntryid = 0
                # also put placeholder for attaching learnedfromEntryObj
                #  so we can derive the first hop of the expect script later
                self.nox_learnedfromEntryObj = None
                self.nox_learnedfromAuthObj = None
            def dump(self,additionalindent=None):
                if additionalindent == None:
                    additionalindent = ''
                msgtext = '\n\r'
                msgtext =  (additionalindent +  "TYPE: AmapContainer().RemoteHost(): \n\r")
                msgtext += (additionalindent +  "\t" + "ID: \t\t\t\t" + self.id + '\n\r')
                msgtext += (additionalindent +  "\t" + "LOCALSLOTPORT: \t\t\t" + str(self.localslotport.value) + '\n\r')
                msgtext += (additionalindent +  "\t" + "LOCALVLAN: \t\t\t" + str(self.localvlan.value) + '\n\r')
                msgtext += (additionalindent +  "\t" + "REMOTEHOSTNAME: \t\t" + str(self.remotehostname.value) + '\n\r')
                msgtext += (additionalindent +  "\t" + "REMOTEDEVICE: \t\t\t" + str(self.remotedevice.value) + '\n\r')
                msgtext += (additionalindent +  "\t" + "REMOTEMAC: \t\t\t" + str(self.remotemac.value) + '\n\r')
                msgtext += (additionalindent +  "\t" + "REMOTESLOTPORT: \t\t" + str(self.remoteslotport.value) + '\n\r')
                msgtext += (additionalindent +  "\t" + "REMOTEVLAN: \t\t\t" + str(self.remotevlan.value) + '\n\r')
                msgtext += (additionalindent +  "\t" + "REMOTEIPS: " + '\n\r')
                for ip in self.remoteips.riplist:
                    msgtext += (additionalindent +  '\t\t\t\tRIP: ' + ip.value + '\n\r')
                msgtext += (additionalindent +  "\t" + "NOX_LINKEDNEID: \t\t" + str(self.nox_linkedNEid) + '\n\r')
                msgtext += (additionalindent +  "\t" + "NOX_LEARNEDFROMNEID: \t\t" + str(self.nox_learnedfromNEid) + '\n\r')
                msgtext += (additionalindent +  "\t" + "NOX_LEARNEDFROMENTRYID: \t" + str(self.nox_learnedfromEntryid) + '\n\r')
                try:
                    msgtext += (additionalindent +  "\t" + "NOX_LEARNEDFROMENTRYOBJ: \t" + str(self.nox_learnedfromEntryObj) + '\n\r')
                    msgtext += (additionalindent +  "\t" + "NOX_LEARNEDFROMAUTHOBJ: \t" + str(self.nox_learnedfromAuthObj) + '\n\r')
                except:
                    msgtext += (additionalindent +  "\t" + "NOX_LEARNEDFROMENTRYOBJ: \t" + "NONE" + '\n\r')
                    msgtext += (additionalindent +  "\t" + "NOX_LEARNEDFROMAUTHOBJ: \t" + "NONE" + '\n\r')
                return msgtext
            def dump_rowformat(self):
                # msg = fmt.format(*hdr) + '\r\n'
                row = []
                row.append(self.id)
                row.append(str(self.localslotport.value))
                row.append(str(self.remotehostname.value))
                row.append(str(self.remotedevice.value))
                row.append(str(self.remotemac.value))
                row.append(str(self.remoteslotport.value))
                try:
                    row.append(self.remoteips.riplist[0].value)
                except:
                    row.append('NONE')
                row.append(str(self.nox_linkedNEid))
                row.append(str(self.nox_learnedfromNEid))
                row.append(str(self.nox_learnedfromEntryid))
                try:
                    row.append(str(self.nox_learnedfromEntryObj)[:24])
                    row.append(str(self.nox_learnedfromAuthObj)[:24])
                except:
                    row.append('NONE')
                    row.append('NONE')
                row.append(str(self.localvlan.value))
                row.append(str(self.remotevlan.value))
                return(nwConfig.remotehost_fmt.format(*row))
        def __init__(self):
            self.amaplist = []
            self.amapstatus = self.AmapStatus()
    class ArpTable(BaseClass):
        xmldesc = 'arptable'
        xmlparent = 'type'
        class Arp(BaseClass):
            xmldesc = 'arp'
            xmlparent = 'arptable'
            class Ip(BaseClass):
                xmldesc = 'ip'
                xmlparent = 'arp'
            class Mac(BaseClass):
                xmldesc = 'mac'
                xmlparent = 'arp'
            class Type(BaseClass):
                xmldesc = 'type'
                xmlparent = 'arp'
            class SlotPort(BaseClass):
                xmldesc = 'slotport'
                xmlparent = 'arp'
            class Interface(BaseClass):
                xmldesc = 'interface'
                xmlparent = 'arp'
            def __init__(self,id):
                self.id = id
                self.ip = self.Ip()
                self.mac = self.Mac()
                self.typestring = self.Type()
                self.slotport = self.SlotPort()
                self.interface = self.Interface()
        def __init__(self):
            self.arplist = []
    class DhcpContainer(BaseClass):
        xmldesc = 'dhcp'
        xmlparent = 'type'
        class ServerName(BaseClass):
            xmldesc = 'servername'
            xmlparent = 'dhcp'
        class ServerStatus(BaseClass):
            xmldesc = 'serverstatus'
            xmlparent = 'dhcp'
        class NumSubnetsManaged(BaseClass):
            xmldesc = 'numsubnetsmanaged'
            xmlparent = 'dhcp'
        class NumLeases(BaseClass):
            xmldesc = 'numleases'
            xmlparent = 'dhcp'
        class Lease(BaseClass):
            xmldesc = 'lease'
            xmlparent = 'dhcp'
            requiresId = True            
            class IpAddr(BaseClass):
                xmldesc = 'ipaddr'
                xmlparent = 'lease'
            class Mac_Lease(BaseClass):
                xmldesc = 'mac'
                xmlparent = 'lease'
            class TimeGranted(BaseClass):
                xmldesc = 'timegranted'
                xmlparent = 'lease'
            class TimeExpires(BaseClass):
                xmldesc = 'timeexpires'
                xmlparent = 'lease'
            class Type_Lease(BaseClass):
                xmldesc = 'type'
                xmlparent = 'lease'
            def __init__(self,id):
                self.id = id
                self.ipaddr = self.IpAddr()
                self.mac = self.Mac_Lease()
                self.timegranted = self.TimeGranted()
                self.timeexpires = self.TimeExpires()
                self.typestring = self.Type_Lease()
        def __init__(self):
            self.servername = self.ServerName()
            self.serverstatus = self.ServerStatus()
            self.numsubnetsmanaged = self.NumSubnetsManaged()
            self.numleases = self.NumLeases()
            self.leaselist = []
    class ConfigurationContainer(BaseClass):
        xmldesc = 'configuration'
        xmlparent = 'type'
        class Text(BaseClass):
            xmldesc = 'text'
            xmlparent = 'configuration'
        def __init__(self):
            self.text = self.Text()
    def __init__(self):
        self.ports = self.PortsContainer()
        self.vlans = self.VlanContainer()
        self.modules = self.ModuleContainer()
        self.chassis = self.ChassisContainer()
        self.routes = self.RoutesContainer()
        self.interfaces = self.InterfacesContainer()
        self.dhcp = self.DhcpContainer()
        self.configuration = self.ConfigurationContainer()
        self.arptable = self.ArpTable()
        self.amap = self.AmapContainer()
        # prepend non-xml related props with nox
        self.nox_discoverycommandlist = self.genDiscoveryCommandList()
        self.nox_expectbody = self.genExpectBody()
        # holder for the filename of the discovery expect script
        self.nox_discoveryexpectscript = ''
        self.nox_discoveryexpectcommand = ''
        self.nox_discoveryoutput = []
    def genDiscoveryCommandList(self):
        # build the discovery command list from the discoveryCommands
        #  list of dictionaries imported at the top of this module
        templist = []
        for chunk in discoveryCommands:
            if chunk.get('type') == self.typestring:
                for command in chunk.get('commands'):
                    templist.append(command)
        return templist
    def genExpectBody(self):
        ''' Takes the discovery command list and builds the
        body of an expect script. 
        '''
        '''
        expect {
            ">" {send "show system\r" 
                expect ">" { send "exit\r" }
                } 
            "#" {send "show system information\r" 
                 expect ")" { send "g" 
                    expect "#" {send "logout\r"}
                    }
                }
            timeout {send $CTRL_C; puts "Timed Out!"; exit 1}
            }
        '''
        lister = self.nox_discoverycommandlist
        def linecreator(command):
            msg = ''
            msg += ('expect ">" {send "' + command + '\\r"' + '\r\n')
            # add an additional return char to stabilize scripts
            msg += 'expect ">" {send "\\r" \r\n'
            return(msg)
        body = ''
        endchar = '}'
        for i,o in enumerate(lister):
            body += linecreator(o)
            if i+1 == len(lister):
                # add the closing curly braces, two for every command
                body += (endchar * (len(lister)*2))
        return body
    def dumpDiscoveryOutputToFile(self):
        ''' Takes the content in self.nox_discoveryoutput and
        dumps to filename modeled after expect script name. 
        '''
        filename = self.nox_discoveryexpectscript + "-output.log"
        with open(filename,'wb') as f:
            for line in self.nox_discoveryoutput:
                f.write(line)

    def genxml(self):
        ''' Dumps all data to XML
        '''
        props = [x for x in dir(self) if not x.startswith('__') and not callable(getattr(self,x))]
        x_type = ET.Element(self.xmldesc,attrib={'type':self.typestring})
        x_ports = ET.SubElement(x_type, self.ports.xmldesc)
        x_vlans = ET.SubElement(x_type, self.vlans.xmldesc)
        x_mods = ET.SubElement(x_type, self.modules.xmldesc)
        x_chassis = ET.SubElement(x_type, self.chassis.xmldesc)
        x_routes = ET.SubElement(x_type, self.routes.xmldesc)
        x_interfaces = ET.SubElement(x_type, self.interfaces.xmldesc)
        x_amap = ET.SubElement(x_type,self.amap.xmldesc)
        x_arptable = ET.SubElement(x_type,self.arptable.xmldesc)
        x_dhcp = ET.SubElement(x_type,self.dhcp.xmldesc)
        x_configuration = ET.SubElement(x_type,self.configuration.xmldesc)
        for port in self.ports.portlist:
            x_port = ET.SubElement(x_ports,port.xmldesc,attrib={'id':port.id})
            
            x_slotport = ET.SubElement(x_port,port.slotport.xmldesc)
            x_slotport.text = port.slotport.value
            
            x_operstatus = ET.SubElement(x_port,port.operstatus.xmldesc)
            x_operstatus.text = port.operstatus.value
            
            x_sfp = ET.SubElement(x_port,port.sfp.xmldesc)
            x_sfp.text = port.sfp.value

            x_mac = ET.SubElement(x_port,port.mac.xmldesc)
            x_mac.text = port.mac.value
            
            x_autonegotiate = ET.SubElement(x_port,port.autonegotiate.xmldesc)
            x_autonegotiate.text = port.autonegotiate.value

            # Build the port speed Detected section
            x_detected = ET.SubElement(x_port,port.detected.xmldesc)
            
            x_detected_speed = ET.SubElement(x_detected,port.detected.speed.xmldesc)
            x_detected_speed.text = port.detected.speed.value

            x_detected_duplex = ET.SubElement(x_detected,port.detected.duplex.xmldesc)
            x_detected_duplex.text = port.detected.duplex.value
            
            x_detected_hybridtype = ET.SubElement(x_detected,port.detected.hybridtype.xmldesc)
            x_detected_hybridtype.text = port.detected.hybridtype.value

            # Build the port speed Configured section
            x_configured = ET.SubElement(x_port,port.configured.xmldesc)
            
            x_configured_speed = ET.SubElement(x_configured,port.configured.speed.xmldesc)
            x_configured_speed.text = port.configured.speed.value

            x_configured_duplex = ET.SubElement(x_configured,port.configured.duplex.xmldesc)
            x_configured_duplex.text = port.configured.duplex.value

            x_configured_hybridtype = ET.SubElement(x_configured,port.configured.hybridtype.xmldesc)
            x_configured_hybridtype.text = port.configured.hybridtype.value

            x_associatedmacs = ET.SubElement(x_port,port.associatedmacs.xmldesc)
            for mac in port.associatedmacs.maclist:
                x_associatedmacs_mac = ET.SubElement(x_associatedmacs,mac.xmldesc)
                
                x_associatedmacs_mac_vlan = ET.SubElement(x_associatedmacs_mac,mac.vlan.xmldesc)
                x_associatedmacs_mac_vlan.text = mac.vlan.value

                x_associatedmacs_mac_mac = ET.SubElement(x_associatedmacs_mac,mac.mac.xmldesc)
                x_associatedmacs_mac_mac.text = mac.mac.value

                x_associatedmacs_mac_type = ET.SubElement(x_associatedmacs_mac,mac.typestring.xmldesc)
                x_associatedmacs_mac_type.text = mac.typestring.value

        for vlan in self.vlans.vlanlist:
            x_vlans_vlan = ET.SubElement(x_vlans,vlan.xmldesc,attrib={'id':vlan.id})

            x_vlans_vlan_description = ET.SubElement(x_vlans_vlan,vlan.description.xmldesc)
            x_vlans_vlan_description.text = vlan.description.value

            x_vlans_vlan_name = ET.SubElement(x_vlans_vlan,vlan.name.xmldesc)
            x_vlans_vlan_name.text = vlan.name.value

            x_vlans_vlan_type = ET.SubElement(x_vlans_vlan,vlan.typestring.xmldesc)
            x_vlans_vlan_type.text = vlan.typestring.value

            x_vlans_vlan_ident = ET.SubElement(x_vlans_vlan,vlan.ident.xmldesc)
            x_vlans_vlan_ident.text = vlan.ident.value

            x_vlans_vlan_adminstatus = ET.SubElement(x_vlans_vlan,vlan.adminstatus.xmldesc)
            x_vlans_vlan_adminstatus.text = vlan.adminstatus.value

            x_vlans_vlan_operstatus = ET.SubElement(x_vlans_vlan,vlan.operstatus.xmldesc)
            x_vlans_vlan_operstatus.text = vlan.operstatus.value

            x_vlans_vlan_ipstatus = ET.SubElement(x_vlans_vlan,vlan.ipstatus.xmldesc)
            x_vlans_vlan_ipstatus.text = vlan.ipstatus.value
        for mod in self.modules.modulelist:
            x_mods_mod = ET.SubElement(x_mods,mod.xmldesc,attrib={'id':mod.id})

            x_mods_mod_slot = ET.SubElement(x_mods_mod,mod.slot.xmldesc)
            x_mods_mod_slot.text = mod.slot.value

            x_mods_mod_status = ET.SubElement(x_mods_mod,mod.status.xmldesc)
            x_mods_mod_status.text = mod.status.value

            x_mods_mod_description = ET.SubElement(x_mods_mod,mod.description.xmldesc)
            x_mods_mod_description.text = mod.description.value

            x_mods_mod_partnumber = ET.SubElement(x_mods_mod,mod.partnumber.xmldesc)
            x_mods_mod_partnumber.text = mod.partnumber.value

            x_mods_mod_mac = ET.SubElement(x_mods_mod,mod.mac.xmldesc)
            x_mods_mod_mac.text = mod.mac.value

            # create the gbic container which contains the list of gbics
            x_mods_mod_gbics = ET.SubElement(x_mods_mod,mod.gbics.xmldesc)
            # now loop through list of gbics and assign to gbic container parent
            for gbic in mod.gbics.gbiclist:
                x_gbic = ET.SubElement(x_mods_mod_gbics,gbic.xmldesc,attrib={'id':gbic.id})

                x_gbic_ident = ET.SubElement(x_gbic,gbic.ident.xmldesc)
                x_gbic_ident.text = gbic.ident.value

                x_gbic_modelname = ET.SubElement(x_gbic,gbic.modelname.xmldesc)
                x_gbic_modelname.text = gbic.modelname.value

                x_gbic_partnumber = ET.SubElement(x_gbic,gbic.partnumber.xmldesc)
                x_gbic_partnumber.text = gbic.partnumber.value

                x_gbic_serial = ET.SubElement(x_gbic,gbic.serial.xmldesc)
                x_gbic_serial.text = gbic.serial.value

                x_gbic_adminstatus = ET.SubElement(x_gbic,gbic.adminstatus.xmldesc)
                x_gbic_adminstatus.text = gbic.adminstatus.value

                x_gbic_operstatus = ET.SubElement(x_gbic,gbic.operstatus.xmldesc)
                x_gbic_operstatus.text = gbic.operstatus.value

                x_gbic_laserwavelength = ET.SubElement(x_gbic,gbic.laserwavelength.xmldesc)
                x_gbic_laserwavelength.text = gbic.laserwavelength.value
        # now generate the chassis xml
        x_chassis_model = ET.SubElement(x_chassis,self.chassis.model.xmldesc)
        x_chassis_model.text = self.chassis.model.value

        x_chassis_description = ET.SubElement(x_chassis,self.chassis.description.xmldesc)
        x_chassis_description.text = self.chassis.description.value

        x_chassis_adminstatus = ET.SubElement(x_chassis,self.chassis.adminstatus.xmldesc)
        x_chassis_adminstatus.text = self.chassis.adminstatus.value
        
        x_chassis_operstatus = ET.SubElement(x_chassis,self.chassis.operstatus.xmldesc)
        x_chassis_operstatus.text = self.chassis.operstatus.value

        x_chassis_mac = ET.SubElement(x_chassis,self.chassis.mac.xmldesc)
        x_chassis_mac.text = self.chassis.mac.value

        x_chassis_serial = ET.SubElement(x_chassis,self.chassis.serial.xmldesc)
        x_chassis_serial.text = self.chassis.serial.value

        # now do routes with xml parent of x_routes
        for route in self.routes.routelist:
            x_routes_route = ET.SubElement(x_routes,route.xmldesc,attrib={'id':route.id})
            
            x_routes_route_destination = ET.SubElement(x_routes_route,route.destination.xmldesc)
            x_routes_route_destination.text = route.destination.value

            x_routes_route_gateway = ET.SubElement(x_routes_route,route.gateway.xmldesc)
            x_routes_route_gateway.text = route.gateway.value

            x_routes_route_interface = ET.SubElement(x_routes_route,route.interface.xmldesc)
            x_routes_route_interface.text = route.interface.value

            x_routes_route_metric = ET.SubElement(x_routes_route,route.metric.xmldesc)
            x_routes_route_metric.text = route.metric.value

            x_routes_route_type = ET.SubElement(x_routes_route,route.typestring.xmldesc)
            x_routes_route_type.text = route.typestring.value

        # now do interfaces with xml parent of x_interfaces
        for interface in self.interfaces.interfacelist:
            x_interfaces_interface = ET.SubElement(x_interfaces,interface.xmldesc,attrib={'id':interface.id})

            x_interfaces_interface_name = ET.SubElement(
                                            x_interfaces_interface,interface.name.xmldesc)
            x_interfaces_interface_name.text = interface.name.value

            x_interfaces_interface_address = ET.SubElement(
                                            x_interfaces_interface,interface.address.xmldesc)
            x_interfaces_interface_address.text = interface.address.value

            x_interfaces_interface_subnetmask = ET.SubElement(
                                            x_interfaces_interface,interface.subnetmask.xmldesc)
            x_interfaces_interface_subnetmask.text = interface.subnetmask.value

            x_interfaces_interface_status = ET.SubElement(
                                            x_interfaces_interface,interface.status.xmldesc)
            x_interfaces_interface_status.text = interface.status.value

            x_interfaces_interface_device = ET.SubElement(
                                            x_interfaces_interface,interface.device.xmldesc)
            x_interfaces_interface_device.text = interface.device.value
        for arp in self.arptable.arplist:
            x_arptable_arp = ET.SubElement(x_arptable,arp.xmldesc,attrib={'id':arp.id})

            x_arptable_arp_ip = ET.SubElement(x_arptable_arp,arp.ip.xmldesc)
            x_arptable_arp_ip.text = arp.ip.value

            x_arptable_arp_mac = ET.SubElement(x_arptable_arp,arp.mac.xmldesc)
            x_arptable_arp_mac.text = arp.mac.value

            x_arptable_arp_type = ET.SubElement(x_arptable_arp,arp.typestring.xmldesc)
            x_arptable_arp_type.text = arp.typestring.value

            x_arptable_arp_slotport = ET.SubElement(x_arptable_arp,arp.slotport.xmldesc)
            x_arptable_arp_slotport.text = arp.slotport.value

            x_arptable_arp_interface = ET.SubElement(x_arptable_arp,arp.interface.xmldesc)
            x_arptable_arp_interface.text = arp.interface.value

        # now process the amap remote hosts
        x_amap_status = ET.SubElement(x_amap,self.amap.amapstatus.xmldesc)
        x_amap_status.text = self.amap.amapstatus.value
        for rhost in self.amap.amaplist:
            x_amap_rhost = ET.SubElement(x_amap,rhost.xmldesc,attrib={'id':rhost.id})

            x_amap_rhost_localslotport = ET.SubElement(x_amap_rhost,rhost.localslotport.xmldesc)
            x_amap_rhost_localslotport.text = rhost.localslotport.value

            x_amap_rhost_localvlan = ET.SubElement(x_amap_rhost,rhost.localvlan.xmldesc)
            x_amap_rhost_localvlan.text = rhost.localvlan.value

            x_amap_rhost_remotehostname = ET.SubElement(x_amap_rhost,rhost.remotehostname.xmldesc)
            x_amap_rhost_remotehostname.text = rhost.remotehostname.value

            x_amap_rhost_remotedevice = ET.SubElement(x_amap_rhost,rhost.remotedevice.xmldesc)
            x_amap_rhost_remotedevice.text = rhost.remotedevice.value

            x_amap_rhost_remotemac = ET.SubElement(x_amap_rhost,rhost.remotemac.xmldesc)
            x_amap_rhost_remotemac.text = rhost.remotemac.value

            x_amap_rhost_remoteslotport = ET.SubElement(x_amap_rhost,rhost.remoteslotport.xmldesc)
            x_amap_rhost_remoteslotport.text = rhost.remoteslotport.value

            x_amap_rhost_remotevlan = ET.SubElement(x_amap_rhost,rhost.remotevlan.xmldesc)
            x_amap_rhost_remotevlan.text = rhost.remotevlan.value

            # put the linked NE ID into the XML, even though it says "NOX"
            x_amap_rhost_nox_linkedNEid = ET.SubElement(x_amap_rhost,'linkedNEid')
            x_amap_rhost_nox_linkedNEid.text = str(rhost.nox_linkedNEid)

            x_amap_rhost_remoteips = ET.SubElement(x_amap_rhost,rhost.remoteips.xmldesc)
            # now loop through the remote host IPs
            for rip in rhost.remoteips.riplist:
                x_amap_rhost_remoteips_remoteip = ET.SubElement(x_amap_rhost_remoteips,rip.xmldesc)
                x_amap_rhost_remoteips_remoteip.text = rip.value

        # now process dhcp stuff
        x_dhcp_servername = ET.SubElement(x_dhcp,self.dhcp.servername.xmldesc)
        x_dhcp_servername.text = self.dhcp.servername.value

        x_dhcp_serverstatus = ET.SubElement(x_dhcp,self.dhcp.serverstatus.xmldesc)
        x_dhcp_serverstatus.text = self.dhcp.serverstatus.value

        x_dhcp_numsubnetsmanaged = ET.SubElement(x_dhcp,self.dhcp.numsubnetsmanaged.xmldesc)
        x_dhcp_numsubnetsmanaged.text = self.dhcp.numsubnetsmanaged.value

        x_dhcp_numleases = ET.SubElement(x_dhcp,self.dhcp.numleases.xmldesc)
        x_dhcp_numleases.text = self.dhcp.numleases.value
        for lease in self.dhcp.leaselist:
            x_dhcp_lease = ET.SubElement(x_dhcp,lease.xmldesc,attrib={'id':lease.id})

            x_dhcp_lease_ipaddr = ET.SubElement(x_dhcp_lease,lease.ipaddr.xmldesc)
            x_dhcp_lease_ipaddr.text = lease.ipaddr.value

            x_dhcp_lease_mac = ET.SubElement(x_dhcp_lease,lease.mac.xmldesc)
            x_dhcp_lease_mac.text = lease.mac.value

            x_dhcp_lease_timegranted = ET.SubElement(x_dhcp_lease,lease.timegranted.xmldesc)
            x_dhcp_lease_timegranted.text = lease.timegranted.value

            x_dhcp_lease_timeexpires = ET.SubElement(x_dhcp_lease,lease.timeexpires.xmldesc)
            x_dhcp_lease_timeexpires.text = lease.timeexpires.value

            x_dhcp_lease_type = ET.SubElement(x_dhcp_lease,lease.typestring.xmldesc)
            x_dhcp_lease_type.text = lease.typestring.value

        # and finally, the configuration text
        x_configuration_text = ET.SubElement(x_configuration,self.configuration.text.xmldesc)
        x_configuration_text.text = self.configuration.text.value

        # now return as an xml object instead of a string
        return(x_type)


class CommandOutput():
    ''' Class to define a command and hold data about its
    corresponding output. Example: this class will self generate
    the regex required to match the command in a list of output
    as well as pull/store just the relevant output for that command.
    '''
    def __init__(self,commandstring):
        self.commandstring = commandstring
        self.command_human = commandstring
        # append thing to end of string so only capture exactly the command specified
        self.commandstring += "(?! )"
        self.commandstring_regex = self.genregex_commandstring()
        # holder for the line that the match was found on
        self.linefound = []
        self.startline = None
        self.stopline = None
        self.sectionoutput = []
        ''' list of dictionaries describing the data I want 
          from this command. Used later during the parsing. '''
        # format: ['want':'slotport','identifier':idobject]
        self.thingsiwant = []
    def genregex_commandstring(self):
        ''' Generates a regex for the commandstring
        '''
        return(re.compile(self.commandstring))
    def check_match(self,linestring):
        ''' Takes a line of data as input and returns
        true if a match was found.
        '''
        match = re.search(self.commandstring_regex,linestring)
        if match:
            return True
        else:
            return False



class RegexIdentifier_SingleLine():
    ''' Takes the identifier string and value string
    needed to create the regex identifer and builds it
    and the methods needed to match and retrieve value.
    '''
    def __init__(self,identifierstring,valuestring):
        self.stringer = (
            "(?P<indicator>" + identifierstring + ")" +
            "(?P<value>" + valuestring + ")"
            )
        self.regex = re.compile(self.stringer)
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
            try:
                value = value.rstrip(',\n\r') 
            except Exception as e:
                msg = "RegexIdentifier_SingleLine(): "
                msg +=" give_group_value(): Exception "
                msg += "processing value: " + str(e)
                logging.debug("\t" + msg)
                value = ''
            return value
        else:
            return("NO_MATCH!")

class ElementIdentifier():
    ''' Takes a string as a source command
    and a string for regex detection then 
    creates a RegexIdentifier() object and 
    creates properties to hold both. 
    '''
    def __init__(self,sourcecommand,identifierstring,valuestring):
        self.sourcecommand = sourcecommand
        self.identifier = RegexIdentifier_SingleLine(identifierstring,valuestring)


class Parser_Port():
    ''' Class to handle port parsing. Holds 
    things like the regexes needed for 
    detecting sections of output data.
    ''' 
    class TableParser_ShowMacTable():
        ''' Takes a raw text table as input and 
        parses it specifically for the 
        'show mac-address-table' command on 
        the ALU 6450

        Holds list of Element() with properties
            that line up with the column headers.
        '''
        class Element():
            ''' Takes chunklist as input and
            parses the data into specific properties.
            '''
            def __init__(self,chunk):
                self.vlan = chunk[0]
                self.mac = chunk[1]
                self.typestring = chunk[2]
                self.protocol = chunk[3]
                self.operation = chunk[4]
                self.slotport = chunk[5]
            def dump(self):
                msg = '\tTableParser_ShowMacTable.Element:\n\r'
                msg += "\t\tVlan: " + self.vlan + "\n\r"
                msg += "\t\tMac: " + self.mac + "\n\r"
                msg += "\t\tType: " + self.typestring + "\n\r"
                msg += "\t\tProtocol: " + self.protocol + "\n\r"
                msg += "\t\tOperation: " + self.operation + "\n\r"
                msg += "\t\tSlotport: " + self.slotport + "\n\r"
                return(msg)

        headers =   [   'vlan',
                        'mac',
                        'typestring',
                        'protocol',
                        'operation',
                        'slotport',
                    ]
        sourcecommand = 'show mac-address-table'
        # line to start at after stripping lines with '/'
        startatline = 0
        def __init__(self,text):
            self.texttable = self.stripextra(text)
            self.elementlist = self.parsedata()
        def stripextra(self,text):
            temp = []
            for i,line in enumerate(text):
                if '/' in line:
                    temp.append(line)
            return(temp)
        def parsedata(self):
            temp = []
            for line in range(self.startatline,len(self.texttable)):
                chunk = (self.texttable[line].split())
                #print(str(chunk))
                temp.append(self.Element(chunk))
            return(temp)
        def dump(self):
            msg = 'TableParser_ShowMacTable:\n\r'
            for e in self.elementlist:
                msg += e.dump()
            return msg
    class TableParser_ShowIntStatus():
        ''' Takes a raw text table as input and 
        parses it specifically for the 'show interface status'
        command on the ALU 6450

        Holds list of Element() with properties
            that line up with the column headers.
        '''
        class Element():
            ''' Takes chunklist as input and
            parses the data into specific properties.
            '''
            def __init__(self,chunk):
                self.slotport = chunk[0]
                self.autonegotiate = chunk[1]
                self.detected_speed = chunk[2]
                self.detected_duplex = chunk[3]
                self.detected_hybrid = chunk[4]
                self.configured_speed = chunk[5]
                self.configured_duplex = chunk[6]
                self.configured_hybrid = chunk[7]
                self.traplinkupdown = chunk[8]
            def dump(self):
                msg = "\tTableParser_ShowIntStatus().Element():\n\r"
                msg += "\t\tslotport: " + self.slotport + "\n\r"
                msg += "\t\tautonegotiate: " + self.autonegotiate + "\n\r"
                msg += "\t\tdetected_speed: " + self.detected_speed + "\n\r"
                msg += "\t\tdetected_duplex: " + self.detected_duplex + "\n\r"
                msg += "\t\tdetected_hybrid: " + self.detected_hybrid + "\n\r"
                msg += "\t\tconfigured_speed: " + self.configured_speed + "\n\r"
                msg += "\t\tconfigured_duplex: " + self.configured_duplex + "\n\r"
                msg += "\t\tconfigured_hybrid: " + self.configured_hybrid + "\n\r"
                msg += "\t\ttraplinkupdown: " + self.traplinkupdown + "\n\r"
                return(msg)
        headers =   [   'slotport',
                        'autonegotiate',
                        'detected_speed',
                        'detected_duplex',
                        'detected_hybrid',
                        'configured_speed',
                        'configured_duplex',
                        'configured_hybrid'
                        'traplinkupdown',
                    ]
        sourcecommand = 'show interfaces status'
        # line to start at after stripping lines with '/'
        startatline = 1
        def __init__(self,text):
            self.texttable = self.stripextra(text)
            self.elementlist = self.parsedata()
        def stripextra(self,text):
            temp = []
            for i,line in enumerate(text):
                if '/' in line:
                    temp.append(line)
            return(temp)
        def parsedata(self):
            temp = []
            for line in range(self.startatline,len(self.texttable)):
                chunk = (self.texttable[line].split())
                temp.append(self.Element(chunk))
            return(temp)
        def dump(self):
            msg = "TableParser_ShowIntStatus()"
            for e in self.elementlist:
                msg += e.dump()
            return(msg)
                
    class ChunkParser_ShowInt():
        ''' Takes raw text as input and 
        parses it specifically for the 
        'show interfaces' command on 
        the ALU 6450

        Holds list of Element() with properties.
        '''
        ########################################################
        class Element():
            ''' Holds properties of interface detected
            in the 'show interfaces' command
            '''
            def __init__(self,slotport):
                self.slotport = slotport
                self.operstatus = ''
                self.sfp = ''
                self.mac = ''
                self.startline = None
                self.stopline = None
                self.chunk = []
            def dump(self):
                msg = '\tChunkParser_ShowInt().Element():\n\r'
                msg += "\t\tSlotport: " + self.slotport + "\r\n"
                msg += "\t\tOperstatus: " + self.operstatus + "\r\n"
                msg += "\t\tSFP: " + self.sfp + "\r\n"
                msg += "\t\tMac: " + self.mac + "\r\n"
                return(msg)
        sourcecommand = 'show interfaces'
        ''' define all of the identifiers used in this Parser.
        Each identifer is a classed object. the first property
        describes which command the idenfier should be used for.
        The second element is the Identifier() object used for 
        detection
        '''
        id_slotport = ElementIdentifier('show interfaces',    
                                        " Slot/Port  ",
                                        "\d*/\d*")
        id_operstatus = ElementIdentifier('show interfaces',    
                                        "  Operational Status     : ",
                                        "\w*")
        id_sfp = ElementIdentifier('show interfaces',
                                    "  SFP/SFP\+/XFP           : ",
                                    ".*")
        id_mac = ElementIdentifier('show interfaces',
                                    "  MAC address            : ",
                                    "([0-9A-Fa-f]{2}[-:]){5}[0-9A-Fa-f]{2})|(([0-9A-Fa-f]{4}.){2}[0-9A-Fa-f]{4}")
        def __init__(self,text):
            self.alltext = text
            self.elementlist = self.chunkdata()
            self.populateElements()
        def chunkdata(self):
            # chunks the big block of interfaces text into slotport sections
            #   and then appends those to a list.
            templist = []
            for i,line in enumerate(self.alltext):
                if self.id_slotport.identifier.check_match(line):
                    temp_slotport = self.id_slotport.identifier.give_group_value(line)
                    temp_element = self.Element(temp_slotport)
                    temp_element.startline = i
                    templist.append(temp_element)
            for r,element in enumerate(templist):
                indexofnextelement = r+1
                try:
                    # add some end of list protection
                    if r == len(templist)-1 and element.stopline == None:
                        element.stopline = len(self.alltext)
                    else:
                        element.stopline = templist[indexofnextelement].startline
                    for linenumber in range(element.startline+1,element.stopline):
                        element.chunk.append(self.alltext[linenumber])
                except Exception as e:
                    print("Exception pulling startline of nextelementinlist: " + str(e))
            return(templist)
        def populateElements(self):
            ''' takes the sorted chunks in the elementlist and populates
            the rest of the Element() properties. 
            '''
            for element in self.elementlist:
                for line in element.chunk:
                    if self.id_operstatus.identifier.check_match(line):
                        element.operstatus = self.id_operstatus.identifier.give_group_value(line)
                    elif self.id_sfp.identifier.check_match(line):
                        element.sfp = self.id_sfp.identifier.give_group_value(line)
                    elif self.id_mac.identifier.check_match(line):
                        element.mac = self.id_mac.identifier.give_group_value(line)
        def dump(self):
            msg = "ChunkParser_ShowInt():\n\r"
            for e in self.elementlist:
                msg += e.dump()
            return(msg)
    class Port():
        ''' Class used for building a port object based
        on the smaller parser classes. 
        '''
        class AssocMac():
            ''' Mini class to hold associated macs
            '''
            def __init__(self):
                self.vlan = ''
                self.mac = ''
                self.typestring = ''
                self.slotport = ''
        def __init__(self,slotport):
            self.slotport = slotport
            self.operstatus = ''
            self.sfp = ''
            self.mac = ''
            self.autonegotiate = ''
            self.detected_speed = ''
            self.detected_duplex = ''
            self.detected_hybrid = ''
            self.configured_speed = ''
            self.configured_duplex = ''
            self.configured_hybrid = ''
            self.associatedmacs = []
        def dump(self):
            msg = ''
            msg += "\tParser_Port().Port(): \n\r"
            msg += "\t\tSlotport:\t\t" + self.slotport + "\r\n"
            msg += "\t\tOperstatus:\t\t" + self.operstatus + "\r\n"
            msg += "\t\tSFP:\t\t\t" + self.sfp + "\r\n"
            msg += "\t\tMac:\t\t\t" + self.mac + "\r\n"
            msg += "\t\tautonegotiate:\t\t" + self.autonegotiate + "\n\r"
            msg += "\t\tdetected_speed:\t\t" + self.detected_speed + "\n\r"
            msg += "\t\tdetected_duplex:\t" + self.detected_duplex + "\n\r"
            msg += "\t\tdetected_hybrid:\t" + self.detected_hybrid + "\n\r"
            msg += "\t\tconfigured_speed:\t" + self.configured_speed + "\n\r"
            msg += "\t\tconfigured_duplex:\t" + self.configured_duplex + "\n\r"
            msg += "\t\tconfigured_hybrid:\t" + self.configured_hybrid + "\n\r"
            msg += "\t\tAssociatedMacs[]:\n\r"
            for mac in self.associatedmacs:
                msg += "\t\t\tVlan:\t\t\t" + mac.vlan + "\n\r"
                msg += "\t\t\tMac:\t\t\t" + mac.mac + "\n\r"
                msg += "\t\t\tType:\t\t\t" + mac.typestring + "\n\r"
                msg += "\t\t\tslotport:\t\t" + mac.slotport + "\n\r"
                msg += "\t\t\t------------\n\r"
            return(msg)
    def __init__(self,loo_commandlist):
        # now pull those commands involved in as objects along with their data
        self.commandos = self.attach_relevant_commandos(loo_commandlist)
        self.ints = None
        self.ints_status = None
        self.mac_table = None
        # now build the above properties with the custom class parsers
        self.send_commando_data_to_parsers() 
        ''' Once portparsers initialize, data looks like this '''
        # ChunkParser_ShowInt(text)
        '''
        ChunkParser_ShowInt():
            ChunkParser_ShowInt().Element():
                    Slotport: 1/1
                    Operstatus: up
                    SFP: 1000Base-T
                    Mac: e8:e7:32:a3:06:de
        '''
        # TableParser_ShowIntStatus(text)
        '''
        TableParser_ShowIntStatus() 
            TableParser_ShowIntStatus().Element():
                slotport: 1/1
                autonegotiate: Enable
                detected_speed: 1000
                detected_duplex: Full
                detected_hybrid: NA
                configured_speed: 1000
                configured_duplex: Full
                configured_hybrid: NA
                traplinkupdown: -
        '''
        # TableParser_ShowMacTable(text)
        '''
        TableParser_ShowMacTable:
            TableParser_ShowMacTable.Element:
                Vlan: 2
                Mac: 00:30:ab:2b:96:29
                Type: learned
                Protocol: ---
                Operation: bridging
                Slotport: 1/1
        '''
        self.portlist = self.initialize_ports()
        self.finalize_ports()
    def attach_relevant_commandos(self,loo_commandlist):
        ''' takes list of CommandOutput objects and matches 
        them up with the commandsinvolved list, pulls that list
        of objects and returns it. 
        '''
        templist = []
        for c in loo_commandlist:
            for ci in self.commandsinvolved:
                if ci == c.command_human:
                    templist.append(c)
        return(templist)
    def send_commando_data_to_parsers(self):
        for command in self.commandos:
            if command.command_human == 'show interfaces':
                self.ints = self.ChunkParser_ShowInt(command.sectionoutput)
            elif command.command_human == 'show interfaces status':
                self.ints_status = self.TableParser_ShowIntStatus(command.sectionoutput)
            elif command.command_human == 'show mac-address-table':
                self.mac_table = self.TableParser_ShowMacTable(command.sectionoutput)
    def initialize_ports(self):
        ''' Takes the data from the self.ints and creates
        new Port() objects
        '''
        templist = []
        for thing in self.ints.elementlist:
            tport = self.Port(thing.slotport)
            templist.append(tport)
        return(templist)
    def finalize_ports(self):
        ''' takes the portlist and then checks the other
        two lists for slotports of the same and fills in 
        the rest of the data.
        '''
        for port in self.portlist:
            for element in self.ints_status.elementlist:
                if port.slotport == element.slotport:
                    port.autonegotiate = element.autonegotiate
                    port.detected_speed = element.detected_speed
                    port.detected_duplex = element.detected_duplex
                    port.detected_hybrid = element.detected_hybrid
                    port.configured_speed = element.configured_speed
                    port.configured_duplex = element.configured_duplex
                    port.configured_hybrid = element.configured_hybrid
            for element in self.mac_table.elementlist:
                if port.slotport == element.slotport:
                    tmac = port.AssocMac()
                    tmac.vlan = element.vlan
                    tmac.mac = element.mac
                    tmac.typestring = element.typestring
                    tmac.slotport = element.slotport
                    port.associatedmacs.append(tmac)
            for element in self.ints.elementlist:
                if port.slotport == element.slotport:
                    port.operstatus = element.operstatus
                    port.sfp = element.sfp
                    port.mac = element.mac
    def dumpfull(self):
        msg = ''
        msg += self.ints.dump()
        msg += self.ints_status.dump()
        msg += self.mac_table.dump()
        msg += "Parser_Port():\n\r"
        for obj in self.portlist:
            msg += obj.dump()
        return(msg)
    def dump(self):
        msg = ''
        msg += "Parser_Port():\n\r"
        for obj in self.portlist:
            if obj.operstatus == 'up':
                msg += obj.dump()
        return(msg)
    commandsinvolved = [   'show interfaces',
                                    'show interfaces status',
                                    'show mac-address-table',
                                    'show arp',
                                ]

class PortGenerator_TypeContainer_ALU_SCS():
    ''' Takes a Parser_Port() object on init and then 
    generates port objects in the format desired for 
    the specific type of network element. 
    '''
    def __init__(self,parserobj):
        self.parserobj = parserobj
        self.RealPort = TypeContainer_ALU_SCS.PortsContainer.Port
        self.portlist = self.convertPorts()
    def convertPorts(self):
        ''' takes the parser object ports and turns them into the 
        port type that we want for the specific typeModule
        '''
        portlist = []
        for pport in self.parserobj.portlist:
            uid                                 = werd.genUID()
            #                                   imported as RealPort
            aport                               = self.RealPort(uid)
            aport.slotport.value                = pport.slotport
            aport.operstatus.value              = pport.operstatus
            aport.sfp.value                     = pport.sfp
            aport.mac.value                     = pport.mac
            aport.autonegotiate.value           = pport.autonegotiate
            aport.detected.speed.value          = pport.detected_speed
            aport.detected.duplex.value         = pport.detected_duplex
            aport.detected.hybridtype.value     = pport.detected_hybrid
            aport.configured.speed.value        = pport.configured_speed
            aport.configured.duplex.value       = pport.configured_duplex
            aport.configured.hybridtype.value   = pport.configured_hybrid
            for assocmac in pport.associatedmacs:
                uid                                 = werd.genUID()
                amac                                = aport.associatedmacs.MacContainer(uid)
                amac.vlan.value                     = assocmac.vlan
                amac.mac.value                      = assocmac.mac
                amac.typestring.value               = assocmac.typestring
                aport.associatedmacs.maclist.append(amac)
            portlist.append(aport)
        return(portlist)
    def dump(self):
        try:
            return("PortGenerator_TypeContainer_ALU_SCS(): Length of self.portlist = " + str(len(self.portlist)))
        except:
            return("PortGenerator_TypeContainer_ALU_SCS(): No data in self.portlist")

class InterfaceGenerator_TypeContainer_ALU_SCS():
    ''' Takes a TableParser_ShowIpInterface() object 
    on init and then generates interface objects in 
    the format desired for the specific type of 
    network element. 
    '''
    def __init__(self,parserobj):
        self.parserobj = parserobj
        self.RealInt = TypeContainer_ALU_SCS.InterfacesContainer.Interface
        self.intlist = self.convertParserObj()
    def convertParserObj(self):
        ''' takes the parser object interfaces and turns them into the 
        interface type that we want for the specific typeModule
        '''
        '''
        anint = new.interfaces.Interface('1')
        anint.name.value = 'Loopback'
        anint.address.value = '127.0.0.1'
        anint.subnetmask.value = '255.0.0.1'
        anint.status.value = 'UP'
        anint.device.value = 'Loopback'
        new.interfaces.interfacelist.append(anint)
        '''
        intlist = []
        for pint in self.parserobj.elementlist:
            uid                                 = werd.genUID()
            #                                   imported as RealInt
            anint                               = self.RealInt(uid)
            anint.name.value                    = pint.name
            anint.address.value                 = pint.address
            anint.subnetmask.value              = pint.subnetmask
            anint.status.value                  = pint.status
            anint.device.value                  = pint.device
            intlist.append(anint)
        return(intlist)
    def dump(self):
        try:
            return("InterfaceGenerator_TypeContainer_ALU_SCS(): Length of self.intlist = " + str(len(self.portlist)))
        except:
            return("InterfaceGenerator_TypeContainer_ALU_SCS(): No data in self.intlist")

class TableParser_ShowIpInterface():
    ''' Takes a raw text table as input and 
    parses it specifically for the 
    'show ip interface' command on 
    the ALU 6450

    Holds list of Element() with properties
        that line up with the column headers.
    '''
    class Element():
        ''' Takes chunklist as input and
        parses the data into specific properties.
        '''
        def __init__(self,chunk):
            self.name = chunk[0]
            self.address = chunk[1]
            self.subnetmask = chunk[2]
            self.status = chunk[3]
            if chunk[5] == 'vlan':
                self.device = chunk[5] + " " + chunk[6]
            else:
                self.device = chunk[5]
            '''
            <name>Loopback</name>
                    <address>127.0.0.1</address>
                    <subnetmask>255.0.0.0</subnetmask>
                    <status>UP</status>
                    <device>Loopback</device>
            '''
    headers =   [   'name',
                    'ipaddress',
                    'subnetmask',
                    'status',
                    'forward',
                    'device',
                ]
    sourcecommand = 'show ip interface'
    # line to start at after stripping lines without an IP
    startatline = 0
    def __init__(self,loo_commandlist):
        self.text = []
        self.attach_relevant_commandos(loo_commandlist)
        self.texttable = self.stripextra(self.text)
        self.elementlist = self.parsedata()
    def attach_relevant_commandos(self,loo_commandlist):
        ''' take full list of command output and find the one we
        want for this parser based on self.sourcecommand
        '''
        for cmd in loo_commandlist:
            if cmd.command_human == self.sourcecommand:
                self.text = cmd.sectionoutput
    def stripextra(self,text):
        temp = []
        # define regex for matching an IP address
        import re
        re_ip = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        for i,line in enumerate(text):
            re_ip_match = re.search(re_ip,line)
            if re_ip_match:
                temp.append(line)
        # now have temp list with only the lines with an IP
        return(temp)
    def parsedata(self):
        temp = []
        for line in range(self.startatline,len(self.texttable)):
            chunk = (self.texttable[line].split())
            temp.append(self.Element(chunk))
        return(temp)
    def displayelements(self):
        for e in self.elementlist:
            print("Name = " + e.name + ", Address: " + e.address)

class SectionParser_ShowChassis():
        ''' Takes loo_commandlist as input and 
        parses it specifically for the 
        'show chassis' command on 
        the ALU 6450. Designed for sections of text
        without multiple sections.

        Holds a single Element() with properties.
        '''
        ########################################################
        class Element():
            ''' Holds properties of chassis detected
            in the 'show chassis' command
            '''
            def __init__(self):
                self.model = ''
                self.description = ''
                self.adminstatus = ''
                self.operstatus = ''
                self.mac = ''
                self.serial = ''
            def dump(self):
                msg = '\tSectionParser_ShowChassis().Element():\n\r'
                msg += "\t\tmodel: " + self.model + "\r\n"
                msg += "\t\tdescription: " + self.description + "\r\n"
                msg += "\t\tadminstatus: " + self.adminstatus + "\r\n"
                msg += "\t\toperstatus: " + self.operstatus + "\r\n"
                msg += "\t\tmac: " + self.mac + "\r\n"
                msg += "\t\tserial: " + self.serial + "\r\n"
                return(msg)
        sourcecommand = 'show chassis'
        ''' define all of the identifiers used in this Parser.
        Each identifer is a classed object. the first property
        describes which command the idenfier should be used for.
        The second element is the Identifier() object used for 
        detection
        '''
        # ElementIdentifier(sourcecommand, pattern for search, pattern for value)
        id_model = ElementIdentifier('show chassis',    
                                        "  Model Name:                    ",
                                        ".*")
        id_description = ElementIdentifier('show chassis',    
                                        "  Description:                   ",
                                        ".*")
        id_adminstatus = ElementIdentifier('show chassis',
                                    "  Admin Status:                  ",
                                    ".*")
        id_operstatus = ElementIdentifier('show chassis',
                                    "  Operational Status:            ",
                                    ".*")
        id_mac = ElementIdentifier('show chassis',
                                    "  MAC Address:                   ",
                                    "([0-9A-Fa-f]{2}[-:]){5}[0-9A-Fa-f]{2})|(([0-9A-Fa-f]{4}.){2}[0-9A-Fa-f]{4}")
        id_serial = ElementIdentifier('show chassis',
                                    "  Serial Number:                 ",
                                    ".*")
        def __init__(self,loo_commandlist):
            self.text = []
            self.attach_relevant_commandos(loo_commandlist)
            self.element = self.populateElement()
        def attach_relevant_commandos(self,loo_commandlist):
            ''' take full list of command output and find the one we
            want for this parser based on self.sourcecommand
            '''
            for cmd in loo_commandlist:
                if cmd.command_human == self.sourcecommand:
                    self.text = cmd.sectionoutput
        def populateElement(self):
            ''' takes the command text in the specific command and 
            parses it to create the Element() 
            '''
            '''
            self.model = ''
            self.description = ''
            self.adminstatus = ''
            self.operstatus = ''
            self.mac = ''
            self.serial = ''
            '''
            element = self.Element()
            for line in self.text:
                if self.id_model.identifier.check_match(line):
                    element.model = self.id_model.identifier.give_group_value(line)
                elif self.id_description.identifier.check_match(line):
                    element.description = self.id_description.identifier.give_group_value(line)
                elif self.id_adminstatus.identifier.check_match(line):
                    element.adminstatus = self.id_adminstatus.identifier.give_group_value(line)
                elif self.id_operstatus.identifier.check_match(line):
                    element.operstatus = self.id_operstatus.identifier.give_group_value(line)
                elif self.id_mac.identifier.check_match(line):
                    element.mac = self.id_mac.identifier.give_group_value(line)
                elif self.id_serial.identifier.check_match(line):
                    element.serial = self.id_serial.identifier.give_group_value(line)
            return(element)
        def dump(self):
            msg = "SectionParser_ShowChassis():\n\r"
            msg += self.element.dump()
            return(msg)

class ChassisGenerator_TypeContainer_ALU_SCS():
    ''' Takes a SectionParser_ShowChassis() object 
    on init and then generates a chassis objects in 
    the format desired for the specific type of 
    network element. 
    '''
    def __init__(self,parserobj):
        self.parserobj = parserobj
        self.RealType = TypeContainer_ALU_SCS.ChassisContainer
        self.chassis = self.convertParserObj()
    def convertParserObj(self):
        ''' takes the parser object chassis and turns int into the 
        chassis type that we want for the specific typeModule
        '''
        '''
        new.chassis.model.value = 'OS6450-U24'
        new.chassis.description.value = '22 100/1000 BaseX + 2 Combo + 2 1/10G STK/UPLINK'
        new.chassis.adminstatus.value = 'POWER ON'
        new.chassis.operstatus.value = 'UP'
        new.chassis.mac.value = 'e8:e7:32:a3:06:dc'
        new.chassis.serial.value = 'blahblah'
        '''
        chassis = self.RealType()
        chassis.model.value = self.parserobj.element.model
        chassis.description.value = self.parserobj.element.description
        chassis.adminstatus.value = self.parserobj.element.adminstatus
        chassis.operstatus.value = self.parserobj.element.operstatus
        chassis.mac.value = self.parserobj.element.mac
        chassis.serial.value = self.parserobj.element.serial
        return(chassis)
    def dump(self):
        # this one is so simple, dump not needed right now
        pass

class Parser_Module():
    ''' Class to handle module parsing. Holds 
    things like the regexes needed for 
    detecting sections of output data.
    '''
    commandsinvolved = [   'show module',
                           'show module long',
                           'show module status',
                       ]
    
    class TableParser_ShowModule():
        ''' Takes a raw text table as input and 
        parses it specifically for the 
        'show module' command on 
        the ALU 6450

        Holds list of Element() with properties
            that line up with the column headers.
        '''
        class Element():
            ''' Takes chunklist as input and
            parses the data into specific properties.
            For this 'show module' table we only need
            the slot and partnumber. The rest we get from
            'show module long'
            '''
            def __init__(self,chunk):
                self.slot = chunk[0]
                self.partnumber = chunk[1]
            def dump(self):
                msg = '\tTableParser_ShowModule.Element:\n\r'
                msg += "\t\tslot: " + self.slot + "\n\r"
                msg += "\t\tpartnumber: " + self.partnumber + "\n\r"
                return(msg)
        headers =   [   'slot',
                        'partnumber',
                        'serial',
                        'hwrev',
                        'mfgdate',
                        'modelname',
                    ]
        sourcecommand = 'show module'
        startatline = 3
        def __init__(self,loo_commandlist):
            self.texttable = []
            self.attach_relevant_commandos(loo_commandlist)
            self.texttable = self.stripextra(self.texttable)
            self.elementlist = self.parsedata()
        def attach_relevant_commandos(self,loo_commandlist):
            ''' take full list of command output and find the one we
            want for this parser based on self.sourcecommand
            '''
            for cmd in loo_commandlist:
                if cmd.command_human == self.sourcecommand:
                    self.texttable = cmd.sectionoutput
        def stripextra(self,text):
            temp = []
            for i in range(self.startatline,len(text)-1):
                temp.append(text[i])
            return(temp)
        def parsedata(self):
            temp = []
            for line in self.texttable:
                chunk = (line.split())
                if len(chunk) > 0 and chunk[0] != '':
                    element = self.Element(chunk)
                    temp.append(element)
            return(temp)
        def dump(self):
            msg = 'TableParser_ShowModule:\n\r'
            for e in self.elementlist:
                msg += e.dump()
            return msg
    class TableParser_ShowModuleStatus():
            ''' Takes a raw text table as input and 
            parses it specifically for the 
            'show module status' command on 
            the ALU 6450

            Holds list of Element() with properties
                that line up with the column headers.
            '''
            class Element():
                ''' Takes chunklist as input and
                parses the data into specific properties.
                For this 'show module' table we only need
                the slot and partnumber. The rest we get from
                'show module long'
                '''
                def __init__(self,chunk):
                    self.slot = chunk[0]
                    self.mac = chunk[5]
                def dump(self):
                    msg = '\tTableParser_ShowModuleStatus(): Element():\n\r'
                    msg += "\t\tslot: " + self.slot + "\n\r"
                    msg += "\t\tmac: " + self.mac + "\n\r"
                    return(msg)
            headers =   [   'slot',
                            'operationalstatus',
                            'admin-status',
                            'firmwarerev',
                            'mac',
                        ]
            sourcecommand = 'show module status'
            startatline = 3
            def __init__(self,loo_commandlist):
                self.texttable = []
                self.attach_relevant_commandos(loo_commandlist)
                self.texttable = self.stripextra(self.texttable)
                self.elementlist = self.parsedata()
            def attach_relevant_commandos(self,loo_commandlist):
                ''' take full list of command output and find the one we
                want for this parser based on self.sourcecommand
                '''
                for cmd in loo_commandlist:
                    if cmd.command_human == self.sourcecommand:
                        self.texttable = cmd.sectionoutput
            def stripextra(self,text):
                temp = []
                for i in range(self.startatline,len(text)-1):
                    temp.append(text[i])
                return(temp)
            def parsedata(self):
                temp = []
                for line in self.texttable:
                    chunk = (line.split())
                    if len(chunk) > 0 and chunk[0] != '':
                        element = self.Element(chunk)
                        temp.append(element)
                return(temp)
            def dump(self):
                msg = 'TableParser_ShowModuleStatus(): :\n\r'
                for e in self.elementlist:
                    msg += e.dump()
                return msg
    class ChunkParser_ShowModuleLong():
        ''' Takes raw text as input and 
        parses it specifically for the 
        'show module long' command on 
        the ALU 6450

        Holds list of Element() with properties.
        '''
        ########################################################
        sourcecommand = 'show module long'
        class Module():
            ''' Class used for building a port object based
            on the smaller parser classes. 
            '''
            class Gbic():
                ''' Mini class to hold associated gbics
                '''
                def __init__(self):
                    self.modelname = ''
                    self.partnumber = ''
                    self.serial = ''
                    self.adminstatus = ''
                    self.operstatus = ''
                    self.laserwavelength = ''
            def __init__(self):
                self.slot = ''
                self.partnumber = ''
                self.status = ''
                self.operstatus = ''
                self.adminstatus = ''
                self.description = ''
                self.mac = ''
                self.gbics = []
            def dump(self):
                msg = ''
                msg += "\tParser_Module().Module(): \n\r"
                msg += "\t\tslot:\t\t" + self.slot + "\r\n"
                msg += "\t\tpartnumber:\t\t" + self.partnumber + "\r\n"
                msg += "\t\tstatus:\t\t\t" + self.status + "\r\n"
                msg += "\t\tdescription:\t\t\t" + self.description + "\r\n"
                msg += "\t\tmac:\t\t\t" + self.mac + "\r\n"
                msg += "\t\tGbics[]:\n\r"
                for gbic in self.gbics:
                    msg += "\t\t\tmodelname:\t\t\t" + gbic.modelname + "\n\r"
                    msg += "\t\t\tpartnumber:\t\t\t" + gbic.partnumber + "\n\r"
                    msg += "\t\t\tserial:\t\t\t" + gbic.serial + "\n\r"
                    msg += "\t\t\tadminstatus:\t\t" + gbic.adminstatus + "\n\r"
                    msg += "\t\t\toperstatus:\t\t" + gbic.operstatus + "\n\r"
                    msg += "\t\t\tlaserwavelength:\t\t" + gbic.laserwavelength + "\n\r"
                    msg += "\t\t\t------------\n\r"
                return(msg)
        class Chunk():
            ''' mini class to hold chunk text and start/stop line info
            '''
            def __init__(self):
                self.startline = 0
                self.stopline = None
                self.chunkblock = []
                self.hasgbics = False
                # holds Chunk_Gbic() objects
                self.gbic_chunks = []
            def dump(self):
                msg = ''
                msg += "\tChunkParser_ShowModuleLong(): Chunk()\n\r"
                msg += "\t\tstartline = " + str(self.startline) + "\n\r"
                msg += "\t\tstopline = " + str(self.stopline) + "\n\r"
                for line in self.chunkblock:
                    msg += "\t\t\t" + line + "\n\r"
                for gbic_chunk in self.gbic_chunks:
                    msg += gbic_chunk.dump()
                return(msg)
        class Chunk_Gbic():
            ''' mini class to hold gbic chunk text and start/stop line info
            '''
            def __init__(self):
                self.startline = 0
                self.stopline = None
                self.chunkblock = []
                self.gbicid = ''
            def dump(self):
                msg = ''
                msg += "\t\t\t\tChunkParser_ShowModuleLong(): Chunk_Gbic()\n\r"
                msg += "\t\t\t\t\tstartline = " + str(self.startline) + "\n\r"
                msg += "\t\t\t\t\tstopline = " + str(self.stopline) + "\n\r"
                msg += "\t\t\t\t\tgbicid = " + self.gbicid + "\n\r"
                for line in self.chunkblock:
                    msg += "\t\t\t\t\t" + line + "\n\r"
                return(msg)
        ''' define all of the identifiers used in this Parser.
        Each identifer is a classed object. the first property
        describes which command the idenfier should be used for.
        The second element is the Identifier() object used for 
        detection
        '''
        # the id_slotsection is just to find the chunks, won't use the group value
        id_slotsection = ElementIdentifier('show module long',
                                            "in slot",
                                            ".*")
        id_gbic = ElementIdentifier('show module long',
                                            "  GBIC  ",
                                            ".*")
        id_adminstatus = ElementIdentifier('show module long',    
                                        "  Admin Status:                  ",
                                        ".*")
        id_operstatus = ElementIdentifier('show module long',    
                                        "  Operational Status:            ",
                                        ".*")
        id_description = ElementIdentifier('show module long',
                                        "  Description:                   ",
                                        ".*")
        id_mac = ElementIdentifier('show module long',
                                    "  MAC Address:                   ",
                                    "([0-9A-Fa-f]{2}[-:]){5}[0-9A-Fa-f]{2})|(([0-9A-Fa-f]{4}.){2}[0-9A-Fa-f]{4}")
        id_gbic_modelname = ElementIdentifier('show module long',
                                    "        Model Name:                    ",
                                    ".*")
        id_gbic_partnumber = ElementIdentifier('show module long',
                                    "        Part Number:                   ",
                                    ".*")
        id_gbic_serial = ElementIdentifier('show module long',
                                    "        Serial Number:                 ",
                                    ".*")
        id_gbic_adminstatus = ElementIdentifier('show module long',
                                    "        Admin Status:                  ",
                                    ".*")
        id_gbic_operstatus = ElementIdentifier('show module long',
                                    "        Operational Status:            ",
                                    ".*")
        id_gbic_laserwavelength = ElementIdentifier('show module long',
                                    "        Laser Wave Length:             ",
                                    ".*")
        def __init__(self,loo_commandlist):
            self.alltext = []
            self.modulelist = []
            self.attach_relevant_commandos(loo_commandlist)
            self.chunklist = self.chunkdata()
            self.populateElements()
        def attach_relevant_commandos(self,loo_commandlist):
                ''' take full list of command output and find the one we
                want for this parser based on self.sourcecommand
                '''
                for cmd in loo_commandlist:
                    if cmd.command_human == self.sourcecommand:
                        self.alltext = cmd.sectionoutput
        def chunkdata(self):
            # chunks the big block of modules text into slot and gbic 
            # sections and then appends those to a list.
            templist = []
            for i,line in enumerate(self.alltext):
                if self.id_slotsection.identifier.check_match(line):
                    temp_chunk = self.Chunk()
                    temp_chunk.startline = i
                    templist.append(temp_chunk)
            for r,chunk in enumerate(templist):
                indexofnextelement = r+1
                try:
                    # add some end of list protection
                    if r == len(templist)-1 and chunk.stopline == None:
                        chunk.stopline = len(self.alltext)
                    else:
                        chunk.stopline = templist[indexofnextelement].startline
                    for linenumber in range(chunk.startline+1,chunk.stopline):
                        chunk.chunkblock.append(self.alltext[linenumber])
                except Exception as e:
                    print("Exception pulling startline of nextelementinlist: " + str(e))
            # now scan through and identify sections with gbics
            for chunk in templist:
                for y,line in enumerate(chunk.chunkblock):
                    if self.id_gbic.identifier.check_match(line):
                        chunk.hasgbics = True
                        # now have to churn through and find the gbic start stop sections
                        #for i,liner in enumerate(chunk.chunkblock):
                            #print("CHUUUUUUUNKY: --" + str(i) + "-- " + liner)
                        #if self.id_gbic.identifier.check_match(line):
                        temp_chunk_gbic = self.Chunk_Gbic()
                        temp_chunk_gbic.gbicid = self.id_gbic.identifier.give_group_value(line)
                        temp_chunk_gbic.startline = y
                        chunk.gbic_chunks.append(temp_chunk_gbic)
            # now go through the gbic chunks
            for chunk in templist:
                for gbicchunkindex,gbicchunk in enumerate(chunk.gbic_chunks):
                    #for r,line in enumerate(gbicchunk.chunkblock):
                    indexofnextelement = gbicchunkindex+1
                    try:
                        gbicchunk.stopline = chunk.gbic_chunks[indexofnextelement].startline
                        for linenumber in range(gbicchunk.startline,gbicchunk.stopline):
                            gbicchunk.chunkblock.append(chunk.chunkblock[linenumber])
                    except Exception as e:
                        # Exception means that we probably hit end of list and can't do indexofnextelement
                        gbicchunk.stopline = len(chunk.chunkblock)
                        for linenumber in range(gbicchunk.startline,gbicchunk.stopline):
                            gbicchunk.chunkblock.append(chunk.chunkblock[linenumber])

            return(templist)
        def populateElements(self):
            ''' takes the sorted chunks in the chunklist and creates
            Module() objects based on regex matches
            '''
            # each chunk will be an individual module
            for chunk in self.chunklist:
                temp_module = self.Module()
                for line in chunk.chunkblock:
                    if self.id_adminstatus.identifier.check_match(line):
                        temp_module.adminstatus = self.id_adminstatus.identifier.give_group_value(line)
                    # The OPERSTATUS is the one we're picking for overall Module().status
                    elif self.id_operstatus.identifier.check_match(line):
                        temp_module.status = self.id_operstatus.identifier.give_group_value(line)
                    elif self.id_mac.identifier.check_match(line):
                        temp_module.mac = self.id_mac.identifier.give_group_value(line)
                    elif self.id_description.identifier.check_match(line):
                        temp_module.description = self.id_description.identifier.give_group_value(line)
                # now check to see if has gbic info, if so, parse those gbic chunks
                if chunk.hasgbics:
                    for chunk_gbic in chunk.gbic_chunks:
                        temp_gbic = temp_module.Gbic()
                        temp_gbic.id = chunk_gbic.gbicid
                        for line in chunk_gbic.chunkblock:
                            if self.id_gbic_modelname.identifier.check_match(line):
                                temp_gbic.modelname = self.id_gbic_modelname.identifier.give_group_value(line)
                            elif self.id_gbic_partnumber.identifier.check_match(line):
                                temp_gbic.partnumber = self.id_gbic_partnumber.identifier.give_group_value(line)
                            elif self.id_gbic_serial.identifier.check_match(line):
                                temp_gbic.serial = self.id_gbic_serial.identifier.give_group_value(line)
                            elif self.id_gbic_adminstatus.identifier.check_match(line):
                                temp_gbic.adminstatus = self.id_gbic_adminstatus.identifier.give_group_value(line)
                            elif self.id_gbic_operstatus.identifier.check_match(line):
                                temp_gbic.operstatus = self.id_gbic_operstatus.identifier.give_group_value(line)
                            elif self.id_gbic_laserwavelength.identifier.check_match(line):
                                temp_gbic.laserwavelength = self.id_gbic_laserwavelength.identifier.give_group_value(line)
                        temp_module.gbics.append(temp_gbic)
                self.modulelist.append(temp_module)
        def dump(self):
            msg = "ChunkParser_ShowModuleLong():\n\r"
            for e in self.modulelist:
                msg += e.dump()
            return(msg)
    ''' THIS IS INIT FOR TOP LEVEL PARSER_MODULE()'''
    def __init__(self,loo_commandlist):
        # now pull those commands involved in as objects along with their data
        self.commandos = self.attach_relevant_commandos(loo_commandlist)
        self.modules = None
        self.module_long = None
        # now build the above properties with the custom class parsers
        self.module = self.TableParser_ShowModule(self.commandos)
        self.module_long = self.ChunkParser_ShowModuleLong(self.commandos)
        # The primary class global object "Parser_Module().Module()" gets built in self.module_long
        #  the other modules are built with proprietary internal Element() objects.
        #  the self.finalize_modules() glues them together.
        self.modulelist = self.module_long.modulelist 
        self.module_status = self.TableParser_ShowModuleStatus(self.commandos)
        ''' Once portparsers initialize, data looks like this '''
        ''' 
        ChunkParser_ShowModuleLong()
            Parser_Module().Module(): 
                slot:       
                partnumber:     
                status:         UP
                description:            FINISAR CORP.   
                mac:            e8:e7:32:a3:06:de
                Gbics[]:
                    id:         1
                    modelname:          FINISAR CORP.   
                    partnumber:         FCLF8521P2BTL-A5
                    serial:         PQ96GY4         
                    adminstatus:        POWER ON
                    operstatus:     UP
                    laserwavelength:        n/a
                    ------------
                    id:         2
                    modelname:          FINISAR CORP.   
                    partnumber:         FCLF8521P2BTL-A5
                    serial:         PQ96GVM         
                    adminstatus:        POWER ON
                    operstatus:     UP
                    laserwavelength:        n/a

        TableParser_ShowModuleStatus(): :
            TableParser_ShowModuleStatus(): Element():
                slot: CMM-1
                mac: e8:e7:32:a3:06:dc

        TableParser_ShowModule:
            TableParser_ShowModule.Element:
                slot: CMM-1
                partnumber: 903175-90
        '''
        self.finalize_modules()
    def attach_relevant_commandos(self,loo_commandlist):
        ''' takes list of CommandOutput objects and matches 
        them up with the commandsinvolved list, pulls that list
        of objects and returns it. 
        '''
        templist = []
        for c in loo_commandlist:
            for ci in self.commandsinvolved:
                if ci == c.command_human:
                    templist.append(c)
        return(templist)
    def finalize_modules(self):
        ''' takes the modulelist and then checks the other
        two lists for linking data and fills in 
        the rest of the data.
        '''
        for module in self.modulelist:
            ''' since module_long.modulelist = self.modulelist now 
            go through self.module and self.module_status to get rest 
            of the data we need.
            '''
            for element in self.module_status.elementlist:
                if element.mac == module.mac:
                    module.slot = element.slot
            # now that we know the slot, we can tie in the partnumber
            #   from the 'show module' command.
            #   In hindsight, we don't really need the 'show module' 
            #   command since partnumber is in 'show module long' and
            #   can be tied to 'show module status' by mac address
            for element in self.module.elementlist:
                if element.slot == module.slot:
                    module.partnumber = element.partnumber
            #print(module.dump())
    def dump(self):
        msg = ''
        msg += "Parser_Module():\n\r"
        for obj in self.modulelist:
            msg += obj.dump()
        return(msg)

class ModuleGenerator_TypeContainer_ALU_SCS():
    ''' Takes a Parser_Module() object on init and then 
    generates port objects in the format desired for 
    the specific type of network element. 
    '''
    def __init__(self,parserobj):
        self.parserobj = parserobj
        self.RealModule = TypeContainer_ALU_SCS.ModuleContainer.Module
        self.modulelist = self.convertModules()
    def convertModules(self):
        ''' takes the parser object ports and turns them into the 
        port type that we want for the specific typeModule
        '''
        modulelist = []
        for pmod in self.parserobj.modulelist:
            uid                                 = werd.genUID()
            #                                   imported as RealModule
            amod                                = self.RealModule(uid)
            amod.slot.value                     = pmod.slot
            amod.status.value                   = pmod.status
            amod.description.value              = pmod.description
            amod.partnumber.value               = pmod.partnumber
            amod.mac.value                      = pmod.mac
            for pgbic in pmod.gbics:
                # GBIC has both a UID 'id' and ALU 'ident'
                uid                                 = werd.genUID()
                agbic                               = amod.gbics.Gbic(uid)
                agbic.ident.value                   = pgbic.id
                agbic.modelname.value               = pgbic.modelname
                agbic.partnumber.value              = pgbic.partnumber
                agbic.serial.value                  = pgbic.serial
                agbic.adminstatus.value             = pgbic.adminstatus
                agbic.operstatus.value              = pgbic.operstatus
                agbic.laserwavelength.value         = pgbic.laserwavelength
                amod.gbics.gbiclist.append(agbic)
            modulelist.append(amod)
        return(modulelist)
    def dump(self):
        try:
            return("ModuleGenerator_TypeContainer_ALU_SCS(): Length of self.modulelist = " + str(len(self.modulelist)))
        except:
            return("ModuleGenerator_TypeContainer_ALU_SCS(): No data in self.modulelist")

class TableParser_ShowVlan():
    ''' Takes a raw text table as input and 
    parses it specifically for the 
    'show vlan' command on 
    the ALU 6450

    Holds list of Element() with properties
        that line up with the column headers.
    '''
    class Element():
        ''' Takes chunklist as input and
        parses the data into specific properties.
        '''
        def __init__(self,chunk):
            self.name = chunk[10]
            self.ident = chunk[0]
            self.typestring = chunk[1]
            self.adminstatus = chunk[2]
            self.operstatus = chunk[3]
            self.ipstatus = chunk[7]
        def dump(self):
            msg = '\tTableParser_ShowVlan(): Element():\n\r'
            msg += "\t\tname: " + self.name + "\n\r"
            msg += "\t\tident: " + self.ident + "\n\r"
            msg += "\t\ttypestring: " + self.typestring + "\n\r"
            msg += "\t\tadminstatus: " + self.adminstatus + "\n\r"
            msg += "\t\toperstatus: " + self.operstatus + "\n\r"
            msg += "\t\tipstatus: " + self.ipstatus + "\n\r"
            return(msg)
    headers =   [   'vlan',
                    'type',
                    'admin',
                    'oper',
                    'stree-1x1',
                    'stree-flat',
                    'auth',
                    'ip',
                    'mbletag',
                    'srclrn',
                    'name',
                ]
    sourcecommand = 'show vlan'
    startatline = 3
    def __init__(self,loo_commandlist):
        self.texttable = []
        self.attach_relevant_commandos(loo_commandlist)
        self.texttable = self.stripextra(self.texttable)
        self.elementlist = self.parsedata()
    def attach_relevant_commandos(self,loo_commandlist):
        ''' take full list of command output and find the one we
        want for this parser based on self.sourcecommand
        '''
        for cmd in loo_commandlist:
            if cmd.command_human == self.sourcecommand:
                self.texttable = cmd.sectionoutput
    def stripextra(self,text):
        temp = []
        for i in range(self.startatline,len(text)-1):
            temp.append(text[i])
        return(temp)
    def parsedata(self):
        temp = []
        for line in self.texttable:
            chunk = (line.split())
            if len(chunk) > 0 and chunk[0] != '':
                element = self.Element(chunk)
                temp.append(element)
        return(temp)
    def dump(self):
        msg = 'TableParser_ShowVlan(): :\n\r'
        for e in self.elementlist:
            msg += e.dump()
        return msg

class VlanGenerator_TypeContainer_ALU_SCS():
    ''' Takes a TableParser_ShowVlan() object 
    on init and then generates interface objects in 
    the format desired for the specific type of 
    network element. 
    '''
    def __init__(self,parserobj):
        self.parserobj = parserobj
        self.RealVlan = TypeContainer_ALU_SCS.VlanContainer.Vlan
        self.vlanlist = self.convertParserObj()
    def convertParserObj(self):
        ''' takes the parser object interfaces and turns them into the 
        interface type that we want for the specific typeModule
        '''
        '''
        avlan = new.vlans.Vlan('1')
        avlan.name.value = '5'
        avlan.typestring.value = 'learned'
        avlan.ident.value = '1'
        avlan.description.value = 'vlan 1'
        avlan.adminstatus.value = 'up'
        avlan.operstatus.value = 'up'
        avlan.ipstatus.value = 'active'
        new.vlans.vlanlist.append(avlan)
        '''
        vlanlist = []
        for pvl in self.parserobj.elementlist:
            uid                                 = werd.genUID()
            #                                   imported as RealVlan
            avlan                               = self.RealVlan(uid)
            avlan.name.value                    = pvl.name
            avlan.typestring.value              = pvl.typestring
            avlan.ident.value                   = pvl.ident
            #                                   this one is for sanity
            avlan.description.value             = "vlan " + pvl.ident
            avlan.adminstatus.value             = pvl.adminstatus
            avlan.operstatus.value              = pvl.operstatus
            avlan.ipstatus.value                = pvl.ipstatus
            vlanlist.append(avlan)
        return(vlanlist)
    def dump(self):
        try:
            return("VlanGenerator_TypeContainer_ALU_SCS(): Length of self.vlanlist = " + str(len(self.vlanlist)))
        except:
            return("VlanGenerator_TypeContainer_ALU_SCS(): No data in self.vlanlist")

class TableParser_ShowIpRouterDatabase():
            ''' Takes a raw text table as input and 
            parses it specifically for the 
            'show ip router database' command on 
            the ALU 6450

            Holds list of Element() with properties
                that line up with the column headers.
            '''
            class Element():
                ''' Takes chunklist as input and
                parses the data into specific properties.
                '''
                def __init__(self,chunk):
                    self.destination = chunk[0]
                    self.gateway = chunk[1]
                    self.interface = chunk[2]
                    # these chunks fail when there's an
                    #   "Inactive Static Routes" section.
                    try:
                        self.metric = chunk[4]
                    except:
                        self.metric = ''
                    try:
                        self.typestring = chunk[3]
                    except:
                        self.typestring = ''
                def dump(self):
                    msg = '\tTableParser_ShowIpRouterDatabase(): Element():\n\r'
                    msg += "\t\tdestination: " + self.destination + "\n\r"
                    msg += "\t\tgateway: " + self.gateway + "\n\r"
                    msg += "\t\tinterface: " + self.interface + "\n\r"
                    msg += "\t\tmetric: " + self.metric + "\n\r"
                    msg += "\t\ttypestring: " + self.typestring + "\n\r"
                    return(msg)
            headers =   [   'destination',
                            'gateway',
                            'interface',
                            'protocol',
                            'metric',
                            'tag',
                        ]
            sourcecommand = 'show ip router database'
            startatline = 4
            def __init__(self,loo_commandlist):
                self.texttable = []
                self.attach_relevant_commandos(loo_commandlist)
                self.texttable = self.stripextra(self.texttable)
                self.elementlist = self.parsedata()
            def attach_relevant_commandos(self,loo_commandlist):
                ''' take full list of command output and find the one we
                want for this parser based on self.sourcecommand
                '''
                for cmd in loo_commandlist:
                    if cmd.command_human == self.sourcecommand:
                        self.texttable = cmd.sectionoutput
            def stripextra(self,text):
                temp = []
                for line in text:
                    if "/" in line:
                        temp.append(line)
                #for i in range(self.startatline,len(text)-1):
                    #temp.append(text[i])
                return(temp)
            def parsedata(self):
                temp = []
                for line in self.texttable:
                    chunk = (line.split())
                    if len(chunk) > 0 and chunk[0] != '':
                        element = self.Element(chunk)
                        temp.append(element)
                return(temp)
            def dump(self):
                msg = 'TableParser_ShowIpRouterDatabase(): :\n\r'
                for e in self.elementlist:
                    msg += e.dump()
                return msg

class RouteGenerator_TypeContainer_ALU_SCS():
    ''' Takes a TableParser_ShowIpRouterDatabase() object 
    on init and then generates interface objects in 
    the format desired for the specific type of 
    network element. 
    '''
    def __init__(self,parserobj):
        self.parserobj = parserobj
        self.RealRoute = TypeContainer_ALU_SCS.RoutesContainer.Route
        self.routelist = self.convertParserObj()
    def convertParserObj(self):
        ''' takes the parser object interfaces and turns them into the 
        interface type that we want for the specific typeModule
        '''
        '''
        aroute = new.routes.Route('1')
        aroute.destination.value = '0.0.0.0/0'
        aroute.gateway.value = '11.50.155.97'
        aroute.interface.value = 'external'
        aroute.metric.value = '1'
        aroute.typestring.value = 'LOCAL'
        new.routes.routelist.append(aroute)
        '''
        routelist = []
        for prt in self.parserobj.elementlist:
            uid                                 = werd.genUID()
            #                                   imported as RealRoute
            aroute                              = self.RealRoute(uid)
            aroute.destination.value            = prt.destination
            aroute.gateway.value                = prt.gateway
            aroute.interface.value              = prt.interface
            aroute.metric.value                 = prt.metric
            aroute.typestring.value             = prt.typestring
            routelist.append(aroute)
        return(routelist)
    def dump(self):
        try:
            return("RouteGenerator_TypeContainer_ALU_SCS(): Length of self.route = " + str(len(self.routelist)))
        except:
            return("RouteGenerator_TypeContainer_ALU_SCS(): No data in self.route")


class Parser_Dhcp():
    ''' Class to handle dhcp parsing. Holds 
    things like the regexes needed for 
    detecting sections of output data.
    '''
    commandsinvolved = [   'show dhcp-server statistics',
                           'show dhcp-server leases',
                       ]
    
    class TableParser_ShowDhcpServerLeases():
        ''' Takes a raw text table as input and 
        parses it specifically for the 
        'show dhcp-server leases' command on 
        the ALU 6450

        Holds list of Element() with properties
            that line up with the column headers.
        '''
        class Element():
            ''' Takes chunklist as input and
            parses the data into specific properties.
            '''
            def __init__(self,chunk):
                self.ipaddr = chunk[0]
                self.mac = chunk[1]
                self.timegranted = ' '.join(chunk[2:6])
                self.timeexpires = ' '.join(chunk[6:10])
                self.typestring = chunk[10]
            def dump(self):
                msg = '\tTableParser_ShowDhcpServerLeases.Element:\n\r'
                msg += "\t\tipaddr: " + self.ipaddr + "\n\r"
                msg += "\t\tmac: " + self.mac + "\n\r"
                msg += "\t\ttimegranted: " + self.timegranted + "\n\r"
                msg += "\t\ttimeexpires: " + self.timeexpires + "\n\r"
                msg += "\t\ttypestring: " + self.typestring + "\n\r"
                return(msg)
        headers =   [   'ipaddress',
                        'macaddress',
                        'leasegranted',
                        'leaseexpiry',
                        'typestring',
                    ]
        sourcecommand = 'show dhcp-server leases'
        startatline = 5
        def __init__(self,loo_commandlist):
            self.texttable = []
            self.attach_relevant_commandos(loo_commandlist)
            self.texttable = self.stripextra(self.texttable)
            self.elementlist = self.parsedata()
        def attach_relevant_commandos(self,loo_commandlist):
            ''' take full list of command output and find the one we
            want for this parser based on self.sourcecommand
            '''
            for cmd in loo_commandlist:
                if cmd.command_human == self.sourcecommand:
                    self.texttable = cmd.sectionoutput
        def stripextra(self,text):
            temp = []
            import re
            re_ip = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
            for i,line in enumerate(text):
                re_ip_match = re.search(re_ip,line)
                if re_ip_match:
                    temp.append(line)
            return(temp)
        def parsedata(self):
            temp = []
            for line in self.texttable:
                chunk = (line.split())
                if len(chunk) > 0 and chunk[0] != '':
                    element = self.Element(chunk)
                    temp.append(element)
            return(temp)
        def dump(self):
            msg = 'TableParser_ShowDhcpServerLeases:\n\r'
            for e in self.elementlist:
                msg += e.dump()
            return msg
    class SectionParser_ShowDhcpServerStatistics():
            ''' Takes loo_commandlist as input and 
            parses it specifically for the 
            'show dhcp-server statistics' command on 
            the ALU 6450. Designed for sections of text
            without multiple sections.

            Holds a single Element() with properties.
            '''
            ########################################################
            class Element():
                ''' Holds properties of chassis detected
                in the 'show chassis' command
                '''
                def __init__(self):
                    self.servername = ''
                    self.serverstatus = ''
                    self.numsubnetsmanaged = ''
                    ''' won't do numleases here instead will just count length of leaselist'''
                    #self.numleases = ''
                def dump(self):
                    msg = '\tSectionParser_ShowDhcpServerStatistics().Element():\n\r'
                    msg += "\t\tservername: " + self.servername + "\r\n"
                    msg += "\t\tserverstatus: " + self.serverstatus + "\r\n"
                    msg += "\t\tnumsubnetsmanaged: " + self.numsubnetsmanaged + "\r\n"
                    return(msg)
            sourcecommand = 'show dhcp-server statistics'
            ''' define all of the identifiers used in this Parser.
            Each identifer is a classed object. the first property
            describes which command the idenfier should be used for.
            The second element is the Identifier() object used for 
            detection
            '''
            # ElementIdentifier(sourcecommand, pattern for search, pattern for value)
            id_servername = ElementIdentifier('show dhcp-server statistics',    
                                            "  DHCP Server Name              : ",
                                            ".*")
            id_serverstatus = ElementIdentifier('show dhcp-server statistics',    
                                            "  DHCP Server Status            : ",
                                            ".*")
            id_numsubnetsmanaged = ElementIdentifier('show dhcp-server statistics',
                                            "  Total Subnets Managed         : ",
                                            ".*")
            def __init__(self,loo_commandlist):
                self.text = []
                self.attach_relevant_commandos(loo_commandlist)
                self.element = self.populateElement()
            def attach_relevant_commandos(self,loo_commandlist):
                ''' take full list of command output and find the one we
                want for this parser based on self.sourcecommand
                '''
                for cmd in loo_commandlist:
                    if cmd.command_human == self.sourcecommand:
                        self.text = cmd.sectionoutput
            def populateElement(self):
                ''' takes the command text in the specific command and 
                parses it to create the Element() 
                '''
                '''
                self.servername = ''
                self.serverstatus = ''
                self.numsubnetsmanaged = ''
                '''
                element = self.Element()
                logging.debug("SectionParser_ShowDhcpServerStatistics(): Length of element.text: " + str(len(self.text)))
                if len(self.text) > 1:
                    for line in self.text:
                        if self.id_servername.identifier.check_match(line):
                            element.servername = self.id_servername.identifier.give_group_value(line)

                        elif self.id_serverstatus.identifier.check_match(line):
                            element.serverstatus = self.id_serverstatus.identifier.give_group_value(line)

                        elif self.id_numsubnetsmanaged.identifier.check_match(line):
                            element.numsubnetsmanaged = self.id_numsubnetsmanaged.identifier.give_group_value(line)


                elif len(self.text) == 0:
                    # meaning the DHCP is probably turned off
                    logging.debug("SectionParser_ShowDhcpServerStatistics(): Setting 'element.serverstatus' = 'Disabled'")
                    element.serverstatus = "Disabled"
                return(element)
            def dump(self):
                msg = "SectionParser_ShowDhcpServerStatistics():\n\r"
                msg += self.element.dump()
                return(msg)
    ''' THIS IS INIT FOR TOP LEVEL PARSER_DHCP()'''
    def __init__(self,loo_commandlist):
        # now pull those commands involved in as objects along with their data
        self.commandos = self.attach_relevant_commandos(loo_commandlist)
        self.stats = None
        self.leases = None
        # now build the above properties with the custom class parsers
        #self.stats = self.TableParser_ShowDhcpServerLeases(self.commandos)
        self.stats = (self.SectionParser_ShowDhcpServerStatistics(self.commandos)).element
        self.leaselist = (self.TableParser_ShowDhcpServerLeases(self.commandos)).elementlist
        #self.leaselist = self.leases.elementlist
        #self.leaselist = self.leases.leaselist

        ''' Once dhcpparsers initialize, data looks like this '''
        ''' 
        SectionParser_ShowDhcpServerStatistics():
            SectionParser_ShowDhcpServerStatistics().Element():
                servername: 11.8.26.33
                serverstatus: Enabled
                numsubnetsmanaged: 1
        TableParser_ShowDhcpServerLeases:
            TableParser_ShowDhcpServerLeases.Element:
                ipaddr: 11.8.26.36
                mac: 00:30:ab:2b:99:15
                timegranted: FEB 03 14:31:47 2002
                timeexpires: FEB 04 14:31:47 2002
                typestring: DYNAMIC
            TableParser_ShowDhcpServerLeases.Element:
                ipaddr: 11.8.26.37
                mac: 00:30:ab:2b:98:c8
                timegranted: FEB 03 14:00:27 2002
                timeexpires: FEB 04 14:00:27 2002
                typestring: DYNAMIC
        '''
    def attach_relevant_commandos(self,loo_commandlist):
        ''' takes list of CommandOutput objects and matches 
        them up with the commandsinvolved list, pulls that list
        of objects and returns it. 
        '''
        templist = []
        for c in loo_commandlist:
            for ci in self.commandsinvolved:
                if ci == c.command_human:
                    templist.append(c)
        return(templist)
    def dump(self):
        msg = ''
        msg += "Parser_Dhcp():\n\r"
        msg += self.stats.dump()
        for lease in self.leaselist:
            msg += lease.dump()
        return(msg)

class DhcpGenerator_TypeContainer_ALU_SCS():
    ''' Takes a Parser_Dhcp() object 
    on init and then generates interface objects in 
    the format desired for the specific type of 
    network element. 
    '''
    def __init__(self,parserobj):
        self.parserobj = parserobj
        self.RealDhcp = TypeContainer_ALU_SCS.DhcpContainer
        self.dhcpcontainer = self.convertParserObj()
    def convertParserObj(self):
        ''' takes the parser object interfaces and turns them into the 
        interface type that we want for the specific typeModule
        '''
        '''
        new.dhcp.servername.value = '11.8.26.33'
        new.dhcp.serverstatus.value = 'Enabled'
        new.dhcp.numsubnetsmanaged.value = '1'
        new.dhcp.numleases.value = '3'
        alease = new.dhcp.Lease('1')
        alease.ipaddr.value = '11.8.26.36'
        alease.mac.value = '00:30:ab:2b:99:15'
        alease.timegranted.value = 'DEC 31 05:30:46 2001'
        alease.timeexpires.value = 'JAN 01 05:30:46 2002'
        alease.typestring.value = 'DYNAMIC'
        new.dhcp.leaselist.append(alease)
        '''
        #        imported as RealDhcp
        dhcpcontainer = self.RealDhcp()
        dhcpcontainer.servername.value = self.parserobj.stats.servername
        dhcpcontainer.serverstatus.value = self.parserobj.stats.serverstatus
        dhcpcontainer.numsubnetsmanaged.value = self.parserobj.stats.numsubnetsmanaged
        dhcpcontainer.numleases.value = str(len(self.parserobj.leaselist))
        for please in self.parserobj.leaselist:
            uid                                 = werd.genUID()
            alease                              = self.RealDhcp.Lease(uid)
            alease.ipaddr.value                 = please.ipaddr
            alease.mac.value                    = please.mac
            alease.timegranted.value            = please.timegranted
            alease.timeexpires.value            = please.timeexpires
            alease.typestring.value             = please.typestring
            dhcpcontainer.leaselist.append(alease)
        return(dhcpcontainer)
    def dump(self):
        try:
            return("DhcpGenerator_TypeContainer_ALU_SCS(): Length of self.dhcpcontainer.leaselist = " + str(len(self.dhcpcontainer.leaselist)))
        except:
            return("DhcpGenerator_TypeContainer_ALU_SCS(): No data in self.dhcpcontainer.leaselist")

class SectionParser_ShowConfigurationSnapshot():
    ''' Takes loo_commandlist as input and 
    parses it specifically for the 
    'show configuration snapshot' command on 
    the ALU 6450. Designed for sections of text
    without multiple sections.

    Holds a single Element() with properties.
    '''
    ########################################################

    sourcecommand = 'show configuration snapshot'
    
    ''' define all of the identifiers used in this Parser.
    Each identifer is a classed object. the first property
    describes which command the idenfier should be used for.
    The second element is the Identifier() object used for 
    detection
    '''
    # ElementIdentifier(sourcecommand, pattern for search, pattern for value)
    # none needed for the config parser
    '''
    id_servername = ElementIdentifier('show dhcp-server statistics',    
                                    "  DHCP Server Name              : ",
                                    ".*")
    '''
    def __init__(self,loo_commandlist):
        self.text = []
        self.attach_relevant_commandos(loo_commandlist)
    def attach_relevant_commandos(self,loo_commandlist):
        ''' take full list of command output and find the one we
        want for this parser based on self.sourcecommand
        '''
        for cmd in loo_commandlist:
            if cmd.command_human == self.sourcecommand:
                self.text = cmd.sectionoutput
    def dump(self):
        msg = "SectionParser_ShowConfigurationSnapshot():\n\r"
        msg += "\ttext = \n\r"
        for line in self.text:
            msg += "\t\t" + line
        return(msg)

class ConfigurationGenerator_TypeContainer_ALU_SCS():
    ''' Takes a SectionParser_ShowConfigurationSnapshot() object 
    on init and then generates interface objects in 
    the format desired for the specific type of 
    network element. 
    '''
    def __init__(self,parserobj):
        self.parserobj = parserobj
        self.RealConfig = TypeContainer_ALU_SCS.ConfigurationContainer
        self.configurationcontainer = self.convertParserObj()
    def convertParserObj(self):
        ''' takes the parser object interfaces and turns them into the 
        interface type that we want for the specific typeModule
        '''
        configurationcontainer = self.RealConfig()
        configurationcontainer.text.value = '\n\r'.join(self.parserobj.text)
        return(configurationcontainer)
    def dump(self):
        pass

class TableParser_ShowArp():
    ''' Takes a raw text table as input and 
    parses it specifically for the 
    'show arp' command on 
    the ALU 6450

    Holds list of Element() with properties
        that line up with the column headers.
    '''
    class Element():
        ''' Takes chunklist as input and
        parses the data into specific properties.
        '''
        def __init__(self,chunk):
            self.ip = chunk[0]
            self.mac = chunk[1]
            self.typestring = chunk[2]
            if '/' in chunk[3]:
                self.slotport = chunk[3]
                self.interface = ' '.join(chunk[4:6])
            else: # means there's something in the "flag" column
                self.slotport = chunk[4]
                self.interface = ' '.join(chunk[5:7])
        def dump(self):
            msg = '\tTableParser_ShowArp(): Element():\n\r'
            msg += "\t\tip: " + self.ip + "\n\r"
            msg += "\t\tmac: " + self.mac + "\n\r"
            msg += "\t\ttypestring: " + self.typestring + "\n\r"
            msg += "\t\tslotport: " + self.slotport + "\n\r"
            msg += "\t\tinterface: " + self.interface + "\n\r"
            return(msg)
    headers =   [   'ipaddr',
                    'hardwareaddr',
                    'type',
                    'flags',
                    'port',
                    'interface',
                    'name',
                ]
    sourcecommand = 'show arp'
    startatline = 4
    def __init__(self,loo_commandlist):
        self.texttable = []
        self.attach_relevant_commandos(loo_commandlist)
        self.texttable = self.stripextra(self.texttable)
        self.elementlist = self.parsedata()
    def attach_relevant_commandos(self,loo_commandlist):
        ''' take full list of command output and find the one we
        want for this parser based on self.sourcecommand
        '''
        for cmd in loo_commandlist:
            if cmd.command_human == self.sourcecommand:
                self.texttable = cmd.sectionoutput
    def stripextra(self,text):
        temp = []
        import re
        re_ip = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        for i,line in enumerate(text):
            re_ip_match = re.search(re_ip,line)
            if re_ip_match:
                temp.append(line)
        return(temp)
    def parsedata(self):
        temp = []
        for line in self.texttable:
            chunk = (line.split())
            if len(chunk) > 0 and chunk[0] != '':
                element = self.Element(chunk)
                temp.append(element)
        return(temp)
    def dump(self):
        msg = 'TableParser_ShowArp(): :\n\r'
        for e in self.elementlist:
            msg += e.dump()
        return msg

class ArpGenerator_TypeContainer_ALU_SCS():
    ''' Takes a TableParser_ShowArp() object 
    on init and then generates interface objects in 
    the format desired for the specific type of 
    network element. 
    '''
    def __init__(self,parserobj):
        self.parserobj = parserobj
        self.RealArp = TypeContainer_ALU_SCS.ArpTable.Arp
        self.arplist = self.convertParserObj()
    def convertParserObj(self):
        ''' takes the parser object interfaces and turns them into the 
        interface type that we want for the specific typeModule
        '''
        '''
        anarp = new.arptable.Arp('1')
        anarp.ip.value = '5.5.5.5'
        anarp.mac.value = 'ab:ab:ab:ab:ab:ab'
        anarp.typestring.value = 'DYNAMIC'
        anarp.slotport.value = '1/2'
        anarp.interface.value = 'vlan 1'
        new.arptable.arplist.append(anarp)
        '''
        arplist = []
        for parp in self.parserobj.elementlist:
            uid                                 = werd.genUID()
            #                                   imported as RealArp
            anarp                               = self.RealArp(uid)
            anarp.ip.value                      = parp.ip
            anarp.mac.value                     = parp.mac
            anarp.typestring.value              = parp.typestring
            anarp.slotport.value                = parp.slotport
            anarp.interface.value               = parp.interface
            arplist.append(anarp)
        return(arplist)
    def dump(self):
        try:
            return("ArpGenerator_TypeContainer_ALU_SCS(): Length of self.arplist = " + str(len(self.arplist)))
        except:
            return("ArpGenerator_TypeContainer_ALU_SCS(): No data in self.arplist")

class SectionParser_ShowAmap_RemoteHosts():
        ''' Takes loo_commandlist as input and 
        parses it specifically for the 
        'show amap' command on 
        the ALU 6450. Designed for sections of text
        without multiple sections.

        Holds a single Element() with properties.
        '''
        ########################################################
        class Chunk():
            ''' object for holding chunks of text marked by start/stop lines
            '''
            def __init__(self):
                self.startline = 0
                self.stopline = None
                self.chunkblock = []
            def dump(self):
                msg = ''
                msg += "SectionParser_ShowAmap_RemoteHosts().Chunk(): \n\r"
                msg += "\tstartline: " + str(startline) + "\n\r"
                msg += "\tstopline: " + str(stopline) + "\n\r"
                msg += "\tCHUNKBLOCK: \n\r"
                for line in self.chunkblock:
                    msg += "\t\t\t" + line
                return(msg)
        class Element():
            ''' Holds properties of remote hosts detected
            in the 'show amap' command
            '''
            def __init__(self):
                self.localslotport = ''
                self.localvlan = ''
                self.remotehostname = ''
                self.remotedevice = ''
                self.remotemac = ''
                self.remoteslotport = ''
                self.remotevlan = ''
                self.remoteips = []
            def dump(self):
                msg = '\t\tSectionParser_ShowAmap_RemoteHosts.Element():\n\r'
                msg += "\t\t\tlocalslotport: " + self.localslotport + "\r\n"
                msg += "\t\t\tlocalvlan: " + self.localvlan + "\r\n"
                msg += "\t\t\tremotehostname: " + self.remotehostname + "\r\n"
                msg += "\t\t\tremotedevice: " + self.remotedevice + "\r\n"
                msg += "\t\t\tremotemac: " + self.remotemac + "\r\n"
                msg += "\t\t\tremoteslotport: " + self.remoteslotport + "\r\n"
                msg += "\t\t\tremotevlan: " + self.remotevlan + "\r\n"
                msg += "\t\t\tremoteips: \r\n"
                for ip in self.remoteips:
                    msg += "\t\t\t\t Remote IP: " + ip + "\n\r"
                return(msg)
        sourcecommand = 'show amap'
        ''' define all of the identifiers used in this Parser.
        Each identifer is a classed object. the first property
        describes which command the idenfier should be used for.
        The second element is the Identifier() object used for 
        detection
        '''
        # ElementIdentifier(sourcecommand, pattern for search, pattern for value)
        id_amap_operstatus = ElementIdentifier('show amap',    
                                        "  Operational Status = ",
                                        ".*")
        # sample line "Remote Host 'HRP_Bobo_Warehouse_SW2_EER' On Port 1/3 Vlan 1 :"
        id_amap_remotehost_localslotport_localvlan_remotehostname = re.compile(
            "(Remote Host ')(?P<hostname>.*)(' On Port )(?P<slotport>.*)( Vlan )(?P<vlan>\d*)")

        id_amap_remotehost_remotedevice = ElementIdentifier('show amap',
                                        "  Remote Host Device      = ",
                                        ".*")
        id_amap_remotehost_remotemac = ElementIdentifier('show amap',
                                        "  Remote Base MAC         = ",
                                        ".*")
        id_amap_remotehost_remoteslotport = ElementIdentifier('show amap',
                                        "  Remote Interface        = ",
                                        ".*")
        id_amap_remotehost_remotevlan = ElementIdentifier('show amap',
                                        "  Remote Vlan             = ",
                                        ".*")
        # basically an IP regex with some leading spaces
        id_amap_remotehost_remoteip = re.compile(
            "   \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")

        def __init__(self,loo_commandlist):
            self.text = []
            self.attach_relevant_commandos(loo_commandlist)
            self.chunklist = self.chunkdata()
            self.elementlist = self.populateElements()
            self.operstatus = self.detect_operstatus()
            ''' Data looks like this
            SectionParser_ShowAmap_RemoteHosts:
                operstatus: enabled, 
                    SectionParser_ShowAmap_RemoteHosts.Element():
                        localslotport: 1/1
                        localvlan: 1
                        remotehostname: 
                        remotedevice: OS6450-10
                        remotemac: e8:e7:32:8b:86:cc
                        remoteslotport: 1/9
                        remotevlan: 1
                        remoteips: 
                             Remote IP:    11.1.214.100
                             Remote IP:    11.1.215.200
                    SectionParser_ShowAmap_RemoteHosts.Element():
                        localslotport: 1/2
                        localvlan: 1
                        remotehostname: 
                        remotedevice: OS6450-10
                        remotemac: e8:e7:32:87:40:16
                        remoteslotport: 1/9
                        remotevlan: 1
                        remoteips: 
                             Remote IP:    11.1.214.101
                             Remote IP:    11.1.215.201
            '''
        def attach_relevant_commandos(self,loo_commandlist):
            ''' take full list of command output and find the one we
            want for this parser based on self.sourcecommand
            '''
            for cmd in loo_commandlist:
                if cmd.command_human == self.sourcecommand:
                    self.text = cmd.sectionoutput
        def chunkdata(self):
            ''' Takes the full text block and breaks it up into chunks
            '''
            chunklist = []
            # first go through and find the start lines
            for i,line in enumerate(self.text):
                match_hostvlanslot = re.search(
                    self.id_amap_remotehost_localslotport_localvlan_remotehostname,line)
                if match_hostvlanslot:
                    chunk = self.Chunk()
                    chunk.startline = i
                    chunklist.append(chunk)
            # now go through again and find the stop lines
            for index,chunk in enumerate(chunklist):
                nextindex = index+1
                try:
                    # stop line for this chunk = start line of next chunk
                    chunk.stopline = chunklist[nextindex].startline
                except:
                    # unless we're at end of list in which case it's the end of the file
                    chunk.stopline = len(self.text)-1
                # now take thos text blocks and append them to the chunks
                for x in range(chunk.startline,chunk.stopline):
                    chunk.chunkblock.append(self.text[x])
            return(chunklist)

        def populateElements(self):
            ''' takes the command text in the specific command and 
            parses it to create the Element() 
            '''
            '''
            self.localslotport = ''
            self.localvlan = ''
            self.remotehostname = ''
            self.remotedevice = ''
            self.remotemac = ''
            self.remoteslotport = ''
            self.remotevlan = ''
            self.remoteips = []
            '''

            elementlist = []
            for chunk in self.chunklist:
                element = self.Element()
                for line in chunk.chunkblock:
                    # set up the non ElementIdentifier regexes
                    match_hostvlanslot = re.search(
                        self.id_amap_remotehost_localslotport_localvlan_remotehostname,line)
                    match_ip = re.search(self.id_amap_remotehost_remoteip,line)
                    
                    if match_hostvlanslot:
                        sp = match_hostvlanslot.group('slotport')
                        lv = match_hostvlanslot.group('vlan')
                        rh = match_hostvlanslot.group('hostname')
                        element.localslotport = sp
                        element.localvlan = lv.rstrip(' :\r\n')
                        element.remotehostname = rh
                    if match_ip:
                        ip = match_ip.group()
                        ip = ip.rstrip(' :\r\n')
                        ip = ip.strip(' ')
                        element.remoteips.append(ip)

                    elif self.id_amap_remotehost_remotedevice.identifier.check_match(line):
                        element.remotedevice = self.id_amap_remotehost_remotedevice.identifier.give_group_value(line).rstrip(', ')

                    elif self.id_amap_remotehost_remotemac.identifier.check_match(line):
                        element.remotemac = self.id_amap_remotehost_remotemac.identifier.give_group_value(line).rstrip(', ')

                    elif self.id_amap_remotehost_remoteslotport.identifier.check_match(line):
                        element.remoteslotport = self.id_amap_remotehost_remoteslotport.identifier.give_group_value(line).rstrip(', ')

                    elif self.id_amap_remotehost_remotevlan.identifier.check_match(line):
                        element.remotevlan = self.id_amap_remotehost_remotevlan.identifier.give_group_value(line).rstrip(', ')
                elementlist.append(element)
            return(elementlist)
        def detect_operstatus(self):
            operstatus = ''
            for line in self.text:
                if self.id_amap_operstatus.identifier.check_match(line):
                    operstatus = self.id_amap_operstatus.identifier.give_group_value(line)
            return(operstatus)
        def dump(self):
            msg = "SectionParser_ShowAmap_RemoteHosts:\n\r"
            msg += "\toperstatus: " + self.operstatus + "\n\r"
            for element in self.elementlist:
                msg += element.dump()
            return(msg)

class AmapGenerator_TypeContainer_ALU_SCS():
    ''' Takes a SectionParser_ShowAmap_RemoteHosts() object 
    on init and then generates interface objects in 
    the format desired for the specific type of 
    network element. 
    '''
    def __init__(self,parserobj):
        self.parserobj = parserobj
        self.RealAmap = TypeContainer_ALU_SCS.AmapContainer
        self.amap = self.convertParserObj()
    def convertParserObj(self):
        ''' takes the parser object interfaces and turns them into the 
        interface type that we want for the specific typeModule
        '''
        '''
        anamap = new.AmapContainer()
        anamap.amapstatus = 'enabled'

        aremotehost = anamp.RemoteHost('1485851')
        aremotehost.localslotport.value = '1/1'
        aremotehost.localvlan.value = 'vlan 1'
        aremotehost.remotehostname.value = 'SOME_SWITCH'
        aremotehost.remotedevice.value = 'OS6450-10'
        aremotehost.remotemac.value = 'ab:ab:ab:ab:ab:ab'
        aremotehost.remoteslotport.value = '1/9'
        aremotehost.remotevlan.value = 'vlan 1'

        aremotehost_ip = aremotehost.RIpList.Rip()
        aremotehost_ip.value = '11.4.67.123'
        aremotehost.remoteips.riplist.append(aremotehost_ip)

        anamap.amaplist.append(aremotehost)
        new.amap = anamap
        '''
        anamap = self.RealAmap()
        anamap.amapstatus.value = self.parserobj.operstatus
        for prh in self.parserobj.elementlist:
            uid                                 = werd.genUID()
            #                                   imported as RealArp
            aremotehost                         = anamap.RemoteHost(uid)
            aremotehost.localslotport.value     = prh.localslotport
            aremotehost.localvlan.value         = "vlan " + prh.localvlan
            aremotehost.remotehostname.value    = prh.remotehostname
            aremotehost.remotedevice.value      = prh.remotedevice
            aremotehost.remotemac.value         = prh.remotemac
            aremotehost.remoteslotport.value    = prh.remoteslotport
            aremotehost.remotevlan.value        = "vlan " + prh.remotevlan
            for rip in prh.remoteips:
                aremotehost_ip                              = aremotehost.RIpList.Rip()
                aremotehost_ip.value                        = rip
                aremotehost.remoteips.riplist.append(aremotehost_ip)
            anamap.amaplist.append(aremotehost)
        return(anamap)
    def dump(self):
        try:
            return("AmapGenerator_TypeContainer_ALU_SCS(): Length of self.amap.amaplist = " + str(len(self.amap.amaplist)))
        except:
            return("AmapGenerator_TypeContainer_ALU_SCS(): No data in self.amap.amaplist")