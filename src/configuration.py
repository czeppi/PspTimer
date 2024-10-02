from __future__ import annotations
import datetime
import re
from typing import List, Dict, Optional

import wx

from daytime import Daytime

CONFIG_SEP_CHAR = '#'
DATE_REX = re.compile("^([0-9][0-9])([0-9][0-9])([0-9][0-9])$")


class Config(wx.Config):

    def __init__(self, app_name: str):
        wx.Config.__init__(self, app_name)
        self._cur_day = datetime.date.today()
        self._round_min = 1
        self.read_settings()

    def set_day(self, day: datetime.date) -> None:
        self._cur_day = day

    def get_day(self) -> datetime.date:
        return self._cur_day

    def read_days(self) -> List[datetime.date]:
        self.SetPath("/")

        day_list = []  # list of datetime.date
        ok, group, ind = self.GetFirstGroup()
        while ok:
            m = DATE_REX.match(group)
            if m:
                day = datetime.date(2000 + int(m.group(1)), int(m.group(2)), int(m.group(3)))
                day_list.append(day)
            ok, group, ind = self.GetNextGroup(ind)

        return sorted(day_list)

    def read_day_times(self) -> List[Daytime]:
        day_times: List[Daytime] = []
        self.SetPath(self._cur_day.strftime("/%y%m%d"))

        ok, time_str, ind = self.GetFirstEntry()
        while ok:
            daytime = Daytime.create_from_str(time_str)
            if daytime:
                day_times.append(daytime)
            ok, time_str, ind = self.GetNextEntry(ind)

        self.SetPath("/")
        return sorted(day_times)

    def read_timeval(self, daytime) -> Timeval:
        self.SetPath(self._cur_day.strftime("/%y%m%d"))
        val_as_str = self.Read(str(daytime))
        val = self._create_time_val_from_str(val_as_str)
        self.SetPath("/")
        return val

    @staticmethod
    def _create_time_val_from_str(s: str) -> Timeval:
        val = s.split(CONFIG_SEP_CHAR)
        job = ""
        psp = ""
        if len(val) >= 1:
            job = val[0]
            if len(val) >= 2:
                psp = val[1]
        return Timeval(job, psp)

    def read_day_items(self) -> Dict[Daytime, Timeval]:
        day_items: Dict[Daytime, Timeval] = {}  # minutes -> list of values
        for daytime in self.read_day_times():
            timeval = self.read_timeval(daytime)
            day_items[daytime] = timeval

        return day_items

    def del_day_item(self, daytime: Daytime) -> bool:
        self.SetPath(self._cur_day.strftime("/%y%m%d"))
        ok = self.DeleteEntry(str(daytime))
        self.SetPath("/")
        return ok

    def write_day_item(self, daytime: Daytime, timeval: Timeval) -> bool:
        self.SetPath(self._cur_day.strftime("/%y%m%d"))
        ok = self.Write(str(daytime), str(timeval))
        self.SetPath("/")
        return ok

    def rename_daytime(self, old_time: Daytime, new_time: Daytime) -> bool:
        self.SetPath(self._cur_day.strftime("/%y%m%d"))
        ok = self.RenameEntry(str(old_time), str(new_time))
        self.SetPath("/")
        if not ok:
            wx.MessageBox(
                "Zeit konnte nicht geändert werden.\n"
                "Vermutlich gibt es schon eine Zeile mit dieser Zeit.",
                "Fehler beim umbenennen")
        return ok

    def write_job(self, job: str, daytime: Optional[Daytime]) -> bool:
        # val.job
        if daytime:
            val = self.read_timeval(daytime)
        else:
            daytime = Daytime.create_with_current_time(self._round_min)
            val     = Timeval("", "")
        val.job = job

        # search val.psp in other items of the same day
        psp_set = set()
        for t in self.read_day_times():
            v = self.read_timeval(t)
            if v.job == job and v.psp:
                psp_set.add(v.psp)

        # found nothing -> search val.psp in other items of all days
        if len(psp_set) == 0:
            cur_day = self.get_day()
            for day in reversed(self.read_days()):
                self.set_day(day)
                for t in self.read_day_times():
                    v = self.read_timeval(t)
                    if v.job == job and v.psp:
                        psp_set.add(v.psp)
                if len(psp_set) > 0:  # found item (but read allways the whole day)
                    break
            self.set_day(cur_day)

        if len(psp_set) == 1:  # are values unique?
            val.psp = psp_set.pop()

        # write
        return self.write_day_item(daytime, val)

    def write_psp(self, psp: str, daytime: Optional[Daytime]) -> List[Daytime]:
        if daytime:
            chg: List[Daytime] = []
            job = self.read_timeval(daytime).job
            for t in self.read_day_times():
                v = self.read_timeval(t)
                if v.job == job:
                    v.psp = psp
                    if self.write_day_item(t, v):
                        chg.append(t)
            return chg
        else:
            now = Daytime.create_with_current_time(self._round_min)
            val = Timeval("", new_text)
            self.write_day_item(now, val)
            return [now]

    def read_settings(self) -> None:
        self.SetPath("/")
        self._round_min = self.ReadInt("round_min", 1)

    def write_settings(self) -> None:
        self.SetPath("/")
        self.WriteInt("round_min", self._round_min)


class Timeval:

    def __init__(self, job: str, psp: str):
        self.job = job
        self.psp = psp

    def __str__(self):
        return self.job + CONFIG_SEP_CHAR + self.psp
