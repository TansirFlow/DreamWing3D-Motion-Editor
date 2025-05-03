from agent.Base_Agent import Base_Agent
from behaviors.custom.Step.Step_Generator import Step_Generator
from math_ops.Math_Ops import Math_Ops as M
from os import listdir
from os.path import isfile, join, exists
import os
import xml.etree.ElementTree as xmlp
import numpy as np

class Editor_Kick(Base_Agent):

    def __init__(self, base_agent: Base_Agent) -> None:
        self.behavior = base_agent.behavior
        self.world = base_agent.world
        self.path_manager = base_agent.path_manager
        self.state_slot_number = 0
        self.state_slot_start_time_ms = 0
        self.state_slot_start_angles = None
        self.state_init_zero = True

        r_type = self.world.robot.type

        self.description = "This motion is used for motion editor"
        self.auto_head = True
        self.behaviors = []

        self.reset()

        self.ready_for_kick = False  # 是否位置校准完毕可以开始踢球
        self.deep_train_progress = 0
        self.deep_train_indices = None
        self.deep_train_target = None

    def set_slots(self, phase_list,ignore_arm=False):
        slots = []
        for phase in phase_list:
            delta_ms = float(phase['time'])*1000
            joint = phase['joint']
            indices = []
            angles = []
            for joint_id in joint:
                if joint_id in ['14','15','16','17','18','19','20','21']:
                    if ignore_arm:
                        continue
                if self.world.robot.type!=4 and (joint_id=="22" or joint_id=="23"):
                    continue
                joint_angle = joint[joint_id]
                indices.append(int(joint_id))
                angles.append(float(joint_angle))
            slots.append((delta_ms, indices, angles))
        self.behaviors = slots

    def execute(self, name, reset, step_name, abort=False, direction=0, area=None,
                bias_dir=0) -> bool:  # You can add more arguments
        # print(f"step_name: {step_name}")
        w = self.world
        r = self.world.robot
        b = w.ball_rel_torso_cart_pos
        t = w.time_local_ms

        if step_name == "adjust_pos":
            '''调整位置到目标区域，以便执行踢球动作'''
            if reset:
                self.reset_time = t

            self.ball_x_limits = area[0:2]
            self.ball_y_limits = area[2:4]
            self.ball_x_center = (self.ball_x_limits[0] + self.ball_x_limits[1]) / 2
            self.ball_y_center = (self.ball_y_limits[0] + self.ball_y_limits[1]) / 2
            self.bias_dir = bias_dir

            gait: Step_Generator = self.behavior.get_custom_behavior_object("Walk").env.step_generator

            biased_dir = M.normalize_deg(direction + self.bias_dir)  # add bias to rectify direction
            ang_diff = abs(
                M.normalize_deg(biased_dir - r.loc_torso_orientation))  # the reset was learned with loc, not IMU

            next_pos, next_ori, dist_to_final_target = self.path_manager.get_path_to_ball(
                x_ori=biased_dir, x_dev=-self.ball_x_center, y_dev=-self.ball_y_center, torso_ori=biased_dir)

            if (w.ball_last_seen > t - w.VISUALSTEP_MS and ang_diff < 5 and  # ball is visible & aligned
                    self.ball_x_limits[0] < b[0] < self.ball_x_limits[1] and  # ball is in kick area (x)
                    self.ball_y_limits[0] < b[1] < self.ball_y_limits[1] and  # ball is in kick area (y)
                    t - w.ball_abs_pos_last_update < 100 and  # ball absolute location is recent
                    dist_to_final_target < 0.03 and  # if absolute ball position is updated
                    not gait.state_is_left_active and gait.state_current_ts == 2 and  # walk gait phase is adequate
                    t - self.reset_time > 500):  # to avoid kicking immediately without preparation & stability
                # print(f"校准位置完毕{t}")
                # 位置校准完毕，可以开始踢球
                self.ready_for_kick = True
                return True
            else:
                # print(f"校准位置{t}")
                # 位置校准尚未完成，继续校准
                dist = max(0.07, dist_to_final_target)
                reset_walk = reset and self.behavior.previous_behavior != "Walk"  # reset walk if it wasn't the previous behavior
                self.behavior.execute_sub_behavior("Walk", reset_walk, next_pos, True, next_ori, True,
                                                   dist)  # target, is_target_abs, ori, is_ori_abs, distance
                return abort  # abort only if self.phase == 0

        elif step_name == "kick_ball":
            # print(f"踢球{t}")
            '''执行踢球动作'''
            if reset:
                self.reset()
            elapsed_ms = self.world.time_local_ms - self.state_slot_start_time_ms
            delta_ms, indices, angles = self.behaviors[self.state_slot_number]

            # Check slot progression
            if elapsed_ms >= delta_ms:
                self.state_slot_start_angles[indices] = angles  # update start angles based on last target

                # Prevent 2 rare scenarios:
                # 1 - this function is called after the behavior is finished & reset==False
                # 2 - we are in the last slot, syncmode is not active, and we lost the last step
                if self.state_slot_number + 1 == len(self.behaviors):
                    return True  # So, the return indicates a finished behavior until a reset is sent via the arguments

                self.state_slot_number += 1
                elapsed_ms = 0
                self.state_slot_start_time_ms = self.world.time_local_ms
                delta_ms, indices, angles = self.behaviors[self.state_slot_number]

            # Execute
            progress = (elapsed_ms + 20) / delta_ms
            target = (angles - self.state_slot_start_angles[indices]) * progress + self.state_slot_start_angles[indices]

            # 将数据同步，以便优化类能从外部获取目标角度等信息
            self.deep_train_progress = progress
            self.deep_train_indices = indices
            self.deep_train_target = target

            self.world.robot.set_joints_target_position_direct(indices, target, False)
            is_finished = bool(elapsed_ms + 20 >= delta_ms and self.state_slot_number + 1 == len(
                self.behaviors))  # true if next step (now+20ms) is out of bounds

            if is_finished:  # 本次踢球结束，ready_for_kick复位
                self.ready_for_kick = False

            # Return True if finished (this is the last step)
            return is_finished

    def is_ready(self) -> any:  # You can add more arguments
        ''' Returns True if this behavior is ready to start/continue under current game/robot conditions '''
        return True

    def reset(self):
        ''' Initialize/Reset slot behavior '''
        self.state_slot_number = 0
        self.state_slot_start_time_ms = self.world.time_local_ms
        self.state_slot_start_angles = np.copy(self.world.robot.joints_position)
