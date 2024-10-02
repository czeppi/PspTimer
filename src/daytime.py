from __future__ import annotations
import datetime
import re
from typing import Optional

TIME_REX = re.compile("^([0-9]{1,2}):?([0-9]{2})$")


class Daytime(int):

    @staticmethod
    def create_from_str(s: str) -> Optional[Daytime]:
        # HH:MM
        m = TIME_REX.match(s)
        if m:
            return Daytime(60 * int(m.group(1)) + int(m.group(2)))

        # only one value => hours
        if s.isdigit():
            return Daytime(60 * int(s))

    @staticmethod
    def create_with_current_time(round_min: int) -> Optional[Daytime]:
        now = datetime.datetime.now()
        minutes = 60 * now.hour + now.minute
        step = round_min
        minutes = ((minutes + step / 2) / step) * step
        return Daytime(minutes)

    def get_minutes(self):
        return int(self)

    def __add__(self, other: Daytime) -> Daytime:
        return Daytime(int(self) + int(other))

    def __sub__(self, other: Daytime) -> Daytime:
        return Daytime(int(self) - int(other))

    def __mul__(self, other: int) -> Daytime:
        return Daytime(int(self) * int(other))

    def __str__(self) -> str:
        return "%02i:%02i" % (self / 60, self % 60)
