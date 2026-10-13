"""
Tests for ZurichDevice, HF2LI, and data_management.

All tests mock zhinst.toolkit so no hardware or LabOne server is required.
"""

import functools
import sys
import types
import numpy as np
import pytest
import h5py
from unittest.mock import ANY, MagicMock, patch, call


# ---------------------------------------------------------------------------
# Mock the zhinst.toolkit module before importing our code
# ---------------------------------------------------------------------------
mock_toolkit = types.ModuleType("zhinst.toolkit")
mock_zhinst = types.ModuleType("zhinst")
mock_zhinst.toolkit = mock_toolkit
mock_toolkit.Session = MagicMock
sys.modules["zhinst"] = mock_zhinst
sys.modules["zhinst.toolkit"] = mock_toolkit

import scipy.signal

from optomechanics.Zurich.Device_Zurich_Super import ZurichDevice
from optomechanics.Zurich.HF2LI import HF2LI, bandwidth_to_tc, tc_to_bandwidth
from optomechanics.Zurich.zurich_data_management import save_sweep_to_hdf5, save_spectrum_to_hdf5, save_iq_to_hdf5

# The savers prefix filenames with a timestamp by default; the tests need the
# exact path they passed in.
save_sweep_to_hdf5    = functools.partial(save_sweep_to_hdf5,    prepend_datetime=False)
save_spectrum_to_hdf5 = functools.partial(save_spectrum_to_hdf5, prepend_datetime=False)
save_iq_to_hdf5       = functools.partial(save_iq_to_hdf5,       prepend_datetime=False)


@pytest.fixture(autouse=True)
def _skip_readback_verification():
    """MagicMock nodes can't return the values written to them, so make
    HF2LI._verify_node echo the expected value instead of reading back."""
    with patch.object(HF2LI, "_verify_node",
                      staticmethod(lambda node, expected, label, rtol=0.01: float(expected))):
        yield



class _MockAmplitudes(MagicMock):
    """sigouts[n].amplitudes stand-in: HF2LI finds the per-oscillator nodes
    by listing digit-named children (on the HF2, output 0 uses 6 and 7)."""
    def __dir__(self):
        return ["6", "7"]


def _mock_device():
    device = MagicMock()
    device.sigouts.__getitem__.return_value.amplitudes = _MockAmplitudes()
    return device

# ===========================================================================
# ZurichDevice tests
# ===========================================================================

class TestZurichDeviceInit:
    def test_defaults(self):
        dev = ZurichDevice("dev1374")
        assert dev.device_id == "dev1374"
        assert dev.server_host == "localhost"
        assert dev.port == 8004
        assert dev.session is None
        assert dev.device is None

    def test_custom_params(self):
        dev = ZurichDevice("dev9999", server_host="192.168.1.10", port=8005)
        assert dev.device_id == "dev9999"
        assert dev.server_host == "192.168.1.10"
        assert dev.port == 8005


class TestZurichDeviceOpenClose:
    def test_open_creates_session_and_connects(self):
        mock_session = MagicMock()
        mock_device = MagicMock()
        mock_device.device_type = "HF2LI"
        mock_device.serial = "dev1374"
        mock_session.connect_device.return_value = mock_device

        with patch("optomechanics.Zurich.Device_Zurich_Super.Session", return_value=mock_session) as MockSession:
            dev = ZurichDevice("dev1374", port=8005)
            result = dev.open()

            MockSession.assert_called_once_with("localhost", 8005)
            mock_session.connect_device.assert_called_once_with("dev1374")
            assert dev.session is mock_session
            assert dev.device is mock_device
            assert result is dev  # returns self for chaining

    def test_close_disconnects(self):
        mock_session = MagicMock()
        mock_device = MagicMock()
        mock_session.connect_device.return_value = mock_device

        with patch("optomechanics.Zurich.Device_Zurich_Super.Session", return_value=mock_session):
            dev = ZurichDevice("dev1374")
            dev.open()
            dev.close()

            mock_session.disconnect_device.assert_called_once_with("dev1374")
            assert dev.device is None
            assert dev.session is None

    def test_context_manager(self):
        mock_session = MagicMock()
        mock_device = MagicMock()
        mock_device.device_type = "HF2LI"
        mock_device.serial = "dev1374"
        mock_session.connect_device.return_value = mock_device

        with patch("optomechanics.Zurich.Device_Zurich_Super.Session", return_value=mock_session):
            with ZurichDevice("dev1374") as dev:
                assert dev.device is mock_device
            # after exiting, device should be disconnected
            assert dev.device is None


# ===========================================================================
# HF2LI tests
# ===========================================================================

class TestHF2LIInit:
    def test_defaults(self):
        hf = HF2LI()
        assert hf.device_id == "dev1374"
        assert hf.port == 8005

    def test_custom_device_id(self):
        hf = HF2LI(device_id="dev9999")
        assert hf.device_id == "dev9999"


class TestHF2LIConfigureOutput:
    def test_configure_output_enables(self):
        hf = HF2LI()
        hf.device = _mock_device()

        hf.configure_output(channel=0, amplitude=0.5, enable=True)

        hf.device.sigouts[0].on.assert_called_with(1)
        hf.device.sigouts[0].amplitudes[0].assert_called_with(0.5)

    def test_configure_output_disables(self):
        hf = HF2LI()
        hf.device = _mock_device()

        hf.configure_output(channel=1, amplitude=0.0, enable=False)

        hf.device.sigouts[1].on.assert_called_with(0)


