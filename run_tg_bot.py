import os
import yaml

with open('users_config.yaml', 'r') as f:
    config = (yaml.load(f))

for d in config:
    for user in d:
        if user != 'azzik' and user != 'emptyn':
            os.system('/home/titto/proga/tg/bin/telegram-cli --json -d -P ' + str(d[user]['port']) + ' -p ' + user + ' > /dev/null &' )
            os.system('python3 /home/titto/proga/chat-wars-bot/main.py --admin ' + d[user]['admin'] + ' --order BlueOysterBot --port ' + str(d[user]['port']) + ' > /dev/null &')
