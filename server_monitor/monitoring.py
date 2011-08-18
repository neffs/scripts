#!/usr/bin/env python
# encoding: utf-8
"""
monitoring.py

Created by David Kreitschmann on 2010-05-16.
Copyright (c) 2010 K3com. All rights reserved.
"""

import sys
import os
import xmlrpclib
import ConfigParser
import urllib2
import httplib
from datetime import datetime
import smtplib

CONFIG_FILE = "monitoring.cfg"


DEFAULT_CONFIG = {"sipgate user":"", "sipgate password": "", "sms to":"", "mail to":"",
                        "last status": "1", "last status change":str(datetime.now()),
                        "sms text": "Monitoring: %(url)s is offline!",
                        "smtp server":"", "smtp user":"", "smtp password":"",
                        "mail from":"", "mail text":"Monitoring: %(url)s is offline!"}

config = ConfigParser.SafeConfigParser(DEFAULT_CONFIG)
config.read(CONFIG_FILE)

def sendSMS(number, text, user, password):
    sp = xmlrpclib.ServerProxy("https://%s:%s@samurai.sipgate.net/RPC2"% (user, password))
    result = sp.samurai.ClientIdentify({"ClientName":"pysms", "ClientVersion": "1.0", "ClientVendor":"k3com"})
    result = sp.samurai.SessionInitiate({"RemoteUri":"sip:%s@sipgate.net"% number, "TOS":"text", "Content":text})
    

def sendMail(adresses, text, server, from_adress, user, password):
    smtp = smtplib.SMTP()
    smtp.connect(server)
    if user and password:
        smtp.login(user, password)
    msg = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s"
               % (from_adress, ", ".join(adresses), text, text))
    
    smtp.sendmail(from_adress, adresses, msg)
    smtp.quit()

def checkURL(url):
    try:
        response = urllib2.urlopen(url)
    except urllib2.URLError:
        return False
    except urllib2.HTTPError:
        return False
    return True
    

def main():
    config_changed = False
    for section in config.sections():
        url = config.get(section, "url")
        current_status = checkURL(url)
        previous_status = config.getint(section, "last status")
        
        if not bool(current_status) == bool(previous_status):
            config_changed = True
            config.set(section, "last status", str(int(current_status)))
            config.set(section, "last status change", str(datetime.now()))
            if not current_status:
                sms_text = config.get(section, "sms text")
                #sms_text = sms_text % {"url": url}
                numbers = config.get(section, "sms to").split(",")
                mails = config.get(section, "mail to").split(",")
                mail_text = config.get(section, "mail text")
                for n in numbers:
                    n = n.strip()
                    if n != "":
                        print "Sending SMS to %s\nText: %s" % (n,sms_text)
                        sendSMS(n, sms_text, config.get(section, "sipgate user"), config.get(section, "sipgate password"))
                if mails:
                    mails = [a.strip() for a in mails]
                    sendMail(mails, mail_text, config.get(section, "smtp server"), config.get(section, "mail from"),
                            config.get(section, "smtp user"), config.get(section, "smtp password"))
                        
    
    if config_changed:
        configfile = open(CONFIG_FILE,"wb")
        config.write(configfile)



if __name__ == '__main__':
    main()

