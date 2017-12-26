# External libraries
import itchat
from itchat.content import *

import multiprocessing
import queue
from threading import Thread
import time

# Other modules
from shell import Shell

chat_instance = itchat.new_instance()

# switch to filehelper! remember!

#these hashes change all the day!
current_user = "filehelper"
my_user_name = "filehelper"

friend_added = False


shell_instance = Shell()
stop_auto_reply = False

def reply(message):
    chat_instance.send(message, toUserName=current_user)


def auto_reply():
    while stop_auto_reply == False:
        time.sleep(0.3)# so that you don't get clogged up with too many message
        out = "[机器人]\n"
        while True:
            try:
                out = out  + shell_instance.output_buffer.get(block=False)
                # TODO:block?
                # TODO:
            except queue.Empty:
                time.sleep(0.3)
                break
        if out != "[机器人]\n":
            reply(out)

@chat_instance.msg_register(TEXT, isFriendChat=True, isGroupChat=False, isMpChat=False)
def WeChatShell(msg):
    print(msg.user, msg["ToUserName"])
    global friend_added
    global current_user
    global my_user_name
    if msg["Text"] != "芝麻开门" and msg["ToUserName"] == my_user_name:
        print(msg["Text"])
        shell_instance.input_buffer.put(msg["Text"])
    if msg["Text"] == "芝麻开门" and friend_added == False:
        friend_added = True
        current_user = msg["FromUserName"]
        my_user_name = msg["ToUserName"]
        shell_instance.input_buffer.put("你好！很高兴认识你！我是笨笨的机器人。", block=False)

        #print(shell_instance.input_buffer.qsize())
'''
@chat_instance.msg_register(FRIENDS)
def add_friend(msg):
    if not friend_added:
        msg.user.verify()
        strrr = msg["Text"]
        print("加人验证" + strrr)
        print("验证",msg)
        #if strrr[0:2] == "我是":
        #    msg.user.send('你好！很高兴认识你！')
        friend_added = True
        current_user = msg["FromUserName"]
        my_user_name = msg["ToUserName"]
'''
# Temp code just for pre!
# delete afterwards

chat_instance.auto_login(hotReload=True)


p = Thread(target = auto_reply, daemon=True)
p.start()

shell_instance.start()

chat_instance.run()
# while true：
#    select?
chat_instance.logout()
# why? ctrl C
