#! /bin/python3
import sys
import requests
import socket

from light import SmartLight

TIMEOUT = 5

#print(socket.gethostbyname_ex(socket.gethostname()))

raw_command = sys.argv[1:]
print(raw_command)
light = SmartLight()
light.ip = [192, 168, 31, 1]
command_url = light._generate_command_url(raw_command)
print(command_url)
try:
    r = requests.get(command_url, timeout=TIMEOUT)
    print("command ", raw_command, "excecuted!")
except requests.RequestException:
    print("Shit! Something went wrong!")
