# Python standard library
import threading
import time

# External libraries
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import StartTcpServer

# Simulation classes
from alarm_states import AlarmStates
from field_devices import FieldDevices
from process_sim import ProcessSim
from process_values import ProcessValues
from pump import Pump
from sim_database import SimDatabase

# Local constants
from constants import (
    COIL_COUNT,
    HOLDING_REGISTER_COUNT,
    MODBUS_HOST,
    MODBUS_PORT,
    SCAN_CYCLE_TIME_S,
)


store = ModbusDeviceContext(  # store is used as the variable for ModbusSlaveContext, this object is the main PLC memory table
    co=ModbusSequentialDataBlock(0, [0] * COIL_COUNT),  #coils (ON/OFF points)
    hr=ModbusSequentialDataBlock(0, [0] * HOLDING_REGISTER_COUNT),  # holding registers (VALUEs)
)

context = ModbusServerContext(devices=store, single=True)


def scan(store, pump, process, device, sim, alarms):
    # stores certain values first scan only
    sim.first_scan_items(store)

    # publishes current sim state to modbus
    process.write_holding_registers(store)
    pump.write_pump_coils(store)
    device.write_device_coils(store)

    # read commands & operator inputs
    pump.update_pump_cmd(store)
    process.operator_vfd_set_point(store)

    # update device states & process model
    pump.pump_fault()
    pump.inertia_check(store)
    pump.pump_state()
    device.chlorine_inj_pump_on()
    sim.vfd_command()
    sim.update_flow_gpm()
    process.distribution_system_head()
    process.pump_curve()
    process.update_pressure()
    sim.update_chemical_dose_gph()

    # alarms & interlocks
    alarms.pump_fault_unlatch(store)
    alarms.low_psi_alarm(store)
    alarms.pump_run_permit_ok(store)

    # simulation timekeeping
    sim.sim_time()
    sim.sim_time_holding_registers(store)

stop_event = threading.Event()

def main():  # everything working together
    pump = Pump()
    process = ProcessValues(pump)
    device = FieldDevices(pump,process)
    sim = ProcessSim(process,pump,device)
    alarms = AlarmStates(process,pump)
    db = SimDatabase()

    db.init_db()

    try:
        while not stop_event.is_set():
            scan(store, pump, process, device, sim, alarms)
            time.sleep(SCAN_CYCLE_TIME_S)
    finally:
        print("ganster")
        db.close_db()

print(f"Starting Virtual PLC/RTU on {MODBUS_HOST}:{MODBUS_PORT}")
t = threading.Thread(target=main)  # separate thread to run main() & host server at the same time
t.start()
try:
    StartTcpServer(context=context, address=(MODBUS_HOST, MODBUS_PORT))  # Tcp host for node-red and the future HMI
except KeyboardInterrupt:
    print("Ctrl+C received")
finally:
    stop_event.set()
    t.join()
    print("Shutdown complete")

