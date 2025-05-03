import sys

from PyQt5.QtWidgets import QApplication

from agent.Base_Agent import Base_Agent as Agent
from math_ops.Math_Ops import Math_Ops as M
from scripts.commons.Script import Script
import numpy as np

'''
Objective:
----------
Demonstrate kick
'''


class Motion_Editor():
    def __init__(self, script: Script) -> None:
        self.script = script

    def execute(self):

        a = self.script.args
        player = Agent(a.i, a.p, a.m, a.u, a.r,
                       "DreamWing")  # Args: Server IP, Agent Port, Monitor Port, Uniform No., Robot Type, Team Name
        player.path_manager.draw_options(enable_obstacles=True,
                                         enable_path=True)  # enable drawings of obstacles and path to ball

        app = QApplication(sys.argv)
        from motioneditor.Editor import EditorMainWindow
        window = EditorMainWindow(player)
        window.show()
        sys.exit(app.exec())