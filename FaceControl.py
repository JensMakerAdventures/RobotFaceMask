# 29-7-2023
# Jens Oosterkamp
#
# My contributions on this project are on Creative Commons Attribution V4.
#
# This code is quick and dirty. It might not work for you. It's not optimized.
# I didn't practice best practices. It might make you cry. Use at your own risk.
#
# Code to control my white mask face project. It reads from a person sensor and displays
# two eyes and a mouth display. There is a power switch and friend/not friend switch
# in the head. Also there is a hidden demo switch which controls if a demo animation is played
#
# SPI is used for the displays. There are 3 displays, 2 are 8x8 and 1 is 8x16.
# All screens share the same SPI bus, but have their own CS (chip select) pins.
# I2C is used for the Useful Sensors Person Sensor.
# The web pages below were useful.
# https://github.com/usefulsensors/person_sensor_circuit_python
# https://microcontrollerslab.com/max7219-led-dot-matrix-display-raspberry-pi-pico/

from machine import Pin, SPI
import max7219
from time import sleep
import machine
import struct
import time
from math import sin
import random

# PIN CONFIGURATION
spi = SPI(0,sck=Pin(2),mosi=Pin(3)) # GP2 = clock, GP3 = MOSI
eyeLCS = Pin(8, Pin.OUT)
mouthCS = Pin(6, Pin.OUT)
eyeRCS = Pin(7, Pin.OUT)
camInterrupt = Pin(9, Pin.IN)
camScl = machine.Pin(5)
camSda=machine.Pin(4)
friendIsOn = Pin(10, Pin.IN, pull=Pin.PULL_DOWN)
demoIsOn = Pin(11, Pin.IN, pull=Pin.PULL_DOWN)

# CAM DATA STRUCTURE CONSTANTS BY MANUFACTURER
PERSON_SENSOR_I2C_ADDRESS = 0x62
PERSON_SENSOR_I2C_HEADER_FORMAT = "BBH"
PERSON_SENSOR_I2C_HEADER_BYTE_COUNT = struct.calcsize(
    PERSON_SENSOR_I2C_HEADER_FORMAT)

PERSON_SENSOR_FACE_FORMAT = "BBBBBBbB"
PERSON_SENSOR_FACE_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_FACE_FORMAT)

PERSON_SENSOR_FACE_MAX = 4
PERSON_SENSOR_RESULT_FORMAT = PERSON_SENSOR_I2C_HEADER_FORMAT + \
    "B" + PERSON_SENSOR_FACE_FORMAT * PERSON_SENSOR_FACE_MAX + "H"
PERSON_SENSOR_RESULT_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_RESULT_FORMAT)
PERSON_SENSOR_DELAY = 0.2

# INSTANCES
eyeL = max7219.Matrix8x8(spi, eyeLCS, 1)
mouth = max7219.Matrix8x8(spi, mouthCS, 2)
eyeR = max7219.Matrix8x8(spi, eyeRCS, 1)
sleep(3) # workaround, Pi Pico not ready to initialize i2c when connecting to a PC
i2c = machine.I2C(0, scl=camScl, sda=camSda, freq=100000)
displays = [eyeL, mouth, eyeR]
eyes = [eyeL, eyeR]
random.seed(1)

# VARIABLES
animating = True
prevAnimating = False
bootTime = time.ticks_ms()
screenOnTimeStart = time.ticks_ms()
camInterruptPrev = False
start = 0
eyeMode = 'normal'
animateIsOn = True
startNoFace = 0
startFaceSeen = 0
faceAvgLR = 128.0
faceAvgTB = 128.0
box_confidence = 0
box_left = 0
box_top = 0
box_right = 0
box_bottom = 0
xScroll = 0
yScroll = 0
id_confidence = 0
is_facing = False
satisfaction = 0 # [-3, 3]. Negative value is anger, positive is happiness



for x in displays: # 1-15
    x.brightness(15)
    x.fill(0)
    x.show()

if demoIsOn.value():
    sleep(30)
    bootTime = time.ticks_ms()

