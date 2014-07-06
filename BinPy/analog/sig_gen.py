from BinPy import *
import threading
import math


class SignalGenerator(threading.Thread):

    """
    Signal Generator Block
    ======================

    Create a SignalGenerator object ( runs on a child thread ) used to generate an analog voltage signal of the desired type.
    The frequency, amplitude and modulation parameters can be customized.

    All inputs / outputs / enable are Bus types

    METHODS
    =======

    set_enable(enable_Bus_1_bit)     : link the enable_Bus_1_bit with the Buffer's enable.

    set_type(integer_type)           : Set the output waveform type.

                                       ================================================================
                                       | TYPE_NO   |    TYPE         |    Built-in Constant Name      |
                                       ================================================================
                                       |   0       |    Sine         |    SignalGenerator.SIN         |
                                       |   1       |    Square       |    SignalGenerator.SQUARE      |
                                       |   2       |    Ramp         |    SignalGenerator.RAMP        |
                                       |   3       |    Triangular   |    SignalGenerator.TRIANGULAR  |
                                       |   4       |    Saw Tooth    |    SignalGenerator.SAWTOOTH    |
                                       |   5       |    TTL          |    SignalGenerator.TTL         |
                                       ================================================================

    set_attenuation(float)           : The integer_level decides the attenuation level.
                                       Though this can be configured to any custom floating point value, it is adviced to choose among the
                                       standard attenuation levels using the SignalGenerator.ATTEN_LEVEL dict.

    set_amplitude(float_percent_max) : The amplitute is set as a linearly varying percent of the total maximum ( out of 100 ) for the current Attenuation level.

    set_outputs(output_Bus_2_bit)    : The output is linked to the 2 Bit Bus passed to the method.
                                       output_Bus_2_bit[0] will link to the signal generator output
                                       output_Bus_2_bit[1] will link to the SignalGenerator's GND

    set_frequency_range(tuple)       : set the frequency range of the SignalGenerator object.
                                       NOTE: While this can be configured to any value, it is very strongly emphasized to use standard frequency ranges as
                                       defined in the SignalGenerator.FREQ_RANGE dict which contains tuples of predefined ranges.
                                       This will ensure stable behaviour.

    set_frequency(float_percent_max) : The final output frequency is the float_percent_max percent of the currently set frequency range.

    set_frequency_exact(float)       : This method is used to set the exact output frequency of the SignalGenerator object.
                                       If the given value is above SignalGenerator.FREQ_MAX or below SignalGenerator.FREQ_MIN the output frequency
                                       saturates at the either extremes.
                                       NOTE: This method is preferred over setting custom frequency ranges.

    set_amplitude_exact(float)       : This method is used to set the exact output amplitude of the SignalGenerator object.
                                       If the given value is above SignalGenerator.AMPL_MAX or below SignalGenerator.AMPL_MIN the output amplitude
                                       saturates at the either extremes.
                                       NOTE: This method is preferred over setting custom amplitude attenuation values.

    set_modulation_input(Bus_2_bit)  : Link the external modulation input to modulate the output accordingly.

    set_modulation_type(integer_type): Set the modulation type to the desired value.

                                       =======================================================
                                       | TYPE_NO   |    TYPE   |    Built-in Constant Name   |
                                       =======================================================
                                       |   0       |    NONE   |    SignalGenerator.NO_MOD   |
                                       |   1       |    AM     |    SignalGenerator.AM_MOD   |
                                       |   2       |    FM     |    SignalGenerator.FM_MOD   |
                                       =======================================================


    trigger()                        : Calculate and update the time varying output based on the current setting.


    PROPERTIES
    ==========

    type                             : Returns the type no of the output waveform
    frequency                        : Current Frequency of the output ( in Hz )
    frequency_range                  : Returns a tuple of the current frequency range
    time_period                      : Current Time period of the output in s
    attenuation                      : Current Attenuation level in db
    amplitude                        : Current amplitude level
    enabled                          : Returns true if the enable input is HIGH
    disabled                         : Returns true if the enable input is LOW

    CONSTANTS
    =========

    AMPL_MIN                         : 0.0  v
    AMPL_MAX                         : 10.0 v
    FREQ_MIN                         : 0.1 Hz ( 10s Total time period )
    FREQ_MAX                         : 1,000,000,000 Hz ( 1 GHz )

    NO_MOD                           : 0
    AM_MOD                           : 1
    FM_MOD                           : 2

    SIN                              : 0
    SQUARE                           : 1
    RAMP                             : 2
    TRIANGULAR                       : 3
    SAWTOOTH                         : 4
    TTL                              : 5

    FREQ_RANGE                       : {
                                         0 : ( 0.1, 10   ),
                                         1 : ( 10, 100   ),
                                         2 : ( 100, 1k   ),
                                         3 : ( 1k, 10k   ),
                                         4 : ( 10k, 100k ),
                                         5 : ( 100k, 1M  ),
                                         6 : ( 1M,  10M  ),
                                         7 : ( 10M, 1G   )
                                       }

    ATTEN_LEVEL                      : { 0 : 0db, 1 : 10db, 2 : 20db, 3 : 30db, 4 : 40db }


    USAGE
    =====

    >>> sig1 = SignalGenerator(typ = SignalGenerator.SIN, freq = 1000, ampl = 5.0, modulation = SignalGenerator.NO_MOD)
    >>> a = Bus(2); a.set_type(analog=True);
    >>> sig1.set_output(a)

    # Checking the output
    >>> start_time = time.time()
    >>> table = []
    >>> while ( ( time.time() - start_time ) <= a.time_period ):
            # Print values for 1 time period
            table.append( len(table), ( float(a[0]) - float(a[1]) )) # Sampling table
            time.sleep(a.time_period / float(10))

    >>> print ( table )
    (0, 0.2), ()


    """

    # Defining the constants

    AMPL_MIN = 0.0
    AMPL_MAX = 10.0
    FREQ_MIN = 0.1
    FREQ_MAX = 1000000000

    NO_MOD = 0
    AM_MOD = 1
    FM_MOD = 2

    SIN = 0
    SQUARE = 1
    RAMP = 2
    TRIANGULAR = 3
    SAWTOOTH = 4
    TTL = 5

    FREQ_RANGE = {
        0: (0.1, 10),
        1: (10, 100),
        2: (100, 1000),
        3: (1000, 10000),
        4: (10000, 100000),
        5: (100000, 1000000),
        6: (1000000, 10000000),
        7: (10000000, 1000000000)
    }

    ATTEN_LEVEL = {0: 0, 1: 10, 2: 20, 3: 30, 4: 40}

    def __init__(self, typ=0, freq=1000, ampl=5):
        threading.Thread.__init__(self)
        self.daemon = True

        self.enable = Bus(1)

        self.outputs = Bus(2)
        self.outputs.set_type(analog=True)
        self.set_offset(0.0)

        self.mod_ip = Bus(2)
        self.mod_ip.set_type(analog=True)
        self.set_modulation_type(0)  # Default value is no modulation

        self.set_type(typ)

        self._frequency = 1000.0
        self.set_frequency_exact(freq)
        # This will calculate the range / freq percent ( equiv. to freq. knob )
        # and update them accordingly

        self._amplitude = 1.0
        self.set_amplitude_exact(ampl)
        # This will calculate the ampl range / amplitude percent ( equiv. to
        # amplitude knob ) and update them accordingly

        self._exit = False
        # Auto start the thread
        self.start()

    @property
    def frequency(self):
        return float(self._frequency)

    @property
    def time_period(self):
        return float(self._time_period)

    @property
    def attenuation(self):
        return float(self._attenuation)

    @property
    def amplitude(self):
        return float(self._amplitude)

    @property
    def offset(self):
        return float(self._offset)

    @property
    def type(self):
        return float(self._type)

    @property
    def enabled(self):
        return bool(self._enable)

    @property
    def disabled(self):
        return not self.enabled

    @property
    def frequency_range(self):
        return self._frequency_range

    @property
    def SAMPLING_TIME_INTERVAL(self):
        # Much greater than the nyquist rate for an accurate output with the
        # least deviation.
        return self._time_period / float(500)

    def set_amplitude_exact(self, ampl):
        """ Set the amplitude of the output signal """
        if (type(ampl) not in [int, float]):
            raise Exception(
                "ERROR: Amplitude can only be a float ( or int ) value.")

        if ampl <= self.AMPL_MIN:
            self._amplitude = 0
            self._attenuation = 0

        if ampl >= self.AMPL_MAX:
            self._amplitude = 10  # 10v is the maximum amplitude
            self._attenuation = 0

        self._attenuation = 20 * (math.log10(float(ampl) / 10))
        self._amplitude = float(ampl)

    def set_attenuation(self, attenuation):
        """ Set the attenuation value. Use float values for input or use predefined dictionary SignalGenerator.ATTEN_LEVEL """
        if (type(attenuation) not in [int, float]):
            raise Exception(
                "ERROR: Attenuation can only be a float ( or int ) value.")

        if (attenuation < 0):
            raise Exception("ERROR: Only positive values can be given")

        self._attenuation = attenuation

    def set_amplitude(self, percent_range):
        """
        Set the amplitude as the percentage value of the current range. - Knob like usage.
        The current range is decided by the current attenuation value.
        Set appropriate attenuation value before setting the amplitude.
        """
        if (type(percent_range) not in [int, float]):
            raise Exception("ERROR: Only int or float values can be passed.")

        if (percent_range < 0 or percent_range > 100):
            raise Exception(
                "ERROR: Only values between 1 to 100 can be passed")

        self._amplitude = float(self.AMPL_MIN +
                                (((10 ** (-
                                          self._attenuation /
                                          20)) *
                                  self.AMPL_MAX) *
                                 percent_range *
                                 0.01))

    def set_frequency_range(self, range_tuple):
        """
        Set the frequency range of the output. Use ranges within SignalGenerator.FREQ_MAX and SignalGenerator.FREQ_MIN.
        Specify input as a tuple containg the LOW followed by the HIGH frequency limits. Preferably use the predefined constant dictionary
        SignalGenerator.FREQ_RANGE

        FREQ_RANGE    {
                         0 : ( 0.1, 10   ),
                         1 : ( 10, 100   ),
                         2 : ( 100, 1k   ),
                         3 : ( 1k, 10k   ),
                         4 : ( 10k, 100k ),
                         5 : ( 100k, 1M  ),
                         6 : ( 1M,  10M  ),
                         7 : ( 10M, 1G   )
                       }
        """

        if (type(range_tuple) not in [list, tuple]):
            raise Exception(
                "ERROR: Invalid input. Input can be specified only as a list or a tuple")

        if (len(range_tuple)) != 2:
            raise Exception(
                "ERROR: The length of the frequency range tuple is not 2")

        if (range_tuple[0] > range_tuple[1]):
            raise Exception(
                "ERROR: Low frequency limit is higher than the High frequency limit")

        if (range_tuple[0] < self.FREQ_MIN):
            range_tuple[0] = self.FREQ_MIN

        if (range_tuple[1] > self.FREQ_MAX):
            range_tuple[1] = self.FREQ_MAX

        self._frequency_range = tuple(range_tuple)

    def set_frequency(self, percent_range):
        """
        Set the frequency as the percentage value of the current range. - Knob like usage.
        Set appropriate range before setting the frequency.
        """
        if (type(percent_range) not in [int, float]):
            raise Exception("ERROR: Only int or float values can be passed.")

        if (percent_range < 0 or percent_range > 100):
            raise Exception(
                "ERROR: Only values between 1 to 100 can be passed")

        self._frequency = float(self._frequency_range[
                                0] + (self._frequency_range[1] - self._frequency_range[0]) * percent_range)

        if self._frequency != 0:
            self._time_period = float(1) / self._frequency
        else:
            self._time_period = float("inf")

    def set_frequency_exact(self, frequency):
        """
        Set the given frequency as the freqency of the output. The current range will be varied based on the value.
        """
        if (type(frequency) not in [int, float]):
            raise Exception(
                "ERROR: Invalid Input type. Frequency can only be a float value")

        if (frequency < self.FREQ_MIN):
            self._frequency = self.FREQ_MIN

        if (frequency > self.FREQ_MAX):
            self._frequency = self.FREQ_MAX

        self._frequency = float(frequency)

        # Choose the appropriate frequency range based on the passed value.
        for i in range(len(self.FREQ_RANGE)):
            if (frequency <= self.FREQ_RANGE[i][0] and frequency >= self.FREQ_RANGE[i][0]):
                self._frequency_range = self.FREQ_RANGE[i]
                break

        if self._frequency != 0:
            self._time_period = float(1) / self._frequency

        else:
            self._time_period = float("inf")

    def set_type(self, typ):
        """
        Set the type number of the output waveform.

        ================================================================
        | TYPE_NO   |    TYPE         |    Built-in Constant Name      |
        ================================================================
        |   0       |    Sine         |    SignalGenerator.SIN         |
        |   1       |    Square       |    SignalGenerator.SQUARE      |
        |   2       |    Ramp         |    SignalGenerator.RAMP        |
        |   3       |    Triangular   |    SignalGenerator.TRIANGULAR  |
        |   4       |    Saw Tooth    |    SignalGenerator.SAWTOOTH    |
        |   5       |    TTL          |    SignalGenerator.TTL         |
        ================================================================

        It is recommended to use the Build-in Constants as inputs.
        """
        if typ in range(6):
            self._type = typ

        else:
            raise Exception(
                "ERROR: Invalid input. Please give a numerical value between 0 and 5 ( both inclusive ) ")

    def set_offset(self, offset):
        """
        Set a DC offset voltage for the output waveform
        Range of the acceptable offset value is [ -SignalGenerator.AMPL_MAX, SignalGenerator.AMPL_MIN ]
        """
        if type(offset) not in [float, int]:
            raise Exception(
                "ERROR: Offset can be a float ( or int value ) withing the specified range only.")

        if (offset > self.AMPL_MAX) or (offset < -self.AMPL_MAX):
            raise Exception(
                "ERROR: Invalid offset value. Specify offset within the range")

        self._offset = float(offset)

    def set_enable(self, enable):
        """
        Link the enable connector ( or Bus_1_bit ) with the SignalGenerator object's enable input.
        """

        with AutoUpdater._lock:
            if isinstance(enable, Bus):
                AutoUpdater.remove_link(self._enable)
                AutoUpdater.add_link(
                    enable,
                    self._enable)
            else:
                raise Exception(
                    "ERROR: Invalid Enable input. Enable must be a 1-bit Bus or a Connector.")

    def set_outputs(self, outputs):
        """
        Set the outputs to be linked with the outputs of the SignalGenerator
        """
        if not isinstance(outputs, Bus):
            raise Exception("ERROR: Invalid output Bus")

        if (outputs.width != self.outputs.width):
            raise Exception("ERROR: Output width mismatch.")

        with AutoUpdater._lock:
            AutoUpdater.remove_link(self.outputs)
            AutoUpdater.add_link(
                self.outputs,
                outputs)

    def set_modulation_type(self, mod_type):
        """
        Set the modulation type that must be applied to the generated output signal,
        which will act as a carrier signal
        """
        if mod_type not in [0, 1, 2]:
            raise Exception(
                "ERROR: Invalid input for modulation type. Allowed values are 0, 1 or 2")

        self._mod_type = mod_type

    def set_modulation_input(self, mod_input):
        """
        Link the mod_input Analog Bus of width 2, with the modulating input.
        """
        if (not isinstance(mod_input, Bus)) or (not mod_input.analog):
            raise Exception(
                "ERROR: Invalid modulation input. The modulation input must be 2 connector analog Bus.")

        if (mod_input.width != self.mod_ip.width):
            raise Exception("ERROR: The bus must be a 2 connector Bus.")

        with AutoUpdater._lock:
            AutoUpdater.remove_link(self.mod_ip)
            AutoUpdater.add_link(
                mod_input,
                self.mod_ip)

    def run(self):
        """
        The main run module which periodically updates the output.
        """

        cur_time_offset = time.time() % self._time_period
        old_time_offset = cur_time_offset - self._time_period

        while not self._exit:
            cur_time_offset = time.time() % self._time_period
            if abs(cur_time_offset - old_time_offset) >= self.SAMPLING_TIME_INTERVAL:
                # Update the time varying value of the output.

                # Getting the modulating input
                m_t = (float(self.mod_ip[0]) - float(self.mod_ip[1]))

                # If modulation is selected as FM
                if (self._mod_type == 2):
                    freq = self._frequency + m_t
                    if freq != 0:
                        time_p = 1 / freq

                    else:
                        time_p = float("inf")

                else:
                    freq = self._frequency
                    time_p = self._time_period

                # If sine wave
                if (self.type == 0):
                    voltage = math.sin(
                        2 * math.pi * freq * cur_time_offset) + 0.5

                # If square wave
                if (self.type == 1):
                    voltage = 1 if (
                        (cur_time_offset) < time_p /
                        float(2)) else 0

                # If Ramp
                if (self.type == 2):
                    voltage = cur_time_offset / time_p

                # If Sawtooth or triangular
                if (self.type == 3 or self.type == 4):
                    voltage = 2 * \
                        ((cur_time_offset / time_p) - ((cur_time_offset / time_p) + 0.5))

                # If triangular
                if (self.type == 3):
                    voltage = abs(voltage)

                # If Sawtooth
                if (self.type == 4):
                    voltage += 1

                if (self._mod_type == 1):
                    c_t = voltage

                    voltage = (1 + m_t) * c_t

                self.outputs.set_voltage_all(
                    (voltage * self._amplitude) + self._offset,
                    0)

                old_time_offset = cur_time_offset

                time.sleep(self.SAMPLING_TIME_INTERVAL)

    def kill(self):
        """ To terminate this thread """
        self._exit = True
