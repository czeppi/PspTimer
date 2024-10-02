import datetime
from pathlib import Path

import wx

from configuration import Config
from daytime import Daytime, DaytimeFromStr
from mainlistctrl import MainListCtrl
from settingsdialog import SettingsDlg


num_history_entries = 20


class MyFrame(wx.Frame):
    """Frame class."""

    ############################################################################
    ## Init

    def __init__(self, app_name: str, etc_dpath: Path, config: Config,
                 pos=(0,0), size=(250, 200)):
        """Create a Frame instance."""
        self._app_name = app_name
        self._etc_dpath = etc_dpath
        self._config = config
        parent = None
        wx.Frame.__init__(self, parent, -1, app_name, pos, size)  # style=wx.WANTS_CHARS

        self.ignore_next_end_edit_event = False

        self.SetIcon(wx.Icon(str(self._etc_dpath / "psptimer.ico"), wx.BITMAP_TYPE_ICO))
        self.CreateToolBar()
        self.list = MainListCtrl(
            self, -1,
            config=self._config,
            style=wx.LC_REPORT | wx.BORDER_NONE)# | wx.LC_SORT_ASCENDING)
        self.list.ShowCurDay()
        self.SetTitle()
        self.settings = self._config.ReadSettings()

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
        bmp = wx.Bitmap(str(self._etc_dpath / bmp_name) + ".bmp", wx.BITMAP_TYPE_BMP)
        label = ""
        new_tool = toolbar.AddTool(wx.ID_ANY, label, bmp, tooltip)
        self.Bind(wx.EVT_TOOL, handler, id = new_tool.GetId())

    def SetTitle(self):
        today   = datetime.date.today()
        cur_day = self._config.GetDay()
        if cur_day == today:
            datestr = "heute"
        elif cur_day == today + datetime.timedelta(days=1):
            datestr = "morgen"
        elif cur_day == today + datetime.timedelta(days=-1):
            datestr = "gestern"
        else:
            datestr = cur_day.strftime("%a %d. %b %Y")
        title = self._app_name + " - " + datestr
        wx.Frame.SetTitle(self, title)

    ############################################################################
    ## events

    def OnDayList(self, event):
        str2date     = {}
        datestr_list = []
        for day in reversed(self._config.ReadDays()):
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
                self._config.SetDay(str2date[datestr])
                self.SetTitle()
                self.list.ShowCurDay()

        dlg.Destroy()

    def OnPrevDay(self, event):
        if self.list.editor.IsShown():
            self.list.CloseEditor()
        cur_day = self._config.GetDay()
        cur_day -= datetime.timedelta(days = 1)
        self._config.SetDay(cur_day)
        self.SetTitle()
        self.list.ShowCurDay()

    def OnNextDay(self, event):
        if self.list.editor.IsShown():
            self.list.CloseEditor()
        cur_day = self._config.GetDay()
        cur_day += datetime.timedelta(days = 1)
        self._config.SetDay(cur_day)
        self.SetTitle()
        self.list.ShowCurDay()

    def OnDelDay(self, event):
        if self.list.editor.IsShown():
            self.list.CloseEditor()
        answer = wx.MessageBox(
            "Alle Tageseinträge löschen?", "Tag löschen",
            wx.YES_NO | wx.ICON_QUESTION)

        if answer == wx.YES:
            self._config.SetPath("/")
            self._config.DeleteGroup(self._config.GetDay().strftime("/%y%m%d"))
            self.list.ShowCurDay()

    def OnSum(self, event):
        # time2psp
        time2psp = {}
        for t in self._config.ReadDaytimes():
            psp = self._config.ReadTimeval(t).psp
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
        msg_title = self._app_name + ' - Sum(' + self._config.GetDay().strftime("%d.%m.%y") + ')'
        wx.MessageBox(msg_text, msg_title)

    def OnSettings(self, event):
        dlg = SettingsDlg(self, round_min=self._config.round_min)

        if dlg.ShowModal() == wx.ID_OK:
            # round_min
            round_str = dlg.round_ctrl.GetValue()
            if round_str and round_str.isdigit():
                self._config.round_min = int(round_str)

            self._config.WriteSettings()
            self._config.Flush()

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
        cur_day = self._config.GetDay()
        for day in self._config.ReadDays():
            self._config.SetDay(day)
            for daytime in self._config.ReadDaytimes():
                val  = self._config.ReadTimeval(daytime)
                line = "%s;%s;%s;%s" % (str(day), str(daytime), val.job, val.psp)
                lines.append(line)
        self._config.SetDay(cur_day)

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
        self._config.SetPath("/")
        for day in self._config.ReadDays():
            self._config.SetDay(day)
            self._config.DeleteGroup(day.strftime("/%y%m%d"))

        # neue Daten schreiben
        for day in sorted(import_data.keys()):
            self._config.SetDay(day)
            day_data = import_data[day]
            for daytime in sorted(day_data.keys()):
                timeval = day_data[daytime]
                self._config.WriteDayitem(daytime, timeval)

        # Anzeige
        last_day = sorted(import_data.keys())[-1]
        self._config.SetDay(last_day)

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
            cur_day = self._config.GetDay()
            for day in reversed(self._config.ReadDays()):
                self._config.SetDay(day)
                for daytime in reversed(self._config.ReadDaytimes()):
                    timeval = self._config.ReadTimeval(daytime)
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
            self._config.SetDay(cur_day)

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
