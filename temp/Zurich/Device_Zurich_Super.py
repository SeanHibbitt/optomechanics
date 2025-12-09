"""
A Class to handle non-device specific Zurich Instruments, LabOne Communications.
To be inheritted by indivdual device classes

"""

from zhinst.toolkit import Session
device_id = 'dev1374'
apilevel = 6

class zuirch():

    """
    useful links:
    https://docs.zhinst.com/zhinst-toolkit/en/latest/examples/common_device.html
    """
    def __init__(self, address = "localhost",):
        self.address   = address

    def open_session(self):
        self.session = Session(self.address)





class device():
    """
    Make instances of this class to connect to specific devices via the device_id

    useful commands:
    list(device.child_nodes())
    list(device.demods[0].child_nodes(recursive=True))
    with device.set_transaction():
    device.demods["*"].enable(1)
    device.demods[1].harmonic(3)
    device.demods[0].harmonic(2)
    device.demods[0].rate(2000)
    """

    def __init__(self, session,device_id):
        """
        session:
        Session argument created via the zurich class

        device_id = 'devXXXX', e.g dev1374
        """
        self.session = session
        self.device_id = device_id

    def open_device(self):
        """
        Open a specific device via the device id
        """
        self.device = self._session.connect_device(self.device_id) 
        print(self.device.serial)
        print(self.device.device_type)

    def close_device(self, device_id):
        self.device.disconnect_device(device_id)

    

    def scope():
        """
        https://docs.zhinst.com/labone_api_user_manual/modules/scope/index.html
        
        """

    