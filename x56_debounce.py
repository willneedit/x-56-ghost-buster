from pygame.constants import GL_CONTEXT_ROBUST_ACCESS_FLAG
import pygame.joystick as js
import pygame as pg
import pygame.event as evt
import time as t
import pyvjoy as vj
import sys
import numpy as np

pg.init()
js.init()

print("\nPygame joystick handler initialised.\n  %d devices found." % js.get_count())

print("\nSearching for X56 Throttle...\n")
vJoy_found = False
x56_found = False
if len(sys.argv) == 2:
    dbTime = int(sys.argv[1])*1000
else:
    dbTime = 50000
joys = [js.Joystick(i) for i in range(js.get_count())]
for i in range(js.get_count()):
    joys[i] = js.Joystick(i)
    joys[i].init()
    
    if joys[i].get_name() == "Saitek Pro Flight X-56 Rhino Throttle":
        print("X56 Throttle found at index %d" % i)
        x56 = joys[i]
        print("Buttons: %d" % x56.get_numbuttons())
        print("Axes: %d\n" % x56.get_numaxes())
        x56_found = True
    
    elif joys[i].get_name() == "vJoy Device":
        print("vJoy Device found at index %d" % i)
        vJoy = joys[i]
        print("Buttons: %d" % vJoy.get_numbuttons())
        print("Axes: %d\n" % vJoy.get_numaxes())
        vJoy_found = True
        j = vj.VJoyDevice(1)

    else:
        print("Other joystick/gamepad: %s\n" % joys[i].get_name())
        
    if vJoy_found and x56_found:
        break
        
button_count = vJoy.get_numbuttons()
button_timers = [-1] * button_count
button_states = np.zeros(button_count)
button_set = np.zeros(button_count)

axis_count = vJoy.get_numaxes()
axis_state = np.zeros(axis_count)
axis_dropped = [False] * axis_count

print("\nLooping...")

while  vJoy_found and x56_found:
    loop_start = t.time_ns()/1000
    for event in evt.get():
        if event.type == pg.JOYBUTTONDOWN:
            for i in range(button_count):
                if x56.get_button(i):
                    button_timers[i] = loop_start
                    # print("Button %d down" % (i+1))
        if event.type == pg.JOYBUTTONUP:
            for i in range(button_count):
                if not x56.get_button(i):
                    button_timers[i] = -1.0
                    # print("Button %d up" % (i+1))

    for i in range(axis_count):
        new_axis_state = x56.get_axis(i)
        axis_diff = new_axis_state - axis_state[i]
        if axis_state[i] != new_axis_state:
            if new_axis_state > 0.995 and axis_state[i] < 0.800:
                print("Dropout in axis %d (%6.3f)!" % (i, new_axis_state))
                old_axis_dropped = axis_dropped[i]
                axis_dropped[i] = True
                if old_axis_dropped:
                    axis_state[i] = new_axis_state
            else:
                axis_dropped[i] = False
                axis_state[i] = new_axis_state
                # print("Axis %d state %6.3f" % (i , axis_state[i]))

    button_states_mem = np.copy(button_states)

    for i in range(button_count):
        if button_timers[i] == -1.0:
            button_states[i] = 0
        elif loop_start - button_timers[i] > dbTime:
            button_states[i] = 1
        elif i<=30 and i>=29:
            button_states[i] = 1

    button_states_diff = np.logical_and(np.logical_xor(button_states, button_states_mem),np.logical_not(button_states_mem))
    
    if np.sum(button_states_diff[0:button_count-3])> 1:
        button_states[0:button_count-3] = np.copy(button_states_mem[0:button_count-3])
        # print("Button diff is %d, which is greater than 1!" % np.sum(button_states_diff[0:button_count-3]))
    
    if np.sum(button_states[button_count-3:button_count]) > 1:
        button_states[button_count-3:button_count] = np.copy(button_states_mem[button_count-3:button_count])

    for i in range(axis_count):
        j.set_axis(i + 0x30,int(axis_state[i] * 0x8000 + 0x3FFF))
        
    for i in range(button_count):
        if (i>30 or i<29):
            if button_states[i] == 1 and button_set[i] == 0:
                j.set_button(i+1,1)
                button_set[i] = 1
                print("Button %d is set to 1" % (i+1))

            elif button_states[i] == 0 and button_set[i] == 1:
                j.set_button(i+1,0)
                button_set[i] = 0
                print("Button %d is set to 0" % (i+1))
        else:
            if button_states[i] == 1 and button_set[i] == 0:
                j.set_button(i+1,1)
                button_set[i] = 1
                print("Button %d is set to 1(UNFILTERED)"% (i+1))

            elif button_states[i] == 0 and button_set[i] == 1:
                j.set_button(i+1,0)
                button_set[i] = 0
                print("Button %d is set to 0(UNFILTERED)" % (i+1))
        

    x56_found = False
    vJoy_found = False
    for i in range(js.get_count()):
        joys[i] = js.Joystick(i)
        joys[i].init()
        
        if joys[i].get_name() == "Saitek Pro Flight X-56 Rhino Throttle":
            x56_found = True
            x56 = joys[i]
        
        if joys[i].get_name() == "vJoy Device":
            vJoy_found = True
            vJoy = joys[i]

        if vJoy_found and x56_found:
            break

    loop_end = t.time_ns()/1000
    loop_time = (loop_end - loop_start)
    if loop_time < 10*(10**3):
        t.sleep(0.01 - loop_time/(10**6))
    else:
        print("\rLoop time: %.3f ms!!!" % (loop_time/(10**3)))

print("\nDevice plugged out (x56_found: %d, vJoy_found: %d). Stopping..." % (x56_found,vJoy_found))