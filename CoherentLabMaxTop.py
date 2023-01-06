import EnergyMeterHandler
from tango import AttrWriteType, DevState, AttrWriteType, DispLevel, DebugIt
from tango.server import Device, attribute, command, device_property
from enum import IntEnum

class units(IntEnum):
    nJ = 0
    nW = 1
class CoherentLabMaxTop(Device):
    # device properties
    Port = device_property(
        dtype=str,
        default_value="COM1",
    )
    Baudrate = device_property(
        dtype=int,
        default_value=9600
    )
    measure_value = attribute(
        label= "Value",
        dtype = 'DevFloat',
        unit = "nW",
        access= AttrWriteType.READ,
        format="%10.4f"
    )
    measurement_type = attribute(
        label = 'Measumenten type',
        dtype = units,
        access= AttrWriteType.READ_WRITE
    )
    

    def init_device(self):
        Device.init_device(self)
        self.set_state(DevState.INIT)
        self.pmSensor = EnergyMeterHandler.EnergyMeterHandler(self.Port,baud_rate =self.Baudrate)
        self._measure_value = 0.0
        self._measurement_type = units.nW
        self.set_state(DevState.ON)

    def read_measure_value(self):
        self._measure_value = self.pmSensor.get_energy_n()
        self.info_stream(str(self._measure_value))
        self.measure_value.set_value(self._measure_value)
        return self._measure_value
    
    def read_measurement_type(self):
        return self._measurement_type
    def write_measurement_type(self, inp):
        self._measurement_type = units(inp).name
        if inp==0:
            a = 'J'
            change_prop = self.measure_value.get_properties()
            change_prop.unit = "nJ"
            self.measure_value.set_properties(change_prop)
        else:
            a='W'
            change_prop = self.measure_value.get_properties()
            change_prop.unit = "nW"
            self.measure_value.set_properties(change_prop)
        self.pmSensor.set_value_energy_meter('CONF:MEAS',a)

    '''
    @command(
        dtype_in = 'String'
    )
    def change_units(unt):
        if unt.value==0:
            a = 'J'
            self.measure_value.set_display_unit("nJ")
        else:
            a='W'
            self.measure_value.set_display_unit("nW")
        self.pmSensor.set_value_energy_meter('CONF:MEAS',a)'''

if __name__ == "__main__":
    CoherentLabMaxTop.run_server()