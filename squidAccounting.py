#!/usr/bin/env python

import string
import re
import posixfile
import time
import glob
import os
import sys

bandwidth_cost = 7.7  # cents per megabyte


global_lock = posixfile.open('/var/acct/global.lock','w')
global_lock.lock('w|')

# The way I am keeping atomicity is to write my new
# state into a new directory.  
CURRENT_DATA_DIRECTORY = '/var/acct/current/'
NEW_DATA_DIRECTORY = '/var/acct/new/'
# So, when I'm finished,  I rename CURRENT to PAST...
PAST_DATA_DIRECTORY = '/var/acct/past/'
# ... and rename NEW to CURRENT
if not(os.path.exists(CURRENT_DATA_DIRECTORY)):
    # .. then something went wrong.  Let's back out
    if os.path.exists(PAST_DATA_DIRECTORY):
        os.rename(PAST_DATA_DIRECTORY,CURRENT_DATA_DIRECTORY)
        sys.stderr.write('Went back to old state\n')
    else:
        # no current,  no past,  huh???
        sys.exit('No current; no past;  what to do?')


os.system('rm -rf ' + NEW_DATA_DIRECTORY) # start afresh
os.mkdir(NEW_DATA_DIRECTORY)


# Now some assertions...
if not(os.path.exists(CURRENT_DATA_DIRECTORY)):
    sys.exit("assertion failed -- current directory not present")

ACCOUNT_FILE_ENDING = '.acct'
def user_acct_file(fromwhere,user):    return fromwhere + user + ACCOUNT_FILE_ENDING
def user_tstamp_file(fromwhere,user): return fromwhere + user + '.tstamp'
def position_file(fromwhere):         return fromwhere + 'position.idx'
def nice_time(t): return time.asctime(time.localtime(t))

######################################################################

# sample lines from squid's access.log
#1015260196.061     58 127.0.0.1 TCP_DENIED/407 1420 GET http://www.ifost.org.au/ - NONE/- -
#1015260206.296   1657 127.0.0.1 TCP_MISS/200 1719 GET http://www.ifost.org.au/ gregb DIRECT/203.42.87.219 text/html

access_log = open('/var/log/squid/access.log','r')
now = time.time()
last_record_for_user = {}
usage = {}

def transaction_log(*text):
    global now
    log = open('/var/acct/trans.log','a')
    log.write("["+time.asctime(time.localtime(now))+"] ")
    string_type = type("")
    for item in text:
        if type(item) == string_type:
            log.write(item)
        else:
            log.write(`item`)
    log.write('\n')
    log.close()
    
def get_current_account(user):
    if os.path.isfile(user_acct_file(CURRENT_DATA_DIRECTORY,user)):
        current_account_file = open(user_acct_file(CURRENT_DATA_DIRECTORY,user))
        current_account = string.atof(current_account_file.read())
        current_account_file.close()
    else:
        current_account = 0.0
        # ouch -- they have no account,  but they fetched something
        transaction_log('Account file missing for ',user)
    return current_account
        
    
######################################################################



# Where did I get up to?  What is the latest point in the log
# file that I am absolutely positively that I have handled every
# record before that point?
try:
    final_record_file = open(position_file(CURRENT_DATA_DIRECTORY))
    final_record_point = final_record_file.read()
    final_record_file.close()
    final_record_point = string.atol(final_record_point)
except IOError:
    final_record_point = 0
    transaction_log("Couldn't open position file")
except ValueError:
    final_record_point = 0
    transaction_log("Position file is corrupt")

access_log.seek(final_record_point)
spaces = " +"
for line in access_log.readlines():
    # must fix up that readlines -- that will be a huge file,  I just
    # hope that we won't be reading it very often
    line = string.strip(line)
    [when,elapsed,srcip,status,bytes_fetched,method,url,user,how,contenttype] = re.split(spaces,line)
    if status[:10] == 'TCP_DENIED': continue # wrong password or something
    # should now check to see if they were fetching something in the
    # wireless network (free),  on the ausbone (2.2c/Mb), on the ifost
    # network (maybe free) or in some other wireless network's peer proxy
    # cache.
    when = string.atof(when)
    bytes_fetched = string.atoi(bytes_fetched)
    if user == "-": continue
    if re.match('^[a-zA-Z0-9]+$',user) is None: continue
    if last_record_for_user.has_key(user):
        # have we handled this record for this user before?
        if last_record_for_user[user] > when:
            transaction_log("Skipping record at ",when," for ",user)
            continue
    else:
        try:
            lrfu_file = open(user_tstamp_file(CURRENT_DATA_DIRECTORY,user))
            lrfu = lrfu_file.read()
            lrfu_file.close()
            last_record_for_user[user] = string.atof(lrfu)
            transaction_log("First record of ",user," - seen until ",time.asctime(time.localtime(last_record_for_user[user])))
            if last_record_for_user[user] > when:
                transaction.log("Skipping record at ",when," for ",user)
                continue
        except ValueError:
            transaction_log("No time stamp file (or corrupt) for ",user)
            last_record_for_user[user] = 0
            
    if usage.has_key(user):
        usage[user] = usage[user] + bytes_fetched
    else:
        usage[user] = bytes_fetched

new_pos = open(position_file(NEW_DATA_DIRECTORY),'w')
new_pos.write(`access_log.tell()`)
new_pos.close()

this_session_recorded_users = usage.keys()
ok_users = []
for user in this_session_recorded_users:
    expense =  bandwidth_cost * usage[user] / 1000000.0
    try:
        current_account = get_current_account(user)
        new_account = current_account - expense
        new_account_file = open(user_acct_file(NEW_DATA_DIRECTORY,user),'w')
        new_account_file.write(`new_account`)
        new_account_file.close()
        new_tstamp_file = open(user_tstamp_file(NEW_DATA_DIRECTORY,user),'w')
        new_tstamp_file.write(`now`)
        new_tstamp_file.close()
        transaction_log('Subtracted ',expense,' cents from ',user,
                        ' for using ',usage[user],' bytes since ',
                        nice_time(last_record_for_user[user]),
                        '; old balance was ',
                        current_account,', new balance is now ',
                        new_account)
        ok_users.append(user)
        
    except IOError:
        transaction_log('Exception while processing ',user,
                        ' -- did not subtract ',expense,' cents for ',
                        'using ',usage[user],' bytes since ',
                        time.asctime(time.localtime(last_record_for_user[user])))

all_user_files = glob.glob(CURRENT_DATA_DIRECTORY+"*" + ACCOUNT_FILE_ENDING)
def filename_to_user(filename):
    return filename[string.rindex(filename,'/')+1:string.index(filename,ACCOUNT_FILE_ENDING)]

all_users = map (filename_to_user,all_user_files)
     
for file in all_users:
    if file in ok_users: continue
    os.system("cp "
              +user_acct_file(CURRENT_DATA_DIRECTORY,user)+" "
              +user_acct_file(NEW_DATA_DIRECTORY,user))

    os.system("cp "
              +user_tstamp_file(CURRENT_DATA_DIRECTORY,user)+" "
              +user_tstamp_file(NEW_DATA_DIRECTORY,user))

os.rename(CURRENT_DATA_DIRECTORY,PAST_DATA_DIRECTORY)
os.rename(NEW_DATA_DIRECTORY,CURRENT_DATA_DIRECTORY)
os.system("rm -rf " + PAST_DATA_DIRECTORY)

global_lock.lock("u|")
