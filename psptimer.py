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
import cPickle
import re
import wx
import wx.lib.mixins.listctrl  as  listmix

#---------------------------------------------------------------------------

app_name = "PSP-Timer"
config = wx.Config(app_name)
config_sep_char = '#'
config_num_cols = 2
time_rexp = re.compile("^([0-9]{1,2}):?([0-9]{2})$")
date_rexp = re.compile("^([0-9][0-9])([0-9][0-9])([0-9][0-9])$")
num_history_entries = 20

#---------------------------------------------------------------------------

class Minutes:
    def __init__(self, i):
        self.val = i
    
    def GetInt(self):
        return self.val
        
    def __str__(self):
        return "%02i:%02i" % (self.val / 60, self.val % 60)

def MinutesFromStr(s):
    m = time_rexp.match(key)
    if m:
        return Minutes(60 * int(m.group(1)) + int(m.group(2)))

def ConfigReadDays():
    """ Liefert eine Liste von datetime.date aus der Regestry 
    """
    config.SetPath("/")
    
    day_list = []
    ok, group, ind = config.GetFirstGroup()
    while ok:
        m = date_rexp.match(group)
        if not m:
            continue
        day = datetime.date(2000 + int(m.group(1)), int(m.group(2)), int(m.group(3)))
        day_list.append(day)
        ok, group, ind = config.GetNextGroup(ind)
        
    return sorted(day_list)
        
def ConfigReadTimeVal(time_key):
    ### config muss auf dem gewünschten Tag stehen
    val = config.Read(time_key).split(config_sep_char)  # liesst Wert zur Zeit key
    if len(val) < config_num_cols:
        val += (config_num_cols - len(val)) * ['']
    elif len(val) > config_num_cols:
        val = val[:(len(val) - config_num_cols)]
    return val

#~ def ConfigReadDayKeys(day):
    #~ day_items = {}  # Minuten -> Liste von Werten
    #~ config.SetPath(day.strftime("/%y%m%d"))
    
    #~ ok, key, ind = config.GetFirstEntry()
    #~ while ok:
        #~ # num_min
        #~ num_min = -1
        #~ m = time_rexp.match(key)
        #~ if not m:
            #~ contiue
        #~ num_min = 60 * int(m.group(1)) + int(m.group(2))
            
        #~ # day_items
        #~ val = ConfigReadTimeVal(key)
        #~ day_items[num_min] = val
        #~ ok, key, ind = config.GetNextEntry(ind)
        
    #~ config.SetPath(day.strftime("/"))
    #~ return day_items

def ConfigReadDayItems(day):
    day_items = {}  # Minuten -> Liste von Werten
    config.SetPath(day.strftime("/%y%m%d"))
    
    ok, key, ind = config.GetFirstEntry()
    while ok:
        # num_min
        num_min = -1
        m = time_rexp.match(key)
        if not m:
            contiue
        num_min = 60 * int(m.group(1)) + int(m.group(2))
            
        # day_items
        val = ConfigReadTimeVal(key)
        day_items[num_min] = val
        ok, key, ind = config.GetNextEntry(ind)
        
    config.SetPath(day.strftime("/"))
    return day_items

def ConfigMinutes2Timestr(num_min):
    return datetime.time(num_min/60,num_min%60).strftime('%H:%M')

def ConfigWriteItem(day, num_min, val_list):
    pass

def SortCallback(item1, item2):
    return item1 - item2

