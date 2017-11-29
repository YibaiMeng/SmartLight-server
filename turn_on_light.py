import itchat
import requests
import os
from itchat.content import TEXT

@itchat.msg_register(TEXT, isFriendChat=True, isGroupChat=True, isMpChat=True)
#def Store(msg):
    #print(msg["FromUserName"], msg["ToUserName"])
    #print(msg["Text"])
def WeChatShell(msg):
    if msg["ToUserName"] == "filehelper":
        print(msg["Text"])
        command = msg["Text"]
        command = command.strip()
        if command[0] == '#':
            return
        execute_program = os.popen("./programmes/"+command, "r")
        reply = execute_program.read()
        print(reply)
        if reply != "":
            itchat.send("$s"+ reply, toUserName='filehelper')



itchat.auto_login(hotReload=True)
itchat.run()
