#!/usr/bin/env python3

import time
from datetime import datetime
import colorsys
import os
import sys
import ST7735
from thread import *
from threading import *

try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

from bme280 import BME280
from enviroplus import gas
from subprocess import PIPE, Popen
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from fonts.ttf import RobotoMedium as UserFont
import logging

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logging.info("""all-in-one.py - Displays readings from all of Enviro plus' sensors
Press Ctrl+C to exit!
""")

# BME280 temperature/pressure/humidity sensor
bme280 = BME280()

# Create ST7735 LCD display class
st7735 = ST7735.ST7735(
    port=0,
    cs=1,
    dc=9,
    backlight=12,
    rotation=270,
    spi_speed_hz=10000000
)

# Initialize display
st7735.begin()

WIDTH = st7735.width
HEIGHT = st7735.height

# Set up canvas and font
img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
draw = ImageDraw.Draw(img)
path = os.path.dirname(os.path.realpath(__file__))
font_size = 20
font = ImageFont.truetype(UserFont, font_size)

message = ""

# The position of the top bar
top_pos = 25


# Displays data and text on the 0.96" LCD
def display_text(variable, data, unit):
    # Maintain length of list
    values[variable] = values[variable][1:] + [data]
    # Scale the values for the variable between 0 and 1
    vmin = min(values[variable])
    vmax = max(values[variable])
    colours = [(v - vmin + 1) / (vmax - vmin + 1) for v in values[variable]]
    # Format the variable name and value
    message = "{}: {:.1f} {}".format(variable[:4], data, unit)
    logging.info(message)
    draw.rectangle((0, 0, WIDTH, HEIGHT), (255, 255, 255))
    draw.rectangle((0, 25, WIDTH, HEIGHT), (255, 255, 255))
    # Write the text at the top in black
    draw.text((0, 0), message, font=font, fill=(0, 0, 0))
    draw.text((0, 25), message, font=font, fill=(0, 0, 0))
    st7735.display(img)


# Get the temperature of the CPU for compensation
def get_cpu_temperature():
    try:
        process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE, universal_newlines=True)
        output, _error = process.communicate()
        return float(output[output.index('=') + 1:output.rindex("'")])
    except:
        return float(0)


# Tuning factor for compensation. Decrease this number to adjust the
# temperature down, and increase to adjust up
factor = 2.25

cpu_temps = [get_cpu_temperature()] * 5

delay = 0.5  # Debounce the proximity tap
mode = 0  # The starting mode
last_page = 0
light = 1

# Create a values dict to store the data
variables = ["temperatureC",
             "temperatureF",
             "pressure",
             "humidity",
             "light"]

values = {}

for v in variables:
    values[v] = [1] * WIDTH
    
def displayData():

        proximity = ltr559.get_proximity()

        # If the proximity crosses the threshold, toggle the mode
        if proximity > 1500 and time.time() - last_page > delay:
            mode += 1
            mode %= len(variables)
            last_page = time.time()

        # datetime for timestamp
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%y %H:%M:%S")

        # variable = "temperatureF"
        unit = "F"
        cpu_temp = get_cpu_temperature()
        # Smooth out with some averaging to decrease jitter
        global cpu_temps
        cpu_temps = cpu_temps[1:] + [cpu_temp]
        avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
        raw_temp = bme280.get_temperature()
        dataTemp = raw_temp - ((avg_cpu_temp - raw_temp) / factor)
        dataTemp = (dataTemp * 1.8) + 32
        
        # variable = "pressure"
        # unit = "hPa"
        dataPressure = bme280.get_pressure()
        
        # variable = "humidity"
        #unit = "%"
        dataHumidity = bme280.get_humidity()
        
        # variable = "light"
        #unit = "Lux"
        if proximity < 10:
            dataLight = ltr559.get_lux()
        else:
            dataLight = 1
            
        # Format the variable name and value
        messageTemp = "{:.1f}{} {:.1f}{}".format(dataTemp, "F", dataPressure, "hPa")
        #messagePressure = "{}: {:.1f} {}".format("pressure"[:4], dataPressure, "hPa")
        messageHumidity = "{}: {:.1f} {}".format("humidity", dataHumidity, "%")
        #messageLight = "{}: {:.1f} {}".format("light"[:4], dataLight, "Lux")
        logging.info("Update")
        draw.rectangle((0, 0, WIDTH, HEIGHT), (13, 13, 13))
        draw.rectangle((0, 25, WIDTH, HEIGHT), (13, 13, 13))
        draw.rectangle((0, 50, WIDTH, HEIGHT), (13, 13, 13))
        #draw.rectangle((0, 75, WIDTH, HEIGHT), (13, 13, 13))
        # Write the text at the top in black
        draw.text((0, 0), messageTemp, font=font, fill=(217, 217, 217))
        #draw.text((0, 25), messagePressure, font=font, fill=(217, 217, 217))
        draw.text((0, 25), messageHumidity, font=font, fill=(217, 217, 217))
        #draw.text((0, 75), messageLight, font=font, fill=(0, 0, 0))
        draw.text((0, 50), dt_string, font=font, fill=(217, 217, 217))
        st7735.display(img)
    
def updateDisplay():
  Timer(10, updateDisplay).start()
  displayData()

updateDisplay()
