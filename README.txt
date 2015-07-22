---NetWalk-----
This program was created by Russell Endicott 
for the purpose of crawling remote switches 
and routers through an SSH interface in order to 
determine network topoplogy and various other
configurations of interest.

It's XML driven in that it expects an input XML
for targets to crawl and returns an XML based
toplogy.

Written by Russell Endicott (rendicott@gmail.com)
----------------

1. Limitations
2. Background
3. Usage
4. Debugging
5. Helper tools
6. Assistance


-=-=-=-=-=-=-=-=- LIMITATIONS -=-=-=-=-=-=-=-=-

Currently the NetWalk crawler only supports crawling one type of switch:

    --- Alcatel-Lucent 6450 Omniswitch

I started to work in the support for the Alcatel Lucent SAR-H 7705 router but
haven't finished yet. 

I tried to design the code so that it was vendor agnostic and all of the vendor
stuff is stored in modules. So that way I can write modules/parsers for each specific
type of equipment. 

-=-=-=-=-=-=-=-=- BACKGROUND -=-=-=-=-=-=-=-=-

This tool was originally created due to the absence of an EMS (Element Management System)
for the small cell switches and routers in the live network. It was designed to address
the issues surrounding break-fix on remote small cell deployments and to aid in locating 
specific equipment on the remote LAN in order to reboot the correct small cell. 

In addition we decided it would be nice to collect more information from the switches and
routers while we were in there crawling the network. The goal is to reach out over a common
interface (i.e., SSH since SNMP and other protocols are not always available) and query the
network elements for as much information as possible by running 'show' commands. The data is
then parsed into an object class structure and some simple logic is run against the objects.
If the result of that analysis is that there are probably more unknown objects reachable on
the same network then another round of discovery crawls is generated and analyzed until we
run out of network elements.

At the end we churn through the full population of discovered network elements and try to build
a parent/child relationship structure. Once this structure is generated and duplicates are removed
it's all dumped into an XML file and the program exits. The ultimate goal of the 'XML in, XML out'
model is that it would eventually be turned into a SOAP API or something easier to use than files.


-=-=-=-=-=-=-=-=- USAGE -=-=-=-=-=-=-=-=-

First of all you'll need to find a Linux server that has open internet access. This was always done
from the 'Small Cell Jump Server' but it could be run from a laptop if you're in out in the wild 
somewhere. Essentially you just need a machine that can run Python and Expect scripts and SSH out to
public IP's.

At the minimum you'll need to copy the following files to a directory on the 'jump' server:

        -rw-r----- 1 russ grouper   27591 May  5 09:14 nwClasses.py
        -rw-r----- 1 russ grouper    6189 Apr 28 23:37 nwConfig.py
        -rw-r----- 1 russ grouper   51206 May 21 15:45 nwCrawl.py
        -rw-r----- 1 russ grouper     120 Mar 20 15:34 nw_NE_Type_SCR_7705.py
        -rw-r----- 1 russ grouper  147195 Apr 27 16:01 nw_NE_Type_SCS_6450.py
        -rw-r----- 1 russ grouper    6575 May 20 12:51 nwOrchestrator.py
        -rw-r----- 1 russ grouper    5180 Apr 27 09:48 nwOUIexplorer.py
        -rw-r----- 1 russ grouper   62468 Jun  4 14:11 nwParser_ALU_7705_6450.py
        -rw-r----- 1 russ grouper   12804 Apr 27 09:42 nwProcessInput.py
        -rw-r----- 1 russ grouper   10416 Apr 29 09:41 nw.py
        -rw-r----- 1 russ grouper 3470344 Apr 16 12:36 oui-database.txt
        -rw-r----- 1 russ grouper     967 Apr 23 12:49 primer-ALU-7705-6450.exp
        -rw-r----- 1 russ grouper    1661 Apr 23 12:50 primer-hop1-ALU-7705-6450.exp
        -rw-r----- 1 russ grouper    2756 Apr 23 12:50 primer-hop2-ALU-7705-6450.exp

So that's essentially:
        -- all of the .py files
        -- the three primer expect scripts
        -- the OUI database txt file

Now if you get to command line in that directory on the server you can start using the crawler. 

Usage is pretty straightforward. If you run the 'nw.py' script like so:

        python nw.py --help

