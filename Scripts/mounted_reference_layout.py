"""Shared centimetre-scale reference terrain, used by Blender and UE placement."""
import math

def ground(x,y):
    radius=math.hypot(x,y)
    outer=max(0.,min(1.,(radius-3400)/9000));outer=outer*outer*(3-2*outer)
    return (.035*x-.10*y+52*math.sin(x/1350)*math.cos(y/1900)
        +135*math.exp(-((x-1100)/1900)**2-((y+1650)/1100)**2)
        -135*math.exp(-(1100/1900)**2-(1650/1100)**2)
        +95*math.sin(x/4700)*math.sin(y/4100)
        +outer*(1300+750*math.sin(x/4500)*math.cos(y/6100)))
