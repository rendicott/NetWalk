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

In the main() method we're initially setting up the name of the function with 'myfunc'
and giveupthefunc(). We use this so we can log the function name in the debug log
which makes it easer to locate troubles when the log shows exceptions. Immediately
after that we're jumping into the parseXMLInput() function which lives inside the
nwProcessInput.py file. So let's go take a look and see what the parseXMLInput()
function does.

First we open the input XML file which is attached to a property of the Cfg() object
named 'werd'. That was set up during the inital program load when it was processing
input arguments. We're going to process that XML file and turn it into one big 
string. From there we initiate the ElementTree library (ET) and tell it to process
the XML string and store it in a variable called 'tree'. As long as there are no
errors we'll start looping through the various layers of the XML and assigning
temporary variables until we have enough information to create some of our custom
objects. 

So if we go all the way down to the bottom of the function we see where it's 
creating a new "nwClasses.Target" object which is defined in the nwClasses.py
file. If you look at that class and it's __init__ method you'll see that it needs
three input parameters before it will let you create a Target--the target id number,
a list of Entrypoint objects, and a list of Auth objects. The Entrypoint and Auth
objects are also defined in nwClasses.py and are custom to NetWalk. The Entrypoint
and Auth objects are created within the ElementTree 'tree' walk in the above loops.
When it's all said and done you have one big "Target" class object which we can
use to start the actual crawling. We take this Target and attach it to the 'werd'
Cfg() object and call it 'werd.loo_targets' which stands for "list of objects_targets".
I try to name any list that contains custom objects with the "loo_" prefix which
helps me understand how to handle things while I'm walking through loops. 

So the main things that the nwProcessInput.parseXMLInput() function does are:
--process the input XML
--Create various custom objects from the parsed XML:
----Entrypoint objects
----AuthPossibility objects
----Target objects
----Member objects

So now, back to the main() method of nw.py: We log some data and then we jump
in and start looping through that list of Targets that we just built. The first 
thing we do is to launch nwCrawl.burrow() and assign all results to 'crawlresults'.
The nwCrawl.burrow() function is what launches all aspects of the crawler and it's
where the real work happens. We'll go into that in a minute but we'll finish up
this main() method first. After the crawl is completed all we really do is
take the xml and write it to disk and do some logging. 

So now let's take a look at that nwCrawl.burrow() function in the nwCrawl.py file.
Within burrow() we'll first set up a flag as false so at some point we can flag
as true and exit the while loop. Inside the while loop we'll first check to make 
sure we're not at the max crawl depth yet and then kick of nwCrawl.primerBrain().

So the main things the nwCrawl.burrow() function does are:
--Kick off primerBrain() which does the crawling on the current target.
--create a new CrawlResults object and store the crawl results in currentCrawl
--kick off initializeNetworkElements() to create NetworkElement objects from crawl results
--look for more targets to crawl
--run the peckingOrder() function on the current crawl results to establish relationships

So let's take a look at primerBrain():
primerBrain() takes a Target object as the input parameter and starts to work
on it. It starts by looping through the list of Entrypoints attached to the 
Target. For each Entrypoint it keeps working on it until the 'entryfinished' 
flag is set. The whole time it's working on the Entrypoint it's checking 
various flags. The main flags it's checking are:
--entry.reachable: 
----this will get set if for some reason the entry is unreachable (e.g., it's a
----bogus IP address or some other situation that is impossible to work around)
--entry.directfailed:
----This will get set if the entrypoint can't be reached directly from the 
----jump server. This doesn't necessarily mean the entrypoint is unreachable
----so we want to flag it and try it again after first logging into another
----entrypoint (i.e., hopping).
--entry.primersuccess:
----This will get set if the primer script (e.e., primer-ALU-7705-6450.exp) was
----successful. This will tell us a lot of things like if the entrypoint is 
----reachable. But if the primer fails it doesn't mean we give up as long as the
----entrypoint is 'reachable'.
So if various combinations of these parameters are set the primerBrain() will
either set the 'entryfinished' flag to True and go back to burrow() or it will
keep kicking off the primerDriver() function until it can set the 'entryfinished'
flag to True. 

Now we'll look at the primerDriver() function. This function takes a Target and
Entrypoint object and works on it until it gets a 'primersuccess' flag set to 
True or it reaches 5 cycles. It starts by feeding the current Entrypoint object
into the adjustAuth() function which somewhat of a learning algorithm to find
the best password based on previous successes. After it adjusts the authentication
for this round it runs the buildExpectCommand() function with the Entrypoint 
object as input. The buildExpectCommand() takes the entry point and based on
it's authentication, whether it needs hops/direct, and whether it's building
a primer or a self-generated Expect script it will build the string required
to kick off the expect script. For example: it would build a string like this:

"/usr/bin/expect primer-ALU-7705-6450.exp 11.5.160.145 22 admin p4ssw0rd 8"

and store it in Entrypoint.primercommand property. After building the command the
primerDriver() function kicks it off with the runoscommand() function which basically
just runs an os.popen(COMMAND) using whatever command string you fed it. The results
from that runoscommand() come back in the form of a list of result lines.

