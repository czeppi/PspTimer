#! /usr/bin/env python
#-*- coding: latin-1 -*-

##########################################
## PSP-Timer                            ##
## Copyright 2005 by Christian Czepluch ##
##########################################

"""Basic application class."""

__author__ = "Christian Czepluch"
__cvsid__ = "$Id: cvscmd.py,v 1.0.0.0 2003/07/12 21:15:33 RD Exp $"
__revision__ = "$Revision: 1.0.0.0 $"[11:-2]

############################################################

import sys
import datetime
#import cPickle
import re
import wx
import wx.lib.mixins.listctrl  as  listmix

#---------------------------------------------------------------------------

app_name = "PSP-Timer"
config_sep_char = '#'
config_num_cols = 2
time_rexp = re.compile("^([0-9]{1,2}):?([0-9]{2})$")
date_rexp = re.compile("^([0-9][0-9])([0-9][0-9])([0-9][0-9])$")
num_history_entries = 20
max_int = 2147483647

#---------------------------------------------------------------------------

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

        
def DaytimeNow():
    now = datetime.datetime.now()
    minutes = 60 * now.hour + now.minute
    step    = config.round_min
    minutes = ((minutes + step/2) / step) * step
    return Daytime(minutes)
        
#~ class Settings():
    #~ def __init__(self):
        #~ self.round_min = 1
        
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

    def __init__(self):
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
            daytime = DaytimeNow()
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
            cur_day = config.GetDay()
            for day in reversed(config.ReadDays()):
                config.SetDay(day)
                for t in config.ReadDaytimes():
                    v = self.ReadTimeval(t)
                    if v.job == job and v.psp:
                        psp_set.add(v.psp)
                if len(psp_set) > 0: # Eintrag gefunden (aber immer ganzen Tag einlesen)
                    break
            config.SetDay(cur_day)
        
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
                    if config.WriteDayitem(t, v):
                        chg.append(t)
            return chg
        else:
            now = DaytimeNow()
            val = config.Timeval("", new_text)
            config.WriteDayitem(now, val)
            return [now]

    def ReadSettings(self):
        self.SetPath("/")
        self.round_min = self.ReadInt("round_min", 1)

    def WriteSettings(self):
        self.SetPath("/")
        self.WriteInt("round_min", self.round_min)


def SortCallback(item1, item2):
    return item1 - item2

#---------------------------------------------------------------------------
class ListDropTarget(wx.PyDropTarget):
    def __init__(self, list_ctrl):
        wx.DropTarget.__init__(self)
        self.list_ctrl = list_ctrl

        # specify the type of data we will accept
        self.data = wx.CustomDataObject("ListItem")
        self.SetDataObject(self.data)

    # some virtual methods that track the progress of the drag
    def OnEnter(self, x, y, drag_result):
        return drag_result

    def OnLeave(self):
        pass

    def OnDrop(self, x, y):
        row, flags = self.list_ctrl.HitTest(wx.Point(x,y))
        return 0 <= row and row < self.list_ctrl.GetItemCount() - 2

    def OnDragOver(self, x, y, drag_result):
        # The value returned here tells the source what kind of visual
        # feedback to give.  For example, if wxDragCopy is returned then
        # only the copy cursor will be shown, even if the source allows
        # moves.  You can use the passed in (x,y) to determine what kind
        # of feedback to give.  In this case we return the suggested value
        # which is based on whether the Ctrl key is pressed.
        row, flags = self.list_ctrl.HitTest(wx.Point(x,y))
        if 0 <= row and row < self.list_ctrl.GetItemCount() - 2:
            return wx.DragMove
        else:
            return wx.DragNone

    # Called when OnDrop returns True.  We need to get the data and
    # do something with it.
    def OnData(self, x, y, drag_result):
        # copy the data from the drag source to our data object
        
        drop_row, flags = self.list_ctrl.HitTest(wx.Point(x,y))
        
        if self.GetData():
            data = self.data.GetData()
            drag_row = int(data)
            self.list_ctrl.MoveItem(drag_row, drop_row)
            
        # what is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return drag_result
       
