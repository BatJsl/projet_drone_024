# dronekit-sitl copter-3.3 --home=48.8411292,2.5879308,584,353
# mavproxy.exe --master tcp:127.0.0.1:5760 --out udp:127.0.0.1:14550 --out udp:127.0.0.1:14551
# python Test_proportional_corrector.py --connect udp:127.0.0.1:14551

"""
Here, the drone has to regulate its speed
to be at a certain distance away from the ground
using a PROPORTIONAL CORRECTOR
"""

import sys
import time
import argparse
sys.path.insert(0, '../drone')
sys.path.insert(0, '../obstacles')
from virtual_drone_vertical_mov import VirtualDrone
#from wall import WallObstacle
import numpy as np
import matplotlib.pyplot as plt

" -------- Constants and Variables -------- "
#For simulator only
#wall1 = WallObstacle(-1000, 500, 2000, 0)          #For simu only
#walls = [wall1]                                    #For simu only

mission_time = 0           #Increment for the plot log
V_command = 0              #Velocity to command the drone
V_measured = 0             #Velocity of the drone
measured_distance = -1     #Data from the sensor
yaw = 0

K = 0.0025                  #Coefficient for the PID
target_distance = 150      #The drone must stop at this distance from the obstacle

" -------- Initialization -------- "
parser = argparse.ArgumentParser(description='commands')
parser.add_argument('--connect')
args = parser.parse_args()

connection_string = args.connect

drone = VirtualDrone(connection_string, lidar_angle=[0], baudrate=115200,
                     two_way_switches=[7, 8], three_way_switches=[5, 6, 8, 9, 10, 11, 12],
                     critical_distance_lidar=target_distance*1.5)


" -------- Definition of a log -------- "
list_V_command = []
list_V_measured = []
list_measured_distance = []
list_yaw = []
list_time = []

" -------- Starting the mission -------- "
drone.arm_and_takeoff(2)                       #For simu only
drone.launch_mission()

time_0 = time.time()
measured_distance = 180
V_measured=0
time_command = time_0
while drone.mission_running():
    drone.update_time()                                                     # update time since connexion and mission's start
    mission_time = time.time() - time_0                                     #Time used for logs

    #if drone.do_lidar_reading():                                            # ask a reading every 20 ms
        #drone.update_detection(use_lidar=True, debug=True, walls=walls)    # distance measure SIMU
        #drone.update_detection(use_lidar=True, debug=True)                  # distance measure IRL
        #measured_distance = drone.get_distance()

    if drone.do_lidar_reading():
        time_distance = time.time()-time_command
        measured_distance = measured_distance+V_measured*time_distance*100
        print("measured_distance")
        print(measured_distance)
        " --- Automatic Stop Control --- "
        V_command = K * (measured_distance - target_distance)
        V_command = np.min([np.abs(V_command), 0.5]) * np.sign(V_command)   # Verify it doesn't exceed Vmax = 0.5 m/s

    else:
        V_command = 0.5


    print("V_command")
    print(V_command)
    " --- Log Update --- "
    V_measured = drone.get_velocity()[2]
    print("v_measured")
    print(V_measured)
    yaw = drone.get_yaw()
    list_time.append(mission_time)
    list_V_command.append(V_command)
    list_V_measured.append(V_measured)
    list_measured_distance.append(measured_distance)
    list_yaw.append(yaw)

    drone.send_mavlink_go_down(V_command)
    time_command = time.time()
    #drone._send_ned_velocity(V_command, 0.5, 0)

    if mission_time > 60 :
        drone.abort_mission()

    time.sleep(0.1)

drone.set_flight_mode("RTL")       #REMOVE THIS LINE IF IRL, FOR SIMULATOR ONLY
drone.set_flight_mode("POSHOLD")

""" -------- Save of the logs -------- """
"""
name = "log" + str(time.time())+ ".txt"
f = open(name,"w")
f.write("Time \n")
for t in list_time:
    f.write(str(t)+"\n")

f.write("V_command \n")
for t in list_V_command:
    f.write(str(t)+"\n")

f.write("V_measured \n")
for t in list_V_measured:
    f.write(str(t)+"\n")

f.write("measured_distance \n")
for t in list_measured_distance:
    f.write(str(t)+"\n")
"""

""" -------- Plot of the logs -------- """

fig, axes = plt.subplots(nrows=1, ncols=2)
title = "K=" + str(K)

axes[0].plot(list_time,list_V_command, label="Ordered")
axes[0].plot(list_time,list_V_measured, label="Measured")
axes[0].set_xlabel('Time')
axes[0].set_ylabel("Speed on x")
axes[0].legend()

axes[1].plot(list_time,list_measured_distance)
axes[1].plot([list_time[0],list_time[-1]],[target_distance,target_distance])
axes[1].set_xlabel("Time")
axes[1].set_ylabel("Measured Distance")

plt.title(title)
plt.show()



