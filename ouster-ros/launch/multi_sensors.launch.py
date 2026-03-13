# -*- coding: utf-8 -*-
# @Copyright: Copyright (C) 2025 Gahan Ai Pvt Ltd
# @Author: Pavan Patil
# @Date: 2026-01-07 16:39:13
# @Last Modified by:   Pavan Patil
# @Last Modified time: 2026-01-09 12:25:03
# @Description: Launch file for configuring and initializing multiple Ouster LiDAR sensors with staggered startup, static frame transforms, and namespace isolation

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction, LogInfo, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch_ros.actions import LifecycleNode, Node

def generate_launch_description():
    
    lidar_configs = [
        {
            'ns': 'drwig_TOP_licam',
            'hostname': '169.168.168.121',  # <-- Update according to your setup
            'lidar_port': 7504,             # <-- Make sure both sensors have different ports
            'imu_port': 7505,
            'suffix': '128'
        },
        {
            'ns': 'drwig_FB_licam',
            'hostname': '169.168.168.123',  # <-- Update according to your setup
            'lidar_port': 7502,             # <-- Make sure both sensors have different ports
            'imu_port': 7503,
            'suffix': '128'
        }
    ]

    ouster_pkg_dir = get_package_share_directory('ouster_ros')
    params_file = os.path.join(ouster_pkg_dir, 'config', 'driver_params.yaml')

    launch_entities = []

    for i, config in enumerate(lidar_configs):
        ns = config['ns']
        
        driver_node = LifecycleNode(
            package='ouster_ros',
            executable='os_driver',
            name='os_driver',
            namespace=ns,
            output='screen',
            # This ensures the launch file doesn't shut down if only one of the sensors fails to connect or exits
            on_exit=LogInfo(msg=f"Lidar sensor {ns} failed to connect or exited."),
            parameters=[
                params_file,
                {
                    'sensor_hostname': config['hostname'],
                    'lidar_port': config['lidar_port'],
                    'imu_port': config['imu_port'],
                    'viz': False,
                    'auto_start': True,
                    'sensor_frame': ns,            
                    'lidar_frame': f'{ns}_lidar',  
                    'imu_frame': f'{ns}_imu',
                    'udp_dest': '169.168.168.81',   # <-- REQUIRED when using static IPs, set to your host machine's IP
                    'metadata': f'{ns}_metadata.json',
                    'lidar_mode': '1024x10',
                    'point_cloud_frame': ns,  # <-- Set point cloud frame same as sensor frame to rectify orientation of lidar to sensor frames    
                }
            ],
        )

        # Staggered start
        driver_start_time = 3.0 * i
        
        # Wrap the node in a TimerAction
        timed_node = TimerAction(
            period=driver_start_time,
            actions=[driver_node]
        )
        
        launch_entities.append(timed_node)

    # Static Transform Publishers (Kept active so the TF tree stays valid) 
    launch_entities.append(Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_imu_to_top_lidar',
        arguments=['1.57', '0.0', '1.18', '0.0', '0.191986', '0.0', 'imu_link', 'drwig_TOP_licam']
        # Arguments: x, y, z, roll, pitch, yaw, parent_frame, child_frame
    ))

    launch_entities.append(Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_imu_to_fb_lidar',
        arguments=['3.25', '0.0', '0.32', '0.0', '0.558505', '0.0', 'imu_link', 'drwig_FB_licam']
        # Arguments: x, y, z, roll, pitch, yaw, parent_frame, child_frame
    ))

    return LaunchDescription(launch_entities)