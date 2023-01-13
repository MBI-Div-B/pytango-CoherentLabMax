import EnergyMeterHandler
from tango import AttrWriteType, DevState, AttrWriteType, DispLevel, DebugIt
from tango.server import Device, attribute, command, device_property
from enum import IntEnum


class unit_conv(IntEnum):
    J = 0
    mJ = 1
    uJ = 2
    nJ = 3
    W = 4
    mW = 5
    uW = 6
    nW = 7

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


    
    unit_adj= attribute(
        label= 'Convert Units',
        dtype= unit_conv,
        access= AttrWriteType.READ_WRITE
    )
    adj_fact = attribute(
        label= 'Adjustment Factor',
        dtype= 'DevFloat',
        access= AttrWriteType.READ_WRITE
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
        label= "Live Reading",
        dtype = 'DevFloat',
        unit = "J",
        access= AttrWriteType.READ,
        format="%16.16f"
    )

    mean_value = attribute(
        label= "Mean Value",
        dtype = 'DevFloat',
        unit = "J",
        access= AttrWriteType.READ,
        format="%16.16f"
    )
    std_value = attribute(
        label= "Standard Div.",
        dtype = 'DevFloat',
        unit = "J",
        access= AttrWriteType.READ,
        format="%16.16f"
    )
    min_value = attribute(
        label= "Min Value",
        dtype = 'DevFloat',
        unit = "J",
        access= AttrWriteType.READ,
        format="%16.16f"
    )
    max_value = attribute(
        label= "Max Value",
        dtype = 'DevFloat',
        unit = "J",
        access= AttrWriteType.READ,
        format="%16.16f"
    )
    
    sample_duration = attribute(
        label = 'Sample duration',
        dtype = 'DevDouble',
        unit = 'Pulses',
        access= AttrWriteType.READ_WRITE,
    )
    sampling_rate = attribute(
        label = 'Sampling rate',
        dtype = 'DevDouble',
        unit = 'Pulses',
        access= AttrWriteType.READ_WRITE,
    )
    

    def init_device(self):
        Device.init_device(self)
        self.set_state(DevState.INIT)
        self.pmSensor = EnergyMeterHandler.EnergyMeterHandler(self.Port,baud_rate=self.Baudrate)
        self._mean_value = 0.0
        self._std_value =0.0
        self._min_value = 0.0
        self._max_value = 0.0
        self._measure_value = 0.0
        self._unit_fact = 1
        self._adj_fact = 1
        self._unit_adj= unit_conv.J
        for i in [self.measure_value,self.mean_value,self.std_value,self.min_value,self.max_value]:
            self.change_unit(i,'J')

        self._sensor_type = self.pmSensor.get_sensor_type()
        self._pulse_period = 1

        self._sample_duration = 100
        self.pmSensor.set_value_energy_meter('CONF:STAT:BSIZ:PULS', '100') #sets batch size

        self._sampling_rate = 1
        self.pmSensor.set_value_energy_meter('CONF:STAT:RATE:PULS', '1') #sets sampling rate

        self.pmSensor.set_value_energy_meter('CONF:DISP:STAT')
        #self.pmSensor.set_value_energy_meter('SYS:COMM:SER:BAUD',str(self.Baudrate))
        self.pmSensor.set_value_energy_meter('STAT:INIT')
        self.pmSensor.set_value_energy_meter('CONF:STAT:RMO','AUT')
        self.pmSensor.set_value_energy_meter('CONF:STAT:STAR')
        self.pmSensor.set_value_energy_meter('CONF:READ:HEAD','OFF')
        self.pmSensor.set_value_energy_meter('CONF:STAT:DISP','MEAN,MIN,MAX,STDV')


        self.pmSensor.set_value_energy_meter('CONF:READ:SEND','PRI,UNIT,PER')
        self.pmSensor.set_value_energy_meter('CONF:READ:CONT','LAST')
        
        
        self.debug_stream(self.pmSensor.get_value_energy_meter('CONF:READ:SEND?',bytes_to_read=10))
        self.set_state(DevState.ON)


    def allways_execute_hook(self):
        #self.pmSensor.set_value_energy_meter('CONF:DISP:STAT')
        #self.pmSensor.set_value_energy_meter('INIT')
        self.pmSensor.set_value_energy_meter('STAT:INIT')

    def read_measure_value(self):
        self._measure_value, measure_unit , self._pulse_period = self.pmSensor.get_energy_n()
        #self.info_stream(str(self._measure_value))
        #self.info_stream(str(measure_unit))
        #self.info_stream(str(self._pulse_period))
        #self.measure_value.set_value(self._measure_value)
        return self._measure_value* self._unit_fact*self._adj_fact
    


    def read_sensor_type(self):
        self._sensor_type = self.pmSensor.get_sensor_type()
        self.sensor_type.set_value(self._sensor_type)
        return self._sensor_type
    
    def read_pulse_period(self):
        self.pulse_period.set_value(self._pulse_period)
        return self._sensor_type
    
    def read_sample_duration(self):
        #fehlt aktualisierung 
        return self._sample_duration
    
    def write_sample_duration(self, value):
        #self.debug_stream(str(value))
        self.pmSensor.set_value_energy_meter('CONF:STAT:BSIZ:PULS', str(int(value)))
        self._sample_duration = value

    def read_sampling_rate(self):
        #fehlt aktualisierung 
        return self._sampling_rate
    
    def write_sampling_rate(self, value):
        self.pmSensor.set_value_energy_meter('CONF:STAT:RATE:PULS', str(int(value)))
        self._sampling_rate = value

    def read_mean_value(self):
        self.debug_stream(str(self.pmSensor.check_stat_data()))
        if self.pmSensor.check_stat_data():
            self.debug_stream('data aqusition')
            a = self.pmSensor.get_stat_data()
            self.debug_stream(str(a))
            self._mean_value = a[0]
            self._std_value = a[1]
            self._min_value = a[2]
            self._max_value = a[3]
            
        
        return self._mean_value* self._unit_fact*self._adj_fact
    def read_std_value(self):
        return self._std_value* self._unit_fact*self._adj_fact
    def read_min_value(self):
        return self._min_value* self._unit_fact*self._adj_fact
    def read_max_value(self):
        return self._max_value* self._unit_fact*self._adj_fact
    
    def write_unit_adj(self,inp):
        self._unit_fact = 10**(3*(inp%4))
        for i in [self.measure_value,self.mean_value,self.std_value,self.min_value,self.max_value]:
            self.change_unit(i,unit_conv(inp).name)
        if inp < 4:
            self.pmSensor.set_value_energy_meter('CONF:MEAS','J')
        else:
            self.pmSensor.set_value_energy_meter('CONF:MEAS','W')
        self._unit_adj = unit_conv(inp)


    def read_unit_adj(self):
        return  self._unit_adj

    def change_unit(self, attr, u):
        change_prop = attr.get_properties()
        change_prop.unit = u
        attr.set_properties(change_prop)

    def write_adj_fact(self,fact):
        self._adj_fact = fact
    
    def read_adj_fact(self):
        return self._adj_fact


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