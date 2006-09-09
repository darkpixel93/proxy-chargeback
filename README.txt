Web Usage Accounting
====================

This was written by Greg Baker as a first silly idea about charging
wireless usage in a world in which certain legislation has been passed.
For lots of tedious discussion about this, visit 
 http://www.ifost.org.au/~gregb/Greg-Baker-Ifost-Wireless-Submission.pdf

The general idea is that while it might be free to transfer data to the
proxy server, we want to charge people for the data they have downloaded
through the proxy server.  As soon as the user's balance drops below 
zero, they are no longer allowed to download anything.

It may be useful for other organisations that want to charge for
bandwidth, or simply put limits on usage.

This code has never been extensively tested.

[Installation]

1. Look for the line "bandwidth_cost = 7.7" in squidAccounting.py
Change it to whatever is appopriate for your organisation.

2. Create the data storage directory.  Everything ends up as flat files in
this directory.

 mkdir -p /var/acct
 mkdir -p /var/acct/current
 mkdir -p /var/acct/new

3. Set up your squid proxy server to use authentication; specifically,
cause it to use an authentication program.  (Look for the
authenticate_program directive).  Try setting authenticate_children to
1 to make sure performance is acceptable.  Set authenticate_ttl to 5
minutes (How long are you willing to let people go with a negative
balance before you stop them?)  Get this all working.

4. Now change the authenticate_program yourprog arg1 arg2 to being
python authenticator.py yourprog arg1 arg2
What will probably happen is that you can now no longer browse the web
through this proxy server. That's correct,  because you don't have any
money in your account.

5. Create a file under /var/acct/current/(username).acct  where (username) 
is the name you have to give to the proxy authentication prompt. It should
contain some number of dollars.  e.g. 50.0

6. Confirm you can now browse again.  (You might need to wait 5 minutes).

7. Put this into your crontab  (i.e. with crontab -e)
* * * * * python /path/to/squidAccounting.py

8. Browse the web for a while.  Now look at /var/acct/current/(username).acct
and make sure it has reduced a little.  If not work out why.

9. Go and create acct files for all your other users.

10a.  If you are having people pay for their bandwidth, then when 
payment happens, run   "python  payment.py  (username)  (amount)"

10b.  If you just use it to force limits, then create a crontab entry
to reset accounting data for all your users.  Perhaps something like this:
0 3 1 * * find /var/acct/current -name '*.acct' -exec sh -c 'echo 50 > {}'


