import EnergyMeterHandler
from tango import AttrWriteType, DevState, AttrWriteType, DispLevel, DebugIt
from tango.server import Device, attribute, command, device_property
from enum import IntEnum

class units(IntEnum):
    W = 0
    J = 1

class sens(IntEnum):
    Pyroelectric = 0
    Thermophile = 1
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


    sensor_type = attribute(
        label= "Sensor Typ",
        dtype='DevString',
        access= AttrWriteType.READ
    )
    pulse_period=attribute(
        label= "Puls Periode",
        dtype='DevDouble',
        unit= 'us',
        access= AttrWriteType.READ
    )
    measure_value = attribute(
        label= "Value",
        dtype = 'DevFloat',
        unit = "W",
        access= AttrWriteType.READ,
        format="%12.12f"
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
        self._measurement_type = units.W
        self._sensor_type = self.pmSensor.get_sensor_type()
        self._pulse_period = 1
        self.pmSensor.set_value_energy_meter('CONF:READ:SEND','PRI,UNIT,PER')
        self.pmSensor.set_value_energy_meter('CONF:READ:CONT','LAST')
        
        self.debug_stream(self.pmSensor.get_value_energy_meter('CONF:READ:SEND?',bytes_to_read=10))
        self.set_state(DevState.ON)


    #def allways_execute_hook():

    def read_measure_value(self):
        self._measure_value, measure_unit , self._pulse_period = self.pmSensor.get_energy_n()
        self.info_stream(str(self._measure_value))
        self.info_stream(str(measure_unit))
        self.info_stream(str(self._pulse_period))
        self.measure_value.set_value(self._measure_value)
        return self._measure_value
    
    def read_measurement_type(self):
        #self._measurement_type = units[self.pmSensor.get_value_energy_meter('CONF:MEAS?',bytes_to_read=1)]
        return self._measurement_type
    
    def write_measurement_type(self, inp):
        self.debug_stream(self.pmSensor.get_value_energy_meter('CONF:MEAS?',bytes_to_read=10))
        if inp != self._measurement_type.value:
            self.info_stream('in cond')

            if inp==1:
                a = 'J'
                change_prop = self.measure_value.get_properties()
                change_prop.unit = "J"
                
                self.measure_value.set_properties(change_prop)
            else:
                a='W'
                change_prop = self.measure_value.get_properties()
                change_prop.unit = "J" #W
                self.measure_value.set_properties(change_prop)
            self.pmSensor.set_value_energy_meter('CONF:MEAS',a)
            self._measurement_type = units(inp)
            self.measurement_type.set_value(units(inp))

    def read_sensor_type(self):
        self._sensor_type = self.pmSensor.get_sensor_type()
        self.sensor_type.set_value(self._sensor_type)
        return self._sensor_type
    
    def read_pulse_period(self):
        self.pulse_period.set_value(self._pulse_period)
        return self._sensor_type
    

    @command()
    def zero(self):
        self.pmSensor.zero()
    '''
    @command(
        dtype_in = 'String'
    )
    def change_units(self,unt):
        if unt.value==0:
            a = 'J'
            self.measure_value.set_display_unit("nJ")
        else:
            a='W'
            self.measure_value.set_display_unit("nW")
        self.pmSensor.set_value_energy_meter('CONF:MEAS',a)
        '''

if __name__ == "__main__":
    CoherentLabMaxTop.run_server()