class TestHF2LIConfigureInput:
    def test_configure_input_defaults(self):
        hf = HF2LI()
        hf.device = _mock_device()

        hf.configure_input(channel=0)

        hf.device.sigins[0].range.assert_called_with(1.0)
        hf.device.sigins[0].imp50.assert_called_with(0)
        hf.device.sigins[0].ac.assert_called_with(0)

    def test_configure_input_50ohm_ac(self):
        hf = HF2LI()
        hf.device = _mock_device()

        hf.configure_input(channel=0, input_range=0.1, impedance_50ohm=True, ac_coupling=True)

        hf.device.sigins[0].range.assert_called_with(0.1)
        hf.device.sigins[0].imp50.assert_called_with(1)
        hf.device.sigins[0].ac.assert_called_with(1)


class TestHF2LIConfigureDemodulator:
    def test_configure_demod_defaults(self):
        hf = HF2LI()
        hf.device = _mock_device()

        hf.configure_demodulator(index=0)

        hf.device.demods[0].enable.assert_called_with(1)
        hf.device.demods[0].oscselect.assert_called_with(0)
        hf.device.demods[0].harmonic.assert_called_with(1)
        hf.device.demods[0].rate.assert_called_with(1000)
        hf.device.demods[0].order.assert_called_with(4)
        hf.device.demods[0].timeconstant.assert_not_called()

    def test_configure_demod_with_timeconstant(self):
        hf = HF2LI()
        hf.device = _mock_device()

        hf.configure_demodulator(index=2, timeconstant=0.001)

        hf.device.demods[2].timeconstant.assert_called_with(0.001)


class TestHF2LISetOscillatorFrequency:
    def test_set_frequency(self):
        hf = HF2LI()
        hf.device = _mock_device()

        hf.set_oscillator_frequency(0, 400e3)

        hf.device.oscs[0].freq.assert_called_with(400e3)


class TestHF2LISweep:
    def _make_hf2li_with_mock_sweeper(self):
        """Helper: return an HF2LI with mocked session/device/sweeper."""
        hf = HF2LI()
        hf.device = _mock_device()
        hf.session = MagicMock()

        sweeper = MagicMock()
        hf.session.modules.sweeper = sweeper

        sample_node = hf.device.demods[0].sample

        sweep_result = {
            "frequency": np.array([100.0, 200.0, 300.0]),
            "r": np.array([0.01, 0.02, 0.03]),
            "phase": np.array([0.1, 0.2, 0.3]),
            "x": np.array([0.009, 0.019, 0.029]),
            "y": np.array([0.001, 0.002, 0.003]),
        }
        # Sweeper returns a list of chunks, each a list holding one result
        sweeper.read.return_value = {sample_node: [[sweep_result]]}

        return hf, sweeper, sample_node

    def test_sweep_returns_dict_of_arrays(self):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()

        result = hf.sweep(start=100, stop=300, num_points=3)

        assert set(result.keys()) == {"frequency", "r", "phase", "x", "y"}
        for key in result:
            assert isinstance(result[key], np.ndarray)
            assert len(result[key]) == 3

    def test_sweep_configures_sweeper(self):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()

        hf.sweep(start=1000, stop=50e6, num_points=100, log_sweep=True,
                 averaging_samples=10, settling_time=0.01, settling_inaccuracy=0.001)

        sweeper.start.assert_called_with(1000)
        sweeper.stop.assert_called_with(50e6)
        sweeper.samplecount.assert_called_with(100)
        sweeper.xmapping.assert_called_with(1)  # log
        sweeper.averaging.sample.assert_called_with(10)
        sweeper.settling.time.assert_called_with(0.01)
        sweeper.settling.inaccuracy.assert_called_with(0.001)

    def test_sweep_linear(self):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()

        hf.sweep(start=100, stop=300, num_points=3, log_sweep=False)

        sweeper.xmapping.assert_called_with(0)

    def test_sweep_subscribes_and_unsubscribes(self):
        hf, sweeper, sample_node = self._make_hf2li_with_mock_sweeper()

        hf.sweep(start=100, stop=300, num_points=3)

        sweeper.subscribe.assert_called_once_with(sample_node)
        sweeper.execute.assert_called_once()
        sweeper.wait_done.assert_called_once()
        sweeper.unsubscribe.assert_called_once_with(sample_node)

    def test_sweep_raises_on_empty_data(self):
        hf = HF2LI()
        hf.device = _mock_device()
        hf.session = MagicMock()

        sweeper = MagicMock()
        hf.session.modules.sweeper = sweeper
        sample_node = hf.device.demods[0].sample
        sweeper.read.return_value = {sample_node: []}

        with pytest.raises(RuntimeError, match="Sweep returned no data"):
            hf.sweep(start=100, stop=300, num_points=3)

    def test_sweep_save_calls_save_function(self, tmp_path):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()
        filepath = str(tmp_path / "sweep.h5")

        with patch("optomechanics.Zurich.HF2LI.save_sweep_to_hdf5") as mock_save:
            result = hf.sweep(start=100, stop=300, num_points=3,
                              save=True, filepath=filepath,
                              prepend_datetime=False)
        mock_save.assert_called_once()
        args, kwargs = mock_save.call_args
        assert args == (filepath, result)
        assert kwargs["device_id"] == hf.device_id
        assert kwargs["demod_index"] == 0
        assert kwargs["metadata"] == None
        assert kwargs["sweep_params"]["num_points"] == 3

    def test_sweep_save_with_metadata(self, tmp_path):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()
        filepath = str(tmp_path / "sweep.h5")
        meta = {"sample": "resonator_A"}

        with patch("optomechanics.Zurich.HF2LI.save_sweep_to_hdf5") as mock_save:
            result = hf.sweep(start=100, stop=300, num_points=3,
                              save=True, filepath=filepath, metadata=meta,
                              prepend_datetime=False)
        mock_save.assert_called_once()
        args, kwargs = mock_save.call_args
        assert args == (filepath, result)
        assert kwargs["device_id"] == hf.device_id
        assert kwargs["demod_index"] == 0
        assert kwargs["metadata"] == meta
        assert kwargs["sweep_params"]["num_points"] == 3

    def test_sweep_save_false_does_not_call_save(self):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()

        with patch("optomechanics.Zurich.HF2LI.save_sweep_to_hdf5") as mock_save:
            hf.sweep(start=100, stop=300, num_points=3, save=False)
            mock_save.assert_not_called()

    def test_sweep_save_without_filepath_raises(self):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()

        with pytest.raises(ValueError, match="filepath must be set"):
            hf.sweep(start=100, stop=300, num_points=3, save=True, filepath=None)

    def test_sweep_save_false_none_filepath_does_not_raise(self):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()
        # save=False with no filepath must not raise
        hf.sweep(start=100, stop=300, num_points=3, save=False, filepath=None)

    def test_sweep_sets_bandwidth_hz(self):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()
        hf.sweep(start=100, stop=300, num_points=3, bandwidth_hz=10.0)
        sweeper.bandwidth.assert_called_with(10.0)

    def test_sweep_bandwidth_hz_none_not_called(self):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()
        hf.sweep(start=100, stop=300, num_points=3, bandwidth_hz=None)
        sweeper.bandwidth.assert_not_called()

    def test_sweep_sets_filter_order(self):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()
        hf.sweep(start=100, stop=300, num_points=3, filter_order=6)
        hf.device.demods[0].order.assert_called_with(6)

    def test_sweep_filter_order_none_not_called(self):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()
        hf.sweep(start=100, stop=300, num_points=3, filter_order=None)
        hf.device.demods[0].order.assert_not_called()

    def test_sweep_no_progress_uses_wait_done(self):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()
        hf.sweep(start=100, stop=300, num_points=3, progress=False)
        sweeper.wait_done.assert_called_once()
        sweeper.finished.assert_not_called()

    def test_sweep_progress_polls_until_finished(self):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()
        # progress() is polled until it reaches 1.0
        sweeper.progress.side_effect = [0.5, 0.5, 1.0]

        with patch("optomechanics.Zurich.HF2LI.time.sleep") as mock_sleep:
            hf.sweep(start=100, stop=300, num_points=3,
                     progress=True, progress_interval=1)

        sweeper.wait_done.assert_not_called()
        mock_sleep.assert_called_with(1)

    def test_sweep_progress_prints_estimated_time(self, capsys):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()
        # progress() is polled until it reaches 1.0
        sweeper.progress.side_effect = [0.5, 0.5, 1.0]

        with patch("optomechanics.Zurich.HF2LI.time.sleep"):
            hf.sweep(start=100, stop=300, num_points=3,
                     progress=True, progress_interval=1, settling_time=0.1)

        out = capsys.readouterr().out
        assert "Estimated sweep time: 0.3 s" in out

    def test_sweep_progress_timeout_raises(self):
        hf, sweeper, _ = self._make_hf2li_with_mock_sweeper()
        sweeper.finished.return_value = False
        sweeper.progress.return_value = 0.1

        with patch("optomechanics.Zurich.HF2LI.time.sleep"), \
             patch("optomechanics.Zurich.HF2LI.time.time", side_effect=[0, 0, 200, 200, 200]):
            with pytest.raises(TimeoutError):
                hf.sweep(start=100, stop=300, num_points=3,
                         progress=True, progress_interval=1, timeout=60)


