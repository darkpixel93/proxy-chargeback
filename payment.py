#!/usr/bin/env python

import string
import re
import posixfile
import time
import sys
import os
import pwd  # this should become "import nis" if we change to NIS/NIS+

DATA_DIRECTORY = '/var/acct/current/'
ACCOUNT_FILE_ENDING = '.acct'
def user_acct_file(user): return DATA_DIRECTORY+user+ACCOUNT_FILE_ENDING

# Process command line arguments.  Should be
# payment.py  username  amount
#  - but amount might be $20  $20.00  20.00  20 etc.

if len(sys.argv) != 4:
    sys.exit("Usage: " + sys.argv[0] + " username  amount  depositnum")

username = sys.argv[1]
amount = sys.argv[2]
depositnum = sys.argv[3]

# check that the username exists.
if re.match('^[a-zA-Z0-9]+$',username) is None:
    sys.exit("Username given looks odd: " + username)
if not(os.path.exists(user_acct_file(username))):
    try:
        details = pwd.getpwnam(username)
    except KeyError:
        # user not in /etc/passwd;  no datafile for them.  Hmmm??
        sys.exit("User does not appear to exist " + username)

# turn the amount into something useful
money = string.strip(amount)
if money[0] == '$': money = money[1:]
if money[0] == '-' and money[1] == '$': money = '-' + money[2:]
try:
    money = string.atof(money)
except ValueError:
    sys.exit("Does not appear to be a monetary amount " + amount)
    
money = money * 100.0 # we record account balances in cents

# depositnum we just leave as is.

######################################################################


try:
    global_lock = posixfile.open('/var/acct/global.lock','w')
    global_lock.lock('w|')
except IOError,x:
    sys.exit("Can't obtain lock " + `x.strerror`)

now = time.time()

def get_current_account(user):
    if os.path.isfile(user_acct_file(user)):
        current_account_file = open(user_acct_file(user))
        current_account = string.atof(current_account_file.read())
        current_account_file.close()
    else:
        current_account = 0.0
    return current_account
        
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

    
######################################################################

current_account = get_current_account(username)
new_account = current_account + money
try:
    new_account_file = open(user_acct_file(username),'w')
    new_account_file.write(`new_account`)
    new_account_file.close()
    transaction_log('Added ',amount,' (',money,' cents) from ',username,
                    ' for deposit number ',depositnum,
                    '; old balance was ',current_account,
                    ', new balance is now ',new_account)
except IOError:
    transaction_log('Exception while processing ',username,
                    ' -- did not add payment of ',amount,
                    ' (',money, ' cents) payment [corresponding deposit ',
                    'is  ',depositnum,']')
    sys.stderr.write('Could not update ' + username + ' with payment of ' +
                     amount + " (" + `money` + ' cents).\n')


global_lock.lock("u|")
