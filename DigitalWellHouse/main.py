import time
import threading
from pymodbus.server import StartTcpServer # Starts TCP server that stays running listen for Node-red
from pymodbus.datastore import ModbusServerContext, ModbusDeviceContext # Classes for Modbus data storage
from pymodbus.datastore import ModbusSequentialDataBlock # Class to create a block of Modbus memory
from pump import Pump
from process_values import ProcessValues
from field_devices import FieldDevices
from process_sim import ProcessSim
from alarm_states import AlarmStates


store = ModbusDeviceContext(                  # store is used as the variable for ModbusSlaveContext, this object is the main PLC memory table
    co=ModbusSequentialDataBlock(0, [0] * 50), # 50 coils (ON/OFF points)
    hr=ModbusSequentialDataBlock(0, [0] * 50), # 50 holding registers (VALUEs)
)

context = ModbusServerContext(devices=store, single=True)

SCAN_TIME_CYCLE = 1.0

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



def main(): # everything working together
    
    pump = Pump()
    process = ProcessValues(pump)
    device = FieldDevices(pump,process)
    sim = ProcessSim(process,pump,device)
    alarms = AlarmStates(process,pump)
    
    while True:
        scan(store, pump, process, device, sim, alarms)
        time.sleep(SCAN_TIME_CYCLE)



print("Starting Virtual PLC/RTU on 127.0.0.1:5020")
t = threading.Thread(target=main, daemon=True)  # separate thread to run main() & host server at the same time
t.start()
StartTcpServer(context=context, address=("127.0.0.1", 5020)) # Tcp host for node-red and the future HMI

        