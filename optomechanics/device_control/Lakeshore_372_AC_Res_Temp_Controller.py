
from .Device_Visa_Super import Device

# trigger_command = 'KRDG?4'
# TMC_value=float(instrument.query(trigger_command))
# trigger_command1 = 'KRDG?3'
# T1K_value=float(instrument.query(trigger_command1))

#: Module-level safety guard. While ``True`` every method that would send a
#: command to the instrument prints the command instead of transmitting it, so
#: the driver can be exercised with no hardware attached and no risk of
#: changing heater or setpoint state. Queries are never affected.
SAFE_MODE = False


class Temp_Controller(Device):
    """Docstring by Claude. Driver for the Lake Shore Model 372 AC resistance
    bridge and temperature controller.

    The Model 372 combines a low-excitation AC resistance bridge for
    thermometry with a closed-loop temperature controller, and is used here for
    dilution-refrigerator control. It has three control outputs:

    ============ ==================================================
    ``output``   meaning
    ============ ==================================================
    0            sample heater (1 W, closed-loop capable)
    1            warm-up heater (10 W)
    2            analog / still output
    ============ ==================================================

    and two kinds of input: the dedicated control input ``A``, and measurement
    channels ``1``-``16`` provided through a 3726 or 3708 scanner.

    Method naming follows the repository convention: ``Read...`` methods issue
    a query and return the instrument's response, ``Write...`` methods send a
    command through :meth:`safe_write`.

    References
    ----------
    Lake Shore Model 372 User's Manual, Rev. 2.1 (P/N 119-372, 19 Nov 2024).
    Remote command summary TABLE 6-6 (p.143); full command definitions in
    section 6.6.1 (pp.144-170). Each method below cites its manual page.
    """
    def __init__(self, *args, **kwargs):
        Device.__init__(self, *args, **kwargs, )

    # --- safety guard ---------------------------------------------------

    def safe_write(self, cmd):
        """Docstring by Claude. Send a command, unless safe mode is engaged.

        All ``Write...`` methods route through this rather than calling
        :meth:`write` directly, so that the module-level :data:`SAFE_MODE`
        flag can block every state-changing command in one place.

        Parameters
        ----------
        cmd : str
            The fully formatted SCPI command string, e.g. ``"SETP 0,0.1"``.

        Returns
        -------
        bool
            ``True`` if the command was actually transmitted, ``False`` if it
            was suppressed because :data:`SAFE_MODE` is ``True``.
        """
        if SAFE_MODE:
            print(f"[SAFE MODE] would send: {cmd}")
            return False
        print(f"[SEND] {cmd}")
        self.write(cmd)
        return True

    # --- reads ----------------------------------------------------------

    def ReadTemperature(self,channel):
        """Docstring by Claude. Read a channel's temperature in kelvin (``KRDG?``, p.160).

        The reading is the resistance converted to temperature through the
        curve assigned to the channel, so a channel with no curve selected
        returns a meaningless value. An invalid reading (temperature over- or
        under-range, or a sensor fault) is reported as ``0`` here and flagged
        by :meth:`ReadReadingStatus`.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, or ``1``-``16`` for a measurement
            channel. ``0`` returns all measurement channels, comma separated.

        Returns
        -------
        str
            Temperature in kelvin, in ``±nnn.nnnE±nn`` format.
        """
        return self.query(f"KRDG?{channel}")

    def ReadMCTemperature(self):
        """Docstring by Claude. Read the mixing-chamber temperature (channel 4).

        Convenience wrapper over :meth:`ReadTemperature` for the channel the
        mixing-chamber thermometer is wired to on this fridge.

        Returns
        -------
        str
            Mixing-chamber temperature in kelvin.
        """
        return self.ReadTemperature("4")

    def ReadExcitationPower(self, channel):
        """Docstring by Claude. Read the power dissipated in the sensor (``RDGPWR?``, p.166).

        Useful for checking that a thermometer is not being self-heated: the
        excitation must be low enough that the sensor stays in equilibrium
        with the stage it measures, which matters most at the lowest
        temperatures.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, or ``1``-``16`` for a measurement
            channel.

        Returns
        -------
        str
            Excitation power in watts, in ``±nnn.nnnE±nn`` format.
        """
        return self.query(f"RDGPWR?{channel}")

    def ReadResistance(self, channel):
        """Docstring by Claude. Read a channel's resistance in ohms (``RDGR?``, p.166).

        This is the real (in-phase) component of the AC measurement — the raw
        quantity the bridge measures, before any curve is applied. Compare
        with :meth:`ReadQuadrature` for the reactive component.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, or ``1``-``16`` for a measurement
            channel. ``0`` returns all measurement channels.

        Returns
        -------
        str
            Resistance in ohms, in ``±nnn.nnnE±nn`` format.
        """
        return self.query(f"RDGR?{channel}")

    def ReadInputSetup(self, channel):
        """Docstring by Claude. Read a channel's measurement setup (``INTYPE?``, pp.158-160).

        Returns the excitation and range configuration set by
        :meth:`WriteInputSetup`; see that method for the meaning of each
        field.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, or ``1``-``16`` for a measurement
            channel.

        Returns
        -------
        str
            ``<mode>,<excitation>,<autorange>,<range>,<cs shunt>,<units>``.
        """
        return self.query(f"INTYPE?{channel}")

    def ReadHeaterOutput(self, channel):
        """Docstring by Claude. Read the actual heater output (``HTR?``, p.155).

        Reports what the heater is really doing, whether it was commanded by
        the closed loop or set manually. The units depend on the heater's
        display-units setting (see :meth:`WriteHeaterSetup`): percent of full
        range, or power.

        Parameters
        ----------
        channel : int
            Output number: ``0`` sample heater, ``1`` warm-up heater.

        Returns
        -------
        str
            Heater output in ``±nnn.nnnE±nn`` format.
        """
        return self.query(f"HTR?{channel}")

    def ReadManualHeaterOutput(self, channel):
        """Docstring by Claude. Read the manual output setting (``MOUT?``, p.162).

        This is the *commanded* manual value, not the achieved output. In
        open-loop mode it is the whole output; in closed-loop mode it acts as
        a fixed offset added to the PID contribution.

        Parameters
        ----------
        channel : int
            Output number: ``0``, ``1`` or ``2``.

        Returns
        -------
        str
            Manual output value in ``±nnn.nnnE±nn`` format.
        """
        return self.query(f"MOUT?{channel}")

    def ReadHeaterRange(self, channel):
        """Docstring by Claude. Read the heater range (``RANGE?``, p.165).

        The range sets the maximum current the heater can draw, and so the
        coarse scale of available power; ``0`` means the heater is off. See
        :meth:`WriteHeaterRange` for the value table.

        Parameters
        ----------
        channel : int
            Output number: ``0``, ``1`` or ``2``.

        Returns
        -------
        str
            Heater range index.
        """
        return self.query(f"RANGE?{channel}")

    def ReadStillOutput(self, channel):
        """Docstring by Claude. Read the still-heater output level (``STILL?``, p.168).

        Applies to output 2 when it is configured as the still heater. The
        still heater controls the circulation rate of the dilution unit.

        Parameters
        ----------
        channel : int
            Output number (``2`` for the still).

        Returns
        -------
        str
            Still output as a percentage of full scale.
        """
        return self.query(f"STILL?{channel}")

    def ReadPID(self, channel):
        """Docstring by Claude. Read the closed-loop PID gains (``PID?``, p.164).

        Parameters
        ----------
        channel : int
            Output number: ``0`` sample heater or ``1`` warm-up heater.

        Returns
        -------
        str
            ``<P>,<I>,<D>`` — proportional gain, integral (s), derivative (s).
        """
        return self.query(f"PID?{channel}")

    def ReadSetpoint(self, output):
        """Docstring by Claude. Read the control setpoint (``SETP?``, p.168).

        The setpoint is expressed in whatever units the output's control loop
        is set to use — kelvin or ohms, per the ``<units>`` field of
        :meth:`WriteInputSetup` for the controlling input.

        Parameters
        ----------
        output : int
            Output number: ``0`` sample heater or ``1`` warm-up heater.

        Returns
        -------
        str
            Setpoint value in ``±nnn.nnnE±nn`` format.
        """
        return self.query(f"SETP?{output}")

    def ReadOutputMode(self, output):
        """Docstring by Claude. Read an output's control-mode setup (``OUTMODE?``, p.163).

        Returns the fields written by :meth:`WriteOutputMode`; see that method
        for their meaning.

        Parameters
        ----------
        output : int
            Output number: ``0``, ``1`` or ``2``.

        Returns
        -------
        str
            ``<mode>,<input>,<powerup enable>,<polarity>,<filter>,<delay>``.
        """
        return self.query(f"OUTMODE?{output}")

    # --- writes (all safe-mode protected) -------------------------------

    def WritePID(self, output, p, i, d):
        """Docstring by Claude. Set the closed-loop PID gains (``PID``, p.164).

        Only meaningful for an output in a closed-loop mode. Poorly chosen
        gains can make the loop oscillate and dump heat into the fridge, so
        change them deliberately.

        Parameters
        ----------
        output : int
            Output number: ``0`` sample heater or ``1`` warm-up heater.
        p : float
            Proportional gain (sometimes called gain), 0.0 to 1000.
        i : float
            Integral time in seconds (reset), 0 to 10000.
        d : float
            Derivative time in seconds (rate), 0 to 2500.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(f"PID {output},{p},{i},{d}")

    def WriteSetpoint(self, output, setpoint):
        """Docstring by Claude. Set the control setpoint (``SETP``, p.168).

        The value is interpreted in the control loop's units (kelvin or ohms).
        The instrument will drive the heater towards this value using the
        current PID gains and heater range; if the heater range is ``0`` the
        setpoint is stored but nothing happens.

        Parameters
        ----------
        output : int
            Output number: ``0`` sample heater or ``1`` warm-up heater.
        setpoint : float
            Target value, in the control loop's units.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(f"SETP {output},{setpoint}")

    def WriteHeaterRange(self, output, heater_range):
        """Docstring by Claude. Set the heater range (``RANGE``, p.165).

        This is the main power control: it selects the current range, and so
        caps the deliverable power. Setting ``0`` turns the heater off, which
        is the safe state.

        For the sample heater (output 0) the ranges are decade steps of
        current:

        ============ ==============
        ``range``    current
        ============ ==============
        0            off
        1            31.6 uA
        2            100 uA
        3            316 uA
        4            1.00 mA
        5            3.16 mA
        6            10.0 mA
        7            31.6 mA
        8            100 mA
        ============ ==============

        For the warm-up heater and analog output (outputs 1 and 2) the
        parameter is simply ``0`` = off, ``1`` = on.

        Parameters
        ----------
        output : int
            Output number: ``0``, ``1`` or ``2``.
        heater_range : int
            Range index, per the table above.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(f"RANGE {output},{heater_range}")

    def WriteManualOutput(self, output, percent):
        """Docstring by Claude. Set the manual output level (``MOUT``, p.162).

        In open-loop mode this directly sets the output. In closed-loop mode
        it is added to the PID contribution as a fixed offset, which is
        occasionally useful for biasing a loop but usually left at zero.

        Parameters
        ----------
        output : int
            Output number: ``0``, ``1`` or ``2``.
        percent : float
            Output level as a percentage of the current heater range.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(f"MOUT {output},{percent}")

    def WriteOutputMode(self, output, mode, input_channel, powerup_enable=0,
                        polarity=0, use_filter=0, delay=1):
        """Docstring by Claude. Configure an output's control mode (``OUTMODE``, p.163).

        Selects what the output does and which input drives it. This is what
        you use to put the sample heater into closed-loop PID control on a
        chosen thermometer, or to take it out of it.

        Parameters
        ----------
        output : int
            Output number: ``0``, ``1`` or ``2``.
        mode : int
            Control mode:

            ==== ==================================================
            0    off
            1    monitor out
            2    open loop (manual)
            3    zone
            4    still
            5    closed loop (PID)
            6    warm up
            ==== ==================================================
        input_channel : str or int
            Which input the loop controls on: ``A`` for the control input,
            ``1``-``16`` for a measurement channel, ``0`` for none.
        powerup_enable : int, optional
            ``0`` output stays off after a power cycle (default, and the safe
            choice), ``1`` output resumes automatically.
        polarity : int, optional
            ``0`` unipolar (default), ``1`` bipolar.
        use_filter : int, optional
            ``0`` unfiltered reading (default), ``1`` use the filtered reading
            for control. See :meth:`WriteFilter`.
        delay : int, optional
            Delay in seconds for the scanner channel to settle after a change,
            1 to 255. Default 1.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(
            f"OUTMODE {output},{mode},{input_channel},{powerup_enable},"
            f"{polarity},{use_filter},{delay}"
        )

    # --- readings and status --------------------------------------------

    def ReadQuadrature(self, channel):
        """Docstring by Claude. Read the quadrature (reactive) component (``QRDG?``, p.164).

        The bridge measures a complex impedance; :meth:`ReadResistance`
        returns the in-phase part and this returns the out-of-phase part. A
        quadrature reading that is large compared with the resistance
        indicates stray capacitance or inductance in the wiring, so this is
        primarily a diagnostic for cabling problems.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, or ``1``-``16`` for a measurement
            channel.

        Returns
        -------
        str
            Imaginary part of the reading in ohms, ``±nnn.nnnE±nn`` format.
        """
        return self.query(f"QRDG?{channel}")

    def ReadReadingStatus(self, channel):
        """Docstring by Claude. Read a channel's reading-status flags (``RDGST?``, p.166).

        Always worth checking before trusting a temperature: a channel that is
        over-range or open reports a number rather than an error. The return
        is a bit-weighted sum:

        ===== ==================================================
        bit   meaning
        ===== ==================================================
        1     CS OVL — current source overload
        2     VCM OVL — common-mode voltage overload
        4     VMIX OVL — mixer overload
        8     VDIF OVL — differential input overload
        16    R. OVER — resistance over range
        32    R. UNDER — resistance under range
        64    T. OVER — temperature over range
        128   T. UNDER — temperature under range
        ===== ==================================================

        A value of ``0`` means the reading is valid.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, or ``1``-``16`` for a measurement
            channel.

        Returns
        -------
        str
            Bit-weighted status value, ``0`` when the reading is good.
        """
        return self.query(f"RDGST?{channel}")

    def ReadSettleStatus(self):
        """Docstring by Claude. Read whether the reading has settled (``RDGSTL?``, p.167).

        After a range or channel change the measurement needs time to settle.
        This reports whether the current reading is considered settled, which
        is the right thing to poll before recording data following a change.

        Returns
        -------
        str
            ``0`` not settled, ``1`` settled.
        """
        return self.query("RDGSTL?")

    def ReadMinMax(self, channel):
        """Docstring by Claude. Read a channel's recorded minimum and maximum (``MDAT?``, p.161).

        The instrument continuously tracks the extreme readings seen on each
        channel since the last reset. Use :meth:`WriteMinMaxReset` to clear
        them, for example at the start of a stability measurement.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, or ``1``-``16`` for a measurement
            channel.

        Returns
        -------
        str
            ``<min>,<max>`` in the channel's preferred units.
        """
        return self.query(f"MDAT?{channel}")

    def WriteMinMaxReset(self):
        """Docstring by Claude. Clear the stored min/max data (``MNMXRST``, p.161).

        Resets the tracked extremes on every channel at once; there is no
        per-channel form. Takes no parameters.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write("MNMXRST")

    def ReadHeaterStatus(self, output):
        """Docstring by Claude. Read the heater error status (``HTRST?``, p.155).

        Reports whether the heater output has faulted. A non-zero value means
        the instrument has shut the heater down, and the fault must be cleared
        before it will drive again.

        Parameters
        ----------
        output : int
            Output number: ``0`` sample heater or ``1`` warm-up heater.

        Returns
        -------
        str
            ``0`` no error, ``1`` heater open circuit, ``2`` heater short.
        """
        return self.query(f"HTRST?{output}")

    def ReadAnalogOutput(self, output):
        """Docstring by Claude. Read the analog output level (``AOUT?``, p.149).

        Reports the percentage of full scale currently on the analog output
        (output 2), whatever is driving it — manual value, still setting, or
        a monitor-out source.

        Parameters
        ----------
        output : int
            Output number (``2`` for the analog output).

        Returns
        -------
        str
            Output level as a percentage of full scale.
        """
        return self.query(f"AOUT?{output}")

    # --- input configuration --------------------------------------------

    def ReadInputChannelParameter(self, channel):
        """Docstring by Claude. Read a channel's scanning parameters (``INSET?``, p.157).

        Returns the fields written by :meth:`WriteInputChannelParameter`,
        including the autoscan dwell time; see that method for their meaning.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, or ``1``-``16`` for a measurement
            channel.

        Returns
        -------
        str
            ``<enabled>,<dwell>,<pause>,<curve number>,<tempco>``.
        """
        return self.query(f"INSET?{channel}")

    def WriteInputChannelParameter(self, channel, enabled, dwell, pause,
                                   curve_number, tempco):
        """Docstring by Claude. Set a channel's scanning parameters (``INSET``, p.157).

        These are the per-thermometer settings that govern how the scanner
        treats the channel. The dwell time is how long the instrument sits on
        this channel during an autoscan, and the pause time is how long it
        waits after switching to it before believing the reading — both need
        to be long enough for the measurement to settle, which at millikelvin
        temperatures and high resistances can be many seconds.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, ``1``-``16`` for a measurement
            channel, or ``0`` to apply the settings to all measurement
            channels at once.
        enabled : int
            ``0`` channel disabled (skipped by autoscan), ``1`` enabled. At
            least one measurement channel must remain enabled; if all are
            disabled the instrument forces channel 1 back on.
        dwell : int
            Autoscan dwell time in seconds, 1 to 200. Not applicable to the
            control input ``A``.
        pause : int
            Change-pause time in seconds, 3 to 200.
        curve_number : int
            Curve used to convert resistance to temperature: ``0`` for none,
            or ``1``-``59`` for a standard or user curve.
        tempco : int
            Temperature coefficient used when no curve is selected, which
            tells the instrument which way resistance moves with temperature:
            ``1`` negative, ``2`` positive.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(
            f"INSET {channel},{enabled},{dwell},{pause},{curve_number},"
            f"{tempco}"
        )

    def WriteInputSetup(self, channel, mode, excitation, autorange,
                        resistance_range, cs_shunt, units):
        """Docstring by Claude. Set a channel's measurement setup (``INTYPE``, pp.158-160).

        Controls how hard the channel is driven and on what range. Excitation
        is the key thermometry trade-off: too much and the sensor self-heats
        away from the stage temperature, too little and the reading is noisy.
        See :meth:`ReadInputSetup` for the query form and
        :meth:`ReadExcitationPower` to check the resulting dissipation.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, ``1``-``16`` for a measurement
            channel, or ``0`` for all measurement channels.
        mode : int
            Excitation mode: ``0`` voltage excitation, ``1`` current
            excitation.
        excitation : int
            Excitation range index, ``1``-``22``. The meaning depends on
            ``mode``: for voltage excitation ``1`` = 2.00 uV up to ``22`` =
            632 mV, for current excitation ``1`` = 1.00 pA up to ``22`` =
            31.6 mA, in decade-and-a-half steps. See TABLE 6-8 in the manual
            for the full listing.
        autorange : int
            ``0`` off (fixed range), ``1`` autorange, ``2`` ROX 102B
            autorange.
        resistance_range : int
            Resistance range index, ``1`` = 2.00 mohm up to ``22`` = 63.2
            Mohm. Ignored when ``autorange`` is enabled.
        cs_shunt : int
            Current-source shunt: ``0`` current source not shunted (excitation
            on), ``1`` current source shunted (excitation off).
        units : int
            Preferred display and control units: ``1`` kelvin, ``2`` ohms.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(
            f"INTYPE {channel},{mode},{excitation},{autorange},"
            f"{resistance_range},{cs_shunt},{units}"
        )

    def ReadFilter(self, channel):
        """Docstring by Claude. Read a channel's filter settings (``FILTER?``, p.154).

        Returns the fields written by :meth:`WriteFilter`.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, or ``1``-``16`` for a measurement
            channel.

        Returns
        -------
        str
            ``<off/on>,<settle time>,<window>``.
        """
        return self.query(f"FILTER?{channel}")

    def WriteFilter(self, channel, state, settle_time, window):
        """Docstring by Claude. Configure a channel's reading filter (``FILTER``, p.154).

        The filter averages readings to reduce noise, at the cost of response
        time. The window is an escape hatch: a change larger than the window
        is treated as a real step rather than noise, and the filter restarts
        instead of slewing slowly to the new value.

        Note that filtering only affects control if the output is told to use
        the filtered reading — see the ``use_filter`` argument of
        :meth:`WriteOutputMode`.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, ``1``-``16`` for a measurement
            channel, or ``0`` for all measurement channels.
        state : int
            ``0`` filter off, ``1`` filter on.
        settle_time : int
            Filter settle time in seconds, 1 to 200.
        window : int
            Window as a percentage of full scale, 1 to 80. Readings that jump
            by more than this restart the filter.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(
            f"FILTER {channel},{state},{settle_time},{window}"
        )

    def ReadInputName(self, channel):
        """Docstring by Claude. Read a channel's user-assigned name (``INNAME?``, p.157).

        Parameters
        ----------
        channel : int
            Measurement channel, ``1``-``16``.

        Returns
        -------
        str
            The channel name.
        """
        return self.query(f"INNAME?{channel}")

    def WriteInputName(self, channel, name):
        """Docstring by Claude. Set a channel's name (``INNAME``, p.157).

        Naming channels after the stage they measure ("MC", "Still", "50K")
        makes the front panel and logs readable. The name is quoted when sent,
        so spaces and commas are safe.

        Parameters
        ----------
        channel : int
            Measurement channel, ``1``-``16``.
        name : str
            Name to assign, up to 15 characters.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(f'INNAME {channel},"{name}"')

    def ReadInputCurveNumber(self, channel):
        """Docstring by Claude. Read a channel's curve number (``INCRV?``, p.156).

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, or ``1``-``16`` for a measurement
            channel.

        Returns
        -------
        str
            Curve number, ``0`` if no curve is assigned.
        """
        return self.query(f"INCRV?{channel}")

    def WriteInputCurveNumber(self, channel, curve_number):
        """Docstring by Claude. Assign a calibration curve to a channel (``INCRV``, p.156).

        The curve is what turns measured resistance into temperature, so a
        channel with no curve can only report ohms. The curve's format must
        match the sensor type on the channel, or the instrument rejects the
        assignment.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, or ``1``-``16`` for a measurement
            channel.
        curve_number : int
            ``0`` for no curve, ``1``-``59`` for a standard or user curve.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(f"INCRV {channel},{curve_number}")

    def ReadTemperatureLimit(self, channel):
        """Docstring by Claude. Read a channel's temperature limit (``TLIMIT?``, pp.168-169).

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, or ``1``-``16`` for a measurement
            channel.

        Returns
        -------
        str
            Limit in kelvin; ``0`` means no limit is set.
        """
        return self.query(f"TLIMIT?{channel}")

    def WriteTemperatureLimit(self, channel, limit):
        """Docstring by Claude. Set a channel's temperature limit (``TLIMIT``, pp.168-169).

        A protective interlock: if the channel reads above this temperature
        the instrument turns all heater outputs off. Setting a limit on the
        mixing-chamber or still thermometer guards against a runaway loop
        heating the fridge, so it is worth configuring before enabling
        closed-loop control.

        Parameters
        ----------
        channel : str or int
            ``A`` for the control input, or ``1``-``16`` for a measurement
            channel.
        limit : float
            Limit in kelvin. ``0`` disables the limit.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(f"TLIMIT {channel},{limit}")

    def ReadExcitationFrequency(self, channel):
        """Docstring by Claude. Read the excitation frequency (``FREQ?``, p.154).

        Parameters
        ----------
        channel : str or int
            ``0`` for the measurement inputs, ``A`` for the control input.

        Returns
        -------
        str
            Frequency index: ``1`` = 9.8 Hz, ``2`` = 13.7 Hz, ``3`` = 18.2 Hz.
        """
        return self.query(f"FREQ?{channel}")

    def WriteExcitationFrequency(self, channel, frequency):
        """Docstring by Claude. Set the AC excitation frequency (``FREQ``, p.154).

        The bridge measures with an AC excitation, and the frequency is chosen
        to avoid line pickup and to suit the sensor's cabling. Higher
        frequencies settle faster but are more affected by cable capacitance.
        The setting applies to a whole input group, not to individual
        measurement channels.

        Parameters
        ----------
        channel : str or int
            ``0`` for the measurement inputs, ``A`` for the control input.
        frequency : int
            ``1`` = 9.8 Hz, ``2`` = 13.7 Hz, ``3`` = 18.2 Hz.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(f"FREQ {channel},{frequency}")

    def ReadCommonModeReduction(self):
        """Docstring by Claude. Read the common-mode reduction state (``CMR?``, p.150).

        Returns
        -------
        str
            ``0`` off, ``1`` on.
        """
        return self.query("CMR?")

    def WriteCommonModeReduction(self, state):
        """Docstring by Claude. Enable or disable common-mode reduction (``CMR``, p.150).

        Common-mode reduction suppresses the common-mode voltage on the input,
        which is what causes VCM overloads on long or noisy fridge wiring. If
        :meth:`ReadReadingStatus` is reporting VCM OVL, turning this on is the
        first thing to try.

        Parameters
        ----------
        state : int
            ``0`` off, ``1`` on.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(f"CMR {state}")

    # --- outputs and control --------------------------------------------

    def ReadHeaterSetup(self, output):
        """Docstring by Claude. Read a heater's setup (``HTRSET?``, p.155).

        Returns the fields written by :meth:`WriteHeaterSetup`.

        Parameters
        ----------
        output : int
            Output number: ``0`` sample heater or ``1`` warm-up heater.

        Returns
        -------
        str
            ``<resistance>,<max current>,<max user current>,<current/power>``.
        """
        return self.query(f"HTRSET?{output}")

    def WriteHeaterSetup(self, output, resistance, max_current,
                         max_user_current, display):
        """Docstring by Claude. Configure a heater output (``HTRSET``, p.155).

        Tells the instrument what is physically wired to the output, so it can
        convert between current and power correctly and refuse to exceed the
        heater's rating. The maximum current is a hardware protection setting:
        get it wrong in the permissive direction and the heater can be
        overdriven, so it should match the actual resistor.

        Parameters
        ----------
        output : int
            Output number: ``0`` sample heater or ``1`` warm-up heater.
        resistance : float
            Heater resistance in ohms, 1 to 2000.
        max_current : int
            Maximum current selection: ``0`` user-specified (use
            ``max_user_current``), ``1`` 0.45 A, ``2`` 0.63 A, ``3`` 0.89 A,
            ``4`` 1.12 A.
        max_user_current : float
            User-specified maximum current in amps, up to 1.732 A. Only used
            when ``max_current`` is ``0``.
        display : int
            Units the heater output is displayed and commanded in: ``1``
            current, ``2`` power.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(
            f"HTRSET {output},{resistance},{max_current},"
            f"{max_user_current},{display}"
        )

    def ReadRamp(self, output):
        """Docstring by Claude. Read the setpoint ramp settings (``RAMP?``, p.165).

        Parameters
        ----------
        output : int
            Output number: ``0`` sample heater or ``1`` warm-up heater.

        Returns
        -------
        str
            ``<off/on>,<rate value>``.
        """
        return self.query(f"RAMP?{output}")

    def WriteRamp(self, output, state, rate):
        """Docstring by Claude. Configure setpoint ramping (``RAMP``, p.165).

        With ramping on, a new setpoint is approached at a controlled rate
        rather than stepped to immediately. This is gentler on the fridge: a
        step change asks the loop for maximum heater output at once, whereas a
        ramp keeps the heat load predictable.

        Parameters
        ----------
        output : int
            Output number: ``0`` sample heater or ``1`` warm-up heater.
        state : int
            ``0`` ramping off, ``1`` ramping on.
        rate : float
            Ramp rate in kelvin per minute, 0.001 to 10.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(f"RAMP {output},{state},{rate}")

    def ReadRampStatus(self, output):
        """Docstring by Claude. Read whether a setpoint ramp is in progress (``RAMPST?``, p.165).

        Poll this to know when the instrument has finished ramping and the
        setpoint has actually reached its target value.

        Parameters
        ----------
        output : int
            Output number: ``0`` sample heater or ``1`` warm-up heater.

        Returns
        -------
        str
            ``0`` ramp complete (or not ramping), ``1`` currently ramping.
        """
        return self.query(f"RAMPST?{output}")

    def WriteStillOutput(self, output, level):
        """Docstring by Claude. Set the still-heater output level (``STILL``, p.168).

        Applies when output 2 is configured in still mode (see
        :meth:`WriteOutputMode`). The still heater sets the circulation rate
        of the dilution unit, and so indirectly the base temperature.

        Parameters
        ----------
        output : int
            Output number (``2`` for the still).
        level : float
            Output level as a percentage of full scale, 0 to 100.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(f"STILL {output},{level}")

    def ReadAnalogOutputParameter(self, output):
        """Docstring by Claude. Read the analog output configuration (``ANALOG?``, pp.148-149).

        Returns the fields written by :meth:`WriteAnalogOutputParameter`.

        Parameters
        ----------
        output : int
            Output number (``2`` for the analog output).

        Returns
        -------
        str
            ``<polarity>,<mode>,<input>,<source>,<high>,<low>,<manual>``.
        """
        return self.query(f"ANALOG?{output}")

    def WriteAnalogOutputParameter(self, output, polarity, mode,
                                   input_channel, source, high_value,
                                   low_value, manual_value):
        """Docstring by Claude. Configure the analog output (``ANALOG``, pp.148-149).

        Used when the analog output is driven as a monitor: it emits a voltage
        proportional to a chosen reading, scaled so that ``low_value`` maps to
        the bottom of the output range and ``high_value`` to the top. That
        voltage can then be logged by an external DAQ.

        Parameters
        ----------
        output : int
            Output number (``2`` for the analog output).
        polarity : int
            ``0`` unipolar, ``1`` bipolar.
        mode : int
            ``0`` off, ``1`` monitor out, ``2`` open loop, ``4`` still,
            ``5`` closed loop, ``6`` warm up.
        input_channel : str or int
            Input the monitor tracks: ``A`` or ``1``-``16``, ``0`` for none.
        source : int
            Quantity monitored: ``1`` kelvin, ``2`` ohms, ``3`` linear data.
        high_value : float
            Reading corresponding to +100% output.
        low_value : float
            Reading corresponding to 0% (unipolar) or -100% (bipolar) output.
        manual_value : float
            Output level used in manual mode, as a percentage.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(
            f"ANALOG {output},{polarity},{mode},{input_channel},{source},"
            f"{high_value},{low_value},{manual_value}"
        )

    def ReadWarmupMode(self, output):
        """Docstring by Claude. Read the warm-up heater mode (``WARMUP?``, p.169).

        Parameters
        ----------
        output : int
            Output number (``1`` for the warm-up heater).

        Returns
        -------
        str
            ``<mode>,<percentage>``.
        """
        return self.query(f"WARMUP?{output}")

    def WriteWarmupMode(self, output, mode, percentage):
        """Docstring by Claude. Configure the warm-up heater (``WARMUP``, p.169).

        The warm-up heater is the high-power output used to bring the fridge
        back to room temperature. In auto mode the instrument ramps the output
        itself; in continuous mode it holds the given level until told
        otherwise.

        Parameters
        ----------
        output : int
            Output number (``1`` for the warm-up heater).
        mode : int
            ``0`` auto off, ``1`` continuous.
        percentage : float
            Output level as a percentage of full scale, 0 to 100.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(f"WARMUP {output},{mode},{percentage}")

    def ReadZone(self, output, zone):
        """Docstring by Claude. Read one zone's control parameters (``ZONE?``, p.170).

        Parameters
        ----------
        output : int
            Output number: ``0`` sample heater or ``1`` warm-up heater.
        zone : int
            Zone number, ``1``-``10``.

        Returns
        -------
        str
            ``<upper bound>,<P>,<I>,<D>,<mout>,<range>,<rate>,<relay 1>,
            <relay 2>``.
        """
        return self.query(f"ZONE?{output},{zone}")

    def WriteZone(self, output, zone, upper_bound, p, i, d, manual_output,
                  heater_range, ramp_rate, relay_1=0, relay_2=0):
        """Docstring by Claude. Define one zone's control parameters (``ZONE``, p.170).

        Zone mode lets the instrument switch PID gains and heater range
        automatically as the temperature changes, which matters on a dilution
        fridge because gains that are stable at base are wrong at a few
        kelvin. Each zone applies from the previous zone's upper bound up to
        its own, and zones must be entered in ascending order of
        ``upper_bound``. Zone mode is selected with ``mode=3`` in
        :meth:`WriteOutputMode`.

        Parameters
        ----------
        output : int
            Output number: ``0`` sample heater or ``1`` warm-up heater.
        zone : int
            Zone number, ``1``-``10``.
        upper_bound : float
            Upper setpoint boundary of this zone, in kelvin.
        p : float
            Proportional gain for the zone, 0.0 to 1000.
        i : float
            Integral time in seconds, 0 to 10000.
        d : float
            Derivative time in seconds, 0 to 2500.
        manual_output : float
            Manual output offset for the zone, as a percentage.
        heater_range : int
            Heater range used in the zone; see :meth:`WriteHeaterRange`.
        ramp_rate : float
            Setpoint ramp rate in kelvin per minute, 0.001 to 10.
        relay_1 : int, optional
            ``0`` off, ``1`` on. Default 0.
        relay_2 : int, optional
            ``0`` off, ``1`` on. Default 0.

        Returns
        -------
        bool
            ``True`` if sent, ``False`` if suppressed by :data:`SAFE_MODE`.
        """
        return self.safe_write(
            f"ZONE {output},{zone},{upper_bound},{p},{i},{d},"
            f"{manual_output},{heater_range},{ramp_rate},{relay_1},{relay_2}"
        )