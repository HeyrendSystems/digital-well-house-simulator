
import random


delta_time = .5

class Pump:
    def __init__(self):
        self.pump_on = False
        self.pump_running = False
        self.pump_flt = False
        self.pump_run_permit = True
        self.pump_on_counter = 0
        self.pump_inertia_check = 0




    def update_pump_cmd(self, store): # checks operator ON/OFF command from coil 1
        coil_pump_cmd = 0

        self.pump_on = bool(store.getValues(1, coil_pump_cmd, 1)[0])
         

    def pump_fault(self): # writes pump fault to coil 3
        if self.pump_on and not self.pump_flt:
            self.pump_flt = random.random() < 0.005
        elif self.pump_flt:
            self.pump_run_permit = False
        return self.pump_flt, self.pump_run_permit
    
    def inertia_check(self,store):
        self.pump_inertia_check = store.getValues(3,4,1)[0] > 15
        return self.pump_inertia_check

    def pump_state(self):   # writes pump state to coil 2
        self.pump_running = bool(self.pump_on and 
                                 self.pump_run_permit == True and
                                 not self.pump_flt
                                 ) and self.pump_inertia_check
        return self.pump_running

    
    
    def write_pump_coils(self, store):
        values = [
            (1, int(self.pump_running)), #coil 2
            (2, int(self.pump_flt)), #coil 3
            (5, int(self.pump_run_permit)) #coil 6
        ]

        for i, val in values:
            store.setValues(1, i, [val])