#---------------------------------------------------------------------------
class SettingsDlg(wx.Dialog):
    def __init__(self, parent):
        title = 'Einstellungen'
        wx.Dialog.__init__(self, parent, -1, title)
        
        #~ font = self.GetFont()
        #~ font.SetPointSize(config.fontsize)
        #~ self.SetFont(font)
        
        # Ctrls
        ok_button       = wx.Button(self, wx.ID_OK, "OK")
        cancel_button   = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.round_ctrl = wx.TextCtrl(self, -1, str(config.round_min))

        # grid_sizer
        grid_sizer = wx.FlexGridSizer(0, 2, 0, 5)
        grid_sizer.AddGrowableCol(1, 0)
        
        grid_sizer.Add(
            wx.StaticText(self, -1, "Minuten runden auf:"), 
                0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.round_ctrl, 0, wx.EXPAND)

        # button_sizer
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(ok_button, 0, wx.ALIGN_CENTER)
        button_sizer.Add(cancel_button, 0, wx.ALIGN_CENTER)
        
        # Rest
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.AddSpacer(5)
        vsizer.Add(grid_sizer, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, border = 5)
        vsizer.AddSpacer(5)
        vsizer.Add(button_sizer, 0, wx.ALIGN_CENTER|wx.LEFT|wx.RIGHT, border = 5)
        vsizer.AddSpacer(5)

        self.SetSizer(vsizer)
        self.Fit()

