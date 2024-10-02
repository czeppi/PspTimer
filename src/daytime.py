import datetime
import re


time_rexp = re.compile("^([0-9]{1,2}):?([0-9]{2})$")


class Daytime(int):
    def GetMinutes(self):
        return int(self)

    def __add__(self, other):
        return Daytime(int(self) + int(other))

    def __sub__(self, other):
        return Daytime(int(self) - int(other))

    def __mul__(self, other):
        return Daytime(int(self) * int(other))

    def __str__(self):
        return "%02i:%02i" % (self / 60, self % 60)


def DaytimeFromStr(s):
    # HH:MM
    m = time_rexp.match(s)
    if m:
        return Daytime(60 * int(m.group(1)) + int(m.group(2)))

    # nur ein Wert => Stunde
    if s.isdigit():
        return Daytime(60 * int(s))


def DaytimeNow(round_min: int):
    now = datetime.datetime.now()
    minutes = 60 * now.hour + now.minute
    step    = round_min
    minutes = ((minutes + step/2) / step) * step
    return Daytime(minutes)