Now we have some results from the OS command we ran so that's great but now we
need to read that data and determine whether or not we can use it or if we need
to try and pull it again. So first we'll set some flags up like 'directmightfail'
and 'sleepandtryagain'. This way we can set these flags if we see something we
don't like in the results. Now that we have these flags set we can kick off the 
schemaModule.outputInspector() function. This is stored in the schemaModule which 
sounds strange but I'll explain:
---I wanted to keep vendor specific stuff out of the main body of the NetWalk code
---so that the entire thing was as vendor neutral as possible. This way the core
---NetWalk could later be improved to support different vendors. Since reading things
---like the output results from commands run against an Alcatel-Lucent switch are
---very unique to that particular type of equipment I wanted to keep the code that
---reads it separated from the core code. For example, all of the code that is
---Alcatel-Lucent specific is stored in the following files: nwParser_ALU_7705_6450.py,
---nw_NE_Type_SCR_7705.py, and nw_NE_Type_SCS_6450.py
---Rather than reference these files by name I simply import them and reference
---them as "schemaModule". This way I can write modules for different vendors and
---the core code doesn't really change. So for Alcatel-Lucent when I say 
---schemaModule.outputInspector() I'm referring to the outputInspector() function
---inside the nwParser_ALU_7705_6450.py file. The current working schemaModule
---is set within the nwConfig.py file with the following line:
---
---         schemaModule = 'nwParser_ALU_7705_6450'
---
---
So anyways, back to the priverDriver() function...so what we're doing now is 
kicking off the outputInspector() function and telling it to return things like
entry.reachable, authsuccess, sleepandtryagain, and deletesshkeys. Based on the 
output of the inspector we'll set these variables. All we feed into the outputInspector
is the results from the primer output that's stored in entry.primeroutput. 

Now that that's out of the way we'll take a look at the outputInspector() function:
This function takes a list of text and examines it to pull some specific information.
Since the text it's examining is quite specific it lives in the nwParser_ALU_7705_6450
module rather than the main code base. The first thing it does is set up the
regular expression strings so it can detect patterns. Then it goes line by line
in the text looking for matches for those regular expresions. Based on what it
finds it sets certain flags like 'reachable','authsuccess', 'sleepandtryagain',
and 'deletesshkeys'. It returns those flags back to the calling function 
(e.g., primerDriver()). So the main objective of the outputInspector() is to 
determine whether or not the results of an Entrypoint's primer output look normal
or need to be pulled again. The primerDriver() uses this information to determine
whether or not it can flag the entry as finished or if it needs to resubmit it.

So now back to nwCrawl.primerDriver() and we see what primerDriver() does with 
the results. So if the output shows that we have a bad RSA key for an SSH host
we kick off the delete_ssh_keys() function to reset them. If we detected that
the entrypoint is reachable but 'directfailed' we set that flag so that on 
the next loop primerDriver() can rebuild the Expect command to try and go through
another known working element and "hop" instead. We can also take note of the 
'authsuccess' flag and on the next loop use adjustAuth() to change which one of the
password possibilities we're using. Sometimes we just get a message back from the
primer that means the remote network element isn't ready for an SSH session as 
opposed to a straight refusal. In this case we set a flag to 'sleepandtryagain'
and run the nwCrawl.sleeper() function which waits for a configurable period of 
time before primerDriver() tries to run the primer script again. Otherwise, if
everything worked and all the flags are set properly we return the Entrypoint
object back to primerBrain() with all of it's information about how reachable it
is. 

Back in primerBrain() we either kick off another round of primerDriver() or 
set the 'entryfinished' flag to stop the while loop depending on whether or not
the primer was successful. If everything was successful we jump back to burrow().

Now back in burrow() we set up a new nwClasses.CrawlResults object to store 
the crawl results now that we actually have something to store. This object is 
what will eventually hold all of our fancy NetworkElement objects that we parse
out of the raw text data we're getting back from switches and routers. Now that 
we have a place to store our fancy objects we kick off the initializeNetworkElements()
function and the real magic starts to happen. 

Inside the initializeNetworkElements() function we receive a Target object and a
CrawlResults object as input parameters. From there we loop through the Entry 
objects attached to the Target object's list of Entrypoint objects. As long as the 
current Entry object has the 'primersuccess' flag set to True we send the Entry
object into the createBaseNE() function. 

Within the createBaseNE() function we start to look at some interesting data
coming back from the network element we ran the primer against. First we have to
initialize a brand new nwClasses.NetworkElement object. When creating a new one
we have to give it a unique ID number. Rather than guess a number we call on the
neIdRequest() method of the Cfg() class (werd.neIdRequest()) to create one for 
us so we don't have to worry about making duplicate ID numbers. Now that we have
an empty NetworkElement object we can start to set its properties based on some
of the info that came back from the primer script. However, since nwCrawl and the 
base NetWalk core has no idea how it's supposed to read the lines in the primer
it calls on a function within the schemaModule() to handle the parsing for it. To
do this it calls on schemaModule.fetchBaseNEdata() and sends it the current Entry
objects 'primeroutput' text list along with the full Entry object. In return it asks
for the fetchBaseNEdata() function to just tell it what the 'hostname' is and what
the 'typestring' is supposed to be. The 'type' concept is supposed to be a 
customizable field so the NetworkElement object has some idea of a way to tag 
the object with a human readable type. For example, a small cell switch is often
referred to as an 'SCS' and a small cell router is an 'SCR'. 

So if we go and look at the schemaModule.fetchBaseNEdata() function:
All this function is doing is kicking off two other functions: detectNEtype() and
detectNEhostname(). All these two sub functions are doing are taking the text 
within the primer output and scanning it to find the hostname...
