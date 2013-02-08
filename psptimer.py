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

def SortCallback(item1, item2):
    return item1 - item2

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

    def Populate(self):
        # for normal, simple columns, you can add them like this:
        self.InsertColumn(0, "Zeit", format=wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(1, "Aufgabe")
        self.InsertColumn(2, "PSP-Element")

        self.SetColumnWidth(0, 50)
        self.SetColumnWidth(1, 90)
        self.SetColumnWidth(2, 90)

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
        
       
#---------------------------------------------------------------------------

class MyFrame(wx.Frame):
    """Frame class."""
    
    ############################################################################
    ## Init
    
    def __init__(self, parent=None, id=-1, title=app_name,
                 pos=(0,0), size=(300, 200)):
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
        title = app_name + " - " + self.cur_day.strftime("%a %d. %b %Y")
        wx.Frame.SetTitle(self, title)
        
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
        self.cur_day -= datetime.timedelta(days = 1)
        self.SetTitle()
        self.list.ShowDay(self.cur_day)
        
    def OnNextDay(self, event):
        self.cur_day += datetime.timedelta(days = 1)
        self.SetTitle()
        self.list.ShowDay(self.cur_day)
        
    def OnDelDay(self, event):
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
            k + ' = ' + datetime.time(v/60,v%60).strftime('%H:%M') + ' (' + str(round(v / 60.0, 2)) + ')'
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
        old_text = self.list.GetItem(row, col).GetText()
        new_text = event.GetText()
        
        #~ if old_text == new_text:
            #~ return
            
        config.SetPath(self.cur_day.strftime("/%y%m%d"))
        
        if col == 0:  # Zeit
            if old_text and not new_text:  # item löschen
                self.list.DeleteItem(row)
                config.DeleteEntry(old_text)
                config.Flush()
                event.Veto()
            elif new_text:                 # item ändern (oder neu)
                m = time_rexp.match(new_text)
                if m:
                    new_text = ':'.join(m.groups())
                    
                    if old_text:  # ändern
                        config.RenameEntry(old_text, new_text)
                    else:         # neu
                        config.Write(new_text, '')
                    
                    self.list.SetStringItem(row, col, new_text)
                    num_min = 60 * int(m.group(1)) + int(m.group(2))
                    self.list.SetItemData(row, num_min)
                    if not old_text:
                        row = self.list.InsertStringItem(sys.maxint, "")
                        self.list.SetItemData(row, sys.maxint)  # leeres Item hinten anhängen
                        
                    self.list.SortItems(SortCallback)
                    event.Veto()  # da schon mit SetStringItem gesetzt
        else:
            key = self.list.GetItemText(row)
            if key:
                val = ConfigReadTimeVal(key)
                val[col-1] = new_text
                config.Write(key, config_sep_char.join(val))
                config.Flush()
            elif self.cur_day == datetime.date.today() and new_text:
                now = datetime.datetime.now()
                key = now.strftime("%H:%M")
                
                val = config_num_cols * ['']
                val[col-1] = new_text
                config.Write(key, config_sep_char.join(val))
                config.Flush()
                
                num_min = 60 * now.hour + now.minute
                self.list.SetItemData(row, num_min)
                self.list.SetStringItem(row, 0, key)
                
                new_row = self.list.InsertStringItem(sys.maxint, "")
                self.list.SetItemData(new_row, sys.maxint)  # leeres Item hinten anhängen
            else:
                event.Veto()
        
        config.SetPath("/")
        
    def OnRightClick(self, event):
        # col
        x = event.GetPosition().x
        col = 0
        while x >= self.list.GetColumnWidth(col):
            x -= self.list.GetColumnWidth(col)
            col += 1
        if col < 1 or 2 < col:
            return
            
        # self.cur_listitem
        self.cur_listitem = self.list.GetItem(event.GetIndex(), col)
            
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
            
        #~ wx.MessageBox(menuitem.GetText(), menuitem.GetLabel())
        
        config.SetPath(self.cur_day.strftime("/%y%m%d"))
        key = self.list.GetItemText(row)
        if key:
            val = ConfigReadTimeVal(key)
            val[col-1] = new_text
            config.Write(key, config_sep_char.join(val))
            config.Flush()
        elif self.cur_day == datetime.date.today() and new_text:
            now = datetime.datetime.now()
            key = now.strftime("%H:%M")
            
            val = config_num_cols * ['']
            val[col-1] = new_text
            config.Write(key, config_sep_char.join(val))
            config.Flush()
            
            num_min = 60 * now.hour + now.minute
            self.list.SetItemData(row, num_min)
            self.list.SetStringItem(row, 0, key)
            
            new_row = self.list.InsertStringItem(sys.maxint, "")
            self.list.SetItemData(new_row, sys.maxint)  # leeres Item hinten anhängen
        config.SetPath("/")
        
        self.list.SetStringItem(row, col, new_text)
        #self.cur_listitem.SetText(new_text)
        self.cur_listitem = None
        
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
