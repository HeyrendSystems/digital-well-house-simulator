
delta_time = .5

class FieldDevices:
    def __init__(self, pump, process):
        self.pump = pump
        self.process = process
        self.pump_control_valve = False # NC pump control valve
        self.flow_meter = self.process.flow_gpm # reads flow going to system only, control valve must be open for flow
        self.chlorine_generator = False # always false unless tank level setpoint activates it
        self.chlorine_inj_pump = False
        self.pressure_transducer = 0
        self.pressure_relief = False

    def chlorine_inj_pump_on(self): # decide whether inj pump on/off and stores in coil 4
        self.chlorine_inj_pump = bool(self.pump.pump_running)
        return self.chlorine_inj_pump
    
    def write_device_coils(self, store):
        store.setValues(1, 3, [int(self.chlorine_inj_pump)])
