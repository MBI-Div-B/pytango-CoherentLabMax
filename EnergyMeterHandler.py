#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Copyright (C) 2020  MBI-Division-B
# MIT License, refer to LICENSE file



import serial
import time


class EnergyMeterHandler(object):
    def __init__(self, port, baud_rate=115200, timeout=0.5):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.create_serial_port()

    def create_serial_port(self):

        self._port = serial.Serial(
            port=self.port,
            baudrate=self.baud_rate,
            timeout=self.timeout,
            xonxoff=True)

    def sendcmd(self, command, argument=None):
        """
        Send the specified command along with the argument, if any.
        :param command:
        :param argument:
        :return:
        """
        if self._port is None:
            return

        if argument is not None:
            tosend = command + ' ' + argument
        else:
            tosend = command
        self._port.write(tosend)

    def clean_out(self, inp):
        '''
        gets the usefull data from the query
        '''
        return str(inp).strip().replace("\\r\\n'",'').replace("b'",'').split(',')

    def get_energy_n(self):
        """
        Reads energy meter
        :return: 
        """
        self._port.flush()
        time.sleep(0.1)
        self.sendcmd('INIT\n'.encode())
        time.sleep(0.1)
        self.sendcmd('FETC:NEXT?\n'.encode())
        time.sleep(0.1)
        energy = self._readline(32)
        energy = str(energy).strip().replace("\\r\\n'",'').replace("b'",'').split(',')
        energy_nj = float(energy[0])
        
        return energy_nj, energy[1], int(energy[2])

    def _readline(self, read_bytes=None):
        """
        Returns the number of bytes read from the serial.
        """
        if read_bytes is None:
            read_bytes = 1

        try:
            line = self._port.read(read_bytes)
        except:
            line = 0

        return line

    def set_value_energy_meter(self, set_command, value=''):
        """
        :param set_command: command or property to set
        :param value: Value of the parameter to be set
        :return: None
        """
        self.sendcmd(set_command.encode() + ' '.encode() + value.encode() + '\n'.encode())

    def get_value_energy_meter(self, get_command, bytes_to_read=1):
        """
        :param ser_port: energy meter serial port object
        :param get_command: command or property to read
        :param bytes_to_read: Number of bytes expected to be read
        :return:
        """
        self._port.reset_input_buffer()
        self.sendcmd(get_command.encode() + '\n'.encode())
        read_value = self._readline(bytes_to_read)
        return read_value

    def zero(self):

        self.set_value_energy_meter('CONF:ZERO')

    def get_sensor_type(self):
        sens_type = self.clean_out(self.get_value_energy_meter('SYST:INF:PROB:TYPE?', 20))[0]
        return sens_type

    def set_display_mode(self, inp):
        self.set_value_energy_meter('CONF:DISP:PRI')

    def check_stat_data(self):
        a = int(self.clean_out(self.get_value_energy_meter('STAT:FETCH:NREC?', 10))[0])
        if a >= 1:
            return True
        else:
            self.set_value_energy_meter("CONF:STAT:STAR")
            return False
        
    def get_stat_data(self):
        data = self.clean_out(self.get_value_energy_meter('STAT:FETCH:NEXT?', 80))
        return [float(x) for x in data]
    
    def get_measurement_mode(self):
        return self.clean_out(self.get_value_energy_meter('CONF:MEAS?', 10))
    
    def get_responsivity(self):
        
        return self.clean_out(self.get_value_energy_meter('SYST:INF:PROB:RESP?', 30))[0]
    
    def get_head_temp(self):
        return self.clean_out(self.get_value_energy_meter('SYST:INF:PROB:TEMP?', 30))[0]
    
    def get_wavel_corr(self):
        if self.clean_out(self.get_value_energy_meter('CONF:WAVE:CORR?', 30))[0] =='ON':
            return True
        else:
            return False
        
    def get_op_wavel(self):
        return self.clean_out(self.get_value_energy_meter('CONF:WAVE:WAVE?', 30))[0]            

    def get_current_range(self, min=False):
        if min is True:
            return self.clean_out(self.get_value_energy_meter('CONF:RANG:SEL? MIN', 30))[0]
        return self.clean_out(self.get_value_energy_meter('CONF:RANG:SEL?', 30))[0]

    def get_auto_range(self):
        a = self.clean_out(self.get_value_energy_meter('CONF:RANG:SEL?', 30))[0]
        if a == "ON":
            return True
        else:
            return False

    def is_closed(self):
        if self._port:
            return False
        else:
            return True

    def close(self):
        if self._port:
            self._port.close()
            self._port = None

    def __del__(self):
        self.close()
