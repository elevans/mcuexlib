from mcuexlib import display
from machine import I2C, Pin
from micropython import const

# config I2C speed
I2C_FREQ = const(400000)
DSP_HEIGHT = const(32)
DSP_WIDTH = const(128)

# config pins
dsp_scl = Pin(17)
dsp_sda = Pin(16)

# initialize the display
dsp = display.SSD1306_I2C(DSP_WIDTH, DSP_HEIGHT, I2C(id=0, scl=dsp_scl, sda=dsp_sda, freq=I2C_FREQ))
dsp.fill(0)
