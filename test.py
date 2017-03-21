from pytg.sender import Sender
from pytg.receiver import Receiver
from pytg.utils import coroutine
import json
# хост чтоб слушать telegram-cli
host = 'localhost'

# порт по которому сшулать
port = 1338

sender = Sender(host=host, port=port)
receiver = Receiver(host=host, port=port)

sender.send_msg("@devernua", "/report")


@coroutine  # from pytg.utils import coroutine
def main_loop():
    while True:
        msg = (yield)  # it waits until it got a message, stored now in msg.
        #print("Message: ", msg)
        print(json.dumps(msg,indent=4))
    # do more stuff here!
    #

#

# start the Receiver, so we can get messages!
receiver.start()

# let "main_loop" get new message events.
# You can supply arguments here, like main_loop(foo, bar).
receiver.message(main_loop())
# now it will call the main_loop function and yield the new messages.
