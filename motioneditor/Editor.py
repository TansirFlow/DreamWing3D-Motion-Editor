"""
author: Tansor
time: 2025-02-12
"""

import copy
import os
import sys
import time
from functools import partial

import numpy as np
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QSizePolicy, QWidget, QShortcut, QFileDialog

from behaviors.custom.Editor_Kick.Editor_Kick import Editor_Kick
from motioneditor.window.main import Ui_MainWindow
from agent.Base_Agent import Base_Agent as Agent


class EditorMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, player):
        super(EditorMainWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("DreamWing3D motion editor")
        # Args: Server IP, Agent Port, Monitor Port, Uniform No., Robot Type, Team Name, Enable Log, Enable Draw
        self.player = player
        self.world=self.player.world
        self.robot=self.world.robot

        self.current_joint_angle = {
            '2': 0,
            '3': 0,
            '4': 0,
            '5': 0,
            '6': 0,
            '7': 0,
            '8': 0,
            '9': 0,
            '10': 0,
            '11': 0,
            '12': 0,
            '13': 0,
            '14': 0,
            '15': 0,
            '16': 0,
            '17': 0,
            '18': 0,
            '19': 0,
            '20': 0,
            '21': 0,
            '22': 0,
            '23': 0,
        }
        self.phase_list = []

        self.joint_slider_edit = {
            '2': self.joint_2_slider,
            '3': self.joint_3_slider,
            '4': self.joint_4_slider,
            '5': self.joint_5_slider,
            '6': self.joint_6_slider,
            '7': self.joint_7_slider,
            '8': self.joint_8_slider,
            '9': self.joint_9_slider,
            '10': self.joint_10_slider,
            '11': self.joint_11_slider,
            '12': self.joint_12_slider,
            '13': self.joint_13_slider,
            '14': self.joint_14_slider,
            '15': self.joint_15_slider,
            '16': self.joint_16_slider,
            '17': self.joint_17_slider,
            '18': self.joint_18_slider,
            '19': self.joint_19_slider,
            '20': self.joint_20_slider,
            '21': self.joint_21_slider,
            '22': self.joint_22_slider,
            '23': self.joint_23_slider,
        }
        for key in self.joint_slider_edit:
            value = self.joint_slider_edit.get(key)
            value.valueChanged.connect(partial(self.slider2input, joint_index=key))

        self.joint_input_edit = {
            '2': self.joint_2_input,
            '3': self.joint_3_input,
            '4': self.joint_4_input,
            '5': self.joint_5_input,
            '6': self.joint_6_input,
            '7': self.joint_7_input,
            '8': self.joint_8_input,
            '9': self.joint_9_input,
            '10': self.joint_10_input,
            '11': self.joint_11_input,
            '12': self.joint_12_input,
            '13': self.joint_13_input,
            '14': self.joint_14_input,
            '15': self.joint_15_input,
            '16': self.joint_16_input,
            '17': self.joint_17_input,
            '18': self.joint_18_input,
            '19': self.joint_19_input,
            '20': self.joint_20_input,
            '21': self.joint_21_input,
            '22': self.joint_22_input,
            '23': self.joint_23_input,
        }
        for key in self.joint_input_edit:
            value = self.joint_input_edit.get(key)
            value.editingFinished.connect(partial(self.input2slider, joint_index=key))

        self.joint_range = {
            '2': (-90, 1),
            '3': (-90, 1),
            '4': (-25, 45),
            '5': (-25, 45),
            '6': (-25, 100),
            '7': (-25, 100),
            '8': (-130, 1),
            '9': (-130, 1),
            '10': (-45, 75),
            '11': (-45, 75),
            '12': (-45, 25),
            '13': (-45, 25),
            '14': (-120, 120),
            '15': (-120, 120),
            '16': (-1, 95),
            '17': (-1, 95),
            '18': (-120, 120),
            '19': (-120, 120),
            '20': (-1, 90),
            '21': (-1, 90),
            '22': (-1, 70),
            '23': (-1, 70),
        }

        for key in self.joint_range:
            joint_slider = self.joint_slider_edit.get(key)
            value_range = self.joint_range.get(key)
            joint_slider.setMinimum(value_range[0]*100)
            joint_slider.setMaximum(value_range[1]*100)

        # self.apply_btn.clicked.connect(self.set_target)
        self.init_button.clicked.connect(self.init_robot)
        self.add_btn.clicked.connect(self.add_phase)
        self.del_btn.clicked.connect(self.del_phase)

        self.run_btn.clicked.connect(self.run_motion)

        self.time_input.editingFinished.connect(self.change_time)

        self.phase_list_widght.itemClicked.connect(self.select_phase)
        self.phase_list_widght.itemDoubleClicked.connect(self.run_single_phase)

        save_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_S), self)
        save_shortcut.activated.connect(self.save_motion)

        open_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_O), self)
        open_shortcut.activated.connect(self.open_motion)

        self.file_path = ""

        self.state="stop"

        self.kickable_area=(0.2, 0.22, -0.125, 0.095)

        self.x_left_input.editingFinished.connect(self.change_kick_area)
        self.x_right_input.editingFinished.connect(self.change_kick_area)
        self.y_left_input.editingFinished.connect(self.change_kick_area)
        self.y_right_input.editingFinished.connect(self.change_kick_area)
        self.x_left_input.setText(str(self.kickable_area[0]))
        self.x_right_input.setText(str(self.kickable_area[1]))
        self.y_left_input.setText(str(self.kickable_area[2]))
        self.y_right_input.setText(str(self.kickable_area[3]))

    def init_robot(self):
        self.stop_motion()

        for _ in range(25):
            self.player.scom.unofficial_beam((-14.8, 0, 0.50), 0)  # beam player continuously (floating above ground)
            self.player.behavior.execute("Zero")
            self.sync()

        # beam player to ground
        self.player.scom.unofficial_beam((-14.8, 0, self.robot.beam_height), 0)
        self.robot.joints_target_speed[
            0] = 0.01  # move head to trigger physics update (rcssserver3d bug when no joint is moving)
        self.sync()

        # stabilize on ground
        for _ in range(50):
            self.player.behavior.execute("Zero")
            self.sync()

        self.player.scom.unofficial_move_ball((-14, 0, 0.042))  # 把球移动到球员面前


    def update_state(self,state):
        self.state=state
        self.state_show.setText(self.state)

    def update_ball_pos(self,ball_pos):
        self.ball_pos_show.setText(ball_pos)

    def update_ball_dis(self,ball_dis):
        self.ball_dis_show.setText(ball_dis)

    def stop_motion(self):
        if self.state!="stop":
            self.thread.stop_signal.emit()
            self.thread.wait()

    def run_motion(self):
        self.stop_motion()
        self.thread = KickWorkerThread(self.player)
        self.thread.model="Full_Motion"
        self.thread.kickable_area=self.kickable_area
        self.thread.phase_list=self.phase_list
        self.thread.ignore_arm=self.ignore_arm_check.isChecked()
        self.thread.update_state_signal.connect(self.update_state)
        self.thread.update_ball_pos_signal.connect(self.update_ball_pos)
        self.thread.update_ball_dis_signal.connect(self.update_ball_dis)
        self.update_ball_dis("0m")
        self.update_ball_pos("(-14,0)")
        self.thread.start()

    def run_single_phase(self,item):
        self.stop_motion()
        self.thread = KickWorkerThread(self.player)
        self.thread.model = "Single_Phase"
        phase_index = self.phase_list_widght.row(item)
        p_l = [copy.deepcopy(self.phase_list[phase_index])]
        p_l[0]['time']=0.5
        self.thread.phase_list = p_l

        self.thread.update_state_signal.connect(self.update_state)
        self.thread.update_ball_pos_signal.connect(self.update_ball_pos)
        self.thread.update_ball_dis_signal.connect(self.update_ball_dis)
        self.thread.start()


    def save_motion(self):
        if self.file_path == "":
            if self.select_save_file():
                s = ""
                for phase in self.phase_list:
                    time = phase['time']
                    joint = phase['joint']
                    s += f"{time}"
                    for joint_index in joint:
                        joint_angle = joint[joint_index]
                        s += f" {joint_angle}"
                    s += "\n"
                with open(self.file_path, "w") as f:
                    f.write(s)
        else:
            s = ""
            for phase in self.phase_list:
                time = phase['time']
                joint = phase['joint']
                s += f"{time}"
                for joint_index in joint:
                    joint_angle = joint[joint_index]
                    s += f" {joint_angle}"
                s += "\n"
            with open(self.file_path, "w") as f:
                f.write(s)

    def open_motion(self):
        if self.select_open_file():
            with open(self.file_path, "r") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    data=[float(a) for a in line.split()]
                    time=data[0]
                    a_list=data[1:]
                    joint={}
                    for i in range(2,24):
                        joint[f"{i}"]=a_list[i-2]
                    self.phase_list.append({'time':time,'joint':joint})
                    current_index = self.phase_list_widght.currentRow()
                    all_nums = self.phase_list_widght.count()
                    self.phase_list_widght.addItem(f"PHASE {all_nums}")

    def select_save_file(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*);;Text Files (*.txt)", )
        if fileName:
            self.file_path = fileName
            self.setWindowTitle(f"DreamWing3D motion editor - {self.file_path}")
            return True
        return False

    def select_open_file(self):
        fname = QFileDialog.getOpenFileName(self, 'Select file', '/home/ubuntu/motion-editor/motioneditor/motion')
        if fname[0]:
            self.file_path = fname[0]
            self.setWindowTitle(f"DreamWing3D motion editor - {self.file_path}")
            return True
        return False

    def change_kick_area(self):
        x_l=float(self.x_left_input.text())
        x_r=float(self.x_right_input.text())
        y_l=float(self.y_left_input.text())
        y_r=float(self.y_right_input.text())
        self.kickable_area=(x_l,x_r,y_l,y_r)

    def change_time(self):
        current_index = self.phase_list_widght.currentRow()
        all_nums = self.phase_list_widght.count()
        if current_index != -1 and all_nums != 0:
            self.phase_list[current_index]['time'] = float(self.time_input.text())

    def get_joint_input_text(self, joint_index):
        attr_name = f"joint_{joint_index}_input"
        text = getattr(self, attr_name).text()
        print(f"joint_index:{joint_index},text:{text}")
        try:
            return int(text)
        except Exception as e:
            return 0

    def slider2input(self, value, joint_index):
        input_attr_name = f"joint_{joint_index}_input"
        value = int(value)/100
        self.current_joint_angle[joint_index] = value
        getattr(self, input_attr_name).setText(str(value))

        current_index = self.phase_list_widght.currentRow()
        all_nums = self.phase_list_widght.count()
        if current_index != -1 and all_nums != 0:
            self.phase_list[current_index].get('joint')[joint_index] = value

    def input2slider(self, joint_index):
        slider_attr_name = f"joint_{joint_index}_slider"
        input_attr_name = f"joint_{joint_index}_input"
        value = float(getattr(self, input_attr_name).text())
        self.current_joint_angle[joint_index] = value
        getattr(self, slider_attr_name).setValue(int(value*100))

        current_index = self.phase_list_widght.currentRow()
        all_nums = self.phase_list_widght.count()
        if current_index != -1 and all_nums != 0:
            self.phase_list[current_index].get('joint')[joint_index] = value

    def add_phase(self):
        current_index = self.phase_list_widght.currentRow()
        all_nums = self.phase_list_widght.count()
        if current_index == -1 or all_nums == 0:
            self.phase_list_widght.addItem(f"PHASE {all_nums}")
            self.phase_list.append({'time': 1, 'joint': copy.deepcopy(self.current_joint_angle)})
        else:
            self.phase_list_widght.insertItem(current_index + 1, f"PHASE {all_nums}")
            current_phase = self.phase_list[current_index]
            self.phase_list.insert(current_index + 1, copy.deepcopy(current_phase))

    def del_phase(self):
        current_index = self.phase_list_widght.currentRow()
        all_nums = self.phase_list_widght.count()
        if current_index != -1 and all_nums != 0:
            self.phase_list_widght.takeItem(current_index)

    def select_phase(self, item):
        row = self.phase_list_widght.row(item)
        current_phase = self.phase_list[row]
        time = current_phase.get('time')
        self.time_input.setText(str(time))
        joint = current_phase.get('joint')
        for key in joint:
            value = joint.get(key)
            _input = self.joint_input_edit.get(key)
            _input.setText(str(value))
            self.input2slider(joint_index=key)
            self.current_joint_angle[key] = value

    def sync(self):
        ''' Run a single simulation step '''
        self.player.scom.commit_and_send(self.player.world.robot.get_command())
        self.player.scom.receive()



