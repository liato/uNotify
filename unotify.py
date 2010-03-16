#!/usr/bin/env python
import imp
import json
import os
import re
import urllib2
import shlex
import subprocess
import sys
import time
from pprint import pprint

AUTHKEY = None
COMPLETED = {}
SETTINGS = {}

config_name = os.path.join(sys.path[0], 'config.py')
if not os.path.isfile(config_name):
    print >> sys.stderr, 'Error: No config(.py) file found.'
    sys.exit(1)

for key, val in imp.load_source('settings', config_name).__dict__.iteritems():
    if not key.startswith('__'):
        SETTINGS[key] = val
        
for m in SETTINGS['matchers']:
    try:
        r = re.compile(m[0], re.I)
        m[0] = r
    except re.error, e:
        print >> sys.stderr, 'Error while compiling regex: %r' % m[0]
        print >> sys.stderr, 'Error message: %s' % e
        sys.exit(1)

BASEURL =  'http://%s:%s/gui/' % (SETTINGS.get('host','localhost'),
                                  SETTINGS.get('port','5112'))

pwm = urllib2.HTTPPasswordMgrWithDefaultRealm()
pwm.add_password(None, BASEURL, SETTINGS.get('username',''),
                 SETTINGS.get('password',''))
opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(pwm))
try:
    AUTHKEY = opener.open('%stoken.html' % BASEURL)
except urllib2.HTTPError, e:
    if e.code == 401:
        print >> sys.stderr, "Invalid username or password. Edit your config file and try again."
    else:
        print >> sys.stderr, e
    sys.exit(1)

AUTHKEY = re.sub('<[^>]+>', '', AUTHKEY.read()).strip()


data = opener.open("%s?list=1&token=%s" % (BASEURL, AUTHKEY)).read()
data = json.loads(data)
for t in data['torrents']:
    if t[4] == 1000:
        COMPLETED[t[0]] = t[2]
print '%d of %d torrents completed.' % (len(COMPLETED), len(data['torrents']))
time.sleep(SETTINGS.get('interval', 1)*60)

while True:
    try:
        data = opener.open("%s?list=1&token=%s" % (BASEURL, AUTHKEY)).read()
        data = json.loads(data)
        for t in data['torrents']:
            if t[4] == 1000:
                if t[0] not in COMPLETED:
                    print "%s has been downloaded." % t[2]
                    for matcher, commands in SETTINGS.get('matchers', []):
                        if matcher.search(t[2]):
                            for command in commands:
                                print 'Executing: %r' % command
                                command = command.replace('$torrent', t[2]).replace('$id', t[0]).replace('$size', str(t[3]))
                                subprocess.Popen(command)
                COMPLETED[t[0]] = t[2]
    except urllib2.HTTPError, e:
        print e
        print e.read()
    
    time.sleep(SETTINGS.get('interval', 1)*60)