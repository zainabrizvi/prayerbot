import os, time, re
from slackclient import SlackClient

# for date conversion
from datetime import datetime as dt 

# for grabbing data
import pandas as pd

# creates a slack client object with the slack bot token 
# stored as an environment variable
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))


# prayerbot's id is initially None; gets set after startup
prayerbot_id = None


 # number of seconds between reading from RTM
rtm_read_delay = 1

# used to identify mentions to prayerbot
mention_regex = "^<@(|[WU].+?)>(.*)"


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None



def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(mention_regex, message_text)
    # the first group contains the username, the second group contains the remaining message
    print(message_text)
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):

    # if the command is "namaz", return the next prayer    
    if command.startswith("namaz"):

        # get the prayer times from islamicreliefcanada
        df = pd.read_html('http://islamicreliefcanada.org/prayer-times/est/')[0]
      
        # determine which one is next
        
        now = dt.now()
        prayers = df[df.Date == dt.now().day].drop(columns=['Date']).iloc[0]
        for k, v in prayers.items():
            hour = int(v.split(':')[0])
            minute = int(v.split(':')[1])
            if k not in ['Fajr', 'Sunrise']:
                hour = hour + 12

            if hour*60 + minute - now.hour*60 - now.minute > 0:
                break
        
        # Send the response back to the channel
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text='{}: {}'.format(k, v)
        )

    elif command.startswith("sup"):

        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text='lol haha ye'
        )        
    else:
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text='sorry i dont no wut to do lol'
        )


if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(rtm_read_delay)
    else:
        print("Connection failed. Exception traceback printed above.")
