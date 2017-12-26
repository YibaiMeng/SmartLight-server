import queue
import subprocess
import multiprocessing
import time
from threading import Thread
import json

class Shell:
    # TODO: concurrence of buffer objects? What to use?
    input_buffer = multiprocessing.Queue()
    # the buffer where all WeChat messages comes from.
    # only UNPROCESSED STRINGS accepted here!
    output_buffer = multiprocessing.Queue()
    # the buffer where all WeChat replies goes
    command_buffer = multiprocessing.Queue()
    # the buffer where all the commands that is waiting to be processed


    # we expect raw strings in the buffer! nothing more!

    current_process = None
    current_daemon = None

    is_parsing_command = True
    is_starting_command = True

    def __init__(self):
        print("Hello! Shell instance init!")
        self.output_buffer.put("你好！Shell开始运行了！")
        fp = open("programs.json")
        self.programs = json.JSONDecoder().decode(fp.read())


    def parse_command(self):
        while self.is_parsing_command:
            try:
                #print("Is parsing command")
                #print("There are this many inputs in input buffer: ", self.input_buffer.qsize())
                command = self.input_buffer.get(False)
                command = str(command)# just in case
                #print("Command is: ", command)
            except queue.Empty:
                #print("Nothing in input! Buffer!")
                continue
            if not isinstance(command, str):
                #print("Command not a string! Something wrong!")
                continue
            command = command.strip().splitlines()
            true_command = list()
            for indivi_command in command[:]:
                self.command_buffer.put(indivi_command.split())
            time.sleep(0.3)

    def io_daemon(self,popen_obj):
        def output_daemon(self, popen_obj):
            while True:
                line = popen_obj.stdout.readline()
                line = line.decode('utf-8')
                print("now line is", line)
                print("from output_daemon: What we get is", line)
                if line != "":
                    self.output_buffer.put(line)# how about this?
                    continue
                popen_obj.poll()
                print("from output_daemon: The process code is: " + str(popen_obj.returncode) )
                if popen_obj.returncode != None:
                    return
        '''
        def input_daemon(self,  popen_obj):
            while True:
                #print("from input_daemon: The process code is: " + str(popen_obj.returncode) )
                if popen_obj.poll() != None:
                    try:
                        line = self.command_buffer.get(False)
                        realLine = str()
                        for shit in line:
                            realLine += shit
                        print("from input_daemon: What we get is", realLine)
                        if realLine != "":
                            popen_obj.stdin.write(realLine)
                            print("from input_daemon: Set to stdin!")
                    except Exception as e:
                        continue
                else:
                    break
        '''

        #ind =Thread(input_daemon(self, popen_obj), daemon=True)
        oud =Thread(output_daemon(self, popen_obj), daemon=True)
        oud.start() #都开始了，怎么还是阻塞的啊！TODO:加入输入的功能！
        #TODO:为什么Python有bug，然而其他的是好的？
        #oud.join() # why do i need to join it?
        #ind.start()


    # change name to start command!
    def start_command(self):
        while self.is_starting_command:
            try:
                out = self.command_buffer.get(block=False)
                print("from excecute_command: Command is ", out)
            except queue.Empty:
                #print("from excecute_command: Command queue empty.")
                continue

            if self.current_process == None:
                command_is_good = False
                for program in self.programs:
                        if out[0] in program["alias"]:
                            out = program["invoking_program"] + out[:]
                            print(out)
                            command_is_good = True
                            break
                if not command_is_good:
                    out = ["python3", "./programs/ai/main.py"] + out[:]
                try:
                    self.current_process = subprocess.Popen(out, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                    # ask the program to NOT use stderr! Use stderr for server LOCAL logging purpose!
                    print("from excecute_command: Subprocess opened!")
                    print("from excecute_command: current io daemon started!")
                    self.io_daemon(self.current_process)
                    print("from excecute_command: current process finished!")
                    self.current_process = None
                except Exception as e:
                    print(e)

                    print("from excecute_command: Couldn't excecute this command and open a subprocess!")

            else:
                print("from excecute_command: A process is already there! The command will be sent to the exsiting process")
                continue


    def start(self):
        parser = Thread(target=self.parse_command, daemon=True)
        parser.start()
        print("Parser started!")
        starter = Thread(target=self.start_command, daemon=False)# TODO:why that daemon is false> why can't true work?
        starter.start()
        print("Command starter started!")
