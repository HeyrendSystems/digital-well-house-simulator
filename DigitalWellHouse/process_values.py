import numpy as np
from constants import (
    DEFAULT_OPERATOR_VFD_SETPOINT,
    DEFAULT_TANK_LEVEL,
    DEFAULT_VFD_SETPOINT,
    HR_TANK_LEVEL,
    HR_ACTUAL_PSI,
    HR_FLOW_GPM,
    HR_CHEMICAL_DOSE_GPD,
    HR_VFD_SPEED_PERCENT,
    HR_SYSTEM_REQUIRED_PSI,
    HR_TOTAL_HEAD_PSI,
    HR_VFD_SETPOINT,
    FC_HOLDING_REGISTERS,
    PSI_SCALE_MULTIPLIER,
)


class ProcessValues:

    def __init__(self, pump):
        self.pump = pump

        # Measured / Process State
        self.actual_psi = 0
        self.flow_gpm = 0
        self.tank_lvl = DEFAULT_TANK_LEVEL
        self.chemical_dose_gpd = 0

        # Control / Operator Inputs
        self.vfd_pump_speed_control = 0
        self.vfd_set_point = DEFAULT_VFD_SETPOINT
        self.operator_vfd_setpoint = DEFAULT_OPERATOR_VFD_SETPOINT

        # Calculated / Derived Values
        self.system_head = 0
        self.system_required_psi = 0
        self.total_head_psi = 0
        self.friction_loss_ft = 0
        self.head_100pct = 0

        # Counters
        self.psi_counter = 0

        # Static Model Data
        self.curve = np.array([
            [0,    90],
            [250,  85],
            [500,  80],
            [750,  73],  # pump curve array holds different pump flows and heads relative to the specific flow
            [1000, 68],
            [1250, 65],
            [1400, 60],
            [1550, 55],
        ])

    def operator_vfd_set_point(self, store):
        self.operator_vfd_setpoint = store.getValues(FC_HOLDING_REGISTERS, 8, 1)[0]

    def write_holding_registers(self, store):
        values = [
            (HR_TANK_LEVEL, int(self.tank_lvl)),
            (HR_ACTUAL_PSI, int(self.actual_psi)),
            (HR_FLOW_GPM, int(self.flow_gpm)),
            (HR_CHEMICAL_DOSE_GPD, int(self.chemical_dose_gpd)),
            (HR_VFD_SPEED_PERCENT, round(self.vfd_pump_speed_control)),
            (HR_SYSTEM_REQUIRED_PSI, int(self.system_required_psi)),
            (HR_TOTAL_HEAD_PSI, int(self.total_head_psi)),
            (HR_VFD_SETPOINT, int(self.vfd_set_point)),
        ]
        for address, value in values:
            store.setValues(FC_HOLDING_REGISTERS, address, [value])

    def distribution_system_head(self):
        foot_per_psi = 2.31  # foot of water per PSI
        k = 50  # constant to help simulate friction loss from the system variables such as pipe length, diameter, fittings, and material
        nominal_flow_gpm = 1250  # reference flow - design flow, not max
        static_head_ft = 25  # average feet of elevation from source to destination (positive - pump up, negative - gravity plus pump
        static_head = static_head_ft / foot_per_psi  #head feet converted to PSI
        pressure_head_ft = 104
        pressure_head = pressure_head_ft / foot_per_psi  #required PSI, setpoint floor for the outside distribution system
        self.friction_loss_ft = (k * (self.flow_gpm/nominal_flow_gpm)**2) # equation for friction growth/decrease relative to flow
        friction_loss = self.friction_loss_ft / foot_per_psi  # calc for friction loss ft to PSI
        total_head_loss = (static_head + pressure_head + friction_loss) #Total dynamic head
        self.system_required_psi = (total_head_loss * PSI_SCALE_MULTIPLIER)  # simulated system pressure requirement need from pump (pump must produce PSI above this to create flow)
        return self.system_required_psi

    def pump_curve(self):
        flows = self.curve[:, 0]
        heads = self.curve[:, 1]
        self.head_100pct = np.interp(self.flow_gpm, flows, heads)  # debug
        speed_frac = self.vfd_pump_speed_control/100
        if speed_frac < 0.01:  # avoid divide by zero
            return 0.0
        equiv_flow = self.flow_gpm / speed_frac
        per_stage_base_head_ft = np.interp(equiv_flow, flows, heads)
        stages = 4
        total_head_ft = per_stage_base_head_ft * (speed_frac ** 2) * stages
        self.total_head_psi = (total_head_ft / 2.31) * PSI_SCALE_MULTIPLIER
        return self.total_head_psi

    def update_pressure(self):
        pump_capability = self.pump_curve()
        system_requirement = self.distribution_system_head()
        if not self.pump.pump_on:
            self.actual_psi = system_requirement
        elif pump_capability < system_requirement:
            self.actual_psi = system_requirement
        else:
            self.actual_psi = pump_capability
        return self.actual_psi