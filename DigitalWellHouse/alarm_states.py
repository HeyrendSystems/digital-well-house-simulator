delta_time = .5

class AlarmStates:

    def __init__(self, process, pump):
        self.process = process
        self.pump = pump
        self.fault_unlatch = False
        self.double_permit = 0
        self.pump_off_count_down = 0
        

    def tank_lvl_low_alarm(self,store):   # writes low tank lvl into coil 10
        coil_low_tank_lvl = 11
        tank_lvl_low = self.process.tank_lvl < 250
        store.setValues(1,coil_low_tank_lvl,[int(tank_lvl_low)])
        return tank_lvl_low
    
    def tank_lvl_low_low_alarm(self, store):
        coil_low_low_tank_lvl = 12
        tank_lvl_low_low = self.process.tank_lvl < 100
        store.setValues(1, coil_low_low_tank_lvl, [int(tank_lvl_low_low)]) # writes low low tank alarm in coil 11
        return tank_lvl_low_low
    
    def tank_lvl_hi_alarm(self,store):   # writes high tank level alarm to coil 12
        coil_tank_lvl_hi = 13
        tank_lvl_hi = self.process.tank_lvl > 900
        store.setValues(1,coil_tank_lvl_hi,[int(tank_lvl_hi)])
        return tank_lvl_hi
    
    def tank_lvl_hi_hi_alarm(self,store):   # writes high tank level alarm to coil 13
        coil_tank_lvl_hi_hi = 14
        tank_lvl_hi_hi = self.process.tank_lvl > 950
        store.setValues(1,coil_tank_lvl_hi_hi,[int(tank_lvl_hi_hi)])
        return tank_lvl_hi_hi
    
    def low_psi_alarm(self, store):
        low_psi = self.process.actual_psi < 400
        if low_psi:
            self.pump.pump_on = True
            store.setValues(1,15,[int(low_psi)])
            store.setValues(1,0,[self.pump.pump_on]) # writes low psi alarm in coil 14
        if not low_psi:
            low_psi = False
            store.setValues(1,15,[int(low_psi)])
        return low_psi, self.pump.pump_on
    
    def low_low_psi_alarm(self,store):
        coil_low_low_psi = 16
        low_low_psi = self.process.actual_psi < 200
        store.setValues(1,coil_low_low_psi,[int(low_low_psi)]) # writes low low psi alarm in coil 15
        return low_low_psi
    
    def high_psi_alarm(self, store):
        coil_high_psi = 17
        high_psi = self.process.actual_psi > 700
        store.setValues(1,coil_high_psi,[int(high_psi)]) # writes high psi alarm in coil 16
        return high_psi
    
    def high_high_psi_alarm(self,store):
        coil_high_high_psi = 18
        high_high_psi = self.process.actual_psi > 800
        store.setValues(1,coil_high_high_psi,[int(high_high_psi)]) # writes high high psi alarm in coil 17
        return high_high_psi
    
    def pump_fault_unlatch(self, store):
        coil_pump_cmd = 0
        pump_flt_unlatch = 19
        if self.pump.pump_flt:                     # store False value in coil 18 Pump Fault Unlatch
            reset = store.getValues(1,pump_flt_unlatch,1)[0]      # checks if Pump Fault Unlatch True
            if reset:                              # checks if Pump Fault Unlatch True Pump Fault True
                self.pump.pump_flt = False
                self.pump.pump_on = False
                store.setValues(1,coil_pump_cmd,[int(self.pump.pump_on)])
                reset = False
                store.setValues(1,pump_flt_unlatch,[int(reset)])
        else: 
            reset = False
            store.setValues(1,pump_flt_unlatch,[int(reset)])
        return self.pump.pump_flt
    
    def pump_run_permit_ok(self,store):
        if self.pump.pump_on and self.process.flow_gpm < 300 and not self.pump.pump_flt:
            self.pump_off_count_down += delta_time

        if self.pump_off_count_down > 40 and self.process.flow_gpm < 300:
            self.pump.pump_run_permit = False
        if self.pump.pump_run_permit == False:
            self.pump_off_count_down = 0
            store.setValues(1,0,[0])
            self.pump.pump_run_permit = True



        return self.pump.pump_run_permit, self.pump_off_count_down
        