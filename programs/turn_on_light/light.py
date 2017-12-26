#! /bin/python3

base_url = "/exec/ws2812"

class SmartLight:
    ip = list()

    def _generate_command_url(self, commands):
        def _ip_as_str():
            ans_str = str()
            for num in self.ip:
                ans_str = ans_str + str(num) + "."
            return ans_str[:-1]
        command_url = "http://" + _ip_as_str() + base_url
        for command in commands:
            command_url = command_url + "%20" + command
        return command_url