#---------------------------------------------------------------------------
class ListDropTarget(wx.PyDropTarget):
    def __init__(self, list_ctrl):
        wx.PyDropTarget.__init__(self)
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
class MainListCtrl(wx.ListCtrl,
                   listmix.ListCtrlAutoWidthMixin,
                   listmix.TextEditMixin):

    def __init__(self, parent, id, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        self.parent = parent
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

    def ShowDay(self, day):
        self.DeleteAllItems()
        day_items = ConfigReadDayItems(day)
        for num_min in sorted(day_items.keys()):
            val     = day_items[num_min]
            timestr = datetime.time(num_min/60,num_min%60).strftime('%H:%M')            
            row = self.InsertStringItem(sys.maxint, "")
            self.SetItemData(row, num_min)
            self.SetStringItem(row, 0, timestr)
            for i in range(config_num_cols):
                self.SetStringItem(row, i + 1, val[i])
        
        row = self.InsertStringItem(sys.maxint, "")
        self.SetItemData(row, sys.maxint)  # leeres Item hinten anhängen
        self.SortItems(SortCallback)
        
    def DelItem(self, day, row):
        item_time = self.GetItemText(row)
        if item_time:
            config.SetPath(day.strftime("/%y%m%d"))
            self.DeleteItem(row)
            config.DeleteEntry(item_time)
            config.Flush()
            config.SetPath("/")
        
    def ChangeText(self, day, row, col, new_text):
        old_text = self.GetItem(row, col).GetText()
        
        config.SetPath(day.strftime("/%y%m%d"))
        
        if col == 0:  # Zeit
            if new_text:   # item ändern (oder neu)
                m = time_rexp.match(new_text)
                if m:
                    num_min = 60 * int(m.group(1)) + int(m.group(2))
                    new_text = ConfigMinutes2Timestr(num_min)
                    
                    if old_text:  # ändern
                        config.RenameEntry(old_text, new_text)
                    else:         # neu
                        config.Write(new_text, '')
                    
                    self.SetStringItem(row, col, new_text)
                    self.SetItemData(row, num_min)
                    if not old_text:
                        row = self.InsertStringItem(sys.maxint, "")
                        self.SetItemData(row, sys.maxint)  # leeres Item hinten anhängen
                        
                    self.SortItems(SortCallback)
                    
            elif old_text:    # item löschen
                self.DeleteItem(row)
                config.DeleteEntry(old_text)
                config.Flush()
                
        else:  # nicht Zeit
            key = self.GetItemText(row)
            if key:
                val = ConfigReadTimeVal(key)
                val[col-1] = new_text
                config.Write(key, config_sep_char.join(val))
                
                if col == 2:  # PSP-Element
                    for r in range(self.GetItemCount()):
                        k = self.GetItemText(r)
                        v = ConfigReadTimeVal(k)
                        if v[0] == val[0]:
                            v[1] = new_text
                            config.Write(k, config_sep_char.join(v))
                            self.SetStringItem(r, col, new_text)
                        
                config.Flush()
                
            elif new_text:
                now = datetime.datetime.now()
                key = now.strftime("%H:%M")
                
                val = config_num_cols * ['']
                val[col-1] = new_text
                config.Write(key, config_sep_char.join(val))
                config.Flush()
                
                num_min = 60 * now.hour + now.minute
                self.SetItemData(row, num_min)
                self.SetStringItem(row, 0, key)
                
                new_row = self.InsertStringItem(sys.maxint, "")
                self.SetItemData(new_row, sys.maxint)  # leeres Item hinten anhängen
                
        config.SetPath("/")
        
    def MoveItem(self, from_row, to_row):
        #wx.MessageBox(str(to_row), str(from_row))
            
        from_minutes  = self.GetItemData(from_row)
        to_minutes    = self.GetItemData(to_row)
        day_items     = ConfigReadDayItems(self.parent.cur_day)
        sorted_times  = sorted(day_items.keys())
        
        if from_minutes not in sorted_times or to_minutes not in sorted_times:
            return
            
        from_index = sorted_times.index(from_minutes)
        to_index   = sorted_times.index(to_minutes)
        
        if (from_index < 0 or len(sorted_times)-1 <= from_index
        or  to_index   < 0 or len(sorted_times)-1 <= to_index
        or  from_index == to_index):
            return
            
        from_len = sorted_times[from_index+1] - from_minutes
        to_len   = sorted_times[to_index+1]   - to_minutes
            
        # Write Config
        config.SetPath(self.parent.cur_day.strftime("/%y%m%d"))
        
        if from_index < to_index:  # nach hinten schieben
            for i in range(from_index, to_index + 1):
                timestr = ConfigMinutes2Timestr(sorted_times[i])
                config.DeleteEntry(timestr)
                
            for i in range(from_index + 1, to_index + 1):
                minutes_i = sorted_times[i]
                timestr = ConfigMinutes2Timestr(minutes_i - from_len)
                valstr  = config_sep_char.join(day_items[minutes_i])
                config.Write(timestr, valstr)
                
            from_minutes_new = to_minutes + to_len - from_len
            timestr = ConfigMinutes2Timestr(from_minutes_new)
            valstr  = config_sep_char.join(day_items[from_minutes])
            config.Write(timestr, valstr)
                
        else: # nach vorne schieben
            for i in range(to_index, from_index + 1):
                timestr = ConfigMinutes2Timestr(sorted_times[i])
                config.DeleteEntry(timestr)
                
            from_minutes_new = to_minutes
            timestr = ConfigMinutes2Timestr(from_minutes_new)
            valstr  = config_sep_char.join(day_items[from_minutes])
            config.Write(timestr, valstr)
            
            for i in range(to_index, from_index):
                minutes_i = sorted_times[i]
                timestr = ConfigMinutes2Timestr(minutes_i + from_len)
                valstr  = config_sep_char.join(day_items[minutes_i])
                config.Write(timestr, valstr)
                
        config.Flush()
        config.SetPath("/")
            
        # Liste neu anzeigen
        self.ShowDay(self.parent.cur_day)
        
        for row in range(self.GetItemCount()):
            if self.GetItemData(row) == from_minutes_new:
                self.SetItemState(row, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
       
    def OnChar(self, event):
        """ Überschreibt listmix.TextEditMixin.OnChar """

        keycode = event.GetKeyCode()
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
        self.cur_day = datetime.date.today()
        self.ignore_next_end_edit_event = False
        
        self.SetIcon(wx.Icon("psptimer.ico", wx.BITMAP_TYPE_ICO))
        self.CreateToolBar()
        self.list = MainListCtrl(
            self, -1,
            style=wx.LC_REPORT | wx.BORDER_NONE)# | wx.LC_SORT_ASCENDING)
        self.list.ShowDay(self.cur_day)
        self.SetTitle()

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnEndEdit)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnBeginDrag)

    def CreateToolBar(self):
        toolbar = wx.Frame.CreateToolBar(self)
        self.AddToolItem(toolbar, "daylist", self.OnDayList, tooltip="Liste aller Tage")
        self.AddToolItem(toolbar, "prevday", self.OnPrevDay, tooltip="vorheriger Tag")
        self.AddToolItem(toolbar, "nextday", self.OnNextDay, tooltip="nächster Tag")
        self.AddToolItem(toolbar, "delday",  self.OnDelDay,  tooltip="Alle Tageseinträge löschen")
        self.AddToolItem(toolbar, "sum",     self.OnSum,     tooltip="Ergebnis anzeigen")
        toolbar.Realize()

    def AddToolItem(self, toolbar, bmp_name, handler, tooltip=""):
        new_id = wx.NewId()
        bmp = wx.Bitmap(bmp_name + ".bmp", wx.BITMAP_TYPE_BMP)
        toolbar.AddSimpleTool(new_id, bmp, tooltip, "")
        self.Bind(wx.EVT_TOOL, handler, id = new_id)
        return new_id
        
    def SetTitle(self):
        today = datetime.date.today()
        if self.cur_day == today:
            datestr = "heute"
        elif self.cur_day == today + datetime.timedelta(days=1):
            datestr = "morgen"
        elif self.cur_day == today + datetime.timedelta(days=-1):
            datestr = "gestern"
        else:
            datestr = self.cur_day.strftime("%a %d. %b %Y")
        title = app_name + " - " + datestr
        wx.Frame.SetTitle(self, title)
        
    def MoveItem(self, row, steps):
        if steps not in [1,-1]:
            return
            
        num_min      = self.list.GetItemData(row)
        day_items    = ConfigReadDayItems(self.cur_day)
        sorted_times = sorted(day_items.keys())
        
        if num_min not in sorted_times:
            return
            
        # index1, index2: aufsteigend
        if steps == -1:
            index2 = sorted_times.index(num_min)
            index1 = index2 + steps
        elif steps == 1:
            index1 = sorted_times.index(num_min)
            index2 = index1 + steps
        else:
            return
            
        if index1 < 0 or len(sorted_times)-1 <= index2:
            return
            
        #
        minutes1_old = sorted_times[index1]
        minutes2_old = sorted_times[index2]
            
        timestr1_old = ConfigMinutes2Timestr(minutes1_old)
        timestr2_old = ConfigMinutes2Timestr(minutes2_old)
        
        timelen1 = sorted_times[index1+1] - sorted_times[index1]
        timelen2 = sorted_times[index2+1] - sorted_times[index2]
            
        valstr1 = config_sep_char.join(day_items[minutes1_old])
        valstr2 = config_sep_char.join(day_items[minutes2_old])
        
        timestr2_new = timestr1_old
        timestr1_new = ConfigMinutes2Timestr(minutes1_old + timelen2)
            
        # Write Config
        config.SetPath(self.cur_day.strftime("/%y%m%d"))
        
        config.DeleteEntry(timestr1_old)
        config.DeleteEntry(timestr2_old)
        config.Write(timestr1_new, valstr1)
        config.Write(timestr2_new, valstr2)
        config.Flush()
        
        config.SetPath("/")
        
        # Liste neu anzeigen
        self.list.ShowDay(self.cur_day)
        
        if steps < 0:
            sel_num_min = minutes1_old
        else:
            sel_num_min = minutes1_old + timelen2
            
        for row in range(self.list.GetItemCount()):
            if self.list.GetItemData(row) == sel_num_min:
                self.list.SetItemState(row, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        
    ############################################################################
    ## events
    
    def OnDayList(self, event):
        str2date     = {}
        datestr_list = []
        for day in reversed(ConfigReadDays()):
            datestr = day.strftime("%a %d. %b %Y")
            str2date[datestr] = day
            datestr_list.append(datestr)
            
        dlg = wx.SingleChoiceDialog(
            self, 'Bitte einen Tag auswählen', 'Tagauswahl',
            datestr_list, wx.CHOICEDLG_STYLE
            )

        if dlg.ShowModal() == wx.ID_OK:
            datestr = dlg.GetStringSelection()
            self.cur_day = str2date[datestr]
            self.SetTitle()
            self.list.ShowDay(self.cur_day)

        dlg.Destroy()
        
    def OnPrevDay(self, event):
        self.list.CloseEditor()
        self.cur_day -= datetime.timedelta(days = 1)
        self.SetTitle()
        self.list.ShowDay(self.cur_day)
        
    def OnNextDay(self, event):
        self.list.CloseEditor()
        self.cur_day += datetime.timedelta(days = 1)
        self.SetTitle()
        self.list.ShowDay(self.cur_day)
        
    def OnDelDay(self, event):
        self.list.CloseEditor()
        answer = wx.MessageBox(
            "Alle Tageseinträge löschen?", "Tag löschen", 
            wx.YES_NO | wx.ICON_QUESTION)
            
        if answer == wx.YES:
            config.SetPath("/")
            config.DeleteGroup(self.cur_day.strftime("/%y%m%d"))
            self.list.ShowDay(self.cur_day)
        
    def OnSum(self, event):
        # time2psp
        config.SetPath(self.cur_day.strftime("/%y%m%d"))
        time2psp   = {}  # minutes -> psp
        ok, key, ind = config.GetFirstEntry()
        while ok:
            m = time_rexp.match(key)
            if not m:
                continue
            num_min  = 60 * int(m.group(1)) + int(m.group(2))
            psp_elem = ConfigReadTimeVal(key)[1]
            if not psp_elem or not psp_elem[0].isalpha():
                psp_elem = '-'
            time2psp[num_min] = psp_elem
            ok, key, ind = config.GetNextEntry(ind)
        config.SetPath("/")
        
        if len(time2psp) == 0:
            return
        
        # psp_map
        psp_map = {}  # psp -> timesum
        t0 = -1
        sum = 0
        for t1 in sorted(time2psp.keys()):
            if t0 >= 0:
                psp_elem = time2psp[t0]
                if psp_elem not in psp_map:
                    psp_map[psp_elem] = 0
                psp_map[psp_elem] += t1 - t0
                if psp_elem and psp_elem !=  '-':
                    sum += t1 - t0
            t0 = t1
        
        msg_text  = '\n'.join([
            k + '\t = ' + datetime.time(v/60,v%60).strftime('%H:%M') + ' \t(' + str(round(v / 60.0, 2)) + ')'
            for k, v in psp_map.items()])
        msg_text += '\n' + 20 * '-' + '\nsum = ' + str(round(sum / 60.0, 2))
        msg_title = app_name + ' - Sum(' + self.cur_day.strftime("%d.%m.%y") + ')'
        wx.MessageBox(msg_text, msg_title)
        
    def OnEndEdit(self, event):
        ### wird komischerweise 2x aufgerufen
        if self.ignore_next_end_edit_event:
            self.ignore_next_end_edit_event = False
            event.Veto()
            return
            
        self.ignore_next_end_edit_event = True
        
        row      = event.GetIndex()
        col      = event.GetColumn()
        new_text = event.GetText()
        old_text = self.list.GetItem(row, col).GetText()
        
        #~ if old_text == new_text:
            #~ return
            
        self.list.ChangeText(self.cur_day, row, col, new_text)
        
        if col == 0 and (old_text or new_text):
            event.Veto()  # da schon mit SetStringItem gesetzt
        
    def OnRightClick(self, event):
        # col
        x = event.GetPosition().x
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
            
            new_id = wx.NewId()
            menu.Append(new_id, "Zeile löschen")
            self.Bind(wx.EVT_MENU, self.OnDelItem, id = new_id)
            
            if row > 0 and row < self.list.GetItemCount() - 2:
                new_id = wx.NewId()
                menu.Append(new_id, "früher")
                self.Bind(wx.EVT_MENU, self.OnItemMoveUp, id = new_id)
            
            if row < self.list.GetItemCount() - 2:
                new_id = wx.NewId()
                menu.Append(new_id, "später")
                self.Bind(wx.EVT_MENU, self.OnItemMoveDown, id = new_id)
            
            self.PopupMenu(menu, event.GetPosition())
        else:
            # val_list
            val_list = []
            for day in reversed(ConfigReadDays()):
                day_items = ConfigReadDayItems(day)
                for num_min in sorted(day_items.keys(), reverse=True):
                    val = day_items[num_min][col-1]
                    if val and val not in val_list:
                        val_list.append(val)
                        if len(val_list) >= num_history_entries:
                            break
                if len(val_list) >= num_history_entries:
                    break
            
            # menu
            menu = wx.Menu()
            
            for val in val_list[:20]:
                new_id = wx.NewId()
                menu.Append(new_id, val)
                self.Bind(wx.EVT_MENU, self.OnChangeItem, id = new_id)
            
            self.PopupMenu(menu, event.GetPosition())
            
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
        new_text = menuitem.GetLabel()
            
        # set new_text
        self.list.ChangeText(self.cur_day, row, col, new_text)
        self.list.SetStringItem(row, col, new_text)
        self.cur_listitem = None
        
    def OnDelItem(self, event):
        # row, col
        if not isinstance(self.cur_listitem, wx.ListItem):
            return
        row = self.cur_listitem.GetId()
        self.list.DelItem(self.cur_day, row)
        self.cur_listitem = None
    
    def OnItemMoveUp(self, event):
        if not isinstance(self.cur_listitem, wx.ListItem):
            return
        row = self.cur_listitem.GetId()
        self.MoveItem(row, -1)
    
    def OnItemMoveDown(self, event):
        if not isinstance(self.cur_listitem, wx.ListItem):
            return
        row = self.cur_listitem.GetId()
        self.MoveItem(row, 1)
        
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
            self.list.DelItem(self.cur_day, sel_item)
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
        w,h = self.GetClientSizeTuple()
        self.list.SetDimensions(0, 0, w, h)

#---------------------------------------------------------------------------

class App(wx.App):
    """Application class."""

    def OnInit(self):
        self.frame = MyFrame()
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True

    def OnExit(self):
        pass


def main():
    app = App()
    app.MainLoop()

if __name__ == '__main__':
    main()
