"""
Zurich Instruments HF2LI lock-in amplifier control.

Provides convenience methods for common HF2LI operations: input/output
configuration, demodulator setup, and frequency sweeps. The raw
``self.device`` (zhinst.toolkit device object) is always available for
direct access to the full API.
"""

import math
import time
from .Device_Zurich_Super import ZurichDevice
from .zurich_data_management import save_sweep_to_hdf5, save_spectrum_to_hdf5, _maybe_prepend_datetime
from matplotlib import pyplot as plt


# ---------------------------------------------------------------------------
# Window name → LabOne DAQ module integer code
# ---------------------------------------------------------------------------
_DAQ_WINDOW = {
    'rectangular': 0, 'boxcar': 0,
    'hann': 1, 'hanning': 1,
    'hamming': 2,
    'blackman': 3,
    'exponential': 4,
    'cosine': 5,
    'cosine2': 6,
}


def bandwidth_to_tc(f3db_hz, order):
    """Convert 3 dB bandwidth to time constant for an n-th order Butterworth LP cascade.

    The HF2LI demodulator filter is a cascade of *n* identical 1st-order
    Butterworth stages.  The composite -3 dB frequency relates to the
    per-stage corner frequency f_c = 1 / (2π × TC) by:

        f_3dB = f_c × √(2^(1/n) − 1)

    Rearranging gives the time constant:

        TC = √(2^(1/n) − 1) / (2π × f_3dB)

    Correction factor k = √(2^(1/n) − 1) by order:

    ======  ======  =======================
    order   k       TC for 500 Hz 3dB BW
    ======  ======  =======================
    1       1.0000  318.1 µs  (device-confirmed)
    2       0.6436  204.8 µs
    4       0.4349  138.4 µs  (device-confirmed)
    8       0.3008   95.7 µs
    ======  ======  =======================

    Parameters
    ----------
    f3db_hz : float
        Desired 3 dB bandwidth in Hz.
    order : int
        Demodulator low-pass filter order (1–8).

    Returns
    -------
    float
        Time constant in seconds.
    """
    k = math.sqrt(2 ** (1 / order) - 1)
    return k / (2 * math.pi * f3db_hz)


def tc_to_bandwidth(tc_s, order):
    """Convert time constant to 3 dB bandwidth (inverse of :func:`bandwidth_to_tc`).

    Parameters
    ----------
    tc_s : float
        Filter time constant in seconds.
    order : int
        Demodulator low-pass filter order (1–8).

    Returns
    -------
    float
        3 dB bandwidth in Hz.
    """
    k = math.sqrt(2 ** (1 / order) - 1)
    return k / (2 * math.pi * tc_s)