You'll get some usage assistance like so:

        Usage: nw.py [--help] [--debug] [--printtostdout] [--logfile] [--inputfile] [--outputfile]

        Options:
          --version             show program's version number and exit
          -h, --help            show this help message and exit
          -i FILE, --inputfile=FILE
                                This XML file contains the information needed to kick
                                off the crawler. Includes target IP's and possible
                                usernames/passwords. Refer to 'sample-input.xml' for
                                example usage.
          -o FILE, --outputfile=FILE
                                This is the desired output filename that will contain
                                the output topology XML. Default is 'output.xml'

          Debug Options:
            -d DEBUG, --debug=DEBUG
                                Available levels are CRITICAL (3), ERROR (2), WARNING
                                (1), INFO (0), DEBUG (-1)
            -p, --printtostdout
                                Print all log messages to stdout
            -l FILE, --logfile=FILE
                                Desired filename of log file output. Default is
                                "nw.log"
            -f FILE, --fromfile=FILE
                                This adds option to load crawlResults from file
                                instead of doing an actual crawl. Useful for testing
                                relationship parsing. Default is "crawlresults.pkl"

So your basic usage would be:

        python nw.py -i INPUTXMLFILE.XML -o OUTPUTXMLFILE.XML

So it sounds like we need to figure out how to make an input XML file.
That's simple enough. If you look at some of the sample-input XML files that
*should* have been included in the code files you can get a feel for what
the structure should look like. Let's take a look at the 'sample-input.xml'
file. 

        <?xml version="1.0" encoding="utf-8"?>
        <root>
          <target id="1">
            <!-- REQUIRED -->
            <!-- All targets need at least one entrypoint 
                and auth possibility at a bare minimum. Currently with NETWALK 
                v0.5: The parent/child relationship logic will not work if 
                entrypoints from multiple unrelated sites are submitted for a single target.  -->
            <entrypoint id="1">
              <attributes>
                <ipaddr>11.216.26.33</ipaddr>
        ........

If you go through that XML you'll see that it has comments so you can get a feel
for what each field means. At the bare minimum you'll need to change the IP address
for at least one entrypoint in the 'entrypoint' section and you'll need to 
change the usernames and passwords in the 'possibilities' section.

    NOTE: The usernames and passwords are handled in a 'give me a list of possibilities
    and I'll try them until I find one that works' model. This was due to the way the 
    various small cell switches and routers were deployed. There is a mixture of 'standard'
    username/password combinations out on the network. When NetWalk is first running the 
    primer scripts on the IP addresses that it finds it makes a note of which uname/pword
    combination works for a particular network element. For each successful combination 
    it adds weight to that combination moving forward so that it's used first on all the following
    network elements for that crawl. 

So you're most basic input XML would look like this:

        <?xml version="1.0" encoding="utf-8"?>
        <root>
          <target id="1">
            <entrypoint id="1">
              <attributes>
                <ipaddr>11.8.221.193</ipaddr>
                <port>22</port>
              </attributes>
            </entrypoint>
            <auth>
              <possibility id="1">
                <username>admin</username>
                <password>myP4ssW0rd</password>
              </possibility>
            </auth>
          </target>
        </root>

If you saved this above basic XML chunk as 'myfirstcrawl-input.xml' then 
you could launch a crawl like this:

        python nw.py -i myfirstcrawl-input.xml -o myfirstcrawl-output.xml

If everything was successful you wouldn't see very much happening on the screen but
eventually the script would end and you'd have an output xml file sitting on disk. 
Take a look at the 'sample-output.xml' that was included in the code files package
for exhaustive structure details and commentary. 

But let's jump into the debugging section so we can start to get a feel for what the
crawler is doing when it 'crawls'.


-=-=-=-=-=-=-=-=- DEBUGGING -=-=-=-=-=-=-=-=-

The nw.py script has debugging options that will let us watch what the crawler is doing
during the crawl. Take the above example from the USAGE section of this guide--instead of
running this command:

        python nw.py -i myfirstcrawl-input.xml -o myfirstcrawl-output.xml

We can run the same with debugging enabled like this:

        python nw.py -i myfirstcrawl-input.xml -o myfirstcrawl-output.xml -d -1 -p

The '-d' means that we want to specify the debug level. The '-1' means we want the lowest
debug level (i.e., DEBUG) which will enable ALL of the debug messages in the code. The '-p'
means we want to print the output to the screen. Also, the nw.py script will always write to 
a log file no matter what level you specify. By default this is the 'nw.log' file in the 
current directory but you can change it if you want (Check the --help options).

The basic format of the debug messages is as follows:

        TIMESTAMP:DEBUGLEVEL:FUNCTION_NAME  MESSAGE

For example:

    2015-05-05 14:08:02,561:DEBUG:<function adjustAuth at 0x1b5fa28>    have list of auth possibilities length: 4

