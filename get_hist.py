from getopt import getopt
import sys
from pytg.sender import Sender

port = 1347

opts, args = getopt(sys.argv[1:], 'p', ['port='])
for opt, arg in opts:
    if opt in ('-p', '--port'):
        port = int(arg)


sender = Sender(host="localhost", port=port)
print(sender.contacts_search('ChatWarsBot'))
hist = sender.messages_search('@ChatWarsBot', 'На выходе')
with open('history.txt', 'a') as f:
    for d in hist:
        f.write(d['text'] + '\n' + '-'*8)
