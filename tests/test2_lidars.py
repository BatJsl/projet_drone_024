## Test for simulation in SITL, the distances measured by vertical sensors are given by lists of elements.

import sys
import time
import argparse
import numpy as np
sys.path.insert(0, '../drone')
from virtual_drone_vertical_mov import VirtualDrone

simulation = True

parser = argparse.ArgumentParser(description='commands')
parser.add_argument('--connect')
args = parser.parse_args()

connection_string = args.connect

list_up_dist = list(range(250, 300, 1))
list_down_dist = list(range(300, 250, -1))

if connection_string is None:
    connection_string = '/dev/serial0'

if simulation:
    drone = VirtualDrone(connection_string=connection_string, baudrate=115200,
                         two_way_switches=[7, 8], three_way_switches=[5, 6, 8, 9, 10, 11, 12],
                         lidar_angle=[0, 90, -90], critical_distance_lidar=100,
                         list_up_distances=list_down_dist, list_down_distances=list_up_dist)

drone.launch_mission()
# Simulation : arm and takeoff the drone

if simulation:
    drone.arm_and_takeoff(2)

while drone.mission_running():
    drone.update_time()
    drone.update_switch_states()

    if drone.vert_lidar.lidar_reading():
        print("Doing vertical reading")
        drone.vert_lidar.read_up_distance()
        print("distance_up%s")
        print(drone.vert_lidar._distance_up)
        drone.vert_lidar.read_down_distance()
        print("distance_down%s")
        print(drone.vert_lidar._distance_down)

    if drone.is_in_auto_mode():
        print("Drone was in auto mode ")
        print("changing to guided mode ")
        drone.set_guided_mode()
        drone.send_mavlink_stay_stationary()
    drone.set_guided_mode()
    drone.vert_lidar.update_vertical_path()

    if drone.vert_lidar._go_up:
        print("going up")
        #drone.send_mavlink_go_left(0.05)
        drone.send_mavlink_go_up(0.15)
    elif drone.vert_lidar._go_down:
        print("going down")
        #drone.send_mavlink_go_right(0.05)
        drone.send_mavlink_go_down(0.15)


    #time.sleep(2)

    #drone.set_auto_mode()
    print("time")
    print(drone.time_since_mission_launch())
    if drone.time_since_mission_launch() > 300:
        drone.abort_mission()
    time.sleep(5)
time.sleep(10)
