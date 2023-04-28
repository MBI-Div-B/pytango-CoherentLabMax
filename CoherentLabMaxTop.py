#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Copyright (C) 2020  MBI-Division-B
# MIT License, refer to LICENSE file
# Author: Luca Barbera / Email: barbera@mbi-berlin.de


import EnergyMeterHandler
from tango import AttrWriteType, DevState, DispLevel, DebugIt
from tango.server import Device, attribute, command, device_property
from enum import IntEnum
from serial import SerialException
import math


class unit_conv(IntEnum):
    J = 0
    mJ = 1
    uJ = 2
    nJ = 3
    W = 4
    mW = 5
    uW = 6
    nW = 7


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

    unit_adj = attribute(
        label='Convert Units',
        dtype=unit_conv,
        access=AttrWriteType.READ_WRITE
    )
    adj_fact = attribute(
        label='Adjustment Factor',
        dtype='DevFloat',
        access=AttrWriteType.READ_WRITE
    )
    sensor_type = attribute(
        label="Sensor Typ",
        dtype='DevString',
        access=AttrWriteType.READ
    )
    pulse_period = attribute(
        label="Puls Periode",
        dtype='DevLong',
        unit='us',
        access=AttrWriteType.READ
    )
    measure_value = attribute(
        label="Live Reading",
        dtype='DevFloat',
        unit="J",
        access=AttrWriteType.READ,
        format="%16.16f"
    )
    mean_value = attribute(
        label="Mean Value",
        dtype='DevFloat',
        unit="J",
        access=AttrWriteType.READ,
        format="%16.16f"
    )
    std_value = attribute(
        label="Standard Div.",
        dtype='DevFloat',
        unit="J",
        access=AttrWriteType.READ,
        format="%16.16f"
    )
    min_value = attribute(
        label="Min Value",
        dtype='DevFloat',
        unit="J",
        access=AttrWriteType.READ,
        format="%16.16f"
    )
    max_value = attribute(
        label="Max Value",
        dtype='DevFloat',
        unit="J",
        access=AttrWriteType.READ,
        format="%16.16f"
    )
    select_range = attribute(
        label='Max. expected measurment',
        dtype=float,
        access=AttrWriteType.READ_WRITE,
        min_value=0,
    )
    current_range = attribute(
        label='Active Range',
        dtype=float,
        access=AttrWriteType.READ
    )
    auto_range = attribute(
        label='Auto Rangeing',
        dtype='DevBoolean',
        access=AttrWriteType.READ_WRITE
    )
    sample_duration = attribute(
        label='Sample duration',
        dtype='DevLong',
        unit='Pulses',
        access=AttrWriteType.READ_WRITE,
    )
    sampling_rate = attribute(
        label='Sampling rate',
        dtype='DevLong',
        unit='Pulses',
        access=AttrWriteType.READ_WRITE,
    )
    responsivity = attribute(
        label='Resposivity',
        dtype='DevString',
        access=AttrWriteType.READ
    )
    head_temp = attribute(
        label='Head Temperature',
        dtype='DevLong',
        unit='°C',
        access=AttrWriteType.READ
    )
    wavel_corr = attribute(
        label='Wavelength Correction',
        dtype='DevBoolean',
        access=AttrWriteType.READ_WRITE
    )
    op_wavel = attribute(
        label='Operating Wavelenth',
        dtype=int,
        unit='nm',
        access=AttrWriteType.READ_WRITE
    )

    def init_device(self):
        Device.init_device(self)
        self.set_state(DevState.INIT)
        try:
            self.pmSensor = EnergyMeterHandler.EnergyMeterHandler(self.Port,
            baud_rate=self.Baudrate)
        except SerialException:
            self.set_status('can not connect to device')
            self.set_state(DevState.FAULT)
            return
        # init attribute values to not overload serial connection
        self._mean_value = 0.0
        self._std_value = 0.0
        self._min_value = 0.0
        self._max_value = 0.0
        self._measure_value = 0.0
        self._unit_fact = 1
        self._adj_fact = 1
        self._sensor_type = self.pmSensor.get_sensor_type()
        self.sensor_change()   # check sensor
        if self._sensor_type == 'PYRO':   # settings for Pyroelectric sensor
            self._unit_adj = unit_conv.J
            self.pmSensor.set_value_energy_meter('CONF:MEAS', 'J')
            for i in [self.select_range,
                        self.current_range,
                        self.measure_value,
                        self.mean_value,
                        self.std_value,
                        self.min_value,
                        self.max_value]:
                self.change_unit(i, 'J')
        elif self._sensor_type == 'NONE':
            self.set_status('no valid sensor is currently attached')
        else:   # Settings for all other sensors
            self._unit_adj = unit_conv.W
            self.pmSensor.set_value_energy_meter('CONF:MEAS', 'W')
            for i in [self.select_range,
                        self.current_range,
                        self.measure_value,
                        self.mean_value,
                        self.std_value,
                        self.min_value,
                        self.max_value]:
                self.change_unit(i, 'W')

        for i in range(5):
            try:
                self._select_range = float(self.pmSensor.get_current_range())*0.95
                break
            except ValueError:
                pass
        # meter setup
        self._responivity = self.pmSensor.get_responsivity()
        self._pulse_period = 1
        self._sample_duration = 100
        self.pmSensor.set_value_energy_meter('CONF:STAT:BSIZ:PULS', '100')   # sets batch size
        self._sampling_rate = 1
        self.pmSensor.set_value_energy_meter('CONF:RANG:AUTO', 'OFF')  # turns off auto rangeing
        self.pmSensor.set_value_energy_meter('CONF:STAT:RATE:PULS', '1')  # sets sampling rate
        self.pmSensor.set_value_energy_meter('CONF:DISP:STAT')  # sets display mode to statistics
        self.pmSensor.set_value_energy_meter('STAT:INIT')  # initiates statistcs measurement
        self.pmSensor.set_value_energy_meter('CONF:STAT:RMO', 'AUT')  # automatic restart of stat batch
        self.pmSensor.set_value_energy_meter('CONF:STAT:STAR')  # start statistics aquisition
        self.pmSensor.set_value_energy_meter('CONF:READ:HEAD', 'OFF')  # turns of the data header
        self.pmSensor.set_value_energy_meter('CONF:STAT:DISP', 'MEAN,MIN,MAX,STDV')  # sects the send statistcal data
        self.pmSensor.set_value_energy_meter('CONF:READ:SEND', 'PRI,UNIT,PER')  # sects the send current data
        self.pmSensor.set_value_energy_meter('CONF:READ:CONT', 'LAST')  # sets the buffer so only the last data entry is saved

        self.set_state(DevState.ON)

    def allways_execute_hook(self):
        self.pmSensor.set_value_energy_meter('STAT:INIT')  # makes shure the stat is running

    def sensor_change(self):
        '''
        ajusts Settings according to new sensor
        '''
        self._sensor_type = self.pmSensor.get_sensor_type()
        if self._sensor_type == 'NONE':
            self.set_status('no valid sensor is currently attached')
            self.set_state(DevState.FAULT)
            return
        self.sensor_type.set_value(self._sensor_type)
        self._responivity = self.pmSensor.get_responsivity()

        # sets the display format according to the range of the new sensor
        mi = self.pmSensor.get_current_range(min=True)
        self.pmSensor.set_value_energy_meter('CONF:RANG:SEL', str(mi))
        minR = abs(math.floor(math.log10(float(mi*self._unit_fact))))
        for i in [self.select_range, self.current_range]:
            change_prop = i.get_properties()
            change_prop.format = f"%{minR+4}.{minR+1}f"
            i.set_properties(change_prop)
        for i in [self.measure_value, self.mean_value, self.std_value, self.min_value, self.max_value]:
            change_prop = i.get_properties()
            change_prop.format = f"%{minR+5}.{minR+3}f"
            i.set_properties(change_prop)

    def read_measure_value(self):
        self._measure_value, measure_unit, self._pulse_period = self.pmSensor.get_energy_n()

        return self._measure_value * self._unit_fact * self._adj_fact

    def read_sensor_type(self):
        temp = self.pmSensor.get_sensor_type()
        if temp != self._sensor_type:  # activates if sensor is changed
            self.sensor_change()

        return self._sensor_type

    def read_pulse_period(self):
        if self._sensor_type == 'THERMO':
            return None
        self.pulse_period.set_value(self._pulse_period)
        return self._sensor_type
    
    def read_sample_duration(self):
        # fehlt aktualisierung 
        return self._sample_duration
    
    def write_sample_duration(self, value):
        # self.debug_stream(str(value))
        self.pmSensor.set_value_energy_meter('CONF:STAT:BSIZ:PULS', str(int(value)))
        self._sample_duration = value

    def read_sampling_rate(self):
        # fehlt aktualisierung 
        return self._sampling_rate
    
    def write_sampling_rate(self, value):
        self.pmSensor.set_value_energy_meter('CONF:STAT:RATE:PULS', str(int(value)))
        self._sampling_rate = value

    def read_mean_value(self):
        if self.pmSensor.check_stat_data():
            a = self.pmSensor.get_stat_data()
            self._mean_value = a[0]
            self._std_value = a[1]
            self._min_value = a[2]
            self._max_value = a[3]
        else:
            self.set_status('no Statistical data can be aquired')
            
        return self._mean_value * self._unit_fact*self._adj_fact
        
    def read_std_value(self):
        return self._std_value * self._unit_fact*self._adj_fact

    def read_min_value(self):
        return self._min_value * self._unit_fact*self._adj_fact

    def read_max_value(self):
        return self._max_value * self._unit_fact*self._adj_fact

    def write_unit_adj(self, inp):
        self._unit_fact = 10**(3*(inp%4))
        for i in [self.measure_value, self.select_range, self.current_range]:
            if self._sensor_type == 'PYRO':   
                    self.change_unit(i, (unit_conv(inp).name).replace('W', 'J'))
            else:
                self.change_unit(i, unit_conv(inp).name)
        for i in [self.mean_value, self.std_value, self.min_value, self.max_value]:
            self.change_unit(i, unit_conv(inp).name)

        if inp < 4:
            self.pmSensor.set_value_energy_meter('CONF:MEAS', 'J')
        else:
            self.pmSensor.set_value_energy_meter('CONF:MEAS', 'W')
        self._unit_adj = unit_conv(inp)

    def read_unit_adj(self):  # problem with code undefined inp needs fix
        current = self._unit_adj.name
        fut = self.pmSensor.get_measurement_mode()
        if current[-1] != fut[0]:
            for i in [self.measure_value, self.select_range, self.current_range]:
                if self._sensor_type == 'PYRO':   
                    self.change_unit(i, (unit_conv(inp).name).replace('W', 'J'))
                else:
                    self.change_unit(i, unit_conv(inp).name)
            for i in [self.mean_value, self.std_value, self.min_value, self.max_value]:
                self.change_unit(i, unit_conv(inp).name)
            
            self._unit_adj = unit_conv[fut[0]]
            self._unit_fact = 1
        return self._unit_adj

    def change_unit(self, attr, u):
        change_prop = attr.get_properties()
        change_prop.unit = u
        attr.set_properties(change_prop)

    def write_adj_fact(self, fact):
        self._adj_fact = fact
    
    def read_adj_fact(self):
        return self._adj_fact
    
    def read_responsivity(self):
        return self._responivity

    def read_head_temp(self):
        return int(self.pmSensor.get_head_temp())

    def read_wavel_corr(self):
        return self.pmSensor.get_wavel_corr()   

    def write_wavel_corr(self, inp):
        if inp is True:
            self.pmSensor.set_value_energy_meter('CONF:WAVE:CORR', 'ON')
        else:
            self.pmSensor.set_value_energy_meter('CONF:WAVE:CORR', 'OFF')

    def read_op_wavel(self):
        return int(self.pmSensor.get_op_wavel())
    
    def write_op_wavel(self, inp):
        self.pmSensor.set_value_energy_meter('CONF:WAVE:WAVE', str(inp))

    def read_current_range(self):
        return float(self.pmSensor.get_current_range())
    
    def read_select_range(self):
        return self._select_range
    
    def write_select_range(self, rang):
        self.pmSensor.set_value_energy_meter('CONF:RANG:SEL', str(rang))
        self._select_range = rang

    def read_auto_range(self):
        return self.pmSensor.get_auto_range()

    def write_auto_range(self, inp):
        if inp is True:
            self.pmSensor.set_value_energy_meter('CONF:RANG:AUTO', 'ON')
        else:
            self.pmSensor.set_value_energy_meter('CONF:RANG:AUTO', 'OFF')

    def delet_device(self):
        self.pmSensor.close() 

    @command()
    def zero(self):
        '''
        activates zeroing by the meters of the sensor'''
        if self._sensor_type == "PYRO":
            self.set_staus('zeroing has no effect on Pyroelectric sensors') 
        self.pmSensor.zero()
    

if __name__ == "__main__":
    CoherentLabMaxTop.run_server()