class HF2LI(ZurichDevice):
    """
    HF2LI dual lock-in amplifier.

    Parameters
    ----------
    device_id : str, optional
        Device serial. Default is ``'dev1374'``.
    server_host : str, optional
        LabOne Data Server hostname. Default is ``'localhost'``.
    port : int, optional
        HF2 Data Server port. Default is 8005.
    """

    def __init__(self, device_id="dev1374", server_host="localhost", port=8005):
        super().__init__(device_id, server_host, port)

    # ------------------------------------------------------------------
    # Verification helper
    # ------------------------------------------------------------------

    def _range_reader(self, channel):
        """Return a callable that reads ``sigouts/<channel>/range`` as a double.

        zhinst-toolkit treats the HF2 range node as an integer, so reading it
        via ``self.device.sigouts[ch].range()`` truncates 0.01 and 0.1 to 0.
        """
        path = f"/{self.device_id}/sigouts/{channel}/range"
        return lambda: self.session.daq_server.getDouble(path)

    @staticmethod
    def _verify_node(node, expected, label, rtol=0.01):
        """Read back a device node and raise if it doesn't match *expected*.

        Uses a 1 % relative tolerance for all comparisons.  On the first
        failure the method waits 0.5 s and retries once before raising.

        Parameters
        ----------
        node : callable
            Zurich node accessor — call with no args to read.
        expected : int or float
            The value that was just written.
        label : str
            Human-readable name used in the error message.
        rtol : float
            Relative tolerance (default 1 %).

        Returns
        -------
        actual : int or float
            The value read back from the device.
        """
        expected = float(expected)
        def _check(actual, expected, rtol):
            if expected == 0:
                return actual == 0
            return abs(actual - expected) <= rtol * abs(expected)

        actual = float(node())
        if _check(actual, expected, rtol):
            return actual

        # Retry once after settling
        for i in range (50):
            plt.pause(0.1)
            actual = float(node())
            if _check(actual, expected, rtol):
                return actual

        raise RuntimeError(
            f"Verify failed for {label}: wrote {expected}, read back {actual}"
        )

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    def configure_output(self, channel, amplitude, enable=True, osc_index=0, osc_enable=True,
                         range_v=None, offset=None):
        """
        Configure a signal output channel.

        Parameters
        ----------
        channel : int
            Output channel index (0 or 1).
        amplitude : float
            Output amplitude in volts.
        enable : bool, optional
            Enable the output. Default is True.
        osc_index : int, optional
            Oscillator index whose amplitude to set (0 or 1). Default is 0.
        osc_enable : bool, optional
            Enable routing of the oscillator signal to the output. Default is True.
        range_v : float or None, optional
            Output voltage range in volts. Sets the DAC headroom and resolution.
            If None, left unchanged. Default is None.
        offset : float or None, optional
            DC offset in volts. If None, left unchanged. Default is None.
        """
        # Set range first so the fractional amplitude is applied to the new range
        if range_v is not None:
            with self.device.set_transaction():
                self.device.sigouts[channel].range(range_v)
            self._verify_node(self._range_reader(channel), range_v,
                              f'sigouts/{channel}/range')

        amps = self.device.sigouts[channel].amplitudes
        amp_indices = sorted([int(k) for k in dir(amps) if k.isdigit()])
        device_amp_index = amp_indices[osc_index]

        with self.device.set_transaction():
            self.device.sigouts[channel].on(int(enable))
            if offset is not None:
                self.device.sigouts[channel].offset(offset)
            amps[device_amp_index](amplitude)
            self.device.sigouts[channel].enables[device_amp_index](int(osc_enable))

        # Read-back verification
        self._verify_node(self.device.sigouts[channel].on, int(enable),
                          f'sigouts/{channel}/on')
        if offset is not None:
            self._verify_node(self.device.sigouts[channel].offset, offset,
                              f'sigouts/{channel}/offset')
        self._verify_node(amps[device_amp_index], amplitude,
                          f'sigouts/{channel}/amplitudes/{device_amp_index}')
        self._verify_node(self.device.sigouts[channel].enables[device_amp_index],
                          int(osc_enable),
                          f'sigouts/{channel}/enables/{device_amp_index}')

    def configure_input(self, channel, input_range=1.0, impedance_50ohm=False, ac_coupling=False):
        """
        Configure a signal input channel.

        Parameters
        ----------
        channel : int
            Input channel index (0 or 1).
        input_range : float, optional
            Input range in volts. Default is 1.0.
        impedance_50ohm : bool, optional
            Use 50 Ohm input impedance. Default is False (1 MOhm).
        ac_coupling : bool, optional
            Enable AC coupling. Default is False (DC).
        """
        with self.device.set_transaction():
            self.device.sigins[channel].range(input_range)
            self.device.sigins[channel].imp50(int(impedance_50ohm))
            self.device.sigins[channel].ac(int(ac_coupling))

        # Read-back verification
        self._verify_node(self.device.sigins[channel].range, input_range,
                          f'sigins/{channel}/range')
        self._verify_node(self.device.sigins[channel].imp50, int(impedance_50ohm),
                          f'sigins/{channel}/imp50')
        self._verify_node(self.device.sigins[channel].ac, int(ac_coupling),
                          f'sigins/{channel}/ac')

    def configure_demodulator(self, index, oscselect=0, harmonic=1, rate=1000,
                              order=4, timeconstant=None):
        """
        Configure a demodulator channel.

        Parameters
        ----------
        index : int
            Demodulator index (0–5 on HF2LI).
        oscselect : int, optional
            Oscillator to use (0 or 1). Default is 0.
        harmonic : int, optional
            Harmonic of the reference frequency. Default is 1.
        rate : float, optional
            Data transfer rate in Sa/s. Default is 1000.
        order : int, optional
            Low-pass filter order (1–8). Default is 4.
        timeconstant : float or None, optional
            Filter time constant in seconds. If None, left unchanged.
        """
        with self.device.set_transaction():
            self.device.demods[index].enable(1)
            self.device.demods[index].oscselect(oscselect)
            self.device.demods[index].harmonic(harmonic)
            self.device.demods[index].rate(rate)
            self.device.demods[index].order(order)
            if timeconstant is not None:
                self.device.demods[index].timeconstant(timeconstant)

        # Read-back verification
        self._verify_node(self.device.demods[index].enable, 1,
                          f'demods/{index}/enable')
        self._verify_node(self.device.demods[index].oscselect, oscselect,
                          f'demods/{index}/oscselect')
        self._verify_node(self.device.demods[index].harmonic, harmonic,
                          f'demods/{index}/harmonic')
        self._verify_node(self.device.demods[index].rate, float(rate),
                          f'demods/{index}/rate')
        self._verify_node(self.device.demods[index].order, order,
                          f'demods/{index}/order')
        if timeconstant is not None:
            self._verify_node(self.device.demods[index].timeconstant, timeconstant,
                              f'demods/{index}/timeconstant')

    def set_oscillator_frequency(self, oscillator, frequency):
        """
        Set the frequency of an oscillator.

        Parameters
        ----------
        oscillator : int
            Oscillator index (0 or 1).
        frequency : float
            Frequency in Hz.
        """
        self.device.oscs[oscillator].freq(frequency)
        self._verify_node(self.device.oscs[oscillator].freq, frequency,
                          f'oscs/{oscillator}/freq')

    # ------------------------------------------------------------------
    # Sweep
    # ------------------------------------------------------------------

    def sweep(self, start, stop, num_points, demod_index=0, settling_time=None,
              settling_inaccuracy=None, averaging_samples=1, bandwidth_control=1,
              bandwidth_hz=None, filter_order=None, log_sweep=True, timeout=60,
              progress=False, progress_interval=60, progress_callback=None,
              output_channel=None, output_amplitude=None, output_enable=None,
              output_osc_index=0, output_osc_enable=None, output_range=None,
              save=False, filepath=None, metadata=None,
              group_index=0, append=False, prepend_datetime=True):
        """
        Run a frequency sweep and return the results.

        Uses the LabOne Sweeper module to sweep the oscillator frequency
        linked to the chosen demodulator.

        Parameters
        ----------
        start : float
            Start frequency in Hz.
        stop : float
            Stop frequency in Hz.
        num_points : int
            Number of frequency points.
        demod_index : int, optional
            Demodulator index to read during the sweep. Default is 0.
        settling_time : float or None, optional
            Minimum settling time per point in seconds. If None, uses device default.
        settling_inaccuracy : float or None, optional
            Settling inaccuracy (0–1). If None, uses device default.
        averaging_samples : int, optional
            Number of samples to average per point. Default is 1.
        bandwidth_control : int, optional
            Bandwidth control mode (0=manual, 1=fixed, 2=auto). Default is 1.
        bandwidth_hz : float or None, optional
            Demodulator bandwidth in Hz. Used when ``bandwidth_control=0`` (manual).
            If None, left unchanged.
        filter_order : int or None, optional
            Demodulator low-pass filter order (1–8). If None, left unchanged.
        log_sweep : bool, optional
            Logarithmic frequency spacing. Default is True.
        timeout : float, optional
            Maximum time to wait for sweep completion in seconds. Default is 60.
        progress : bool, optional
            If True, print progress updates while the sweep runs. Default is False.
        progress_interval : float, optional
            Time between progress updates in seconds. Default is 60.
        progress_callback : callable or None, optional
            Called at each progress checkpoint with partial sweep data (same
            dict structure as the final result), or None if no data has been
            collected yet at that checkpoint. Only active when progress=True.
            Default is None.
        output_channel : int or None, optional
            Output channel index (0 or 1) to configure before the sweep.
            If None, the output is not touched. Default is None.
        output_amplitude : float or None, optional
            Output amplitude in volts (absolute). When ``output_range`` is
            also provided, this is converted to a fractional amplitude
            (``output_amplitude / output_range``) before being written to the
            device, since the hardware expects a fraction of the output range.
            Applied when ``output_channel`` is set.
            If None, the amplitude is left unchanged. Default is None.
        output_range : float or None, optional
            Output voltage range in volts (0.01, 0.1, 1, or 10). Sets the
            DAC headroom via ``sigouts/n/range``. If None, left unchanged.
            Default is None.
        output_enable : bool or None, optional
            Enable (True) or disable (False) the output before the sweep.
            Applied when ``output_channel`` is set. If None, left unchanged.
            Default is None.
        output_osc_index : int, optional
            Oscillator index whose amplitude to set on the output channel (0 or 1).
            Default is 0, matching the sweep's oscillator (``oscs[0]``).
        output_osc_enable : bool or None, optional
            Enable (True) or disable (False) routing of the oscillator signal to
            the output channel. If None, the enables node is left unchanged.
            Default is None.
        save : bool, optional
            If True, save the result to an HDF5 file after the sweep. Requires
            ``filepath`` to be set. Default is False.
        filepath : str or None, optional
            Destination HDF5 file path. Required when ``save=True``.
        metadata : dict or None, optional
            Extra attributes to store in the HDF5 file (e.g. sample name,
            temperature). Passed directly to ``save_sweep_to_hdf5``.
        prepend_datetime : bool, optional
            If True, prepend the current date and time to the filename in
            the format ``YYYY-MM-DD_HH_MM_SS_``.  Default is True.

        Returns
        -------
        dict
            Keys: ``'frequency'``, ``'r'``, ``'phase'``, ``'x'``, ``'y'``
            — each a 1-D numpy array.

        Raises
        ------
        ValueError
            If ``save=True`` but ``filepath`` is None.
        """
        if save and filepath is None:
            raise ValueError("filepath must be set when save=True")
        if save and filepath is not None:
            import os
            _, ext = os.path.splitext(filepath)
            if ext == "":
                filepath = filepath + ".h5"
            elif ext != ".h5":
                raise ValueError(f"Invalid file suffix '{ext}'. Use '.h5' or provide a path with no suffix.")

        if output_channel is not None:
            # Set range first so the fractional amplitude is applied to the new range
            if output_range is not None:
                with self.device.set_transaction():
                    self.device.sigouts[output_channel].range(output_range)
                output_range = self._verify_node(
                    self._range_reader(output_channel), output_range,
                    f'sigouts/{output_channel}/range')

            with self.device.set_transaction():
                if output_enable is not None:
                    self.device.sigouts[output_channel].on(int(output_enable))
                if output_amplitude is not None or output_osc_enable is not None:
                    amps = self.device.sigouts[output_channel].amplitudes
                    amp_indices = sorted([int(k) for k in dir(amps) if k.isdigit()])
                    device_amp_index = amp_indices[output_osc_index]
                    if output_amplitude is not None:
                        frac = output_amplitude / output_range if output_range is not None else output_amplitude
                        amps[device_amp_index](frac)
                    if output_osc_enable is not None:
                        self.device.sigouts[output_channel].enables[device_amp_index](int(output_osc_enable))

            # Read-back verification — device values override requested values
            if output_enable is not None:
                self._verify_node(self.device.sigouts[output_channel].on, int(output_enable),
                                  f'sigouts/{output_channel}/on')
            if output_amplitude is not None:
                actual_frac = self._verify_node(
                    amps[device_amp_index], frac,
                    f'sigouts/{output_channel}/amplitudes/{device_amp_index}')
                output_amplitude = actual_frac * output_range if output_range is not None else actual_frac
            if output_osc_enable is not None:
                self._verify_node(
                    self.device.sigouts[output_channel].enables[device_amp_index],
                    int(output_osc_enable),
                    f'sigouts/{output_channel}/enables/{device_amp_index}')

        sweeper = self.session.modules.sweeper
        sweeper.device(self.device)

        sweeper.gridnode(self.device.oscs[output_osc_index].freq)
        sweeper.start(start)
        sweeper.stop(stop)
        sweeper.samplecount(num_points)
        sweeper.xmapping(1 if log_sweep else 0)
        sweeper.bandwidthcontrol(bandwidth_control)
        sweeper.averaging.sample(averaging_samples)

        if settling_time is not None:
            sweeper.settling.time(settling_time)
        if settling_inaccuracy is not None:
            sweeper.settling.inaccuracy(settling_inaccuracy)
        if bandwidth_hz is not None:
            sweeper.bandwidth(bandwidth_hz)
        if filter_order is not None:
            self.device.demods[demod_index].order(filter_order)

        sample_node = self.device.demods[demod_index].sample
        sweeper.subscribe(sample_node)

        sweeper.execute()

        _last_read = None
        _quiet = progress_callback is not None
        try:
            if progress:
                if not _quiet:
                    if settling_time is not None:
                        estimated_s = num_points * settling_time
                        print(f"Estimated sweep time: {estimated_s:.1f} s")
                    else:
                        print("Estimated sweep time: unknown (no settling_time set)")
                if progress_callback is not None:
                    try:
                        from matplotlib.pyplot import pause as _pause
                    except ImportError:
                        _pause = None
                else:
                    _pause = None
                t_start = time.time()
                while float(sweeper.progress()) < 1.0:
                    if _pause is not None:
                        _pause(progress_interval)
                    else:
                        time.sleep(progress_interval)
                    elapsed = time.time() - t_start
                    if ((timeout != None) & (elapsed > timeout)):
                        raise TimeoutError(f"Sweep timed out after {timeout:.0f} s")
                    pct = float(sweeper.progress()) * 100
                    if not _quiet:
                        if pct > 0:
                            remaining = (elapsed / (pct / 100)) - elapsed
                            print(f"Progress: {pct:.1f}%  |  Elapsed: {elapsed:.0f} s  |  Est. remaining: {remaining:.0f} s")
                        else:
                            print(f"Progress: {pct:.1f}%  |  Elapsed: {elapsed:.0f} s")
                    if progress_callback is not None:
                        try:
                            partial_raw = sweeper.read()
                            partial_data = partial_raw[sample_node]
                            if partial_data and len(partial_data[-1]) > 0:
                                _last_read = partial_data[-1][0]
                                progress_callback(_last_read)
                            else:
                                progress_callback(None)
                        except KeyError:
                            progress_callback(None)
                if not _quiet:
                    print(f"Sweep complete in {time.time() - t_start:.1f} s")
            else:
                sweeper.wait_done(timeout=timeout)

            result = sweeper.read()
        except BaseException:
            sweeper.finish()
            raise
        finally:
            sweeper.unsubscribe(sample_node)

        try:
            data = result[sample_node]
            if len(data) == 0:
                raise KeyError
            # The sweeper can return multiple result chunks; take the last one.
            # Each chunk is a list with a single structured array at index 0.
            output = data[-1][0]
        except KeyError:
            # Mid-sweep reads consumed the buffer; fall back to last partial result
            if _last_read is None:
                raise RuntimeError("Sweep returned no data")
            output = _last_read

        # Turn off the output after the sweep
        if output_channel is not None:
            self.device.sigouts[output_channel].on(0)

        if save:
            sweep_params = {
                'start_freq_hz':       start,
                'stop_freq_hz':        stop,
                'num_points':          num_points,
                'demod_index':         demod_index,
                'settling_time_s':     settling_time,
                'settling_inaccuracy': settling_inaccuracy,
                'averaging_samples':   averaging_samples,
                'bandwidth_control':   bandwidth_control,
                'bandwidth_hz':        bandwidth_hz,
                'filter_order':        filter_order,
                'log_sweep':           log_sweep,
                'output_channel':      output_channel,
                'output_amplitude':    output_amplitude,
                'output_enable':       output_enable,
                'output_osc_index':    output_osc_index,
                'output_range':        output_range,
                'output_osc_enable':   output_osc_enable,
            }
            if append and getattr(self, '_last_sweep_filepath', None):
                resolved_filepath = self._last_sweep_filepath
            else:
                resolved_filepath = _maybe_prepend_datetime(filepath, prepend_datetime)
                self._last_sweep_filepath = resolved_filepath
            save_sweep_to_hdf5(
                resolved_filepath, output,
                device_id=self.device_id,
                demod_index=demod_index,
                metadata=metadata,
                sweep_params=sweep_params,
                group_index=group_index,
                append=append,
                prepend_datetime=False,
            )

        return output

    # ------------------------------------------------------------------
    # Time-domain IQ acquisition
    # ------------------------------------------------------------------

    def acquire_iq(self, center_freq, span, fft_length, num_segments=None,
                   acquire_time=None, demod_index=0, osc_index=0, filter_order=4,
                   filter_bandwidth_hz=None, timeout=60,
                   save=False, filepath=None, metadata=None,
                   prepend_datetime=True):
        """
        Acquire raw I/Q time-domain segments from the demodulator.

        Uses the LabOne DAQ module in time-domain mode (``spectrum/enable=0``)
        to collect ``num_segments`` consecutive blocks of ``fft_length``
        samples each.  The complex demodulated signal ``x + i·y`` can then
        be windowed and FFT-processed entirely in Python.

        Hardware configuration mirrors :meth:`spectrum`: the oscillator is
        set to ``center_freq`` and the demodulator sample rate is set to
        ``span × 2`` to satisfy the Nyquist criterion for the requested span.

        Parameters
        ----------
        center_freq : float
            Centre frequency in Hz.  The oscillator is set to this value.
        span : float
            Observable frequency span in Hz.  The demodulator sample rate
            is set to ``span × 2``.
        fft_length : int
            Number of samples per segment (columns in the DAQ grid).
            Powers of 2 recommended.
        num_segments : int or None, optional
            Number of consecutive segments to acquire (rows in the DAQ grid).
            Mutually exclusive with ``acquire_time``.  Default is 20 when
            neither parameter is supplied.
        acquire_time : float or None, optional
            Desired total acquisition duration in seconds.  Converted to
            ``num_segments`` via ``ceil(acquire_time * fs / fft_length)``.
            Mutually exclusive with ``num_segments``.
        demod_index : int, optional
            Demodulator channel index (0–5).  Default is 0.
        osc_index : int, optional
            Oscillator index (0 or 1).  Default is 0.
        filter_order : int, optional
            Demodulator LP filter order (1–8, hardware).  Default is 4.
        filter_bandwidth_hz : float or None, optional
            Demodulator LP filter 3 dB bandwidth in Hz.  Converted to a
            time constant via :func:`bandwidth_to_tc` and written to the
            device.  If None, the time constant is left unchanged.
        timeout : float, optional
            Maximum seconds to wait for the DAQ module.  Default is 60.
        save : bool, optional
            If True, save the raw IQ data to an HDF5 file.  Requires
            ``filepath``.  Default is False.
        filepath : str or None, optional
            Destination HDF5 path.  Required when ``save=True``.
        metadata : dict or None, optional
            Extra attributes stored in the HDF5 file.
        prepend_datetime : bool, optional
            If True, prepend the current date and time to the filename in
            the format ``YYYY-MM-DD_HH_MM_SS_``.  Default is True.

        Returns
        -------
        dict
            Keys:

            * ``'x'`` — I component, shape ``(num_segments, fft_length)``.
            * ``'y'`` — Q component, shape ``(num_segments, fft_length)``.
            * ``'fs'`` — sample rate in Hz (= ``span × 2``).
            * ``'params'`` — dict of measurement parameters including
              ``filter_timeconstant`` (TC in seconds as set on device).

        Raises
        ------
        ValueError
            If ``save=True`` but ``filepath`` is None.
        RuntimeError
            If the DAQ module returns no data.
        """
        import math
        import numpy as np

        if num_segments is not None and acquire_time is not None:
            raise ValueError("Specify either num_segments or acquire_time, not both.")

        fs = span * 2
        time_per_segment = fft_length / fs

        if acquire_time is not None:
            num_segments = math.ceil(acquire_time / time_per_segment)
        elif num_segments is None:
            num_segments = 20

        expected_time = num_segments * time_per_segment
        print(f"Expected DAQ time : {expected_time:.3f} s  "
              f"({num_segments} segments × {time_per_segment*1e3:.3f} ms/segment)")

        if save and filepath is None:
            raise ValueError("filepath must be set when save=True")
        if save and filepath is not None:
            import os
            _, ext = os.path.splitext(filepath)
            if ext == "":
                filepath = filepath + ".h5"
            elif ext != ".h5":
                raise ValueError(
                    f"Invalid file suffix '{ext}'. Use '.h5' or provide a path with no suffix."
                )

        # --- Oscillator & demodulator (hardware) ----------------------------
        self.set_oscillator_frequency(osc_index, center_freq)

        tc = None
        with self.device.set_transaction():
            self.device.demods[demod_index].enable(1)
            self.device.demods[demod_index].oscselect(osc_index)
            self.device.demods[demod_index].order(filter_order)
            self.device.demods[demod_index].rate(fs)
            if filter_bandwidth_hz is not None:
                tc = bandwidth_to_tc(filter_bandwidth_hz, filter_order)
                self.device.demods[demod_index].timeconstant(tc)

        # Read-back verification — device values override requested values
        self._verify_node(self.device.demods[demod_index].enable, 1,
                          f'demods/{demod_index}/enable')
        self._verify_node(self.device.demods[demod_index].oscselect, osc_index,
                          f'demods/{demod_index}/oscselect')
        filter_order = self._verify_node(self.device.demods[demod_index].order, filter_order,
                                         f'demods/{demod_index}/order')
        fs = self._verify_node(self.device.demods[demod_index].rate, float(fs),
                               f'demods/{demod_index}/rate')
        if tc is not None:
            tc = self._verify_node(self.device.demods[demod_index].timeconstant, tc,
                                   f'demods/{demod_index}/timeconstant')

        # Read back actual TC (may have been set above or pre-existing)
        tc_actual = float(self.device.demods[demod_index].timeconstant())

        # --- DAQ module (time-domain mode) ----------------------------------
        daq_module = self.session.modules.daq
        daq_module.device(self.device_id)
        daq_module.type(0)                     # 0 = continuous (no trigger)
        daq_module.spectrum.enable(0)           # time-domain, not FFT
        daq_module.grid.cols(fft_length)
        daq_module.grid.rows(num_segments)
        daq_module.historylength(1)
        daq_module.endless(0)
        daq_module.clearhistory(1)

        x_node = f'/{self.device_id}/demods/{demod_index}/sample.x'
        y_node = f'/{self.device_id}/demods/{demod_index}/sample.y'
        daq_module.subscribe(x_node)
        daq_module.subscribe(y_node)

        daq_module.execute()

        try:
            t_start = time.time()
            while not daq_module.finished():
                elapsed = time.time() - t_start
                if elapsed > timeout:
                    daq_module.finish()
                    raise TimeoutError(f"IQ acquisition timed out after {timeout:.0f} s")
                time.sleep(0.2)

            raw = daq_module.read(flat=True)
        except BaseException:
            daq_module.finish()
            raise
        finally:
            daq_module.unsubscribe('*')

        # --- Extract results ------------------------------------------------
        if x_node not in raw or len(raw[x_node]) == 0:
            raise RuntimeError("DAQ module returned no IQ data")

        # Each history entry has a 'value' array of shape (num_segments, fft_length)
        x_data = np.vstack([e['value'] for e in raw[x_node]])  # (num_segments, fft_length)
        y_data = np.vstack([e['value'] for e in raw[y_node]])

        params = {
            'center_freq': center_freq,
            'span': span,
            'fs': fs,
            'fft_length': fft_length,
            'num_segments': num_segments,
            'demod_index': demod_index,
            'osc_index': osc_index,
            'filter_order': filter_order,
            'filter_timeconstant': tc_actual,
            'filter_bandwidth_hz': filter_bandwidth_hz,
        }

        result = {
            'x': x_data,
            'y': y_data,
            'fs': fs,
            'params': params,
        }

        if save:
            from data_management import save_iq_to_hdf5
            save_iq_to_hdf5(
                filepath, x_data, y_data,
                params=params,
                device_id=self.device_id,
                metadata=metadata,
                prepend_datetime=prepend_datetime,
            )

        return result

    # ------------------------------------------------------------------
    # Filter characterisation
    # ------------------------------------------------------------------

    def get_demod_filter_response(self, freqs_rel, demod_index=0):
        """
        Compute the analytical demodulator LP filter frequency response.

        Reads the current time constant and filter order from the device and
        returns the complex transfer function of the cascade of n identical
        first-order Butterworth stages:

            H(f) = 1 / (1 + j·2π·f·TC)^n

        Parameters
        ----------
        freqs_rel : array-like
            Frequencies **relative to the oscillator** (Hz).  Positive values
            are above the centre frequency, negative values below.
        demod_index : int, optional
            Demodulator channel index (0–5).  Default is 0.

        Returns
        -------
        H : ndarray, complex128
            Transfer function at each frequency in ``freqs_rel``.
            ``np.abs(H)`` gives the magnitude (gain) and
            ``np.angle(H)`` gives the phase shift.
        """
        import numpy as np
        tc = float(self.device.demods[demod_index].timeconstant())
        order = int(self.device.demods[demod_index].order())
        freqs_rel = np.asarray(freqs_rel, dtype=float)
        return 1.0 / (1 + 1j * 2 * np.pi * freqs_rel * tc) ** order

    # ------------------------------------------------------------------
    # Spectrum
    # ------------------------------------------------------------------

    def spectrum(self, center_freq, span, fft_length, num_averages=10,
                 demod_index=0, osc_index=0, window='hann',
                 correction='amplitude', filter_order=4,
                 filter_bandwidth_hz=None,
                 output_channel=None, output_amplitude=None,
                 output_enable=None, output_osc_index=0,
                 output_osc_enable=None, output_range_v=None,
                 output_offset=None,
                 timeout=60, save=False, filepath=None, metadata=None,
                 prepend_datetime=True):
        """
        Measure the spectrum around a center frequency using the LabOne DAQ module.

        Layer notes
        -----------
        **Device firmware (hardware):** oscillator frequency, demodulator LP
        filter (time constant, order), demodulator sample rate, signal outputs.

        **LabOne DAQ module (PC software):** FFT computation, windowing,
        frequency axis, spectrum averaging — controlled here via
        ``daq_module.set(...)``.

        **This method:** orchestration, filter bandwidth conversion, save/load.

        Parameters
        ----------
        center_freq : float
            Center frequency in Hz.  The selected oscillator is set to this
            value (hardware).
        span : float
            Total observable frequency span in Hz (DAQ: ``spectrum/frequencyspan``).
            The demodulator sample rate is set to ``2 × span`` to satisfy the
            Nyquist criterion (hardware).  The filter bandwidth should be
            ≥ ``span / 2`` to avoid attenuating the edges of the spectrum.
        fft_length : int
            Number of frequency bins per FFT segment (DAQ: ``grid/cols``).
            Powers of 2 are recommended.
        num_averages : int, optional
            Number of individual FFT segments to acquire (DAQ: ``historylength``).
            All individual spectra are returned.  Default is 10.
        demod_index : int, optional
            Demodulator channel index (0–5).  Default is 0.
        osc_index : int, optional
            Oscillator index (0 or 1).  Default is 0.
        window : str, optional
            Window function for the DAQ module (DAQ: ``spectrum/window``).
            Supported values: ``'hann'`` / ``'hanning'``, ``'hamming'``,
            ``'blackman'``, ``'rectangular'`` / ``'boxcar'``,
            ``'exponential'``, ``'cosine'``, ``'cosine2'``.  Default is
            ``'hann'``.
        correction : str, optional
            Spectral correction applied by the DAQ module:

            * ``'amplitude'`` — subscribes to ``fft.abs.filter``; window
              amplitude correction is applied internally; peaks represent
              true signal amplitude.
            * ``'power'`` — subscribes to ``fft.abs.pwr.avg``; power
              spectral density (area under curve = total power).

            Default is ``'amplitude'``.
        filter_order : int, optional
            Demodulator LP filter order (1–8, hardware).  Default is 4.
        filter_bandwidth_hz : float or None, optional
            Demodulator LP filter 3 dB bandwidth in Hz (hardware).  Converted
            to a time constant via :func:`bandwidth_to_tc` and written to the
            device.  If None, the time constant is left unchanged.
            Default is None.
        output_channel : int or None, optional
            Output channel (0 or 1) to configure before the measurement.
            If None, the output is not touched.  Default is None.
        output_amplitude : float or None, optional
            Output amplitude in volts.  Applied when ``output_channel`` is set.
        output_enable : bool or None, optional
            Enable (True) or disable (False) the output.  Applied when
            ``output_channel`` is set.
        output_osc_index : int, optional
            Oscillator slot on the output channel.  Default is 0.
        output_osc_enable : bool or None, optional
            Route the oscillator signal to the output.  Applied when
            ``output_channel`` is set.
        output_range_v : float or None, optional
            Output voltage range in volts.  Applied when ``output_channel``
            is set.
        output_offset : float or None, optional
            DC offset in volts.  Applied when ``output_channel`` is set.
        timeout : float, optional
            Maximum time in seconds to wait for the DAQ module to finish.
            Default is 60.
        save : bool, optional
            If True, save the full result to an HDF5 file.  Requires
            ``filepath``.  Default is False.
        filepath : str or None, optional
            Destination HDF5 file path.  Required when ``save=True``.
        metadata : dict or None, optional
            Extra attributes to store in the HDF5 file.
        prepend_datetime : bool, optional
            If True, prepend the current date and time to the filename in
            the format ``YYYY-MM-DD_HH_MM_SS_``.  Default is True.

        Returns
        -------
        dict
            Keys:

            * ``'freqs'`` — 1-D array of absolute frequencies in Hz,
              shape ``(fft_length,)``.
            * ``'ffts'`` — 2-D array of individual spectra,
              shape ``(num_averages, fft_length)``.
            * ``'averaged'`` — 1-D mean spectrum, shape ``(fft_length,)``.
            * ``'params'`` — dict of measurement parameters.

        Raises
        ------
        ValueError
            If ``save=True`` but ``filepath`` is None, or if an unrecognised
            ``window`` or ``correction`` value is supplied.
        RuntimeError
            If the DAQ module returns no data.
        """
        import numpy as np

        if save and filepath is None:
            raise ValueError("filepath must be set when save=True")
        if save and filepath is not None:
            import os
            _, ext = os.path.splitext(filepath)
            if ext == "":
                filepath = filepath + ".h5"
            elif ext != ".h5":
                raise ValueError(
                    f"Invalid file suffix '{ext}'. Use '.h5' or provide a path with no suffix."
                )

        window_key = window.lower()
        if window_key not in _DAQ_WINDOW:
            raise ValueError(
                f"Unrecognised window '{window}'. "
                f"Choose from: {', '.join(sorted(set(_DAQ_WINDOW.keys())))}."
            )
        if correction not in ('amplitude', 'power'):
            raise ValueError("correction must be 'amplitude' or 'power'.")

        # --- Output configuration (hardware) --------------------------------
        if output_channel is not None:
            kw = {}
            if output_amplitude is not None:
                kw['amplitude'] = output_amplitude
            else:
                kw['amplitude'] = 0.0          # amplitude is required by configure_output
            if output_enable is not None:
                kw['enable'] = output_enable
            if output_osc_enable is not None:
                kw['osc_enable'] = output_osc_enable
            if output_range_v is not None:
                kw['range_v'] = output_range_v
            if output_offset is not None:
                kw['offset'] = output_offset
            self.configure_output(output_channel, osc_index=output_osc_index, **kw)

        # --- Oscillator & demodulator (hardware) ----------------------------
        self.set_oscillator_frequency(osc_index, center_freq)

        with self.device.set_transaction():
            self.device.demods[demod_index].enable(1)
            self.device.demods[demod_index].oscselect(osc_index)
            self.device.demods[demod_index].order(filter_order)
            self.device.demods[demod_index].rate(span * 2)
            if filter_bandwidth_hz is not None:
                tc = bandwidth_to_tc(filter_bandwidth_hz, filter_order)
                self.device.demods[demod_index].timeconstant(tc)

        # Read-back verification — device values override requested values
        self._verify_node(self.device.demods[demod_index].enable, 1,
                          f'demods/{demod_index}/enable')
        self._verify_node(self.device.demods[demod_index].oscselect, osc_index,
                          f'demods/{demod_index}/oscselect')
        filter_order = self._verify_node(self.device.demods[demod_index].order, filter_order,
                                         f'demods/{demod_index}/order')
        span = self._verify_node(self.device.demods[demod_index].rate, float(span * 2),
                                f'demods/{demod_index}/rate') / 2
        if filter_bandwidth_hz is not None:
            tc = self._verify_node(self.device.demods[demod_index].timeconstant, tc,
                                   f'demods/{demod_index}/timeconstant')
            filter_bandwidth_hz = tc_to_bandwidth(tc, filter_order)

        # --- DAQ module (LabOne PC software) --------------------------------
        daq_module = self.session.modules.daq
        daq_module.device(self.device_id)
        daq_module.type(0)                              # 0 = continuous (no trigger)
        daq_module.set('spectrum/enable', 1)
        daq_module.set('spectrum/frequencyspan', span)
        daq_module.set('spectrum/window', _DAQ_WINDOW[window_key])
        daq_module.set('grid/cols', fft_length)
        daq_module.set('grid/repetitions', 1)
        daq_module.set('historylength', num_averages)
        daq_module.set('endless', 0)
        daq_module.set('clearhistory', 1)

        fft_node = f'/{self.device_id}/demods/{demod_index}/sample.xiy.fft.abs.filter'
        pwr_node = f'/{self.device_id}/demods/{demod_index}/sample.xiy.fft.abs.pwr.avg'

        daq_module.subscribe(fft_node)
        if correction == 'power':
            daq_module.subscribe(pwr_node)

        daq_module.execute()

        try:
            t_start = time.time()
            while not daq_module.finished():
                elapsed = time.time() - t_start
                if elapsed > timeout:
                    daq_module.finish()
                    raise TimeoutError(f"Spectrum acquisition timed out after {timeout:.0f} s")
                time.sleep(0.2)

            raw = daq_module.read(flat=True)
        except BaseException:
            daq_module.finish()
            raise
        finally:
            daq_module.unsubscribe('*')

        # --- Extract results ------------------------------------------------
        if fft_node not in raw or len(raw[fft_node]) == 0:
            raise RuntimeError("DAQ module returned no spectrum data")

        # Each history entry is a dict with 'value' (1-D array) and 'timestamp'
        entries = raw[fft_node]
        ffts = np.array([e['value'] for e in entries])   # (num_averages, fft_length)
        averaged = ffts.mean(axis=0)

        # Frequency axis: center ± span/2
        freqs = np.linspace(center_freq - span / 2, center_freq + span / 2, fft_length)

        params = {
            'center_freq': center_freq,
            'span': span,
            'fft_length': fft_length,
            'num_averages': num_averages,
            'window': window,
            'correction': correction,
            'filter_order': filter_order,
            'filter_bandwidth_hz': filter_bandwidth_hz,
        }

        result = {
            'freqs': freqs,
            'ffts': ffts,
            'averaged': averaged,
            'params': params,
        }

        if save:
            save_spectrum_to_hdf5(
                filepath, result,
                device_id=self.device_id,
                demod_index=demod_index,
                metadata=metadata,
                prepend_datetime=prepend_datetime,
            )

        return result
