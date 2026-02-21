import random
from constants import (
    FC_COILS,
    FC_HOLDING_REGISTERS,
    PUMP_INERTIA_THRESHOLD_PERCENT,
    COIL_PUMP_CMD,
    HR_VFD_SPEED_PERCENT,
    COIL_PUMP_RUNNING,
    COIL_PUMP_FAULT,
    COIL_PUMP_RUN_PERMIT,
)


class Pump:

    def __init__(self):
    # Pump state
        self.pump_on = False
        self.pump_running = False
        self.pump_flt = False
        self.pump_run_permit = True

        # Logic control
        self.pump_inertia_check = False

    def update_pump_cmd(self, store):  # checks operator ON/OFF command from coil 1
        self.pump_on = bool(store.getValues(FC_COILS, COIL_PUMP_CMD, 1)[0])

    def pump_fault(self):  # writes pump fault to coil 3
        if self.pump_on and not self.pump_flt:
            self.pump_flt = random.random() < 0.005
        elif self.pump_flt:
            self.pump_run_permit = False
        return self.pump_flt, self.pump_run_permit

    def inertia_check(self, store):
        current_vfd_speed = store.getValues(FC_HOLDING_REGISTERS, HR_VFD_SPEED_PERCENT, 1)[0]
        self.pump_inertia_check = current_vfd_speed > PUMP_INERTIA_THRESHOLD_PERCENT
        return self.pump_inertia_check

    def pump_state(self):  # writes pump state to coil 2
        self.pump_running = (
            self.pump_on and
            self.pump_run_permit and
            not self.pump_flt
            and self.pump_inertia_check
            )
        return self.pump_running

    def write_pump_coils(self, store):
        values = [
            (COIL_PUMP_RUNNING, int(self.pump_running)),  #coil 2
            (COIL_PUMP_FAULT, int(self.pump_flt)),  #coil 3
            (COIL_PUMP_RUN_PERMIT, int(self.pump_run_permit))  #coil 6
        ]

        for coil_address, value in values:
            store.setValues(FC_COILS, coil_address, [value])