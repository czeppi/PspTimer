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


import sys
from pathlib import Path

import wx

from configuration import Config
from mainframe import MyFrame


APP_NAME = "PSP-Timer"
ROOT_DPATH = Path(sys.argv[0]).absolute().parent.parent
ETC_DPATH = ROOT_DPATH / "etc"


def main():
    config = Config(app_name=APP_NAME)
    app = App()

    app.Init(config=config)
    app.MainLoop()


class App(wx.App):
    """Application class."""

    def Init(self, config: Config):
        self._frame = MyFrame(app_name=APP_NAME, etc_dpath=ETC_DPATH, config=config)
        self._frame.Show()
        self.SetTopWindow(self._frame)
        return True

    def OnExit(self):
        return 0


if __name__ == '__main__':
    main()
