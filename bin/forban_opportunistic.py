import glob
import os.path
import sys
import string
import time
import ConfigParser
import re
config = ConfigParser.RawConfigParser()
config.read("../cfg/forban.cfg")
forbanpath = config.get('global','path')
forbanshareroot = config.get('forban','share')

sys.path.append(forbanpath+"lib/")
import index
import loot
import fetch
import base64e

if not config.get("global","mode") == "opportunistic":
    print "not configured in opportunistic mode"
    exit(1)


forbanpath = config.get('global','path')
try:
    announceinterval = config.get('global','announceinterval')
except ConfigParser.NoOptionError:
    announceinterval = 10

announceinterval = float(announceinterval)


ofilter = config.get('opportunistic','filter')
print "applied regexp filter: %s" % ofilter
refilter = re.compile(ofilter, re.I)
discoveredloot = loot.loot()
allindex = index.manage()
allindex.build()

while(1):

    for uuid in discoveredloot.listall():
        # fetch the index of all discovered and recently announced loots
        # allowing to compare local loot to announced loot
        if discoveredloot.exist(uuid) and discoveredloot.lastannounced(uuid):
            allindex.cache(uuid)

        if not discoveredloot.lastannounced(uuid):
            print "%s (%s) not seen recently, skipped" % (discoveredloot.getname(uuid),(uuid))
            continue

        missingfiles = allindex.howfar(uuid)

        if not missingfiles or (discoveredloot.whoami() == uuid):
            print "missing no files with %s (%s)" % (discoveredloot.getname(uuid),uuid)
        else:
            for missedfile in missingfiles:
                if re.search(refilter, missedfile):
                    sourcev4 = discoveredloot.getipv4(uuid)
                    url =  """http://%s:12555/s/?g=%s&f=b64e""" % (sourcev4, base64e.encode(missedfile))
                    localfile = forbanshareroot + "/" + missedfile
                    localsize = allindex.getfilesize(filename=missedfile)
                    remotesize = allindex.getfilesize(filename=missedfile,uuid=uuid)
                    if localsize < remotesize:
                        print "local file smaller - from %s fetching %s to be saved in %s" % (uuid,url,localfile)
                        fetch.urlget(url,localfile)
                    elif localsize is False:
                        print "local file not existing - from %s fetching %s to be saved in %s" % (uuid,url,localfile)
                        fetch.urlget(url,localfile)
                    elif remotesize is False:
                        print "remote file index issue for %s on loot %s" % (missedfile, uuid)
                    else:
                        print "local file larger or corrupt %s - don't fetch it" % (localfile)
                    allindex.build()

    time.sleep(announceinterval*(announceinterval/(announceinterval-2)))