#---------------------------------------------------------------------------
class MainListCtrl(wx.ListCtrl,
                   listmix.ListCtrlAutoWidthMixin,
                   listmix.TextEditMixin):

    def __init__(self, parent, id, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)

        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.Populate()
        listmix.TextEditMixin.__init__(self)
        drop_target = ListDropTarget(self)
        self.SetDropTarget(drop_target)

    def Populate(self):
        # for normal, simple columns, you can add them like this:
        self.InsertColumn(0, "Zeit", format=wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(1, "Aufgabe")
        self.InsertColumn(2, "PSP-Element")

        self.SetColumnWidth(0, 50)
        self.SetColumnWidth(1, 100)
        self.SetColumnWidth(2, 50)

    def ShowCurDay(self, select = set()):
        self.DeleteAllItems()
        for daytime in config.ReadDaytimes():
            val = config.ReadTimeval(daytime)
            row = self.InsertItem(max_int, "")
            self.SetItemData(row, daytime)
            self.SetItem(row, 0, str(daytime))
            self.SetItem(row, 1, val.job)
            self.SetItem(row, 2, val.psp)
        
        row = self.InsertItem(max_int, "")
        self.SetItemData(row, max_int)  # leeres Item hinten anhängen
        self.SortItems(SortCallback)
        
        for row in range(self.GetItemCount()):
            if self.GetItemData(row) in select:
                self.SetItemState(row, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        
    def DelItem(self, row):
        item_time = DaytimeFromStr(self.GetItemText(row))
        if item_time:
            config.DelDayitem(item_time)
            config.Flush()
            self.DeleteItem(row)
        
    def ChangeText(self, row, col, new_text):
        day = config.GetDay()
        old_text = self.GetItem(row, col).GetText()
        sel_times = []
        changed = False
        
        if old_text == new_text:
            return
        
        if col == 0:  # Zeit
            new_time = DaytimeFromStr(new_text)
            old_time = DaytimeFromStr(old_text)
            sel_times = [new_time]
            
            if new_time:   # item ändern (oder neu)
                if old_time:  # ändern
                    if config.RenameDaytime(old_time, new_time):
                        changed = True
                else:         # neu
                    if config.WriteDayitem(new_time, config.Timeval('', '')):
                        changed = True
                
            elif old_time:    # item löschen
                if config.DeleteDayitem(old_time):
                    changed = True
                
        else:  # nicht Zeit
            daytime = DaytimeFromStr(self.GetItemText(row))
            if daytime or new_text:
                if col == 1:
                    if config.WriteJob(new_text, daytime):
                        sel_times = [daytime]
                        changed = True
                elif col == 2:
                    sel_times = config.WritePsp(new_text, daytime)
                    if sel_times:
                        changed = True
        if changed:
            config.Flush()
            self.ShowCurDay(sel_times)
        
    def MoveItem(self, from_row, to_row):
        from_time     = Daytime(self.GetItemData(from_row))
        to_time       = Daytime(self.GetItemData(to_row))
        day_items     = config.ReadDayItems()
        sorted_times  = sorted(day_items.keys())
        
        if from_time not in sorted_times or to_time not in sorted_times:
            return
            
        from_index = sorted_times.index(from_time)
        to_index   = sorted_times.index(to_time)
        
        if (from_index < 0 or len(sorted_times)-1 <= from_index
        or  to_index   < 0 or len(sorted_times)-1 <= to_index
        or  from_index == to_index):
            return
            
        from_len = sorted_times[from_index+1] - from_time
        to_len   = sorted_times[to_index+1]   - to_time
            
        # Write Config
        if from_index < to_index:  # nach hinten schieben
            for i in range(from_index, to_index + 1):
                config.DelDayitem(sorted_times[i])
                
            for i in range(from_index + 1, to_index + 1):
                old_time = sorted_times[i]
                new_time = old_time - from_len
                config.WriteDayitem(new_time, day_items[old_time])
                
            from_time_new = to_time + to_len - from_len
            config.WriteDayitem(from_time_new, day_items[from_time])
                
        else: # nach vorne schieben
            for i in range(to_index, from_index + 1):
                config.DelDayitem(sorted_times[i])
                
            from_time_new = to_time
            config.WriteDayitem(from_time_new, day_items[from_time])
            
            for i in range(to_index, from_index):
                old_time = sorted_times[i]
                new_time = old_time + from_len
                config.WriteDayitem(new_time, day_items[old_time])
                
        config.Flush()
            
        # Liste neu anzeigen
        self.ShowCurDay(select = set([from_time_new]))
        
    def ChgTimespan(self, row, new_timespan):
        if row + 1 >= self.GetItemCount(): # muss noch Zeile nach 'row' geben
            return
    
        start_time    = Daytime(self.GetItemData(row))
        end_time      = Daytime(self.GetItemData(row + 1))
        old_timespan  = end_time - start_time
        time_diff     = new_timespan - old_timespan
        day_items     = config.ReadDayItems()
        sorted_times  = sorted(day_items.keys())
        
        # betroffene Elemente löschen
        for t in sorted_times:
            if t > start_time:
                config.DelDayitem(t)
        
        # betroffene Elemente ändern
        for t in sorted_times:
            if t > start_time:
                config.WriteDayitem(t + time_diff, day_items[t])
            
        config.Flush()
            
        # Liste neu anzeigen
        self.ShowCurDay(select = set([start_time]))
            
    def OnChar(self, event):
        """ Überschreibt listmix.TextEditMixin.OnChar """

        keycode = event.GetKeyCode()
        print('keycode: {}'.format(keycode))
        
        
        if keycode == wx.WXK_TAB and event.ShiftDown():
            self.CloseEditor()
            if self.curCol-1 >= 0:
                self.OpenEditor(self.curCol-1, self.curRow)
            
        elif keycode == wx.WXK_TAB:
            self.CloseEditor()
            if self.curCol+1 < self.GetColumnCount():
                self.OpenEditor(self.curCol+1, self.curRow)

        elif keycode == wx.WXK_ESCAPE:
            self.CloseEditor()

        elif keycode == wx.WXK_DOWN:
            self.CloseEditor()
            if self.curRow+1 < self.GetItemCount():
                self._SelectIndex(self.curRow+1)
                self.OpenEditor(self.curCol, self.curRow)

        elif keycode == wx.WXK_UP:
            self.CloseEditor()
            if self.curRow > 0:
                self._SelectIndex(self.curRow-1)
                self.OpenEditor(self.curCol, self.curRow)
            
        else:
            event.Skip()
       
#---------------------------------------------------------------------------

class MyFrame(wx.Frame):
    """Frame class."""
    
    ############################################################################
    ## Init
    
    def __init__(self, parent=None, id=-1, title=app_name,
                 pos=(0,0), size=(250, 200)):
        """Create a Frame instance."""
        wx.Frame.__init__(self, parent, id, title, pos, size)  # style=wx.WANTS_CHARS
        self.ignore_next_end_edit_event = False
        
        self.SetIcon(wx.Icon("psptimer.ico", wx.BITMAP_TYPE_ICO))
        self.CreateToolBar()
        self.list = MainListCtrl(
            self, -1,
            style=wx.LC_REPORT | wx.BORDER_NONE)# | wx.LC_SORT_ASCENDING)
        self.list.ShowCurDay()
        self.SetTitle()
        self.settings = config.ReadSettings()

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnEndEdit)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnBeginDrag)
        self.Bind(wx.EVT_ACTIVATE, self.OnActivate)

    def CreateToolBar(self):
        toolbar = wx.Frame.CreateToolBar(self)
        self.AddToolItem(toolbar, "daylist",  self.OnDayList,  tooltip="Liste aller Tage")
        self.AddToolItem(toolbar, "prevday",  self.OnPrevDay,  tooltip="vorheriger Tag")
        self.AddToolItem(toolbar, "nextday",  self.OnNextDay,  tooltip="nächster Tag")
        self.AddToolItem(toolbar, "delday",   self.OnDelDay,   tooltip="Alle Tageseinträge löschen")
        self.AddToolItem(toolbar, "sum",      self.OnSum,      tooltip="Ergebnis anzeigen")
        self.AddToolItem(toolbar, "settings", self.OnSettings, tooltip="Einstellungen")
        self.AddToolItem(toolbar, "export",   self.OnExport,   tooltip="Export aller Daten")
        self.AddToolItem(toolbar, "import",   self.OnImport,   tooltip="Import aller Daten")
        toolbar.Realize()

    def AddToolItem(self, toolbar, bmp_name, handler, tooltip=""):
        bmp = wx.Bitmap(bmp_name + ".bmp", wx.BITMAP_TYPE_BMP)
        label = ""
        new_tool = toolbar.AddTool(wx.ID_ANY, label, bmp, tooltip)
        self.Bind(wx.EVT_TOOL, handler, id = new_tool.GetId())
        
    def SetTitle(self):
        today   = datetime.date.today()
        cur_day = config.GetDay()
        if cur_day == today:
            datestr = "heute"
        elif cur_day == today + datetime.timedelta(days=1):
            datestr = "morgen"
        elif cur_day == today + datetime.timedelta(days=-1):
            datestr = "gestern"
        else:
            datestr = cur_day.strftime("%a %d. %b %Y")
        title = app_name + " - " + datestr
        wx.Frame.SetTitle(self, title)
        
    ############################################################################
    ## events
    
    def OnDayList(self, event):
        str2date     = {}
        datestr_list = []
        for day in reversed(config.ReadDays()):
            datestr = day.strftime("%a %d. %b %Y")
            str2date[datestr] = day
            datestr_list.append(datestr)
            
        dlg = wx.SingleChoiceDialog(
            self, 'Bitte einen Tag auswählen', 'Tagauswahl',
            datestr_list, wx.CHOICEDLG_STYLE
            )

        if dlg.ShowModal() == wx.ID_OK:
            datestr = dlg.GetStringSelection()
            if datestr in str2date:
                config.SetDay(str2date[datestr])
                self.SetTitle()
                self.list.ShowCurDay()

        dlg.Destroy()
        
    def OnPrevDay(self, event):
        if self.list.editor.IsShown():
            self.list.CloseEditor()
        cur_day = config.GetDay()
        cur_day -= datetime.timedelta(days = 1)
        config.SetDay(cur_day)
        self.SetTitle()
        self.list.ShowCurDay()
        
    def OnNextDay(self, event):
        if self.list.editor.IsShown():
            self.list.CloseEditor()
        cur_day = config.GetDay()
        cur_day += datetime.timedelta(days = 1)
        config.SetDay(cur_day)
        self.SetTitle()
        self.list.ShowCurDay()
        
    def OnDelDay(self, event):
        if self.list.editor.IsShown():
            self.list.CloseEditor()
        answer = wx.MessageBox(
            "Alle Tageseinträge löschen?", "Tag löschen", 
            wx.YES_NO | wx.ICON_QUESTION)
            
        if answer == wx.YES:
            config.SetPath("/")
            config.DeleteGroup(config.GetDay().strftime("/%y%m%d"))
            self.list.ShowCurDay()
        
    def OnSum(self, event):
        # time2psp
        time2psp = {}
        for t in config.ReadDaytimes():
            psp = config.ReadTimeval(t).psp
            if not psp or not psp[0].isalpha():
                psp = '-'
            time2psp[t] = psp
                
        if len(time2psp) == 0:
            return
        
        # psp_map
        psp_map = {}  # psp -> timesum
        t0  = Daytime(-1)
        sum = 0
        for t1 in sorted(time2psp.keys()):
            if t0 >= 0:
                psp = time2psp[t0]
                if psp not in psp_map:
                    psp_map[psp] = Daytime(0)
                psp_map[psp] += t1 - t0
                if psp and psp !=  '-':
                    sum += t1 - t0
            t0 = t1
        
        msg_text  = '\n'.join([
            p + '\t = ' + str(t) + ' \t(' + str(round(t / 60.0, 2)) + ')'
            for p, t in psp_map.items()])
        msg_text += '\n' + 20 * '-' + '\nsum = ' + str(round(sum / 60.0, 2))
        msg_title = app_name + ' - Sum(' + config.GetDay().strftime("%d.%m.%y") + ')'
        wx.MessageBox(msg_text, msg_title)
        
    def OnSettings(self, event):
        dlg = SettingsDlg(self)
        
        if dlg.ShowModal() == wx.ID_OK:
            # round_min
            round_str = dlg.round_ctrl.GetValue()
            if round_str and round_str.isdigit():
                config.round_min = int(round_str)
                
            config.WriteSettings()
            config.Flush()

        dlg.Destroy()
        
    def OnExport(self, event):
        # filename
        filename = wx.FileSelector(
            "Exportfile wählen", 
            default_filename="psptimer.dat")
        if not filename:
            return
            
        # lines
        lines = []
        cur_day = config.GetDay()
        for day in config.ReadDays():
            config.SetDay(day)
            for daytime in config.ReadDaytimes():
                val  = config.ReadTimeval(daytime)
                line = "%s;%s;%s;%s" % (str(day), str(daytime), val.job, val.psp)
                lines.append(line)
        config.SetDay(cur_day)
        
        # write
        open(filename, 'w').write('\n'.join(lines))
        
    def OnImport(self, event):
        # filename
        filename = wx.FileSelector(
            "Exportfile wählen", 
            default_filename="psptimer.dat")
        if not filename:
            return
        
        # Daten einlesen
        import_data = {}  # day -> Daytime -> Config.Timeval
        for row, line in enumerate(open(filename, 'r').readlines()):
            except_text = "%i: %s" % (row, line.strip())
            
            # items
            items = line.split(';')
            if len(items) != 4:
                raise Exception(except_text)
                
            # day
            day = datetime.datetime.strptime(items[0].strip(), "%Y-%m-%d") 
            
            # daytime
            daytime = DaytimeFromStr(items[1].strip())
            if not daytime:
                raise Exception(except_text)
                
            # timeval
            job = items[2].strip()
            psp = items[3].strip()
            timeval = Config.Timeval(job, psp)
            
            # import_data
            if day not in import_data:
                import_data[day] = {}
            import_day = import_data[day]
            import_day[daytime] = timeval
            
        if len(import_data) == 0:
            raise Exception('Importdaten sind leer')
        
        # Sicherheitsdialog
        answer = wx.MessageBox(
            "Sollen existierende Daten wirklich ersetzt werden?", 
            "Daten ersetzen",
            wx.YES_NO | wx.CANCEL, self)
        if answer != wx.YES:
            return
        
        # Altdaten löschen
        config.SetPath("/")
        for day in config.ReadDays():
            config.SetDay(day)
            config.DeleteGroup(day.strftime("/%y%m%d"))
            
        # neue Daten schreiben
        for day in sorted(import_data.keys()):
            config.SetDay(day)
            day_data = import_data[day]
            for daytime in sorted(day_data.keys()):
                timeval = day_data[daytime]
                config.WriteDayitem(daytime, timeval)
            
        # Anzeige
        last_day = sorted(import_data.keys())[-1]
        config.SetDay(last_day)
            
        if self.list.editor.IsShown():
            self.list.CloseEditor()
        self.SetTitle()
        self.list.ShowCurDay()
            
    def OnEndEdit(self, event):
        ### wird komischerweise 2x aufgerufen (in der wx-2.6.3.3-Version nicht mehr)
        #~ if self.ignore_next_end_edit_event:
            #~ self.ignore_next_end_edit_event = False
            #~ event.Veto()
            #~ return
            
        self.ignore_next_end_edit_event = True
        
        row      = event.GetIndex()
        col      = event.GetColumn()
        new_text = event.GetText()
        old_text = self.list.GetItem(row, col).GetText()
        
        #~ if old_text == new_text:
            #~ return
            
        self.list.ChangeText(row, col, new_text)
        
        #~ if col == 0 and (old_text or new_text):
            #~ event.Veto()  # da schon mit SetStringItem gesetzt
        event.Veto()
        
    def OnRightClick(self, event):
        # col
        x = event.GetPoint().x
        col = 0
        while x >= self.list.GetColumnWidth(col):
            x -= self.list.GetColumnWidth(col)
            col += 1
            
        # self.cur_listitem
        row = event.GetIndex()
        self.cur_listitem = self.list.GetItem(row, col)
                
        if col == 0:  # Zeit
            # menu
            menu = wx.Menu()
            
            new_menu_item = menu.Append(wx.ID_ANY, "Zeile löschen")
            self.Bind(wx.EVT_MENU, self.OnDelItem, id = new_menu_item.GetId())
            
            if row + 2 < self.list.GetItemCount(): # nicht beim letzten Element
                new_menu_item = menu.Append(wx.ID_ANY, "Zeitdauer ändern")
                self.Bind(wx.EVT_MENU, self.OnChgTimespan, id = new_menu_item.GetId())
            
            t0 = DaytimeFromStr(self.cur_listitem.GetText())
            if t0:
                menu.AppendSeparator()
                
                t_start = t0 + 4 - (t0 + 4) % 5 - 10
                t_stop  = t0 + t0 % 5 + 11
                
                for t in range(t_start, t_stop, 5):
                    new_menu_item = menu.Append(wx.ID_ANY, str(Daytime(t)))
                    self.Bind(wx.EVT_MENU, self.OnChangeItem, id = new_menu_item.GetId())
            
            self.PopupMenu(menu, event.GetPoint())
        else:
            # hist_list
            hist_list = []
            cur_day = config.GetDay()
            for day in reversed(config.ReadDays()):
                config.SetDay(day)
                for daytime in reversed(config.ReadDaytimes()):
                    timeval = config.ReadTimeval(daytime)
                    if col == 1:
                        val = timeval.job
                    elif col == 2:
                        val = timeval.psp
                    else:
                        continue
                    if val and val not in hist_list:
                        hist_list.append(val)
                        if len(hist_list) >= num_history_entries:
                            break
                if len(hist_list) >= num_history_entries:
                    break
            config.SetDay(cur_day)
            
            # menu
            menu = wx.Menu()
            
            for val in hist_list:
                new_menu_item = menu.Append(wx.ID_ANY, val)
                self.Bind(wx.EVT_MENU, self.OnChangeItem, id = new_menu_item.GetId())
            
            self.PopupMenu(menu, event.GetPoint())
            
            #~ item = wx.GetSingleChoice(
                #~ "Bitte eine Element auswählen",
                #~ "Elementauswahl",
                #~ ["aa", "bb", "cc"],
                #~ self)
            
    def OnChangeItem(self, event):
        # row, col
        if not isinstance(self.cur_listitem, wx.ListItem):
            return
        row = self.cur_listitem.GetId()
        col = self.cur_listitem.GetColumn()
            
        # new_text
        menu = event.GetEventObject()
        if not isinstance(menu, wx.Menu):
            return
        menuitem = menu.FindItemById(event.GetId())
        if not isinstance(menuitem, wx.MenuItem):
            return
        new_text = menuitem.GetItemLabelText()
            
        # set new_text
        self.list.ChangeText(row, col, new_text)
        
    def OnDelItem(self, event):
        # row, col
        if not isinstance(self.cur_listitem, wx.ListItem):
            return
        row = self.cur_listitem.GetId()
        self.list.DelItem(row)
        self.cur_listitem = None
    
    def OnChgTimespan(self, event):
        if not isinstance(self.cur_listitem, wx.ListItem):
            return
        row           = self.cur_listitem.GetId()
        start_time    = Daytime(self.list.GetItemData(row))
        end_time      = Daytime(self.list.GetItemData(row + 1))
        old_time_span = int(end_time - start_time)
        
        new_time_str = wx.GetTextFromUser (
            "Bitte neue Zeitlänge in Minuten eingeben.", "Zeitlänge ändern", 
            str(old_time_span), parent = self)
        
        if not new_time_str:
            return
            
        new_time_span = int (new_time_str)
        
        if new_time_span > 0 and new_time_span != old_time_span:
           self.list.ChgTimespan(row, new_time_span)
    
    def OnKeyDown(self, event):
        key_code = event.GetKeyCode()
    
        # num_items
        num_items = self.list.GetItemCount()
        if num_items == 0:
            event.Skip()
            return
    
        # 
        #~ if (event.ShiftDown() or event.ControlDown()
        #~ or  event.AltDown()   or event.MetaDown()):
            #~ event.Skip()
            #~ return
        
        # sel_item
        sel_item = None
        for row in range(num_items):
            if self.list.GetItemState(row, wx.LIST_STATE_SELECTED):
                if sel_item != None:  # nicht eindeutig?
                    event.Skip()
                    return
                sel_item = row
                
        if sel_item == None:
            event.Skip()
            return
        
        if key_code == wx.WXK_DELETE:
            self.list.DelItem(sel_item)
        #~ elif key_code == wx.WXK_UP:
            #~ if choice_nr > 0:
                #~ new_choice_nr = choice_nr - 1
        #~ elif key_code == wx.WXK_DOWN:
            #~ if choice_nr < choice_num - 1:
                #~ new_choice_nr = choice_nr + 1
        #~ elif key_code == wx.WXK_HOME:
            #~ new_choice_nr = 0
        #~ elif key_code == wx.WXK_END:
            #~ new_choice_nr = choice_num - 1
        else:
            event.Skip()
    
    def OnBeginDrag(self, event):
        row = event.GetIndex()
        if row < self.list.GetItemCount()-2:
            drag_source = wx.DropSource(self)
            my_data = wx.CustomDataObject("ListItem")
            my_data.SetData(str(row))
            drag_source.SetData(my_data)
            result = drag_source.DoDragDrop(True)
    
    def OnSize(self, event):
        s = self.GetClientSize()
        w, h = s.width, s.height
        self.list.SetSize(w, h)
        #self.list.SetDimensions(0, 0, w, h)
        
    def OnActivate(self, event):
        if event.GetActive():
            self.list.ShowCurDay()
        

#---------------------------------------------------------------------------

config = None

class App(wx.App):
    """Application class."""

    def Init(self):
        self.frame = MyFrame()
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True

    def OnExit(self):
        return 0


def main():
    global config

    app    = App()
    config = Config()

    app.Init()
    app.MainLoop()

if __name__ == '__main__':
    main()
