# dronekit-sitl copter-3.3 --home=48.8411292,2.5879308,584,353
# mavproxy.exe --master tcp:127.0.0.1:5760 --out udp:127.0.0.1:14550 --out udp:127.0.0.1:14551
# python test_corridor.py --connect udp:127.0.0.1:14551
"""
Test flying in a corridor avoidance with four lidar sensors
Version for simulator (simulation = True) and reality (simulation = False)
"""
import sys
import argparse
sys.path.insert(0, '../drone')
sys.path.insert(0, '../obstacles')
from drone.virtual_drone import VirtualDrone
from obstacles.wall import WallObstacle
from drone. inspection_drone import InspectionDrone
from obstacles.corridor import CorridorObstacle

simulation = True

parser = argparse.ArgumentParser(description='commands')
parser.add_argument('--connect')
args = parser.parse_args()

connection_string = args.connect

if connection_string is None:
    connection_string = '/dev/serial0'

if simulation:
    drone = VirtualDrone(connection_string=connection_string, baudrate=115200,
                         two_way_switches=[7, 8], three_way_switches=[5, 6, 8, 9, 10, 11, 12],
                         lidar_angle=[0, 90, -90, 180], critical_distance_lidar=100)
    first_detection = True

else:
    drone = InspectionDrone(connection_string, baudrate=115200,
                            two_way_switches=[7, 8], three_way_switches=[5, 6, 8, 9, 10, 11, 12],
                            lidar_angle=[0, 90, -90], lidar_address=[0x10, 0x12, 0x11],
                            critical_distance_lidar=200)


# Init obstacles
wall1 = WallObstacle(-1000, 1000, 2000, 0)
walls = [wall1, CorridorObstacle(wall1)]

print(walls)

drone.launch_mission()
# Simulation : arm and takeoff the drone
if simulation:
    drone.arm_and_takeoff(2)

while drone.mission_running():
    drone.update_time()  # update time since connexion and mission's start
    drone.update_switch_states()  # update the RC transmitter switch state
    if drone.do_lidar_reading():  # ask a reading every 20 ms
        if simulation:
            drone.update_detection(use_lidar=True, debug=True, walls=walls)  # distance measure
            drone.update_side_detection(debug=True, walls=walls)
        else:
            drone.update_detection(use_lidar=True, debug=True)  # distance measure
            drone.update_side_detection(use_lidar=True, debug=True)
    if drone.obstacle_detected() and drone.is_in_auto_mode():  # obstacle detected in front of the drone IRL
        drone.set_guided_mode()
        drone.send_mavlink_stay_stationary()
    if drone.obstacle_detected() and simulation and first_detection:  # obstacle detected in front of the drone in simulation
        print("Obstacle detected")
        drone.set_guided_mode()
        drone.send_mavlink_stay_stationary()
        first_detection = False
    if drone.obstacle_detected() and drone.is_in_guided_mode():
        drone.lidar.update_path(drone.obstacle_detected())
        if drone.lidar.go_left:  # no obstacle left
            drone.send_mavlink_go_left(0.5)
        elif drone.lidar.go_right:  # no obstacle right
            drone.send_mavlink_go_right(0.5)
    if not drone.obstacle_detected() and drone.is_in_guided_mode()\
            and drone.time_since_last_obstacle_detected() > 3 and not simulation:  # obstacle avoided IRL
        drone.set_auto_mode()  # resume mission
        drone.lidar.update_path(drone.obstacle_detected())
    if not drone.obstacle_detected() and drone.is_in_guided_mode() \
            and drone.time_since_last_obstacle_detected() > 3 and simulation:  # obstacle avoided simulator
        first_detection = True  # resume mission
        drone.lidar.update_path(drone.obstacle_detected())
    if not drone.obstacle_detected() and simulation and first_detection:  # drone move forward in simulation
        drone.send_mavlink_go_forward(0.5)
    if drone.time_since_last_obstacle_detected() > 60:
        drone.abort_mission()
    time.sleep(0.1)
