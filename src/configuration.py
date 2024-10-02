import datetime
import re

import wx

from daytime import DaytimeFromStr, DaytimeNow


config_sep_char = '#'
date_rexp = re.compile("^([0-9][0-9])([0-9][0-9])([0-9][0-9])$")


class Config(wx.Config):
    class Timeval:
        def __init__(self, job, psp):
            self.job = job
            self.psp = psp

        def __str__(self):
            return self.job + config_sep_char + self.psp

        def GetTuple(self):
            return self.job, self.psp

    def TimevalFromStr(self, s):
        val = s.split(config_sep_char)
        job = ""
        psp = ""
        if len(val) >= 1:
            job = val[0]
            if len(val) >= 2:
                psp = val[1]
        return self.Timeval(job, psp)

    def __init__(self, app_name: str):
        wx.Config.__init__(self, app_name)
        self.cur_day = datetime.date.today()
        self.ReadSettings()

    def SetDay(self, day):
        self.cur_day = day

    def GetDay(self):
        return self.cur_day

    def ReadDays(self):
        self.SetPath("/")

        day_list = []  # Liste von datetime.date
        ok, group, ind = self.GetFirstGroup()
        while ok:
            m = date_rexp.match(group)
            if m:
                day = datetime.date(2000 + int(m.group(1)), int(m.group(2)), int(m.group(3)))
                day_list.append(day)
            ok, group, ind = self.GetNextGroup(ind)

        return sorted(day_list)

    def ReadDaytimes(self):
        day_times = []
        self.SetPath(self.cur_day.strftime("/%y%m%d"))

        ok, timestr, ind = self.GetFirstEntry()
        while ok:
            daytime = DaytimeFromStr(timestr)
            if daytime:
                day_times.append(daytime)
            ok, timestr, ind = self.GetNextEntry(ind)

        self.SetPath("/")
        return sorted(day_times)

    def ReadTimeval(self, daytime):
        self.SetPath(self.cur_day.strftime("/%y%m%d"))
        valstr = self.Read(str(daytime))
        val    = self.TimevalFromStr(valstr)
        self.SetPath("/")
        return val

    def ReadDayItems(self):
        day_items = {}  # Minuten -> Liste von Werten
        for daytime in self.ReadDaytimes():
            timeval = self.ReadTimeval(daytime)
            day_items[daytime] = timeval

        return day_items

    def DelDayitem(self, daytime):
        self.SetPath(self.cur_day.strftime("/%y%m%d"))
        ok = self.DeleteEntry(str(daytime))
        self.SetPath("/")
        return ok

    def WriteDayitem(self, daytime, timeval):
        self.SetPath(self.cur_day.strftime("/%y%m%d"))
        ok = self.Write(str(daytime), str(timeval))
        self.SetPath("/")
        return ok

    def RenameDaytime(self, old_time, new_time):
        self.SetPath(self.cur_day.strftime("/%y%m%d"))
        ok = self.RenameEntry(str(old_time), str(new_time))
        self.SetPath("/")
        if not ok:
            wx.MessageBox(
                "Zeit konnte nicht geändert werden.\n"
                "Vermutlich gibt es schon eine Zeile mit dieser Zeit.",
                "Fehler beim umbenennen")
        return ok

    def WriteJob(self, job, daytime = None):
        # val.job
        if daytime:
            val = self.ReadTimeval(daytime)
        else:
            daytime = DaytimeNow(self.round_min)
            val     = self.Timeval("", "")
        val.job = job

        # val.psp aus anderen Einträgen suchen (gleicher Tag)
        psp_set = set()
        for t in self.ReadDaytimes():
            v = self.ReadTimeval(t)
            if v.job == job and v.psp:
                psp_set.add(v.psp)

        # nix gefunden -> val.psp aus anderen Einträgen suchen (alle Tage)
        if len(psp_set) == 0:
            cur_day = self.GetDay()
            for day in reversed(self.ReadDays()):
                self.SetDay(day)
                for t in self.ReadDaytimes():
                    v = self.ReadTimeval(t)
                    if v.job == job and v.psp:
                        psp_set.add(v.psp)
                if len(psp_set) > 0: # Eintrag gefunden (aber immer ganzen Tag einlesen)
                    break
            self.SetDay(cur_day)

        if len(psp_set) == 1:  # Werte eindeutig?
            val.psp = psp_set.pop()

        # Write
        return self.WriteDayitem(daytime, val)

    def WritePsp(self, psp, daytime = None):
        if daytime:
            chg = []
            job = self.ReadTimeval(daytime).job
            for t in self.ReadDaytimes():
                v = self.ReadTimeval(t)
                if v.job == job:
                    v.psp = psp
                    if self.WriteDayitem(t, v):
                        chg.append(t)
            return chg
        else:
            now = DaytimeNow(self.round_min)
            val = self.Timeval("", new_text)
            self.WriteDayitem(now, val)
            return [now]

    def ReadSettings(self):
        self.SetPath("/")
        self.round_min = self.ReadInt("round_min", 1)

    def WriteSettings(self):
        self.SetPath("/")
        self.WriteInt("round_min", self.round_min)
