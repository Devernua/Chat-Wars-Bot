import os
import yaml

with open('users_config.yaml', 'r') as f:
    config = (yaml.load(f))

for d in config:
    for user in d:
        os.system('/home/titto/tg/bin/telegram-cli --json -d -P ' + d[user]['port'] + ' -p ' + user + ' > /dev/null &' )
        os.system('python3 /home/titto/chat-wars-bot/main.py --admin ' + d[user]['admin'] + ' --order BlueOysterBot --port ' + d[user]['port'] + ' > /dev/null &')
