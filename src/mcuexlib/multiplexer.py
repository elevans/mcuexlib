from mcuexlib.addresses import device_address
from machine import Pin, I2C

I2C_MULTIPLEXER_ADDRESS = device_address.get("TCA9548")

class AnalogMultiplexer:
    """Analog Multiplexer.

    This class provides control methods for an analog Multiplexer.

    :param s0: Select pin 0.
    :param s1: Select pin 1.
    :param s2: Select pin 2.
    :param s3: Select pin 3.
    :param sig: The common or IO pin.
    """
    def __init__(self, s0: Pin, s1: Pin, s2: Pin, s3: Pin, sig: Pin):
        """Constructor method
        """
        self.s0 = s0
        self.s1 = s1
        self.s2 = s2
        self.s3 = s3
        self.sig = sig
        self._ch_reg = {} # dict for the channel register
        self._init_multiplexer()

    def select_channel(self, ch: int):
        """Select a channel.

        Select a channel on the multiplexer.

        :param ch: A channel
        """
        # get and set channel pin config
        ch_conf = self.ch_reg.get(ch)
        self.s0.value(ch_conf[0])
        self.s1.value(ch_conf[1])
        self.s2.value(ch_conf[2])
        self.s3.value(ch_conf[3])

    def _init_multiplexer(self):
        """Initialize the analog multiplexer.
        """
        # cache references as local var
        ch_reg = self._ch_reg
        # create the channel register
        r = range(2)
        for s3 in r:
            for s2 in r:
                for s1 in r:
                    for s0 in r:
                        ch = s3 * 8 + s2 * 4 + s1 * 2 + s0
                        row = bytes([s0, s1, s2, s3])
                        ch_reg[ch] = row

class I2CMultiplexer:
    """I2C Multiplexer.

    This class provides control methods for an I2C Multiplexer.

    :param i2c: An instance of `machine.I2C`.
    """
    def __init__(self, i2c: I2C):
        """Constructor method
        """
        self.device = None # access the channel's device instance
        self.active_channels = bytearray() # array of active channels - for valid channel options
        self.inactive_channels = bytearray() # array of inactive channels - for skpping
        self.channel = 0 # current channel selected on multiplexer
        self.multiplexer = i2c # access to the multiplexer itself
        self.device_reg = {} # dict that stores device id, keys are channel
        self._chs = bytearray(8) # pre-allocate an 8 byte buffer for channel control register
        self._buf = bytearray(1) # pre-allocate a 1 byte temp buffer
        self._init_multiplexer()

    def register_device(self, addr: int, ch: int, name: str, device):
        """Register an I2C device.

        Register an initialized device to the multiplexer's device register.

        :param addr: The device address (e.g. 0x70).
        :param ch: The device channel.
        :param name: The device name.
        :param device: Instance of the initialized device.
        """
        dev_reg = self.device_reg
        if dev_reg.get(ch) is None:
            dev_reg[ch] = ([name], [addr], [device])
        else:
            dev_reg[ch][0].append(name)
            dev_reg[ch][1].append(addr)
            dev_reg[ch][2].append(device)

    def get_device_address(self, ch: int):
        """ Get the device address.

        Get the address or addresses of all devices on a given
        channel.
        
        :param ch: The device channel.
        :return: List of device addresses.
        :rtype: list
        """
        self._set_channel(ch)
        scan_res = self.multiplexer.scan()
        scan_res.remove(I2CMULTIPLEXER_ADDRESS)
        self._set_channel(self.channel)

        return scan_res

    def select_channel(self, ch: int):
        """ Select a channel.

        Select a channel (0 through 7). Access the list
        of connected devices with the `device` attribute.

        :param ch: The device channel.
        """
        self._set_channel(ch)
        self.channel = ch
        self.device = self.device_reg[self.channel][-1]

    def next_channel(self):
        """Select the next channel.

        Select the next channel from the available active channels on the
        multiplexer.
        """
        ch_index = self.active_channels.index(self.channel)
        if ch_index >= 0 and ch_index < len(self.active_channels):
            ch_index += 1
            self.select_channel(self.active_channels[ch_index])
        else:
            ch_index = 0
            self.select_channel(self.active_channels[ch_index])

    def previous_channel(self):
        """Select the previous channel.

        Select the previous channel from the available active channels on the
        multiplexer.
        """
        ch_index = self.active_channels.index(self.channel)
        if ch_index >= 0 and ch_index < len(self.active_channels):
            ch_index -= 1
            self.select_channel(self.active_channels[ch_index])
        else:
            ch_index = len(self.active_channels) - 1
            self.select_channel(self.active_channels[ch_index])

    def _init_multiplexer(self):
        """Initialize the I2C multiplexer.
        """
        # fetch methods and vars
        buf = self._buf
        chs = self._chs
        a_chs = self.active_channels
        i_chs = self.inactive_channels
        scan = self.multiplexer.scan
        write = self.multiplexer.writeto

        # initialize control register
        r = range(8)
        for i in r:
            chs[i] = 1 << i

        # find channels with connected devices
        for j in r:
            buf[0] = chs[j]
            write(I2CMULTIPLEXER_ADDRESS, buf) # select channel j on the mux
            scan_res = scan()
            if len(scan_res) > 1:
                a_chs.append(j)
            else:
                i_chs.append(j)

        # default to first channel
        self._set_channel(self.active_channels[0])

    def _set_channel(self, ch: int):
        """Set the multiplexer channel.
        """
        # fetch the temp buffer
        buf = self._buf
        if ch >= 0 and ch < 8:
            buf[0] = self._chs[ch]
            self.multiplexer.writeto(I2CMULTIPLEXER_ADDRESS, buf)