while True:
    if not demoIsOn.value():
        # Screen on if face detected in past minute
        prevAnimating = animating;
        if not camInterrupt.value():
            if camInterruptPrev:
                startNoFace = time.ticks_ms()
            if time.ticks_diff(time.ticks_ms(), startNoFace) > 5000:
                animating = False
            else:
                animating = True
                startFaceSeen = time.ticks_ms()
        camInterruptPrev = camInterrupt.value()
    
        if animating and not prevAnimating:
            screenOnTimeStart = time.ticks_ms()
        
    screenOnTime = time.ticks_diff(time.ticks_ms(), screenOnTimeStart)
    
    if not demoIsOn.value():
        if friendIsOn.value():
            satisfaction = round(1.5+1.5*sin(screenOnTime/1200))
            for x in displays:
                x.brightness(int(10+5*sin(screenOnTime/800)))
        else:
            #satisfaction = round(-1.5-1.5*sin(screenOnTime/2000))
            satisfaction = round(-1.5-1.5*sin(screenOnTime/2000))
            for x in displays:
                x.brightness(int(10+5*sin(screenOnTime/700)))
    else:
        timeSinceBoot = time.ticks_diff(time.ticks_ms(), bootTime)/1000.0
        print(timeSinceBoot)
        if timeSinceBoot < 5:
            print('waiting to start')
            for x in displays: # 1-15
                x.brightness(1)
                x.fill(0)
                x.show()
            animating = False
            satisfaction = 0
            
        if (timeSinceBoot > 5) and (timeSinceBoot < 10):
            print('pixelating effect')
            for i in range(64):
                for x in eyes:
                    sleep(0.003*(64-i))
                    x.pixel(random.randint(2,5),random.randint(2,5),1)
                    x.show()
                mouth.pixel(random.randint(1,14),random.randint(3,4),1)               
                mouth.show()
                
        if (timeSinceBoot > 18) and (timeSinceBoot < 21):
            print('empty screen')
            for x in displays: # 1-15
                x.brightness(15)
                x.fill(0)
                x.show()
            
            
        if (timeSinceBoot > 21) and (timeSinceBoot < 45):
            print('anger buildup')
            satisfaction = round(-1.5-1.5*sin(-2+(timeSinceBoot-21)/5))
            animating = True
            for x in displays:
                x.brightness(int(8+7*sin(screenOnTime/700 - 5)))
                
        if timeSinceBoot > 45:
            satisfaction = round(3.0*sin(screenOnTime/1200))
            for x in displays:
                x.brightness(int(10+5*sin(screenOnTime/800)))        
    
    if animating:
        for x in displays:
            x.fill(0)
            x.show()
        for idx, x in enumerate(eyes):            
            # Mouth base shape
            mouthXStart = 1
            mouthYStart = 3
            mouthWidth = 14
            mouthHeight = 2
            mouth.rect(mouthXStart, mouthYStart, mouthWidth, mouthHeight, 1, 1)
            mouth.rect(5, 2, 6, 4, 1, 1)
            
            # Eyes base shape
            xStart = 2
            yStart = 2
            width = 4
            height = 4
            screenHeight = 8
            screenWidth = 8
            x.rect(xStart,yStart,height,width,1,1)
            
            #satisfaction = 3
            if satisfaction == -3:
                if idx == 1:
                    x.pixel(xStart+width-1,yStart,0)
                    x.pixel(xStart+width-2,yStart,0)
                    x.pixel(xStart+width-1,yStart+1,0)
                    x.pixel(xStart+1,yStart,0)
                    x.pixel(xStart+2,yStart+1,0)
                    x.pixel(xStart+3,yStart+2,0)
                else:
                    x.pixel(xStart,yStart,0)
                    x.pixel(xStart+1,yStart,0)
                    x.pixel(xStart,yStart+1,0)
                    x.pixel(xStart+width-2,yStart,0)
                    x.pixel(xStart+width-3,yStart+1,0)
                    x.pixel(xStart+width-4,yStart+2,0)
                    
                mouth.hline(0,5,16,0)
                mouth.hline(1,5,2,1)
                mouth.hline(13,5,2,1)
                mouth.hline(1,6,2,1)
                mouth.hline(13,6,2,1)
                mouth.pixel(1,3,0)
                mouth.pixel(14,3,0)
                mouth.hline(5,4,6,0)
                
            if satisfaction == -2:
                if idx == 1:
                    x.pixel(xStart+width-1,yStart,0)
                    x.pixel(xStart+width-2,yStart,0)
                    x.pixel(xStart+width-1,yStart+1,0)
                else:
                    x.pixel(xStart,yStart,0)
                    x.pixel(xStart+1,yStart,0)
                    x.pixel(xStart,yStart+1,0)
                    
                mouth.hline(0,5,16,0)
                mouth.hline(1,5,2,1)
                mouth.hline(13,5,2,1)
                mouth.pixel(1,3,0)
                mouth.pixel(14,3,0)
                mouth.hline(6,4,4,0)
                
            if satisfaction == -1:
                if idx == 1:
                    x.pixel(xStart+width-1,yStart,0)
                else:
                    x.pixel(xStart,yStart,0)
                mouth.hline(0,5,16,0)
                mouth.pixel(1,3,0)
                mouth.pixel(14,3,0)
                
            elif satisfaction == 0:
                pass
            elif satisfaction == 1:
                x.pixel(xStart,yStart,0)
                x.pixel(xStart,yStart+height-1,0)
                x.pixel(xStart+width-1,yStart,0)
                x.pixel(xStart+width-1,yStart+height-1,0)
                
                mouth.hline(0,2,16,0)
                mouth.pixel(1,4,0)
                mouth.pixel(14,4,0)
            elif satisfaction == 2:
                x.pixel(xStart,yStart,0)
                x.pixel(xStart,yStart+height-1,0)
                x.pixel(xStart+width-1,yStart,0)
                x.pixel(xStart+width-1,yStart,0)
                x.pixel(xStart+1,yStart+height-1,0)
                x.pixel(xStart+2,yStart+height-1,0)
                x.pixel(xStart+3,yStart+height-1,0)
                
                mouth.hline(0,2,16,0)
                mouth.hline(1,2,2,1)
                mouth.hline(13,2,2,1)
                mouth.pixel(1,4,0)
                mouth.pixel(14,4,0)
                
            elif satisfaction == 3:
                x.pixel(xStart,yStart,0)
                x.pixel(xStart+width-1,yStart,0)
                x.pixel(xStart+width-1,yStart,0)
                x.pixel(xStart+1,yStart+height-1,0)
                x.pixel(xStart+2,yStart+height-1,0)
                
                mouth.fill(0)
                mouth.rect(mouthXStart, mouthYStart+1, mouthWidth, mouthHeight, 1, 1)
                mouth.rect(5, 2+1, 6, 4, 1, 1)
                mouth.hline(0,3,16,0)
                mouth.hline(1,3,2,1)
                mouth.hline(13,3,2,1)
                mouth.hline(1,2,2,1)
                mouth.hline(13,2,2,1)
                mouth.pixel(1,5,0)
                mouth.pixel(14,5,0)
                mouth.hline(6,4,4,0)
                mouth.hline(1,2,14,1)
                mouth.hline(1,1,14,1)                

            else:
                pass
            xScroll = -int((faceAvgLR - 128.0) / 256.0 * 14) 
            yScroll = int(-2.5 + (faceAvgTB - 128.0) / 256.0 * 14) # -1 compensates for camera mounted at angle
            if xScroll > 2:
                xScroll = 2;
            if xScroll < -2:
                xScroll = -2;
            if yScroll > 2:
                yScroll = 2;
            if yScroll < -2:
                yScroll = -2;
            
            if not demoIsOn.value():
                x.scroll(xScroll, yScroll)
            x.show()                
            
        if not demoIsOn.value():
            mouth.scroll(round(xScroll/2), round(yScroll/2))
        mouth.show()
    
    else:
        for x in displays:
            x.fill(0)
            x.show()
        
    
    # Sensor reading
    read_data = bytearray(PERSON_SENSOR_RESULT_BYTE_COUNT)
    i2c.readfrom_into(PERSON_SENSOR_I2C_ADDRESS, read_data)

    offset = 0
    (pad1, pad2, payload_bytes) = struct.unpack_from(
        PERSON_SENSOR_I2C_HEADER_FORMAT, read_data, offset)
    offset = offset + PERSON_SENSOR_I2C_HEADER_BYTE_COUNT

    (num_faces) = struct.unpack_from("B", read_data, offset)
    num_faces = int(num_faces[0])
    offset = offset + 1

    faces = []
    for i in range(num_faces):
        (box_confidence, box_left, box_top, box_right, box_bottom, id_confidence, id,
         is_facing) = struct.unpack_from(PERSON_SENSOR_FACE_FORMAT, read_data, offset)
        offset = offset + PERSON_SENSOR_FACE_BYTE_COUNT
        face = {
            "box_confidence": box_confidence,
            "box_left": box_left,
            "box_top": box_top,
            "box_right": box_right,
            "box_bottom": box_bottom,
            "id_confidence": id_confidence,
            "id": id,
            "is_facing": is_facing,
        }
        faces.append(face)
    checksum = struct.unpack_from("H", read_data, offset)
    #print(num_faces, faces)
    
    faceAvgLR = (box_left + box_right) / 2.0
    faceAvgTB = (box_top + box_bottom) / 2.0

    sleep(PERSON_SENSOR_DELAY)    