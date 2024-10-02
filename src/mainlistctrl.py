import wx
from wx.lib.mixins import listctrl as listmix

from configuration import Config, Timeval
from daytime import Daytime


MAX_INT = 2147483647


class MainListCtrl(wx.ListCtrl,
                   listmix.ListCtrlAutoWidthMixin,
                   listmix.TextEditMixin):

    def __init__(self, parent, id, config: Config, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        self._config = config

        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self._populate()
        listmix.TextEditMixin.__init__(self)
        drop_target = ListDropTarget(self)
        self.SetDropTarget(drop_target)

    def _populate(self):
        # for normal, simple columns, you can add them like this:
        self.InsertColumn(0, "Zeit", format=wx.LIST_FORMAT_RIGHT)
        self.InsertColumn(1, "Aufgabe")
        self.InsertColumn(2, "PSP-Element")

        self.SetColumnWidth(0, 50)
        self.SetColumnWidth(1, 100)
        self.SetColumnWidth(2, 50)

    def show_cur_day(self, select=None):
        if select is None:
            select = set()
        self.DeleteAllItems()
        for daytime in self._config.read_day_times():
            val = self._config.read_timeval(daytime)
            row = self.InsertItem(MAX_INT, "")
            self.SetItemData(row, daytime)
            self.SetItem(row, 0, str(daytime))
            self.SetItem(row, 1, val.job)
            self.SetItem(row, 2, val.psp)

        row = self.InsertItem(MAX_INT, "")
        self.SetItemData(row, MAX_INT)  # append an empty item
        self.SortItems(lambda item1, item2: item1 - item2)

        for row in range(self.GetItemCount()):
            if self.GetItemData(row) in select:
                self.SetItemState(row, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

    def del_item(self, row):
        item_time = Daytime.create_from_str(self.GetItemText(row))
        if item_time:
            self._config.del_day_item(item_time)
            self._config.Flush()
            self.DeleteItem(row)

    def change_text(self, row, col, new_text):
        old_text = self.GetItem(row, col).GetText()
        sel_times = []
        changed = False

        if old_text == new_text:
            return

        if col == 0:  # time
            new_time = Daytime.create_from_str(new_text)
            old_time = Daytime.create_from_str(old_text)
            sel_times = [new_time]

            if new_time:   # change item (or new)
                if old_time:  # change
                    if self._config.rename_daytime(old_time, new_time):
                        changed = True
                else:  # new
                    if self._config.write_day_item(new_time, Timeval('', '')):
                        changed = True

            elif old_time:  # remove item
                if self._config.DeleteDayitem(old_time):
                    changed = True

        else:  # not time
            daytime = Daytime.create_from_str(self.GetItemText(row))
            if daytime or new_text:
                if col == 1:
                    if self._config.write_job(new_text, daytime):
                        sel_times = [daytime]
                        changed = True
                elif col == 2:
                    sel_times = self._config.write_psp(new_text, daytime)
                    if sel_times:
                        changed = True
        if changed:
            self._config.Flush()
            self.show_cur_day(sel_times)

    def move_item(self, from_row, to_row):
        from_time     = Daytime(self.GetItemData(from_row))
        to_time       = Daytime(self.GetItemData(to_row))
        day_items     = self._config.read_day_items()
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

        # write config
        if from_index < to_index:  # nach hinten schieben
            for i in range(from_index, to_index + 1):
                self._config.del_day_item(sorted_times[i])

            for i in range(from_index + 1, to_index + 1):
                old_time = sorted_times[i]
                new_time = old_time - from_len
                self._config.write_day_item(new_time, day_items[old_time])

            from_time_new = to_time + to_len - from_len
            self._config.write_day_item(from_time_new, day_items[from_time])

        else:  # push forward
            for i in range(to_index, from_index + 1):
                self._config.del_day_item(sorted_times[i])

            from_time_new = to_time
            self._config.write_day_item(from_time_new, day_items[from_time])

            for i in range(to_index, from_index):
                old_time = sorted_times[i]
                new_time = old_time + from_len
                self._config.write_day_item(new_time, day_items[old_time])

        self._config.Flush()

        # show list again
        self.show_cur_day(select={from_time_new})

    def change_timespan(self, row, new_timespan):
        if row + 1 >= self.GetItemCount():  # give it a row behind?
            return

        start_time    = Daytime(self.GetItemData(row))
        end_time      = Daytime(self.GetItemData(row + 1))
        old_timespan  = end_time - start_time
        time_diff     = new_timespan - old_timespan
        day_items     = self._config.read_day_items()
        sorted_times  = sorted(day_items.keys())

        # remove affected items
        for t in sorted_times:
            if t > start_time:
                self._config.del_day_item(t)

        # change affected items
        for t in sorted_times:
            if t > start_time:
                self._config.write_day_item(t + time_diff, day_items[t])

        self._config.Flush()

        # show list again
        self.show_cur_day(select={start_time})

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


class ListDropTarget(wx.DropTarget):

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
            self.list_ctrl.move_item(drag_row, drop_row)

        # what is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return drag_result
