
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