# ===========================================================================
# data_management tests
# ===========================================================================

_SAMPLE_RESULT = {
    "frequency": np.array([100.0, 200.0, 300.0]),
    "r":         np.array([0.01, 0.02, 0.03]),
    "phase":     np.array([0.1, 0.2, 0.3]),
    "x":         np.array([0.009, 0.019, 0.029]),
    "y":         np.array([0.001, 0.002, 0.003]),
}


class TestSaveSweepToHdf5:
    def test_creates_file(self, tmp_path):
        fp = str(tmp_path / "out.h5")
        save_sweep_to_hdf5(fp, _SAMPLE_RESULT)
        assert (tmp_path / "out.h5").exists()

    def test_hdf5_structure(self, tmp_path):
        fp = str(tmp_path / "out.h5")
        save_sweep_to_hdf5(fp, _SAMPLE_RESULT, device_id="dev1374", demod_index=0)

        with h5py.File(fp, "r") as f:
            grp = f["000/dev1374/demods/0/sample"]
            for key in ("frequency", "r", "phase", "x", "y"):
                assert key in grp

    def test_array_values_are_correct(self, tmp_path):
        fp = str(tmp_path / "out.h5")
        save_sweep_to_hdf5(fp, _SAMPLE_RESULT)

        with h5py.File(fp, "r") as f:
            grp = f["000/dev1374/demods/0/sample"]
            np.testing.assert_array_equal(grp["frequency"][:], _SAMPLE_RESULT["frequency"])
            np.testing.assert_array_equal(grp["r"][:], _SAMPLE_RESULT["r"])

    def test_custom_device_id_and_demod(self, tmp_path):
        fp = str(tmp_path / "out.h5")
        save_sweep_to_hdf5(fp, _SAMPLE_RESULT, device_id="dev9999", demod_index=2)

        with h5py.File(fp, "r") as f:
            assert "000/dev9999/demods/2/sample" in f

    def test_creation_date_attribute_stored(self, tmp_path):
        fp = str(tmp_path / "out.h5")
        save_sweep_to_hdf5(fp, _SAMPLE_RESULT)

        with h5py.File(fp, "r") as f:
            assert "file creation date" in f.attrs

    def test_metadata_stored_as_attributes(self, tmp_path):
        fp = str(tmp_path / "out.h5")
        meta = {"sample": "resonator_A", "temperature_K": 4.2}
        save_sweep_to_hdf5(fp, _SAMPLE_RESULT, metadata=meta)

        with h5py.File(fp, "r") as f:
            assert f["000"].attrs["user_sample"] == "resonator_A"
            assert f["000"].attrs["user_temperature_K"] == pytest.approx(4.2)

    def test_append_adds_iteration_group(self, tmp_path):
        fp = str(tmp_path / "out.h5")
        save_sweep_to_hdf5(fp, _SAMPLE_RESULT, group_index=0)
        save_sweep_to_hdf5(fp, _SAMPLE_RESULT, group_index=1, append=True)

        with h5py.File(fp, "r") as f:
            assert "000/dev1374/demods/0/sample" in f
            assert "001/dev1374/demods/0/sample" in f

    def test_creates_parent_directory(self, tmp_path):
        fp = str(tmp_path / "nested" / "dir" / "out.h5")
        save_sweep_to_hdf5(fp, _SAMPLE_RESULT)
        assert (tmp_path / "nested" / "dir" / "out.h5").exists()