class KickWorkerThread(QThread):
    update_state_signal = pyqtSignal(str)
    stop_signal = pyqtSignal()
    update_ball_pos_signal = pyqtSignal(str)
    update_ball_dis_signal = pyqtSignal(str)
    running=False
    phase_list=[]
    kickable_area=None
    model="Full_Motion"
    ignore_arm=False

    def __init__(self,player):
        super().__init__()
        self.player = player
        self.world = self.player.world
        self.robot = self.world.robot
        self.kick_obj: Editor_Kick = self.player.behavior.get_custom_behavior_object("Editor_Kick")  # Step behavior object

        self.stop_signal.connect(self.request_stop)

    def request_stop(self):
        self.running=False

    def init(self):
        print("==============================init==============================")
        self.has_adjust_reset = False
        self.has_kick_reset = False

        for _ in range(25):
            if not self.running:
                return True
            self.update_state_signal.emit("init")
            self.player.scom.unofficial_beam((-14.8, 0, 0.50), 0)  # beam player continuously (floating above ground)
            self.player.behavior.execute("Zero")
            self.sync()

        # beam player to ground
        self.player.scom.unofficial_beam((-14.8, 0, self.robot.beam_height), 0)
        self.robot.joints_target_speed[
            0] = 0.01  # move head to trigger physics update (rcssserver3d bug when no joint is moving)
        self.sync()

        # stabilize on ground
        for _ in range(7):
            if not self.running:
                return True
            self.player.behavior.execute("Zero")
            self.sync()

        self.player.scom.unofficial_set_play_mode("PlayOn")
        self.player.scom.unofficial_move_ball((-14, 0, 0.042))  # 把球移动到球员面前

    def adjust(self):
        self.update_state_signal.emit("adjust")
        # 执行校准位置行为
        # kickable_area = (0.175, 0.225, -0.1, 0)  # x_left,x_right,y_left,y_right
        kickable_area = (0.2, 0.22, -0.125, 0.095)  # x_left,x_right,y_left,y_right
        if self.kickable_area is not None:
            kickable_area=self.kickable_area

        while not self.kick_obj.ready_for_kick:  # step_name,abort,direction=0,area=None
            if not self.running:
                return True
            reset = False
            if not self.has_adjust_reset:
                self.has_adjust_reset = True
                reset = True
            self.player.behavior.execute("Editor_Kick", reset, "adjust_pos", False, 0, kickable_area)
            self.sync()
            if self.robot.cheat_abs_pos[2] < 0.3:
                for _ in range(7):
                    self.player.behavior.execute("Zero")
                    self.sync()
                self.player.scom.unofficial_beam((-14.8, 0, self.robot.beam_height), 0)
                self.player.scom.unofficial_move_ball((-14, 0, 0.042))  # 把球移动到球员面前

        self.player.scom.unofficial_set_game_time(0)

        return True

    def kick(self):
        print("==============================kick==============================")
        while self.kick_obj.ready_for_kick:
            if not self.running:
                return True
            self.update_state_signal.emit("kick")
            reset = False
            if not self.has_kick_reset:
                self.has_kick_reset = True
                reset = True
            self.player.behavior.execute("Editor_Kick", reset, "kick_ball")
            self.sync()


    def run(self):
        self.running = True
        if self.model=="Full_Motion":
            self.kick_obj.set_slots(self.phase_list,self.ignore_arm)
            self.init()
            self.adjust()
            self.kick()
            for _ in range(5*50):
                if not self.running:
                    break
                self.update_state_signal.emit("ball run")
                self.sync()
                ball_pos=self.player.world.ball_abs_pos[:2]
                self.update_ball_pos_signal.emit(f"({round(ball_pos[0],2)},{round(ball_pos[1],2)})")
                p1x=-14
                p1y=0
                p2x=ball_pos[0]
                p2y=ball_pos[1]
                dis=((p2x-p1x)**2+(p2y-p1y)**2)**0.5
                self.update_ball_dis_signal.emit(f"{round(dis,2)}m")
            self.kick_obj.ready_for_kick = False
            self.update_state_signal.emit("stop")

        elif self.model=="Single_Phase":
            self.kick_obj.set_slots(self.phase_list)
            self.single_phase()
            self.kick_obj.ready_for_kick = False
            self.update_state_signal.emit("stop")


    def set_target(self):
        angle_list = []
        for i in range(2, 24):
            angle_list.append(self.current_joint_angle.get(f"{i}"))
        type = self.robot.type
        if type == 4:
            self.robot.set_joints_target_position_direct(
                slice(2, 24),
                np.array(angle_list),
                harmonize=False
            )
        else:
            self.robot.set_joints_target_position_direct(
                slice(2, 22),
                np.array(angle_list[:-2]),
                harmonize=False
            )
        self.sync()

    def single_phase(self):
        self.kick_obj.ready_for_kick = True
        self.has_kick_reset = False
        while self.kick_obj.ready_for_kick:
            if not self.running:
                break
            self.update_state_signal.emit("sing phase")
            reset = False
            if not self.has_kick_reset:
                self.has_kick_reset = True
                reset = True
            self.player.behavior.execute("Editor_Kick", reset, "kick_ball")
            self.sync()


    def sync(self):
        ''' Run a single simulation step '''
        self.player.scom.commit_and_send(self.robot.get_command())
        self.player.scom.receive()
