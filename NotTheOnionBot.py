# -------------------------------------------- #
# NotTheOnionBot 2.5b                          #
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
import traceback

# I hate seeing that red stuff from BeautifulSoup that isn't my fault.
warnings.filterwarnings("ignore")

# Startup Console Text
print('NotTheOnionBot is starting up - v2.4 beta')
print('Sadly, this is NotTheOnionBot.')
print(' ')

r = praw.Reddit(user_agent="NotTheOnionBot v2.4 beta by /u/x_minus_one")
print('Logging in to reddit...')
o = OAuth2Util.OAuth2Util(r, print_log=True)
o.refresh()
print("Done!")

# Submission Limit for TitleCheckBot
titles_limit = 5

# Submission Limit for DeadPostsBot
approvals_limit = 1000

# Submission Limit for KarmaTrainBot
alerts_limit = 1000

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

# Karma score considered "significant" for approval purposes
# Should be set to one less than the real score because of using greater than

IgnoreUpvotedScore = 99

# TITLECHECKBOT #

# Article Text Grabber/Valid URL Checker
def URLisValid(url):
    try:
        urllib.request.urlopen(url)
        return True
    except:
        traceback.print_exc()
        print("Flagrant System Error! URL failed to load. Can't check this submission.")
        return False
def getArticleText(url):
    if URLisValid(url):
        try:
            page = urllib.request.urlopen(url).read()
            soup = BeautifulSoup(page)
            return str(soup)
        except:
            traceback.print_exc()
            print('Whoops!  Checking this article text didnt work.  Skipping submission.')
            pass

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
                    continue
                # Check if title is in article
                elif title.lower() in articletext.lower():
                    print('Submission has the correct title. (', submission.author.name, ') ')
                # Reports for submissions, with wrong titles, that are at greater than +50- this is important when recovering from a downtime so we don't accidentally pull from /r/all or something!
                elif submission.score > IgnoreUpvotedScore:
                    print('Submission has wrong title, but has more than 50 upvotes. Reporting...')
                    submission.report(reason='Submission may have wrong title, but is upvoted.  Please review.')
                    print('Reported submission. (', submission.author.name, ')')
                # Removals for submissions that have the wrong title
                else:
                    print('Submission has wrong title.  Removing and assigning flair...')
                    submission.remove()
                    submission.set_flair(flair_text='Wrong/Altered Title', flair_css_class='removed')
                    print('Done, commenting...')
                    submission.add_comment(getRemovalComment()).distinguish()
                    print('All done! (', submission.author.name, ')')
        except:
            print("Error! Reddit failed to grab a submission or the user deleted it during the cycle. Skipping...")
            traceback.print_exc()
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
            if len(submission.mod_reports + submission.user_reports) > 0: # Skips reported posts (mod or user)
                print('Submission has reports, continuing. (', submission.author.name, ')')
                continue
            if submission.score > IgnoreUpvotedScore: # Skips posts with high enough karma scores to matter in the subreddit
                print('Submission is significantly upvoted (', submission.score, '), continuing. (', submission.author.name, ')')
                #report is unnecessary due to karmatrainbot
                #submission.report(reason='Submission is at +100 and is unapproved. Please review ASAP.')
                continue
            else: # Approves dead posts
              print('Submission is 24hrs old, approving...')
              submission.approve()
              print('Done! (', submission.author.name, ')')
        except:
            print("Error! Reddit failed to grab a submission or the user deleted it during the cycle. Skipping...")
            traceback.print_exc()
            pass

        
# KARMATRAINBOT #
def karmaTrainBot():
  print('Starting KarmaTrainBot cycle.')
  printCurrentTime()
  print('Grabbing unmoderated posts...')
  for submission in rmod.get_unmoderated(limit=alerts_limit):
    try:
        if len(submission.mod_reports + submission.user_reports) > 0:
            print('Submission already mod reported, continuing. (', submission.author.name, ')')
            continue
        if submission.score > IgnoreUpvotedScore:
            print('Submission is at +100, reporting. (', submission.author.name, ')')
            submission.report(reason='Submission reached +100 without being approved.  Please review')
            print('Done!')
            continue
        else:
            print('Submission is not at +100, continuing. (', submission.author.name, ')')
    except:
      print('Reddit gave us an error or the user deleted it during the cycle. Skipping...')
      traceback.print_exc()
      pass

# ---------------- #
# CYCLE SUPERVISOR #
# ---------------- #

# "You're not my NotTheOnionBot supervisor!" -Cheryl Tunt

while True:
  try:
    o.refresh()
    titleCheckBot()
    print('TitleCheckBot cycle completed.')
    print(' ')
    deadPostsBot()
    print('DeadPostsBot cycle completed.')
    print(' ')
    karmaTrainBot()
    print('KarmaTrainBot cycle completed.')
    print('All done, exiting.')
    time.sleep(5)
    os._exit(0)
    #print('Waiting 5 minutes to run next cycle loop.')
    #print(' ')
    #cycleSleepTime = 300
    #time.sleep(float(cycleSleepTime))
    #print('Starting new cycle.')
  except:
    print('THANKS OBAMA!  There was an error.  Retrying cycle.')
    traceback.print_exc()
    exceptionSleepTime = 10
    time.sleep(float(exceptionSleepTime))
    pass

