import wx


class SettingsDlg(wx.Dialog):

    def __init__(self, parent, round_min: int):
        title = 'Einstellungen'
        wx.Dialog.__init__(self, parent, -1, title)

        #~ font = self.GetFont()
        #~ font.SetPointSize(config.fontsize)
        #~ self.SetFont(font)

        # Ctrls
        ok_button = wx.Button(self, wx.ID_OK, "OK")
        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self._round_ctrl = wx.TextCtrl(self, -1, str(round_min))

        # grid_sizer
        grid_sizer = wx.FlexGridSizer(0, 2, 0, 5)
        grid_sizer.AddGrowableCol(1, 0)

        grid_sizer.Add(
            wx.StaticText(self, -1, "Minuten runden auf:"),
                0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self._round_ctrl, 0, wx.EXPAND)

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
