"""
Base class for Zurich Instruments devices using zhinst.toolkit.

Mirrors the Device_Visa_Super lifecycle pattern (context manager, open/close)
while wrapping zhinst.toolkit.Session for Zurich-specific device control.

The raw ``self.session`` and ``self.device`` attributes are exposed so users
can access the full zhinst.toolkit API when the convenience methods are not
enough.
"""

from zhinst.toolkit import Session


class ZurichDevice:
    """
    Base class for Zurich Instruments device control via zhinst.toolkit.

    Parameters
    ----------
    device_id : str
        Device serial string (e.g. ``'dev1374'``).
    server_host : str, optional
        LabOne Data Server hostname. Default is ``'localhost'``.
    port : int, optional
        LabOne Data Server port. Default is 8004.
    """

    def __init__(self, device_id, server_host="localhost", port=8004):
        self.device_id = device_id
        self.server_host = server_host
        self.port = port
        self.session = None
        self.device = None

    def open(self):
        """
        Open a session to the LabOne Data Server and connect to the device.

        Returns
        -------
        ZurichDevice
            Returns ``self`` for chaining and ``with`` block usage.
        """
        self.session = Session(self.server_host, self.port)
        self.device = self.session.connect_device(self.device_id)
        print(f"Connected to {self.device.device_type} — serial: {self.device.serial}")
        return self

    def close(self):
        """Disconnect the device and clean up the session."""
        if self.device is not None:
            self.session.disconnect_device(self.device_id)
            self.device = None
        self.session = None
        print("Device disconnected")

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    @staticmethod
    def connected_devices(server_host="localhost", port=8004):
        """
        List device IDs visible to the LabOne Data Server.

        Parameters
        ----------
        server_host : str, optional
            Data Server hostname. Default is ``'localhost'``.
        port : int, optional
            Data Server port. Default is 8004.

        Returns
        -------
        list of str
            Device ID strings visible to the server.
        """
        session = Session(server_host, port)
        return session.devices.visible()