Would mean that the message was logged on May 5th, 2015 at 14:08 with 'DEBUG' level 
(vs. WARNING or CRITICAL) from the 'adjustauth' function with a message of 
'have list of auth possibilities length: 4'

Not all the lines in the log follow this format but most do. 

-=-=-=-=-=-=-=-=- HELPER TOOLS -=-=-=-=-=-=-=-=-

In addition to the basic flow of nw.py there are a couple 
of helper scripts that were designed to make the running 
of the program easier. 

{{{{{{{{{{{{{{{{{ nwOrchestrator.py }}}}}}}}}}}}}}}}}

So I realize that running the script with the 'input file / output file' method
is bulky and annoying so I made another script called 'nwOrchestrator.py' that 
makes running large groups of crawls much easier.

When you run 'python nwOrchestrator.py' it looks in the current directory for 
any input xml files with the 'nwinput-XXXXXXXXXXXXX--' format, modifies them
to add the normal small cell SCS passwords and runs them into the 'nw.py' script.

You'll have to modify the nwOrchestrator.py script to add your own passwords.

So let's say you had an input XML file in the directory that looked like this:

        nwinput-1-Macquarie_31_32--20150422_151105.xml

It would run the nw.py script like this:

        python nw.py -i nwinput-1-Macquarie_31_32--20150422_151105.xml -o 20150505_141403-Macquarie_31_32.xml -d -1 -p -l 20150505_141403-Macquarie_31_32.log

It assumes the part between 'nwinput' and the '--' is the description (e.g., nwinput-<DESC>--20150422_151105.xml )
and uses it as the description section for the rest of the files involved for that crawl

And at the end it would take all of the expect scripts, the log file, and the expect output logs and zip them up into this file:

        20150505_141403-SUCCESS-Macquarie_31_32.zip

When it's done it keeps going until it runs out of input files. So at the end you'd end up with a
directory full of output XML's and zipped up log files. This makes it easier for large bulk crawls.
The only drawback is that you're storing usernames and passwords in the nwOrchestrator.py file.

{{{{{{{{{{{{{{{{{ nw_offline.py }}}}}}}}}}}}}}}}}

Find the nw_offline.py file and copy it to another directory along with the oui-database.txt file.

Copy the expect output log files from a successful crawl into the directory like this:

        07/21/2015  11:37 AM    <DIR>          .
        07/21/2015  11:37 AM    <DIR>          ..
        05/05/2015  02:06 PM            28,271 expect---23469---GOA_P10-4.sh-output.log
        05/05/2015  02:07 PM            37,228 expect---63927---GOA_P10-4.sh-output.log
        05/05/2015  02:07 PM            37,085 expect---67911---GOA_P10-6.sh-output.log
        05/05/2015  02:07 PM            37,227 expect---71191---GOA_P10-1.sh-output.log
        05/05/2015  02:06 PM            38,997 expect---71395---SCSR--1-GOA_C-9709365834---GOA_P10-3.sh-output.log
        05/05/2015  02:04 PM            38,135 expect---95526---SCSR--1-GOA_C-9709365834---GOA_P10-2.sh-output.log
        05/05/2015  01:58 PM            71,570 expect---97115---GOA_MAIN.sh-output.log
        05/05/2015  02:08 PM            37,173 expect---99923---GOA_P10-5.sh-output.log
        07/21/2015  11:33 AM            11,645 nw_offline.py
        07/21/2015  09:19 AM         3,600,495 oui-database.txt

Run the offline script like this:

        python nw_offline.py -d -1 -p

It will churn through the expect output logs and process the data into NetworkElement objects.

So you can tweak the code so that you could run an IDLE session on the offline files
and be able to poke around in the currentCrawl.loo_ne list of network elements objects. 


-=-=-=-=-=-=-=-=- ADVANCED DEBUGGING -=-=-=-=-=-=-=-=-

In this section we'll go over how the program works so it's easier to follow 
the debug logs.

So in the nw.py file we're importing all of the various modules we need.
Then we're pulling a custom Cfg() class from the nwClasses.py module that was 
initiated as "werd". It's just a placeholder name for what I call the global
config for the modules. If I import this object within all of the modules I can 
basically have global variables that can be passed around as needed.

This 'werd' Cfg() object stores things like the input and output file names and
holds methods for generating incremental numerical identifiers, etc. 

After that we'll import our other NetWalk modules from the other .py files and jump
into the if __name__ == '__main__': function way at the bottom of nw.py.

In this section we're just setting up the logging. Most of this comes from the 
standard 'optparse' packages and 'logging' which I didn't write. After all of the
options are processed and the log files are set up we'll hit the main() method.

In the main() method we're 