# ===========================================================================
# bandwidth_to_tc / tc_to_bandwidth tests
# ===========================================================================

class TestBandwidthTcConversion:
    """Device-confirmed values used as ground truth."""

    # order=1, f_3dB=500 Hz → TC ≈ 318.1 µs  (device-confirmed)
    def test_bandwidth_to_tc_order1_500hz(self):
        tc = bandwidth_to_tc(500.0, 1)
        # 1/(2*pi*500) = 318.3 us; the device displays 318.1 us
        assert tc == pytest.approx(3.181e-4, rel=1e-3)

    # order=4, f_3dB=500 Hz → TC ≈ 138.4 µs  (device-confirmed)
    def test_bandwidth_to_tc_order4_500hz(self):
        tc = bandwidth_to_tc(500.0, 4)
        assert tc == pytest.approx(1.384e-4, abs=1e-7)

    # Analytic check: order=1, f_3dB=1 Hz → TC = 1/(2π)
    def test_bandwidth_to_tc_order1_1hz(self):
        import math
        tc = bandwidth_to_tc(1.0, 1)
        assert tc == pytest.approx(1 / (2 * math.pi), rel=1e-6)

    # Round-trip: tc_to_bandwidth is the exact inverse
    def test_round_trip_order4(self):
        f_in = 500.0
        tc = bandwidth_to_tc(f_in, 4)
        f_out = tc_to_bandwidth(tc, 4)
        assert f_out == pytest.approx(f_in, rel=1e-9)

    def test_round_trip_order1(self):
        f_in = 100.0
        tc = bandwidth_to_tc(f_in, 1)
        f_out = tc_to_bandwidth(tc, 1)
        assert f_out == pytest.approx(f_in, rel=1e-9)

    # tc_to_bandwidth device-confirmed inverse
    def test_tc_to_bandwidth_order4_138us(self):
        bw = tc_to_bandwidth(1.384e-4, 4)
        assert bw == pytest.approx(500.0, abs=0.5)


# ===========================================================================
# configure_output extended parameters
# ===========================================================================

class TestConfigureOutputExtended:
    def test_range_v_is_set(self):
        hf = HF2LI()
        hf.device = _mock_device()

        hf.configure_output(channel=0, amplitude=1.0, range_v=10.0)

        hf.device.sigouts[0].range.assert_called_with(10.0)

    def test_offset_is_set(self):
        hf = HF2LI()
        hf.device = _mock_device()

        hf.configure_output(channel=0, amplitude=1.0, offset=0.5)

        hf.device.sigouts[0].offset.assert_called_with(0.5)

    def test_range_and_offset_none_not_called(self):
        hf = HF2LI()
        hf.device = _mock_device()

        hf.configure_output(channel=0, amplitude=1.0)

        hf.device.sigouts[0].range.assert_not_called()
        hf.device.sigouts[0].offset.assert_not_called()

    def test_range_and_offset_together(self):
        hf = HF2LI()
        hf.device = _mock_device()

        hf.configure_output(channel=1, amplitude=2.0, range_v=5.0, offset=-0.1)

        hf.device.sigouts[1].range.assert_called_with(5.0)
        hf.device.sigouts[1].offset.assert_called_with(-0.1)


# ===========================================================================
# spectrum() tests
# ===========================================================================

