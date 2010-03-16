#!/usr/bin/env python
import datetime
import imp
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib2

COMPLETED = {}
SETTINGS = {}
INITIATED = False
VERBOSE = True

class WebUIOpener(object):
    def __init__(self, opener, settings):
        self.opener = opener
        self.baseurl =  'http://%s:%s/gui/' % (settings.get('host','localhost'),
                                      settings.get('port','5112'))
        self.authkey = None
    
    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            return getattr(object.__getattribute__(self, 'opener'), attr)
    
    def open(self, fullurl, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        if self.authkey:
            fullurl = '%s?token=%s&%s' % (self.baseurl, self.authkey, fullurl)
        else:
            fullurl = '%s%s' % (self.baseurl, fullurl)
            
        return self.opener.open(fullurl, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT)

    def set_authkey(self, authkey):
        self.authkey = authkey


def log(message, output = sys.stdout):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    f = open(os.path.join(sys.path[0], 'unotify.log'), 'a')
    if VERBOSE:
        print >> output, '[%s] %s' % (ts, message)
    f.write('[%s] %s\n' % (ts, message))
    f.close()


def getURLOpener(SETTINGS):
    baseurl =  'http://%s:%s/gui/' % (SETTINGS.get('host','localhost'),
                                      SETTINGS.get('port','5112'))
    pwm = urllib2.HTTPPasswordMgrWithDefaultRealm()
    pwm.add_password(None, baseurl, SETTINGS.get('username',''),
                     SETTINGS.get('password',''))        
    handler = urllib2.HTTPBasicAuthHandler(pwm)        
    opener = urllib2.build_opener(handler)
    opener = WebUIOpener(opener, SETTINGS)
    while True:
        try:
            authkey = opener.open('token.html')
            break
        except urllib2.HTTPError, e:
            if e.code == 401:
                log("Invalid username or password. Edit your config file and try again.", sys.stderr)
                sys.exit(1)
        except urllib2.URLError, e:
            if e.reason.errno == 10061:
                log('Unable to connect to the web ui. Retrying in 5 minutes.', sys.stderr)
                time.sleep(300)
        except Exception, e:
                log('Unknown error: %s' % e, sys.stderr)
                sys.exit(1)
                
    authkey = re.sub('<[^>]+>', '', authkey.read()).strip()
    log('Found new auth token (%s).' % authkey)
    opener.set_authkey(authkey)
    return opener

commandparams = [('id', 0),
                 ('status', 1),
                 ('name', 2),
                 ('torrent', 2),
                 ('size', 3),
                 ('downloaded', 5),
                 ('uploaded', 6),
                 ('label', 11)]
    


if __name__ == '__main__':
    try:
        config_name = os.path.join(sys.path[0], 'config.py')
        if not os.path.isfile(config_name):
            log('Error: No config(.py) file found.', sys.stderr)
            sys.exit(1)
        
        for key, val in imp.load_source('settings', config_name).__dict__.iteritems():
            if not key.startswith('__'):
                SETTINGS[key] = val
        VERBOSE = SETTINGS.get('verbose', True)

        log('uNotify is starting up.')

        for m in SETTINGS['matchers']:
            try:
                r = re.compile(m[0], re.I)
                m[0] = r
            except re.error, e:
                log('Error while compiling regex: %r' % m[0], sys.stderr)
                log('Error message: %s' % e, sys.stderr)
                sys.exit(1)
        
        opener = getURLOpener(SETTINGS)
        
        while True:
            try:
                data = opener.open("list=1").read()
                data = json.loads(data)
    
                if not INITIATED:
                    for t in data['torrents']:
                        if t[4] == 1000:
                            COMPLETED[t[0]] = t[2]
                            
                    INITIATED = True
    
                else:                
                    for t in data['torrents']:
                        if t[4] == 1000:
                            if t[0] not in COMPLETED:
                                log('%s has been downloaded.' % t[2], sys.stderr)
                                for matcher, commands in SETTINGS.get('matchers', []):
                                    if matcher.search(t[2]):
                                        for command in commands:
                                            for w, i in commandparams:
                                                if len(t)-1 >= i:
                                                    command = command.replace('$%s' % w, str(t[i]))
                                            log('Executing: %r' % command, sys.stderr)
                                            subprocess.Popen(command)
                            COMPLETED[t[0]] = t[2]
            except urllib2.HTTPError, e:
                if e.code == 300:
                    log('Auth token has changed. Requesting new token...')
                    opener = getURLOpener(SETTINGS)
            except urllib2.URLError, e:
                if e.reason.errno == 10061:
                    log('Unable to connect to the web ui. Retrying in 5 minutes.', sys.stderr)
                    time.sleep(4*60)
            except Exception, e:
                    log('Unknown error: %s' % e, sys.stderr)
                    time.sleep(4*60)
            
            time.sleep(SETTINGS.get('interval', 1)*60)
    except KeyboardInterrupt:
        log('Exiting.')
        sys.exit(0)