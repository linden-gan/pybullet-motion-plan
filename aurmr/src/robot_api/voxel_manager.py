#!/usr/bin/env python

import pybullet as p
import pybullet_data
import pybullet_utils.bullet_client as bc
import pybullet_planning as pp

import numpy as np
import copy
import os
from termcolor import cprint

import rospy
from sensor_msgs.msg import PointCloud2
import sensor_msgs.point_cloud2

from aurmr.src.robot_api import move

HERE = os.path.dirname(__file__)  # TODO

VOXEL_SIZE = 0.1

ROBOT_URDF = os.path.join(HERE, '..', 'robot_info', 'robot_with_stand.urdf')


def main():
    # initialize the env
    pp.connect(use_gui=True)
    robot = pp.load_pybullet(ROBOT_URDF, fixed_base=True)
    # gravity
    p.setGravity(0, 0, -9.8)

    # block = pp.create_collision_shape()
    # createCollisionShape(shapeType=p.GEOM_BOX, radius=1, )

    # get joint indices
    joint_names = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 'wrist_1_joint',
                   'wrist_2_joint', 'wrist_3_joint']
    joint_indices = pp.joints_from_names(robot, joint_names)

    robot_self_collision_disabled_link_names = [
        ('stand', 'base_link_inertia'), ('stand', 'shoulder_link'), ('stand', 'upper_arm_link'),
        ('base_link_inertia', 'shoulder_link'), ('shoulder_link', 'upper_arm_link'),
        ('upper_arm_link', 'forearm_link'), ('forearm_link', 'wrist_1_link'), ('wrist_1_link', 'wrist_2_link'),
        ('wrist_2_link', 'wrist_3_link')]
    self_collision_links = pp.get_disabled_collisions(robot, robot_self_collision_disabled_link_names)

    # fill voxels
    manager = VoxelManager()
    positions = [(0,2,1), (0,1,1), (0,1,1.5), (0,1,0.5), (0, 1, 0.8), (0,1,2)]
    manager.fill_voxels(positions)

    # test
    pose0 = [-0.6, 0.6, 1.0]
    orien0 = [0, 0, 0, 1]
    move_test(robot, joint_indices, pose0, orien0, [-0.8, 0.7, 1.0], [0, 0, 0, 1],
              self_collision_links, manager.get_all_voxels())

    pp.wait_for_user()


def move_test(robot, joint_indices, pose0, orien0, pose1, orien1,
              self_collision_links, obstacles, debug=False):
    # first, move gripper to an initial position
    move.move_to(robot, joint_indices, pose0, orien0, [], self_collision_links)
    pp.wait_for_user()

    # move gripper to desired ending position
    move.move_to(robot, joint_indices, pose1, orien1, obstacles, self_collision_links, debug=debug)
    pp.wait_for_user()


class VoxelManager:
    def __init__(self):
        self._map: dict = {}
        self._camera_sub = rospy.Subscriber('/camera/depth/color/points', PointCloud2, self.callback, queue_size=10)
        print("111111111111")
        self.flag = True

    def callback(self, msg: PointCloud2):
        # TODO: transform cloud to positions and call fill_voxel to fill them
        # if self.flag:
        #     self.flag = False
        #     print(msg)
        

        positions = []
        print('call back once')
        # data = msg.data
        # for i in range(0, len(data), 20):
        #     positions.append((data[i], data[i + 1], data[i + 2]))
        
        ds_rate = 150
        count = 0
        for point in sensor_msgs.point_cloud2.read_points(msg, skip_nans=True):
            if count % ds_rate == 0:
                positions.append((point[0], point[1], point[2]))
            count += 1

        self.fill_voxels(positions)
        self.clear_voxels(positions)

    def fill_voxel(self, x, y, z):
        """
        fill a single voxel at (x, y, z)
        :param x: x coordinate of voxel
        :param y: y coordinate of voxel
        :param z: z coordinate of voxel
        :return true is success, false if this voxel is already filled
        """
        if self._map.get((x, y, z)) is not None:
            return False

        block = pp.create_box(VOXEL_SIZE, VOXEL_SIZE, VOXEL_SIZE)
        pp.set_pose(block, pp.Pose(pp.Point(x=x, y=y, z=z)))
        # block = p.createCollisionShape(shapeType=p.GEOM_BOX)
        self._map[(x, y, z)] = block
        return True

    def fill_voxels(self, positions: list):
        """
        fill a list of voxels
        :param positions: a list of (x, y, z)
        """
        print(f'the length of positions is {len(positions)}')
        for pose in positions:
            self.fill_voxel(pose[0], pose[1], pose[2])

    def clear_voxel(self, x, y, z):
        """
        clear a single voxel at (x, y, z)
        :param x: x coordinate of voxel
        :param y: y coordinate of voxel
        :param z: z coordinate of voxel
        :return true is success, false if this voxel is already cleared
        """
        if self._map[(x, y, z)] is None:
            return False

        block = self._map.pop((x, y, z))
        pp.remove_body(block)
        return True

    def clear_voxels(self, positions: list):
        """
        clear a list of voxels
        :param positions: a list of (x, y, z)
        """
        for pose in positions:
            self.clear_voxel(pose[0], pose[1], pose[2])

    def get_all_voxels(self):
        """
        return a deep copy all all blocks as voxels
        """
        return copy.copy(list(self._map.values()))


if __name__ == "__main__":
    # # initialize the env
    # pp.connect(use_gui=True)
    # # gravity
    # p.setGravity(0, 0, -9.8)
    #
    # rospy.init_node('voxel_manager')
    # vm = VoxelManager()
    #
    # rospy.spin()

    # for testing purpose
    main()