class TestHF2LISpectrum:
    def _make_hf2li_with_mock_daq(self, num_averages=5, fft_length=64):
        """Return HF2LI with a mocked DAQ module that yields plausible data."""
        hf = HF2LI()
        hf.device = _mock_device()
        hf.session = MagicMock()

        daq_module = MagicMock()
        hf.session.modules.daq = daq_module

        # DAQ module finishes immediately
        daq_module.finished.return_value = True

        # Build fake per-entry FFT values
        fake_value = np.ones(fft_length, dtype=float)
        entries = [{'value': fake_value, 'timestamp': i} for i in range(num_averages)]

        fft_node = f'/dev1374/demods/0/sample.xiy.fft.abs.filter'
        daq_module.read.return_value = {fft_node: entries}

        return hf, daq_module

    # --- Return shape checks ------------------------------------------------

    def test_result_keys(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        result = hf.spectrum(center_freq=1000, span=100, fft_length=64, num_averages=5)
        assert set(result.keys()) == {'freqs', 'ffts', 'averaged', 'params'}

    def test_ffts_shape(self):
        hf, _ = self._make_hf2li_with_mock_daq(num_averages=5, fft_length=64)
        result = hf.spectrum(center_freq=1000, span=100, fft_length=64, num_averages=5)
        assert result['ffts'].shape == (5, 64)

    def test_averaged_shape(self):
        hf, _ = self._make_hf2li_with_mock_daq(num_averages=5, fft_length=64)
        result = hf.spectrum(center_freq=1000, span=100, fft_length=64, num_averages=5)
        assert result['averaged'].shape == (64,)

    def test_freqs_shape_and_range(self):
        hf, _ = self._make_hf2li_with_mock_daq(fft_length=64)
        result = hf.spectrum(center_freq=1000, span=100, fft_length=64, num_averages=5)
        freqs = result['freqs']
        assert freqs.shape == (64,)
        assert freqs[0] == pytest.approx(950.0, rel=1e-6)
        assert freqs[-1] == pytest.approx(1050.0, rel=1e-6)

    def test_averaged_equals_mean_of_ffts(self):
        hf, _ = self._make_hf2li_with_mock_daq(num_averages=5, fft_length=64)
        result = hf.spectrum(center_freq=1000, span=100, fft_length=64, num_averages=5)
        np.testing.assert_array_equal(result['averaged'], result['ffts'].mean(axis=0))

    def test_params_stored(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        result = hf.spectrum(center_freq=1000, span=100, fft_length=64,
                             num_averages=5, window='hann', correction='amplitude',
                             filter_order=4, filter_bandwidth_hz=50.0)
        p = result['params']
        assert p['center_freq'] == 1000
        assert p['span'] == 100
        assert p['fft_length'] == 64
        assert p['num_averages'] == 5
        assert p['window'] == 'hann'
        assert p['correction'] == 'amplitude'
        assert p['filter_order'] == 4
        assert p['filter_bandwidth_hz'] == pytest.approx(50.0)

    # --- DAQ module configuration assertions --------------------------------

    def test_daq_span_set(self):
        hf, daq = self._make_hf2li_with_mock_daq()
        hf.spectrum(center_freq=1000, span=200, fft_length=64, num_averages=5)
        daq.set.assert_any_call('spectrum/frequencyspan', 200)

    def test_daq_fft_length_set(self):
        hf, daq = self._make_hf2li_with_mock_daq(fft_length=128)
        hf.spectrum(center_freq=1000, span=100, fft_length=128, num_averages=5)
        daq.set.assert_any_call('grid/cols', 128)

    def test_daq_historylength_set(self):
        hf, daq = self._make_hf2li_with_mock_daq(num_averages=7)
        hf.spectrum(center_freq=1000, span=100, fft_length=64, num_averages=7)
        daq.set.assert_any_call('historylength', 7)

    def test_daq_window_hann(self):
        hf, daq = self._make_hf2li_with_mock_daq()
        hf.spectrum(center_freq=1000, span=100, fft_length=64, num_averages=5, window='hann')
        daq.set.assert_any_call('spectrum/window', 1)

    def test_daq_window_blackman(self):
        hf, daq = self._make_hf2li_with_mock_daq()
        hf.spectrum(center_freq=1000, span=100, fft_length=64, num_averages=5, window='blackman')
        daq.set.assert_any_call('spectrum/window', 3)

    # --- Filter bandwidth → TC conversion -----------------------------------

    def test_filter_bandwidth_sets_timeconstant(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        hf.spectrum(center_freq=1000, span=100, fft_length=64, num_averages=5,
                    filter_order=4, filter_bandwidth_hz=500.0)
        expected_tc = bandwidth_to_tc(500.0, 4)
        hf.device.demods[0].timeconstant.assert_called_with(pytest.approx(expected_tc, rel=1e-6))

    def test_filter_bandwidth_none_no_timeconstant(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        hf.spectrum(center_freq=1000, span=100, fft_length=64, num_averages=5,
                    filter_bandwidth_hz=None)
        hf.device.demods[0].timeconstant.assert_not_called()

    # --- Oscillator frequency set -------------------------------------------

    def test_oscillator_frequency_set(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        hf.spectrum(center_freq=5000, span=100, fft_length=64, num_averages=5, osc_index=0)
        hf.device.oscs[0].freq.assert_called_with(5000)

    # --- Sample rate set to 2 × span ----------------------------------------

    def test_demodulator_rate_set(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        hf.spectrum(center_freq=1000, span=300, fft_length=64, num_averages=5)
        hf.device.demods[0].rate.assert_called_with(600)

    # --- Save / no-save ------------------------------------------------------

    def test_save_false_does_not_call_save(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        with patch('optomechanics.Zurich.HF2LI.save_spectrum_to_hdf5') as mock_save:
            hf.spectrum(center_freq=1000, span=100, fft_length=64,
                        num_averages=5, save=False)
            mock_save.assert_not_called()

    def test_save_true_calls_save(self, tmp_path):
        hf, _ = self._make_hf2li_with_mock_daq()
        fp = str(tmp_path / "spec.h5")
        with patch('optomechanics.Zurich.HF2LI.save_spectrum_to_hdf5') as mock_save:
            result = hf.spectrum(center_freq=1000, span=100, fft_length=64,
                                 num_averages=5, save=True, filepath=fp)
            mock_save.assert_called_once_with(
                fp, result,
                device_id=hf.device_id,
                demod_index=0,
                metadata=None,
                prepend_datetime=ANY,
            )

    def test_save_without_filepath_raises(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        with pytest.raises(ValueError, match="filepath must be set"):
            hf.spectrum(center_freq=1000, span=100, fft_length=64,
                        num_averages=5, save=True, filepath=None)

    def test_invalid_window_raises(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        with pytest.raises(ValueError, match="Unrecognised window"):
            hf.spectrum(center_freq=1000, span=100, fft_length=64,
                        num_averages=5, window='kaiser')

    def test_invalid_correction_raises(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        with pytest.raises(ValueError, match="correction must be"):
            hf.spectrum(center_freq=1000, span=100, fft_length=64,
                        num_averages=5, correction='magnitude')

    def test_no_data_raises(self):
        hf = HF2LI()
        hf.device = _mock_device()
        hf.session = MagicMock()
        daq_module = MagicMock()
        hf.session.modules.daq = daq_module
        daq_module.finished.return_value = True
        daq_module.read.return_value = {}   # empty — no fft_node key

        with pytest.raises(RuntimeError, match="no spectrum data"):
            hf.spectrum(center_freq=1000, span=100, fft_length=64, num_averages=5)


# ===========================================================================
# save_spectrum_to_hdf5 tests
# ===========================================================================

_SAMPLE_SPECTRUM = {
    'freqs':    np.linspace(950, 1050, 64),
    'ffts':     np.random.rand(5, 64),
    'averaged': np.random.rand(64),
    'params': {
        'center_freq': 1000.0, 'span': 100.0, 'fft_length': 64,
        'num_averages': 5, 'window': 'hann', 'correction': 'amplitude',
        'filter_order': 4, 'filter_bandwidth_hz': 50.0,
    },
}


class TestSaveSpectrumToHdf5:
    def test_creates_file(self, tmp_path):
        fp = str(tmp_path / "spec.h5")
        save_spectrum_to_hdf5(fp, _SAMPLE_SPECTRUM)
        assert (tmp_path / "spec.h5").exists()

    def test_hdf5_structure(self, tmp_path):
        fp = str(tmp_path / "spec.h5")
        save_spectrum_to_hdf5(fp, _SAMPLE_SPECTRUM)

        with h5py.File(fp, "r") as f:
            grp = f["dev1374/demods/0/spectrum"]
            assert "freqs" in grp
            assert "ffts" in grp
            assert "averaged" in grp

    def test_freqs_values_correct(self, tmp_path):
        fp = str(tmp_path / "spec.h5")
        save_spectrum_to_hdf5(fp, _SAMPLE_SPECTRUM)

        with h5py.File(fp, "r") as f:
            grp = f["dev1374/demods/0/spectrum"]
            np.testing.assert_array_almost_equal(
                grp["freqs"][:], _SAMPLE_SPECTRUM["freqs"]
            )

    def test_ffts_shape_correct(self, tmp_path):
        fp = str(tmp_path / "spec.h5")
        save_spectrum_to_hdf5(fp, _SAMPLE_SPECTRUM)

        with h5py.File(fp, "r") as f:
            assert f["dev1374/demods/0/spectrum/ffts"].shape == (5, 64)

    def test_averaged_values_correct(self, tmp_path):
        fp = str(tmp_path / "spec.h5")
        save_spectrum_to_hdf5(fp, _SAMPLE_SPECTRUM)

        with h5py.File(fp, "r") as f:
            np.testing.assert_array_almost_equal(
                f["dev1374/demods/0/spectrum/averaged"][:],
                _SAMPLE_SPECTRUM["averaged"],
            )

    def test_params_stored_as_attributes(self, tmp_path):
        fp = str(tmp_path / "spec.h5")
        save_spectrum_to_hdf5(fp, _SAMPLE_SPECTRUM)

        with h5py.File(fp, "r") as f:
            assert f.attrs["center_freq"] == pytest.approx(1000.0)
            assert f.attrs["span"] == pytest.approx(100.0)
            assert f.attrs["fft_length"] == 64
            assert f.attrs["num_averages"] == 5
            assert f.attrs["window"] == "hann"
            assert f.attrs["correction"] == "amplitude"

    def test_metadata_stored_as_attributes(self, tmp_path):
        fp = str(tmp_path / "spec.h5")
        meta = {"sample": "resonator_A", "temperature_K": 4.2}
        save_spectrum_to_hdf5(fp, _SAMPLE_SPECTRUM, metadata=meta)

        with h5py.File(fp, "r") as f:
            assert f.attrs["sample"] == "resonator_A"
            assert f.attrs["temperature_K"] == pytest.approx(4.2)

    def test_custom_device_id_and_demod(self, tmp_path):
        fp = str(tmp_path / "spec.h5")
        save_spectrum_to_hdf5(fp, _SAMPLE_SPECTRUM, device_id="dev9999", demod_index=3)

        with h5py.File(fp, "r") as f:
            assert "dev9999/demods/3/spectrum" in f

    def test_timestamp_attribute_stored(self, tmp_path):
        fp = str(tmp_path / "spec.h5")
        save_spectrum_to_hdf5(fp, _SAMPLE_SPECTRUM)

        with h5py.File(fp, "r") as f:
            assert "timestamp" in f.attrs

    def test_creates_parent_directory(self, tmp_path):
        fp = str(tmp_path / "nested" / "spec.h5")
        save_spectrum_to_hdf5(fp, _SAMPLE_SPECTRUM)
        assert (tmp_path / "nested" / "spec.h5").exists()


# ===========================================================================
# Window metrics — NENBW and ENBW
# ===========================================================================

class TestWindowMetrics:
    """Verify that NENBW/ENBW computed from window arrays match known values."""

    @staticmethod
    def _nenbw(window_name, N):
        w = scipy.signal.get_window(window_name, N)
        return N * float((w ** 2).sum()) / float(w.sum()) ** 2

    def test_hann_nenbw_approx_1_5(self):
        nenbw = self._nenbw('hann', 512)
        assert nenbw == pytest.approx(1.5, rel=1e-4)

    def test_hann_nenbw_matches_reference_file(self):
        # Reference HDF5 chunkheader reports nenbw=1.50000572 for N=512 Hann
        nenbw = self._nenbw('hann', 512)
        assert nenbw == pytest.approx(1.50000572, rel=1e-5)

    def test_rectangular_nenbw_is_one(self):
        nenbw = self._nenbw('boxcar', 256)
        assert nenbw == pytest.approx(1.0, rel=1e-9)

    def test_enbw_hz_formula(self):
        N = 512
        fs = 1000.0
        nenbw = self._nenbw('hann', N)
        enbw = nenbw * fs / N
        assert enbw == pytest.approx(nenbw * fs / N, rel=1e-12)

    def test_nenbw_independent_of_n(self):
        # For an ideal Hann window NENBW ≈ 1.5 regardless of N (for large N)
        for N in (256, 512, 1024):
            assert self._nenbw('hann', N) == pytest.approx(1.5, rel=1e-4)


# ===========================================================================
# save_iq_to_hdf5 — metadata completeness
# ===========================================================================

_REQUIRED_IQ_ATTRS = [
    'timestamp', 'device_id', 'demod_index',
    'center_freq', 'span', 'fs',
    'fft_length', 'num_segments', 'window',
    'filter_order', 'filter_timeconstant', 'filter_bandwidth_hz',
    'osc_index', 'nenbw', 'enbw',
]

_SAMPLE_IQ_PARAMS = {
    'center_freq': 1000.0,
    'span': 100.0,
    'fs': 200.0,
    'fft_length': 64,
    'num_segments': 10,
    'demod_index': 0,
    'osc_index': 0,
    'window': 'hann',
    'filter_order': 4,
    'filter_timeconstant': 1.384e-4,
    'filter_bandwidth_hz': 500.0,
}


class TestSaveIqToHdf5:
    def test_creates_file(self, tmp_path):
        fp = str(tmp_path / "iq.h5")
        x = np.zeros((10, 64))
        y = np.zeros((10, 64))
        save_iq_to_hdf5(fp, x, y, params=_SAMPLE_IQ_PARAMS)
        assert (tmp_path / "iq.h5").exists()

    def test_all_required_attrs_present(self, tmp_path):
        fp = str(tmp_path / "iq.h5")
        x = np.zeros((10, 64))
        y = np.zeros((10, 64))
        save_iq_to_hdf5(fp, x, y, params=_SAMPLE_IQ_PARAMS)
        with h5py.File(fp, "r") as f:
            for attr in _REQUIRED_IQ_ATTRS:
                assert attr in f.attrs, f"Missing HF2LI attribute: {attr!r}"

    def test_hdf5_structure(self, tmp_path):
        fp = str(tmp_path / "iq.h5")
        x = np.zeros((10, 64))
        y = np.zeros((10, 64))
        save_iq_to_hdf5(fp, x, y, params=_SAMPLE_IQ_PARAMS)
        with h5py.File(fp, "r") as f:
            grp = f["dev1374/demods/0/iq_raw"]
            assert "x" in grp
            assert "y" in grp

    def test_xy_values_correct(self, tmp_path):
        fp = str(tmp_path / "iq.h5")
        x = np.arange(10 * 64, dtype=float).reshape(10, 64)
        y = x * 2
        save_iq_to_hdf5(fp, x, y, params=_SAMPLE_IQ_PARAMS)
        with h5py.File(fp, "r") as f:
            np.testing.assert_array_equal(f["dev1374/demods/0/iq_raw/x"][:], x)
            np.testing.assert_array_equal(f["dev1374/demods/0/iq_raw/y"][:], y)

    def test_nenbw_computed_correctly(self, tmp_path):
        fp = str(tmp_path / "iq.h5")
        save_iq_to_hdf5(fp, np.zeros((10, 64)), np.zeros((10, 64)),
                        params=_SAMPLE_IQ_PARAMS)
        with h5py.File(fp, "r") as f:
            assert f.attrs["nenbw"] == pytest.approx(1.5, rel=1e-4)

    def test_enbw_computed_correctly(self, tmp_path):
        fp = str(tmp_path / "iq.h5")
        save_iq_to_hdf5(fp, np.zeros((10, 64)), np.zeros((10, 64)),
                        params=_SAMPLE_IQ_PARAMS)
        with h5py.File(fp, "r") as f:
            # ENBW = NENBW * fs / N = 1.5 * 200 / 64
            assert f.attrs["enbw"] == pytest.approx(1.5 * 200.0 / 64, rel=1e-4)

    def test_metadata_stored_as_attributes(self, tmp_path):
        fp = str(tmp_path / "iq.h5")
        meta = {"sample": "resonator_A", "temperature_K": 4.2}
        save_iq_to_hdf5(fp, np.zeros((10, 64)), np.zeros((10, 64)),
                        params=_SAMPLE_IQ_PARAMS, metadata=meta)
        with h5py.File(fp, "r") as f:
            assert f.attrs["sample"] == "resonator_A"
            assert f.attrs["temperature_K"] == pytest.approx(4.2)

    def test_custom_device_id(self, tmp_path):
        fp = str(tmp_path / "iq.h5")
        save_iq_to_hdf5(fp, np.zeros((10, 64)), np.zeros((10, 64)),
                        params=_SAMPLE_IQ_PARAMS, device_id="dev9999")
        with h5py.File(fp, "r") as f:
            assert "dev9999/demods/0/iq_raw" in f

    def test_creates_parent_directory(self, tmp_path):
        fp = str(tmp_path / "nested" / "iq.h5")
        save_iq_to_hdf5(fp, np.zeros((10, 64)), np.zeros((10, 64)),
                        params=_SAMPLE_IQ_PARAMS)
        assert (tmp_path / "nested" / "iq.h5").exists()


# ===========================================================================
# HF2LI.acquire_iq tests
# ===========================================================================

class TestHF2LIAcquireIq:
    def _make_hf2li_with_mock_daq(self, num_segments=5, fft_length=64):
        hf = HF2LI()
        hf.device = _mock_device()
        hf.session = MagicMock()

        daq_module = MagicMock()
        hf.session.modules.daq = daq_module
        daq_module.finished.return_value = True

        fake_x = np.ones((num_segments, fft_length))
        fake_y = np.zeros((num_segments, fft_length))
        x_node = f'/dev1374/demods/0/sample.x'
        y_node = f'/dev1374/demods/0/sample.y'
        daq_module.read.return_value = {
            x_node: [{'value': fake_x, 'timestamp': 0}],
            y_node: [{'value': fake_y, 'timestamp': 0}],
        }

        # timeconstant() returns a float
        hf.device.demods[0].timeconstant.return_value = 1.384e-4

        return hf, daq_module

    def test_result_keys(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        result = hf.acquire_iq(center_freq=1000, span=100, fft_length=64, num_segments=5)
        assert set(result.keys()) == {'x', 'y', 'fs', 'params'}

    def test_x_shape(self):
        hf, _ = self._make_hf2li_with_mock_daq(num_segments=5, fft_length=64)
        result = hf.acquire_iq(center_freq=1000, span=100, fft_length=64, num_segments=5)
        assert result['x'].shape == (5, 64)

    def test_y_shape(self):
        hf, _ = self._make_hf2li_with_mock_daq(num_segments=5, fft_length=64)
        result = hf.acquire_iq(center_freq=1000, span=100, fft_length=64, num_segments=5)
        assert result['y'].shape == (5, 64)

    def test_fs_is_span_times_two(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        result = hf.acquire_iq(center_freq=1000, span=200, fft_length=64, num_segments=5)
        assert result['fs'] == pytest.approx(400.0)

    def test_params_center_freq(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        result = hf.acquire_iq(center_freq=5000, span=100, fft_length=64, num_segments=5)
        assert result['params']['center_freq'] == 5000

    def test_params_filter_timeconstant_read_from_device(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        result = hf.acquire_iq(center_freq=1000, span=100, fft_length=64, num_segments=5)
        assert result['params']['filter_timeconstant'] == pytest.approx(1.384e-4, rel=1e-6)

    def test_daq_spectrum_enable_zero(self):
        hf, daq = self._make_hf2li_with_mock_daq()
        hf.acquire_iq(center_freq=1000, span=100, fft_length=64, num_segments=5)
        daq.spectrum.enable.assert_any_call(0)

    def test_daq_grid_cols_set(self):
        hf, daq = self._make_hf2li_with_mock_daq(fft_length=128)
        hf.acquire_iq(center_freq=1000, span=100, fft_length=128, num_segments=5)
        daq.grid.cols.assert_any_call(128)

    def test_daq_grid_rows_set(self):
        hf, daq = self._make_hf2li_with_mock_daq(num_segments=7)
        hf.acquire_iq(center_freq=1000, span=100, fft_length=64, num_segments=7)
        daq.grid.rows.assert_any_call(7)

    def test_demodulator_rate_set(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        hf.acquire_iq(center_freq=1000, span=150, fft_length=64, num_segments=5)
        hf.device.demods[0].rate.assert_called_with(300)

    def test_filter_bandwidth_sets_timeconstant(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        hf.acquire_iq(center_freq=1000, span=100, fft_length=64, num_segments=5,
                      filter_order=4, filter_bandwidth_hz=500.0)
        expected_tc = bandwidth_to_tc(500.0, 4)
        hf.device.demods[0].timeconstant.assert_any_call(pytest.approx(expected_tc, rel=1e-6))

    def test_filter_bandwidth_none_no_timeconstant_write(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        hf.acquire_iq(center_freq=1000, span=100, fft_length=64, num_segments=5,
                      filter_bandwidth_hz=None)
        # timeconstant() is called once to read back the value, but never called with a float arg
        calls_with_args = [c for c in hf.device.demods[0].timeconstant.call_args_list if c.args]
        assert len(calls_with_args) == 0

    def test_no_data_raises(self):
        hf = HF2LI()
        hf.device = _mock_device()
        hf.session = MagicMock()
        daq_module = MagicMock()
        hf.session.modules.daq = daq_module
        daq_module.finished.return_value = True
        daq_module.read.return_value = {}
        hf.device.demods[0].timeconstant.return_value = 1.384e-4

        with pytest.raises(RuntimeError, match="no IQ data"):
            hf.acquire_iq(center_freq=1000, span=100, fft_length=64, num_segments=5)

    def test_save_without_filepath_raises(self):
        hf, _ = self._make_hf2li_with_mock_daq()
        with pytest.raises(ValueError, match="filepath must be set"):
            hf.acquire_iq(center_freq=1000, span=100, fft_length=64, num_segments=5,
                          save=True, filepath=None)


# ===========================================================================
# HF2LI.get_demod_filter_response tests
# ===========================================================================

class TestGetDemodFilterResponse:
    def _make_hf2li(self, tc=1.384e-4, order=4):
        hf = HF2LI()
        hf.device = _mock_device()
        hf.device.demods[0].timeconstant.return_value = tc
        hf.device.demods[0].order.return_value = order
        return hf

    def test_dc_gain_is_one(self):
        hf = self._make_hf2li()
        H = hf.get_demod_filter_response([0.0])
        assert abs(H[0]) == pytest.approx(1.0, rel=1e-9)

    def test_magnitude_rolls_off_at_high_freq(self):
        hf = self._make_hf2li(tc=1e-3, order=1)
        H = hf.get_demod_filter_response([0.0, 1000.0])
        assert abs(H[1]) < abs(H[0])

    def test_order4_steeper_than_order1(self):
        freqs = np.array([500.0])
        hf1 = self._make_hf2li(tc=1e-3, order=1)
        hf4 = self._make_hf2li(tc=1e-3, order=4)
        assert abs(hf4.get_demod_filter_response(freqs)[0]) < abs(hf1.get_demod_filter_response(freqs)[0])

    def test_reads_tc_and_order_from_device(self):
        hf = self._make_hf2li(tc=2e-4, order=2)
        hf.get_demod_filter_response([0.0, 100.0])
        hf.device.demods[0].timeconstant.assert_called_once()
        hf.device.demods[0].order.assert_called_once()

    def test_output_shape(self):
        hf = self._make_hf2li()
        freqs = np.linspace(-100, 100, 50)
        H = hf.get_demod_filter_response(freqs)
        assert H.shape == (50,)
