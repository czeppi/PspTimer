import datetime
from pathlib import Path

import wx

from configuration import Config, Timeval
from daytime import Daytime
from mainlistctrl import MainListCtrl
from settingsdialog import SettingsDlg


NUM_HISTORY_ENTRIES = 20


class MyFrame(wx.Frame):

    def __init__(self, app_name: str, etc_dpath: Path, config: Config,
                 pos=(0,0), size=(250, 200)):
        """Create a Frame instance."""
        self._app_name = app_name
        self._etc_dpath = etc_dpath
        self._config = config
        parent = None
        self._ignore_next_end_edit_event = False

        wx.Frame.__init__(self, parent, -1, app_name, pos, size)  # style=wx.WANTS_CHARS
        self.SetIcon(wx.Icon(str(self._etc_dpath / "psptimer.ico"), wx.BITMAP_TYPE_ICO))

        self._create_toolbar()
        self._list_ctrl = MainListCtrl(
            self, -1,
            config=self._config,
            style=wx.LC_REPORT | wx.BORDER_NONE)# | wx.LC_SORT_ASCENDING)
        self._list_ctrl.show_cur_day()

        self._set_title()
        self._settings = self._config.read_settings()

        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.on_end_edit)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_right_click)
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.on_begin_drag)
        self.Bind(wx.EVT_ACTIVATE, self.on_activate)

    def _create_toolbar(self):
        toolbar = wx.Frame.CreateToolBar(self)
        self._add_tool_item(toolbar, "daylist", self.on_day_list, tooltip="Liste aller Tage")
        self._add_tool_item(toolbar, "prevday", self.on_prev_day, tooltip="vorheriger Tag")
        self._add_tool_item(toolbar, "nextday", self.on_next_day, tooltip="nächster Tag")
        self._add_tool_item(toolbar, "delday", self.on_del_day, tooltip="Alle Tageseinträge löschen")
        self._add_tool_item(toolbar, "sum", self.on_sum, tooltip="Ergebnis anzeigen")
        self._add_tool_item(toolbar, "settings", self.on_settings, tooltip="Einstellungen")
        self._add_tool_item(toolbar, "export", self.on_export, tooltip="Export aller Daten")
        self._add_tool_item(toolbar, "import", self.on_import, tooltip="Import aller Daten")
        toolbar.Realize()

    def _add_tool_item(self, toolbar, bmp_name, handler, tooltip=""):
        bmp = wx.Bitmap(str(self._etc_dpath / bmp_name) + ".bmp", wx.BITMAP_TYPE_BMP)
        label = ""
        new_tool = toolbar.AddTool(wx.ID_ANY, label, bmp, tooltip)
        self.Bind(wx.EVT_TOOL, handler, id = new_tool.GetId())

    def _set_title(self):
        today   = datetime.date.today()
        cur_day = self._config.get_day()
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

    def on_day_list(self, event):
        str2date     = {}
        datestr_list = []
        for day in reversed(self._config.read_days()):
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
                self._config.set_day(str2date[datestr])
                self._set_title()
                self._list_ctrl.show_cur_day()

        dlg.Destroy()

    def on_prev_day(self, event):
        if self._list_ctrl.editor.IsShown():
            self._list_ctrl.CloseEditor()
        cur_day = self._config.get_day()
        cur_day -= datetime.timedelta(days = 1)
        self._config.set_day(cur_day)
        self._set_title()
        self._list_ctrl.show_cur_day()

    def on_next_day(self, event):
        if self._list_ctrl.editor.IsShown():
            self._list_ctrl.CloseEditor()
        cur_day = self._config.get_day()
        cur_day += datetime.timedelta(days = 1)
        self._config.set_day(cur_day)
        self._set_title()
        self._list_ctrl.show_cur_day()

    def on_del_day(self, event):
        if self._list_ctrl.editor.IsShown():
            self._list_ctrl.CloseEditor()
        answer = wx.MessageBox(
            "Alle Tageseinträge löschen?", "Tag löschen",
            wx.YES_NO | wx.ICON_QUESTION)

        if answer == wx.YES:
            self._config.SetPath("/")
            self._config.DeleteGroup(self._config.get_day().strftime("/%y%m%d"))
            self._list_ctrl.show_cur_day()

    def on_sum(self, event):
        # time2psp
        time2psp = {}
        for t in self._config.read_day_times():
            psp = self._config.read_timeval(t).psp
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
            p + '\t = ' + str(t) + ' \t(' + str(round(t / 60, 2)) + ')'
            for p, t in psp_map.items()])
        msg_text += '\n' + 20 * '-' + '\nsum = ' + str(round(sum / 60.0, 2))
        msg_title = self._app_name + ' - Sum(' + self._config.get_day().strftime("%d.%m.%y") + ')'
        wx.MessageBox(msg_text, msg_title)

    def on_settings(self, event):
        dlg = SettingsDlg(self, round_min=self._config.round_min)

        if dlg.ShowModal() == wx.ID_OK:
            # round_min
            round_str = dlg._round_ctrl.GetValue()
            if round_str and round_str.isdigit():
                self._config.round_min = int(round_str)

            self._config.write_settings()
            self._config.Flush()

        dlg.Destroy()

    def on_export(self, event):
        # filename
        filename = wx.FileSelector(
            "Exportfile wählen",
            default_filename="psptimer.dat")
        if not filename:
            return

        # lines
        lines = []
        cur_day = self._config.get_day()
        for day in self._config.read_days():
            self._config.set_day(day)
            for daytime in self._config.read_day_times():
                val  = self._config.read_timeval(daytime)
                line = "%s;%s;%s;%s" % (str(day), str(daytime), val.job, val.psp)
                lines.append(line)
        self._config.set_day(cur_day)

        # write
        open(filename, 'w').write('\n'.join(lines))

    def on_import(self, event):
        # filename
        filename = wx.FileSelector(
            "Exportfile wählen",
            default_filename="psptimer.dat")
        if not filename:
            return

        # read data
        import_data = {}  # day -> Daytime -> Timeval
        for row, line in enumerate(open(filename, 'r').readlines()):
            except_text = "%i: %s" % (row, line.strip())

            # items
            items = line.split(';')
            if len(items) != 4:
                raise Exception(except_text)

            # day
            day = datetime.datetime.strptime(items[0].strip(), "%Y-%m-%d")

            # daytime
            daytime = Daytime.create_from_str(items[1].strip())
            if not daytime:
                raise Exception(except_text)

            # timeval
            job = items[2].strip()
            psp = items[3].strip()
            timeval = Timeval(job, psp)

            # import_data
            if day not in import_data:
                import_data[day] = {}
            import_day = import_data[day]
            import_day[daytime] = timeval

        if len(import_data) == 0:
            raise Exception('Importdaten sind leer')

        # dialog for confirm
        answer = wx.MessageBox(
            "Sollen existierende Daten wirklich ersetzt werden?",
            "Daten ersetzen",
            wx.YES_NO | wx.CANCEL, self)
        if answer != wx.YES:
            return

        # remove old data
        self._config.SetPath("/")
        for day in self._config.read_days():
            self._config.set_day(day)
            self._config.DeleteGroup(day.strftime("/%y%m%d"))

        # write new data
        for day in sorted(import_data.keys()):
            self._config.set_day(day)
            day_data = import_data[day]
            for daytime in sorted(day_data.keys()):
                timeval = day_data[daytime]
                self._config.write_day_item(daytime, timeval)

        # show
        last_day = sorted(import_data.keys())[-1]
        self._config.set_day(last_day)

        if self._list_ctrl.editor.IsShown():
            self._list_ctrl.CloseEditor()
        self._set_title()
        self._list_ctrl.show_cur_day()

    def on_end_edit(self, event):
        self._ignore_next_end_edit_event = True

        row      = event.GetIndex()
        col      = event.GetColumn()
        new_text = event.GetText()
        old_text = self._list_ctrl.GetItem(row, col).GetText()

        self._list_ctrl.change_text(row, col, new_text)

        event.Veto()

    def on_right_click(self, event):
        # col
        x = event.GetPoint().x
        col = 0
        while x >= self._list_ctrl.GetColumnWidth(col):
            x -= self._list_ctrl.GetColumnWidth(col)
            col += 1

        # self.cur_listitem
        row = event.GetIndex()
        self.cur_listitem = self._list_ctrl.GetItem(row, col)

        if col == 0:  # time
            # menu
            menu = wx.Menu()

            new_menu_item = menu.Append(wx.ID_ANY, "Zeile löschen")
            self.Bind(wx.EVT_MENU, self.on_del_item, id = new_menu_item.GetId())

            if row + 2 < self._list_ctrl.GetItemCount(): # not at the last item
                new_menu_item = menu.Append(wx.ID_ANY, "Zeitdauer ändern")
                self.Bind(wx.EVT_MENU, self.on_chg_timespan, id = new_menu_item.GetId())

            t0 = Daytime.create_from_str(self.cur_listitem.GetText())
            if t0:
                menu.AppendSeparator()

                t_start = t0 + 4 - (t0 + 4) % 5 - 10
                t_stop  = t0 + t0 % 5 + 11

                for t in range(t_start, t_stop, 5):
                    new_menu_item = menu.Append(wx.ID_ANY, str(Daytime(t)))
                    self.Bind(wx.EVT_MENU, self.on_change_item, id = new_menu_item.GetId())

            self.PopupMenu(menu, event.GetPoint())
        else:
            # hist_list
            hist_list = []
            cur_day = self._config.get_day()
            for day in reversed(self._config.read_days()):
                self._config.set_day(day)
                for daytime in reversed(self._config.read_day_times()):
                    timeval = self._config.read_timeval(daytime)
                    if col == 1:
                        val = timeval.job
                    elif col == 2:
                        val = timeval.psp
                    else:
                        continue
                    if val and val not in hist_list:
                        hist_list.append(val)
                        if len(hist_list) >= NUM_HISTORY_ENTRIES:
                            break
                if len(hist_list) >= NUM_HISTORY_ENTRIES:
                    break
            self._config.set_day(cur_day)

            # menu
            menu = wx.Menu()

            for val in hist_list:
                new_menu_item = menu.Append(wx.ID_ANY, val)
                self.Bind(wx.EVT_MENU, self.on_change_item, id = new_menu_item.GetId())

            self.PopupMenu(menu, event.GetPoint())

    def on_change_item(self, event):
        # row, col
        if not isinstance(self.cur_listitem, wx.ListItem):
            return
        row = self.cur_listitem.GetId()
        col = self.cur_listitem.GetColumn()

        # new_text
        menu = event.GetEventObject()
        if not isinstance(menu, wx.Menu):
            return

        menu_item = menu.FindItemById(event.GetId())
        if not isinstance(menu_item, wx.MenuItem):
            return
        new_text = menu_item.GetItemLabelText()

        # set new_text
        self._list_ctrl.change_text(row, col, new_text)

    def on_del_item(self, event):
        # row, col
        if not isinstance(self.cur_listitem, wx.ListItem):
            return
        row = self.cur_listitem.GetId()
        self._list_ctrl.del_item(row)
        self.cur_listitem = None

    def on_chg_timespan(self, event):
        if not isinstance(self.cur_listitem, wx.ListItem):
            return
        row           = self.cur_listitem.GetId()
        start_time    = Daytime(self._list_ctrl.GetItemData(row))
        end_time      = Daytime(self._list_ctrl.GetItemData(row + 1))
        old_time_span = int(end_time - start_time)

        new_time_str = wx.GetTextFromUser (
            "Bitte neue Zeitlänge in Minuten eingeben.", "Zeitlänge ändern",
            str(old_time_span), parent = self)

        if not new_time_str:
            return

        new_time_span = int (new_time_str)

        if new_time_span > 0 and new_time_span != old_time_span:
           self._list_ctrl.change_timespan(row, new_time_span)

    def on_key_down(self, event):
        key_code = event.GetKeyCode()

        # num_items
        num_items = self._list_ctrl.GetItemCount()
        if num_items == 0:
            event.Skip()
            return

        # sel_item
        sel_item = None
        for row in range(num_items):
            if self._list_ctrl.GetItemState(row, wx.LIST_STATE_SELECTED):
                if sel_item != None:  # not unique?
                    event.Skip()
                    return
                sel_item = row

        if sel_item == None:
            event.Skip()
            return

        if key_code == wx.WXK_DELETE:
            self._list_ctrl.del_item(sel_item)
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

    def on_begin_drag(self, event):
        row = event.GetIndex()
        if row < self._list_ctrl.GetItemCount()-2:
            drag_source = wx.DropSource(self)
            my_data = wx.CustomDataObject("ListItem")
            my_data.SetData(str(row))
            drag_source.SetData(my_data)
            result = drag_source.DoDragDrop(True)

    def on_size(self, event):
        s = self.GetClientSize()
        w, h = s.width, s.height
        self._list_ctrl.SetSize(w, h)
        #self.list.SetDimensions(0, 0, w, h)

    def on_activate(self, event):
        if event.GetActive():
            self._list_ctrl.show_cur_day()
