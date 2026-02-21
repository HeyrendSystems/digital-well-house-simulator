from constants import (
    DEADBAND,
    DELTA_TIME_S,
    FC_HOLDING_REGISTERS,
    FLOW_GAIN,
    MAX_CHEM_GPM_AT_MAX_FLOW,
    MAX_FLOW_GPM,
    MIN_PROCESS_VALUE,
    MINUTES_IN_DAY,
    VFD_ERROR_GAIN_DIVISOR,
    VFD_MAX_PERCENT,
    VFD_MIN_PERCENT,
    VFD_SAFETY_MARGIN_PERCENT,
)


class ProcessSim:

    def __init__(self, process, pump, device):
        self.process = process
        self.pump = pump
        self.device = device

        # Simulation clock
        self.sim_clock = 0
        self.sim_clock_delta = 1
        self.sim_minute = 0
        self.sim_hour = 0
        self.sim_day = 0

        # Control dynamics
        self.command = 0
        self.accel_time = 0.2
        self.new_vfd_speed = 0

        # Random disturbance counters
        self.rng_down_count = 0
        self.rng_up_count = 0

        # Scan state
        self.first_scan = True

    def first_scan_items(self, store):
        if self.first_scan:
            store.setValues(FC_HOLDING_REGISTERS, 8, [550])
            self.first_scan = False

    def sim_time(self):
        self.sim_clock += self.sim_clock_delta
        if self.sim_clock == 60:  # can be adjusted to 60 for faster sim
            self.sim_minute += 1
            self.sim_clock = 0

            if self.sim_minute % 60 == 0:
                self.sim_hour += 1

                if self.sim_hour % 24 == 0:
                    self.sim_day += 1

        return self.sim_minute, self.sim_hour, self.sim_day

    def sim_time_holding_registers(self, store):
        store.setValues(FC_HOLDING_REGISTERS, 21, [int(self.sim_minute)])
        store.setValues(FC_HOLDING_REGISTERS, 22, [int(self.sim_hour)])
        store.setValues(FC_HOLDING_REGISTERS, 23, [int(self.sim_day)])

    def _in_deadband(self):
        upper = self.process.operator_vfd_setpoint + DEADBAND
        lower = self.process.operator_vfd_setpoint - DEADBAND
        return lower <= self.process.actual_psi <= upper

    def vfd_command(self):
        error = ((self.process.operator_vfd_setpoint - self.process.actual_psi) * self.accel_time * DELTA_TIME_S) / VFD_ERROR_GAIN_DIVISOR
        self.new_vfd_speed = (self.command - self.process.vfd_pump_speed_control) * self.accel_time * DELTA_TIME_S
        self.pump.run_enable = not self.pump.pump_flt
        target = self._in_deadband()
        vfd_upper_trigger = VFD_MAX_PERCENT - VFD_SAFETY_MARGIN_PERCENT
        vfd_lower_trigger = VFD_MIN_PERCENT + VFD_SAFETY_MARGIN_PERCENT

        if self.pump.pump_on and self.pump.pump_flt:
            self.pump.pump_on = False  # intentional off command
            self.command = MIN_PROCESS_VALUE
            self.process.vfd_pump_speed_control += self.new_vfd_speed

        elif (self.pump.pump_on and target) or (self.process.flow_gpm == MAX_FLOW_GPM):
            pass

        elif self.pump.pump_on and not target:
            self.process.vfd_pump_speed_control += error

        elif not self.pump.pump_on or not self.pump.pump_running or self.pump.pump_flt:
            self.command = MIN_PROCESS_VALUE
            self.process.vfd_pump_speed_control += self.new_vfd_speed

            if self.process.vfd_pump_speed_control < MIN_PROCESS_VALUE:
                self.process.vfd_pump_speed_control = MIN_PROCESS_VALUE

        if self.process.vfd_pump_speed_control > vfd_upper_trigger:
            self.process.vfd_pump_speed_control = VFD_MAX_PERCENT

        if self.process.vfd_pump_speed_control < vfd_lower_trigger:
            self.process.vfd_pump_speed_control = VFD_MIN_PERCENT
        return self.process.vfd_pump_speed_control, self.process.actual_psi, self.process.vfd_set_point

    def update_flow_gpm(self):
        self.pump.run_enable = not self.pump.pump_flt
        target = self._in_deadband()
        pump_capability = self.process.total_head_psi
        system_requirement = self.process.system_required_psi
        zero_flow_zone = pump_capability < system_requirement
        delta = pump_capability - system_requirement

        if self.pump.pump_on and self.pump.pump_running and not target:
            self.process.flow_gpm += (FLOW_GAIN * delta * DELTA_TIME_S)

        elif self.pump.pump_on and target:
            pass

        elif not self.pump.pump_running:
            self.process.flow_gpm = self.process.flow_gpm * (self.process.vfd_pump_speed_control / VFD_MAX_PERCENT)

        elif zero_flow_zone and not self.pump.pump_flt:
            self.process.flow_gpm = MIN_PROCESS_VALUE

        if self.process.flow_gpm < MIN_PROCESS_VALUE:
            self.process.flow_gpm = MIN_PROCESS_VALUE

        elif self.process.flow_gpm > MAX_FLOW_GPM:
            self.process.flow_gpm = MAX_FLOW_GPM

        return self.process.flow_gpm

    def update_chemical_dose_gph(self):  #GPH = 1.125 and GPM = 0.0183 relative to system flow gpm 1550 is max GPM in this SIM

        if self.device.chlorine_inj_pump:
            self.process.chemical_dose_gpd = (((MAX_CHEM_GPM_AT_MAX_FLOW / MAX_FLOW_GPM) * self.process.flow_gpm) * MINUTES_IN_DAY)  ## scaled to GPD for holding register, calc to GPM in NODE-RED
        else:
            self.process.chemical_dose_gpd = MIN_PROCESS_VALUE
        return self.process.chemical_dose_gpd
