import os
import yaml

with open('users_config.yaml', 'r') as f:
    config = (yaml.load(f))

for d in config:
    for user in d:
        os.system('/home/centos/tg/bin/telegram-cli --json -d -P ' + str(d[user]['port']) + ' -p ' + user + ' > /dev/null &' )
        os.system('python3 /home/centos/Chat-Wars-Bot/main.py --admin ' + d[user]['admin'] + ' --order BlueOysterBot --port ' + str(d[user]['port']) + ' > /dev/null &')
