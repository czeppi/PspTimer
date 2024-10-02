import datetime
import re

import wx

from daytime import Daytime

CONFIG_SEP_CHAR = '#'
DATE_REX = re.compile("^([0-9][0-9])([0-9][0-9])([0-9][0-9])$")


class Config(wx.Config):

    def __init__(self, app_name: str):
        wx.Config.__init__(self, app_name)
        self.cur_day = datetime.date.today()
        self.read_settings()

    def set_day(self, day):
        self.cur_day = day

    def get_day(self):
        return self.cur_day

    def read_days(self):
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

    def read_day_times(self):
        day_times = []
        self.SetPath(self.cur_day.strftime("/%y%m%d"))

        ok, time_str, ind = self.GetFirstEntry()
        while ok:
            daytime = Daytime.create_from_str(time_str)
            if daytime:
                day_times.append(daytime)
            ok, time_str, ind = self.GetNextEntry(ind)

        self.SetPath("/")
        return sorted(day_times)

    def read_timeval(self, daytime):
        self.SetPath(self.cur_day.strftime("/%y%m%d"))
        val_as_str = self.Read(str(daytime))
        val = self._create_time_val_from_str(val_as_str)
        self.SetPath("/")
        return val

    def _create_time_val_from_str(self, s):
        val = s.split(CONFIG_SEP_CHAR)
        job = ""
        psp = ""
        if len(val) >= 1:
            job = val[0]
            if len(val) >= 2:
                psp = val[1]
        return Timeval(job, psp)

    def read_day_items(self):
        day_items = {}  # minutes -> list of values
        for daytime in self.read_day_times():
            timeval = self.read_timeval(daytime)
            day_items[daytime] = timeval

        return day_items

    def del_day_item(self, daytime):
        self.SetPath(self.cur_day.strftime("/%y%m%d"))
        ok = self.DeleteEntry(str(daytime))
        self.SetPath("/")
        return ok

    def write_day_item(self, daytime, timeval):
        self.SetPath(self.cur_day.strftime("/%y%m%d"))
        ok = self.Write(str(daytime), str(timeval))
        self.SetPath("/")
        return ok

    def rename_daytime(self, old_time, new_time):
        self.SetPath(self.cur_day.strftime("/%y%m%d"))
        ok = self.RenameEntry(str(old_time), str(new_time))
        self.SetPath("/")
        if not ok:
            wx.MessageBox(
                "Zeit konnte nicht geändert werden.\n"
                "Vermutlich gibt es schon eine Zeile mit dieser Zeit.",
                "Fehler beim umbenennen")
        return ok

    def write_job(self, job, daytime = None):
        # val.job
        if daytime:
            val = self.read_timeval(daytime)
        else:
            daytime = Daytime.create_with_current_time(self.round_min)
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

    def write_psp(self, psp, daytime = None):
        if daytime:
            chg = []
            job = self.read_timeval(daytime).job
            for t in self.read_day_times():
                v = self.read_timeval(t)
                if v.job == job:
                    v.psp = psp
                    if self.write_day_item(t, v):
                        chg.append(t)
            return chg
        else:
            now = Daytime.create_with_current_time(self.round_min)
            val = Timeval("", new_text)
            self.write_day_item(now, val)
            return [now]

    def read_settings(self):
        self.SetPath("/")
        self.round_min = self.ReadInt("round_min", 1)

    def write_settings(self):
        self.SetPath("/")
        self.WriteInt("round_min", self.round_min)


class Timeval:

    def __init__(self, job, psp):
        self.job = job
        self.psp = psp

    def __str__(self):
        return self.job + CONFIG_SEP_CHAR + self.psp

    def GetTuple(self):
        return self.job, self.psp