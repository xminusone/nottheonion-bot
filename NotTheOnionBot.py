# -------------------------------------------- #
# NotTheOnionBot 2.1b                          #
# By /u/x_minus_one                            #
# https://github.com/xminusone/nottheonion-bot #
# -------------------------------------------- #

# ------------- #
# Startup Stuff #
# ------------- #

# Import, import, import!
import praw
import time
import datetime
import urllib.request
import warnings
import sys
import OAuth2Util
from bs4 import BeautifulSoup

# I hate seeing that red stuff from BeautifulSoup that isn't my fault.
warnings.filterwarnings("ignore")

# Startup Console Text
print('NotTheOnionBot is starting up - v2.1 beta')
print('Sadly, this is NotTheOnionBot.')
print(' ')

r = praw.Reddit(user_agent="NotTheOnionBot - TitleCheckBot + DeadPostsBot - v2.1 beta by /u/x_minus_one")
print('Logging in to reddit...')
o = OAuth2Util.OAuth2Util(r)
print("Done!")

# Submission Limit for TitleCheckBot
titles_limit = 3

# Submission Limit for DeadPostsBot
approvals_limit = 1000

# Timestamp (used in both scripts, so you can tell if the script hung on a
#            submission)
def printCurrentTime():
    currentSysTime = time.localtime()
    print(time.strftime('%m/%d/%y @ %H:%M:%S', currentSysTime))
    
# External File Imports (for TitleCheckBot only)
# Domain Exemption List
print('Importing TitleCheckBot domain exemption list from exemptions.cfg...')
try:
    with open('exemptions.cfg', 'r') as f:
          exemptlist = [line.strip() for line in f]
    print('Done!')
except:
    print('Error! exemptions.cfg is missing. This may cause submissions to be incorrectly removed.')

# Removal Comment
print('Importing TitleCheckBot removal comment from removalcomment.cfg...')
import os
def getRemovalComment():
    comment = ''
    try:
        if not os.path.exists('removalcomment.cfg'):
            raise IOError
        with open('removalcomment.cfg') as file:
            for line in file:
                comment += line
        try:
            file.close()
        except:
            print('Error!  removalcomment.cfg could not be opened. Attempts to post removal comments may fail...')
            pass
    except IOError:
        print('Error!  removalcomment.cfg is missing. Attempts to post removal comments may fail...')
        pass
    except:
        print('Error!  removalcomment.cfg is missing or something bad happened. Attempts to post removal comments may fail...')
        pass
    return comment
print('Startup tasks complete!')
print('Ready for initial cycle loop.')
print(' ')

# ---------- #
# BOT CYCLES #
# ---------- #

# SHARED INFO #
# (this should be set to "mod" unless you don't want the main sub checked
#  for testing reasons)
rmod = r.get_subreddit("mod")

# TITLECHECKBOT #

# Article Text Grabber/Valid URL Checker
def URLisValid(url):
    try:
        urllib.request.urlopen(url)
        return True
    except:
        print("Flagrant System Error! URL failed to load. Can't check this submission.")
        return False
def getArticleText(url):
    if URLisValid(url):
        page = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(page)
        return str(soup)

# Reddit Submission Checks
def titleCheckBot():
    print('Starting TitleCheckBot cycle.')
    printCurrentTime()
    for submission in rmod.get_unmoderated(limit=titles_limit):
        title = submission.title
        articletext = getArticleText(submission.url)
        exemptcheckurl = submission.url
        try:
            if articletext is not None:
                # Check against domain exemption list
                if any(domain in exemptcheckurl for domain in exemptlist):
                    print('Domain is on exemption list. Cannot check this submission. (', submission.author.name, ') ')
                # Check if title is in article
                elif title.lower() in articletext.lower():
                    print('Submission has the correct title. (', submission.author.name, ') ')
                # Reports for submissions, with wrong titles, that are at greater than +50- this is important when recovering from a downtime so we don't accidentally pull from /r/all or something!
                elif submission.score > 50:
                    print('Submission has wrong title, but has more than 50 upvotes. Reporting...')
                    submission.report(reason='Submission may have wrong title, but is at +50.')
                    print('Reported submission. (', submission.author.name, ')')
                # Removals for submissions that have the wrong title
                else:
                    print('Submission has wrong title.  Removing and assigning flair...')
                    submission.remove()
                    submission.set_flair(flair_text='Wrong/Altered Title', flair_css_class='removed')
                    print('Done! (', submission.author.name, ')')
        except:
            print("Error! Reddit failed to grab a submission or the user deleted it during the cycle. Skipping...")
            pass
          
# DEADPOSTSBOT #
def deadPostsBot():
    print('Starting DeadPostsBot cycle.')
    printCurrentTime()
    print('Updating current time...')
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    print('Checking age of posts in /r/mod...')
    for submission in rmod.get_unmoderated(limit=approvals_limit):
        try:
            age = now - submission.created_utc
            if age < 86400: # Skips posts that are less than 24hrs old
                print('Submission is less than 24hrs old, continuing. (', submission.author.name, ')')
                continue
            elif len(submission.mod_reports + submission.user_reports) > 0: # Skips reported posts (mod or user)
                print('Submission has reports, continuing. (', submission.author.name, ')')
                continue
            # Not working right now?
           #  elif len(submission.score) > 100: # Skips posts with high enough karma scores to matter in the subreddit
               #  print('Submission is significantly upvoted (', submission.score, '), continuing. (', submission.author.name, ')')
                # NEED TO DISCUSS THIS WITH THE OTHER MODS BEFORE UNCOMMENTING
                # submission.report(reason='Submission is at +100 and is unapproved. Please review.')
                continue
            else: # Approves dead posts
              print('Submission is 24hrs old, approving...')
              submission.approve()
              print('Done! (', submission.author.name, ')')
        except:
            print("Error! Reddit failed to grab a submission or the user deleted it during the cycle. Skipping...")

# ---------------- #
# CYCLE SUPERVISOR #
# ---------------- #

# "You're not my NotTheOnionBot supervisor!" -Cheryl Tunt

while True:
  try:
    titleCheckBot()
    print('TitleCheckBot cycle completed.')
    print(' ')
    deadPostsBot()
    print('DeadPostsBot cycle completed.')
    print('Waiting 5 minutes to run next cycle loop.')
    print(' ')
    cycleSleepTime = 300
    time.sleep(float(cycleSleepTime))
    print('Starting new cycle.')
  except:
    print('An error occurred this cycle.  Retrying cycle loop.')
    pass
