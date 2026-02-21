from constants import (
    COIL_HIGH_HIGH_PSI_ALARM,
    COIL_HIGH_PSI_ALARM,
    COIL_LOW_LOW_PSI_ALARM,
    COIL_LOW_PSI_ALARM,
    COIL_PUMP_CMD,
    COIL_PUMP_FAULT_UNLATCH,
    COIL_TANK_LEVEL_HIGH_ALARM,
    COIL_TANK_LEVEL_HIGH_HIGH_ALARM,
    COIL_TANK_LEVEL_LOW_ALARM,
    COIL_TANK_LEVEL_LOW_LOW_ALARM,
    DELTA_TIME_S,
    FC_COILS,
    HIGH_HIGH_PSI_THRESHOLD,
    HIGH_PSI_THRESHOLD,
    LOW_FLOW_THRESHOLD_GPM,
    LOW_LOW_PSI_THRESHOLD,
    LOW_PSI_THRESHOLD,
    PUMP_LOW_FLOW_TRIP_DELAY_S,
    TANK_LEVEL_HIGH_HIGH_THRESHOLD,
    TANK_LEVEL_HIGH_THRESHOLD,
    TANK_LEVEL_LOW_LOW_THRESHOLD,
    TANK_LEVEL_LOW_THRESHOLD,
)


class AlarmStates:

    def __init__(self, process, pump):
        self.process = process
        self.pump = pump

        # Counters
        self.pump_off_count_down = 0

    def tank_lvl_low_alarm(self, store):  # writes low tank lvl into coil 10
        tank_lvl_low = self.process.tank_lvl < TANK_LEVEL_LOW_THRESHOLD
        store.setValues(FC_COILS, COIL_TANK_LEVEL_LOW_ALARM, [int(tank_lvl_low)])
        return tank_lvl_low

    def tank_lvl_low_low_alarm(self, store):
        tank_lvl_low_low = self.process.tank_lvl < TANK_LEVEL_LOW_LOW_THRESHOLD
        store.setValues(FC_COILS, COIL_TANK_LEVEL_LOW_LOW_ALARM, [int(tank_lvl_low_low)])  # writes low low tank alarm in coil 11
        return tank_lvl_low_low

    def tank_lvl_hi_alarm(self, store):  # writes high tank level alarm to coil 12
        tank_lvl_hi = self.process.tank_lvl > TANK_LEVEL_HIGH_THRESHOLD
        store.setValues(FC_COILS, COIL_TANK_LEVEL_HIGH_ALARM, [int(tank_lvl_hi)])
        return tank_lvl_hi

    def tank_lvl_hi_hi_alarm(self, store):  # writes high tank level alarm to coil 13
        tank_lvl_hi_hi = self.process.tank_lvl > TANK_LEVEL_HIGH_HIGH_THRESHOLD
        store.setValues(FC_COILS, COIL_TANK_LEVEL_HIGH_HIGH_ALARM, [int(tank_lvl_hi_hi)])
        return tank_lvl_hi_hi

    def low_psi_alarm(self, store):
        low_psi = self.process.actual_psi < LOW_PSI_THRESHOLD
        if low_psi:
            self.pump.pump_on = True
            store.setValues(FC_COILS, COIL_PUMP_CMD, [self.pump.pump_on])  # writes low psi alarm in coil 14
        store.setValues(FC_COILS, COIL_LOW_PSI_ALARM, [int(low_psi)])
        return low_psi, self.pump.pump_on

    def low_low_psi_alarm(self, store):
        low_low_psi = self.process.actual_psi < LOW_LOW_PSI_THRESHOLD
        store.setValues(FC_COILS, COIL_LOW_LOW_PSI_ALARM, [int(low_low_psi)])  # writes low low psi alarm in coil 15
        return low_low_psi

    def high_psi_alarm(self, store):
        high_psi = self.process.actual_psi > HIGH_PSI_THRESHOLD
        store.setValues(FC_COILS, COIL_HIGH_PSI_ALARM, [int(high_psi)])  # writes high psi alarm in coil 16
        return high_psi

    def high_high_psi_alarm(self, store):
        high_high_psi = self.process.actual_psi > HIGH_HIGH_PSI_THRESHOLD
        store.setValues(FC_COILS, COIL_HIGH_HIGH_PSI_ALARM, [int(high_high_psi)])  # writes high high psi alarm in coil 17
        return high_high_psi

    def pump_fault_unlatch(self, store):
        if self.pump.pump_flt:  # store False value in coil 18 Pump Fault Unlatch
            reset = store.getValues(FC_COILS, COIL_PUMP_FAULT_UNLATCH, 1)[0]  # checks if Pump Fault Unlatch True

            if reset:  # checks if Pump Fault Unlatch True Pump Fault True
                self.pump.pump_flt = False
                self.pump.pump_on = False
                store.setValues(FC_COILS, COIL_PUMP_CMD, [int(self.pump.pump_on)])
                reset = False
                store.setValues(FC_COILS, COIL_PUMP_FAULT_UNLATCH, [int(reset)])
        else:
            reset = False
            store.setValues(FC_COILS, COIL_PUMP_FAULT_UNLATCH, [int(reset)])

        return self.pump.pump_flt

    def pump_run_permit_ok(self, store):
        if self.pump.pump_on and self.process.flow_gpm < LOW_FLOW_THRESHOLD_GPM and not self.pump.pump_flt:
            self.pump_off_count_down += DELTA_TIME_S

        if self.pump_off_count_down > PUMP_LOW_FLOW_TRIP_DELAY_S and self.process.flow_gpm < LOW_FLOW_THRESHOLD_GPM:
            self.pump.pump_run_permit = False

        if self.pump.pump_run_permit == False:
            self.pump_off_count_down = 0
            store.setValues(FC_COILS, COIL_PUMP_CMD, [0])
            self.pump.pump_run_permit = True

        return self.pump.pump_run_permit, self.pump_off_count_down
