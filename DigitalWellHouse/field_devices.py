from constants import (
    COIL_CHLORINE_INJ_PUMP,
    FC_COILS,
    )


class FieldDevices:

    def __init__(self, pump, process):
        self.pump = pump
        self.process = process

        # Flow Path Devices
        self.pump_control_valve = False  # NC pump control valve
        self.flow_meter = self.process.flow_gpm  # reads flow going to system only

        # Chemical Treatment Devices
        self.chlorine_generator = False
        self.chlorine_inj_pump = False

        # Protection / Safety Devices
        self.pressure_transducer = 0
        self.pressure_relief = False

    def chlorine_inj_pump_on(self):  # decide whether inj pump on/off and stores in coil 4
        self.chlorine_inj_pump = bool(self.pump.pump_running)
        return self.chlorine_inj_pump

    def write_device_coils(self, store):
        store.setValues(FC_COILS, COIL_CHLORINE_INJ_PUMP, [int(self.chlorine_inj_pump)])
