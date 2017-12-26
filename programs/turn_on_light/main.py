#! /bin/python3
import sys
import requests
import socket

from light import SmartLight

TIMEOUT = 5

raw_command = sys.argv[1:]
light = SmartLight()

# to be changed by hand
light.ip = [192, 168, 43, 137]


colors_en = {"蓝色":"blue","黄色":"yellow","绿色":"green","紫色":"purple", "红色":"red","白色":"white"}
colors = ["蓝色","黄色","绿色","紫色", "红色","白色"]
def color2en(color_str):
    try:
        return colors_en[color_str]
    except:
        return None

cmd_color = ""
is_rainbow = False
is_breath = False

command  = list()

if sys.argv[1] == "关灯":
    command.append("off")
else:
    command.append("on")

for ind_command in raw_command[1:]:
    if ind_command in colors:
        cmd_color = color2en(ind_command)
    if ind_command=="彩虹":
        is_rainbow = True
    if ind_command=="呼吸":
        is_breath=True

if is_rainbow == True:
    command.append("rainbow")
else:
    if cmd_color != "":
        if is_breath == True:
            command.append("-b")
        command.append("-c")
        command.append(cmd_color)

#    command =

command_url = light._generate_command_url(command)
#print(command_url)
try:
    r = requests.get(command_url, timeout=TIMEOUT)
    print("指令被执行了")
except requests.RequestException:
    print("Shit! Something went wrong!")
    #TODO:errors
