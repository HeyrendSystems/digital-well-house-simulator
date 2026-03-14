# digital-well-house-simulator

A personal project focused on simulating an industrial pump and VFD-driven water system with a real-time HMI built using Python and Node-RED.

---

## Overview

For this project, I am attempting to build a digital well house simulator that models how a real pump-driven water system behaves when interacting with control logic and system hydraulics. This is an ongoing effort to deepen my understanding of industrial control systems, PLC-style communication, and pump hydraulics.

This simulation attempts to model:

- Pump head and system pressure
- VFD speed control
- Flow rate behavior
- Alarm conditions
- Modbus-style register communication
- Real-time HMI visualization via Node-RED

As the project evolves, I will continue refining the hydraulic modeling and system behavior to more closely represent how real pump systems operate in the field.

---

## System Architecture

```
Python Simulation Engine (pump + system model)
        │
        │  Modbus TCP (PyModbus server)
        ▼
Node-RED (data ingestion + HMI logic)
        │
        ▼
HMI (charts • status • alarms)
```

The Python backend models pump physics and control logic.
PyModbus runs a Modbus TCP server exposing PLC-style registers and coils.
Node-RED reads these values and renders a live operational HMI.

---

## Tech Stack

- Python — simulation logic and system modeling
- PyModbus — Modbus TCP register emulation
- NumPy — pump curve interpolation and hydraulic calculations
- Node-RED — real-time data flow and HMI visualization
- Git & GitHub — version control and project documentation

---

## Current Features

- Dynamic pump head vs system head interaction
- VFD ramp-up and ramp-down simulation
- Flow behavior based on pressure conditions
- Alarm state handling
- Pump Fault Unlatch
- Scaled Modbus register values (e.g., 850 represents 85.0%)
- HMI converts scaled register values back to standard engineering units for display
- Clear separation between simulation logic and HMI layer

---

## How It Works

The simulator models the interaction between:

- Pump head generation
- System resistance and friction loss
- Static head and required discharge pressure
- Flow (GPM) changes based on system conditions
- Chemical dosage changes relative to flow

VFD speed directly influences pump head generation. Flow begins only when pump head exceeds system head, establishing the system’s operating point and reflecting real-world pump behavior in industrial systems. The simulation uses an actual pump curve to produce realistic operating behavior.

---

### Pump Curve (Base Stage)

The base pump curve represents a single stage (one bowl) of a multi-stage vertical turbine pump:

```python
self.curve = np.array([
    [0,    90],
    [250,  85],
    [500,  80],
    [750,  73],
    [1000, 68],
    [1250, 65],
    [1400, 60],
    [1550, 55]
])
```

Each row represents:

```
[Flow (GPM), Head (ft)]
```

The head values shown above represent **per-stage head**.
The simulation multiplies these values by 4 to model a four-stage pump assembly.

---

### System Head Model (Distribution System)

The total system head requirement is calculated as:

```python
total_head_loss = static_head + pressure_head + friction_loss
```

Expanded form:

```python
static_head_psi = static_head_ft / foot_per_psi
pressure_head_psi = pressure_head_ft / foot_per_psi
friction_loss_psi = friction_loss_ft / foot_per_psi

total_head_psi = static_head_psi + pressure_head_psi + friction_loss_psi
system_required_psi = total_head_psi * 10
```

The total system head is calculated in PSI and scaled by 10 for Modbus register representation.
For HMI display, the value is divided by 10 to restore standard PSI units.

---

### Pump Head Model (Curve + VFD Scaling)

```python
flows = self.curve[:, 0]
heads = self.curve[:, 1]

speed_frac = self.vfd_pump_speed_control / 100

equiv_flow = self.flow_gpm / speed_frac
per_stage_base_head_ft = np.interp(equiv_flow, flows, heads)

stages = 4
total_head_ft = per_stage_base_head_ft * (speed_frac ** 2) * stages

total_head_psi = (total_head_ft / 2.31) * 10
```

The calculated pump head is converted from feet of head to PSI and scaled by 10 for Modbus register representation.
For HMI display, the value is divided by 10 to restore standard PSI units.

---

### HMI Data Presentation (Node-RED)

Node-RED reads the simulated Modbus registers and displays the following values on the HMI:

#### Process Values (Holding Registers)

- Tank Level (`level`)
- System Pressure, PSI (`pressurePsi`)
- Flow Rate, GPM (`gpmFlow`)
- Chemical Dose Rate (`chemicalDose`)
- VFD Speed, % (`vfdSpeed`)
- Required System Pressure, PSI (`requiredSystemPsi`)
- Pump Discharge Head, PSI (`pumpHeadPsi`)

#### Status & Alarms (Coils / Discrete)

- Pump Command (`pumpCommandOn`)
- Pump Running (`pumpRunning`)
- Pump Fault (`pumpFault`)
- Chlorine Injection Pump Running (`chlrInjPump`)
- Low Pressure Alarm (`lowPsiAlarm`)

---

## How to Run

### 1. Clone the Repository

```bash
git clone https://github.com/HeyrendSystems/digital-well-house-simulator.git
cd digital-well-house-simulator
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Simulator

```bash
python digitalwellhouse/main.py
```

### 4. Run Node-RED Dashboard

1. Install Node-RED
2. Open `http://localhost:1880`
3. Import `nodered/flows.json`
4. Deploy
5. Open the HMI

---

## What I've Learned So Far

- How pump curves and system curves determine the actual operating point
- How VFD speed scaling affects head generation and flow behavior
- Implementing Modbus-style register mapping and scaled value handling
- Designing a real-time industrial telemetry HMI
- Structuring a system so simulation logic remains separate from visualization logic

---

## Future Improvements

- Add a simple demand model (ex: sine-wave based daily usage curve)
- Expand alarm and fault scenarios (more realistic trips and reset behavior)
- Add SQL logging / basic historian
- Make key system parameters editable from the HMI (k-factor, setpoints, ramp rates, etc.)
- Add a REST API (and optionally an MQTT interface)
- Improve code maintainability by centralizing configuration values and reducing hard-coded parameters

---

## License

MIT License
