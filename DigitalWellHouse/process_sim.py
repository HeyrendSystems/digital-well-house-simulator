class ProcessSim:
    VFD_MAX_PERCENT = 100
    VFD_MIN_PERCENT = 0
    VFD_SAFETY_MARGIN_PERCENT = 2
    DEADBAND = 10
    FLOW_GAIN = 5
    MAX_FLOW_GPM = 1550
    MAX_CHEM_GPM_AT_MAX_FLOW = 0.01875
    MIN_PROCESS_VALUE = 0
    MINUTES_IN_DAY = 1440

    def __init__(self, process, pump, device):
        self.process = process
        self.device = device
        self.pump = pump
        self.delta_time = .5
        self.sim_clock = 0
        self.sim_clock_delta = 1
        self.sim_minute = 0
        self.sim_hour = 0
        self.sim_day = 0
        self.rng_down_count = 0
        self.rng_up_count = 0
        self.command = 0
        self.accel_time = .2
        self.first_scan = True
        self.new_vfd_speed = 0
    

    def first_scan_items(self, store):
        if self.first_scan:
            store.setValues(3,8,[550])
            self.first_scan = False

        
    def sim_time(self):
        self.sim_clock += self.sim_clock_delta
        if self.sim_clock == 60: # can be adjusted to 60 for faster sim
            self.sim_minute += 1
            self.sim_clock = 0
            if self.sim_minute % 60 == 0:
                self.sim_hour += 1
                if self.sim_hour % 24 == 0:
                    self.sim_day +=1
        return self.sim_minute, self.sim_hour, self.sim_day
    
    def sim_time_holding_registers(self, store):
        store.setValues(3,21,[int(self.sim_minute)])
        store.setValues(3,22,[int(self.sim_hour)])
        store.setValues(3,23,[int(self.sim_day)])

    def _in_deadband(self):
        upper = self.process.operator_vfd_setpoint + self.DEADBAND
        lower = self.process.operator_vfd_setpoint - self.DEADBAND
        return lower <= self.process.actual_psi <= upper


    def vfd_command(self):
        error = ((self.process.operator_vfd_setpoint - self.process.actual_psi) * self.accel_time * self.delta_time)/5
        self.new_vfd_speed = (self.command - self.process.vfd_pump_speed_control) * self.accel_time * self.delta_time
        self.pump.run_enable = not self.pump.pump_flt
        target = self._in_deadband()
        VFD_UPPER_TRIGGER = self.VFD_MAX_PERCENT - self.VFD_SAFETY_MARGIN_PERCENT
        VFD_LOWER_TRIGGER = self.VFD_MIN_PERCENT + self.VFD_SAFETY_MARGIN_PERCENT

        if self.pump.pump_on and self.pump.pump_flt:
            self.pump_on = False # intentional off command
            self.command = self.MIN_PROCESS_VALUE
            self.process.vfd_pump_speed_control += self.new_vfd_speed

        elif (self.pump.pump_on and target) or (self.process.flow_gpm == self.MAX_FLOW_GPM):
            pass

        elif self.pump.pump_on and not target:
            self.process.vfd_pump_speed_control += error

        elif not self.pump.pump_on or not self.pump.pump_running or self.pump.pump_flt:
            self.command = self.MIN_PROCESS_VALUE
            self.process.vfd_pump_speed_control += self.new_vfd_speed
            if self.process.vfd_pump_speed_control < self.MIN_PROCESS_VALUE:
                self.process.vfd_pump_speed_control = self.MIN_PROCESS_VALUE
        
        if self.process.vfd_pump_speed_control > VFD_UPPER_TRIGGER:
            self.process.vfd_pump_speed_control = self.VFD_MAX_PERCENT 

        if self.process.vfd_pump_speed_control < VFD_LOWER_TRIGGER:
            self.process.vfd_pump_speed_control = self.VFD_MIN_PERCENT
        return self.process.vfd_pump_speed_control, self.process.actual_psi, self.process.vfd_set_point    
    

    def update_flow_gpm(self):
        self.pump.run_enable = not self.pump.pump_flt
        target = self._in_deadband()
        pump_capability = self.process.total_head_psi
        system_requirement = self.process.system_required_psi 
        zero_flow_zone = pump_capability < system_requirement
        delta = pump_capability - system_requirement

        if self.pump.pump_on and self.pump.pump_running and not target:
            self.process.flow_gpm += (self.FLOW_GAIN * delta * self.delta_time)
        elif self.pump.pump_on and target:
            pass
        elif not self.pump.pump_running:
            self.process.flow_gpm = self.process.flow_gpm * (self.process.vfd_pump_speed_control/100)
        elif zero_flow_zone and not self.pump.pump_flt:
            self.process.flow_gpm = self.MIN_PROCESS_VALUE

        if self.process.flow_gpm < self.MIN_PROCESS_VALUE:
            self.process.flow_gpm = self.MIN_PROCESS_VALUE
        elif self.process.flow_gpm > self.MAX_FLOW_GPM:
            self.process.flow_gpm = self.MAX_FLOW_GPM
        return self.process.flow_gpm
        
    def update_chemical_dose_gph(self):  #GPH = 1.125 and GPM = 0.0183 relative to system flow gpm 1550 is max GPM in this SIM

        if self.device.chlorine_inj_pump:
            self.process.chemical_dose_gpd = (((self.MAX_CHEM_GPM_AT_MAX_FLOW / self.MAX_FLOW_GPM) * self.process.flow_gpm) * self.MINUTES_IN_DAY)  ## scaled to GPD for holding register, calc to GPM in NODE-RED
        else:
            self.process.chemical_dose_gpd = self.MIN_PROCESS_VALUE
        return self.process.chemical_dose_gpd
