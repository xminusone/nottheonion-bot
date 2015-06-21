import praw
import datetime
import time

print('/r/NotTheOnion Unmoderated Approval Bot - v1.0b')
print('Logging in to Reddit...')
r = praw.Reddit('NTO Unmoderated Approvals v1.0b - /u/you')
r.login('USERNAME', 'PASSWORD')

# time goes here if doesn't work below

def queueCheckerBot():
    print('Updating current time...')
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    print('Grabbing unmoderated for /r/mod...')
    s = r.get_subreddit('mod')
    unmoderated = s.get_unmoderated(limit=1000)
    print('Checking all unmoderated submissions...')
    for submission in unmoderated:
        try:
            age = now - submission.created_utc
            if age < 86400:
                print('Submission is less than 24hrs old, continuing.')
                # time.sleep(1)
                continue
            if len(submission.mod_reports + submission.user_reports) > 0:
                print('Submission has reports, continuing.')
                # time.sleep(1)
                continue
            print('Submission is 24hrs old, approving...')
            # time.sleep(1)
            submission.approve()
            print('Done!')
        # print('All submissions checked. Exiting in 60 seconds...')
        # time.sleep(60)
        # sys.exit(0)
        except:
            print('Error! Reddit gave us an error. Skipping.')
while True:
    try:
        queueCheckerBot()
        print('Checked all submissions. Rechecking in 60min.')
        time.sleep(3600)
    except:
        print('Error! Something broke. Retrying.')
        pass
