# External libraries
import requests
import itchat
from itchat.content import TEXT

import multiprocessing
import queue
from threading import Thread
import time

# Other modules
from shell import Shell

shell_instance = Shell()
stop_auto_reply = False
chat_instance = itchat.new_instance()

def reply(message):
    chat_instance.send("$ " + message, toUserName='filehelper')


def auto_reply():
    while stop_auto_reply == False:
        time.sleep(0.3)
        out = str()
        while True:
            try:
                out = out + shell_instance.output_buffer.get(block=False)
            except queue.Empty:
                break
        if out != "":
            reply(out)

@chat_instance.msg_register(TEXT, isFriendChat=True, isGroupChat=False, isMpChat=False)
def WeChatShell(msg):
    if msg["ToUserName"] == "filehelper":
        print(msg["Text"])
        shell_instance.input_buffer.put(msg["Text"])
        print(shell_instance.input_buffer.qsize())

chat_instance.auto_login(hotReload=True)

p = Thread(target = auto_reply, daemon=True)
p.start()
shell_instance.start()
chat_instance.run()
chat_instance.logout()
