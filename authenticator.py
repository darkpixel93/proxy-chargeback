#!/usr/bin/env python

import os
import sys
import string

real_authenticator = os.popen2(sys.argv[1:])
(auth_input,auth_output) = real_authenticator

DATA_DIRECTORY = '/var/acct/current/'
ACCOUNT_FILE_ENDING = '.acct'
def user_acct_file(user): return DATA_DIRECTORY+user+ACCOUNT_FILE_ENDING
def get_current_account(user):
    if os.path.isfile(user_acct_file(user)):
        current_account_file = open(user_acct_file(user))
        current_account = string.atof(current_account_file.read())
        current_account_file.close()
    else:
        current_account = 0.0
    return current_account

while 1:
    line = sys.stdin.readline()
    auth_input.write(line)
    auth_input.flush()
    answer = auth_output.readline()
    if answer == 'OK\n':
        # have they got credit?
        [user,password] = string.split(line,' ',1)
        try:
            balance = get_current_account(user)
            if balance > 0.0:
                sys.stdout.write("OK\n")
                sys.stdout.flush()
            else:
                sys.stdout.write("ERR\n")
                sys.stdout.flush()
        except:
            sys.stdout.write("ERR\n")
            sys.stdout.flush()
    else:
        sys.stdout.write("ERR\n")
        sys.stdout.flush()

