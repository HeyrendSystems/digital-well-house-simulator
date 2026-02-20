from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusServerContext, ModbusDeviceContext
from pymodbus.datastore import ModbusSequentialDataBlock
import threading

store = ModbusDeviceContext(
    co=ModbusSequentialDataBlock(0, [0] * 50),
    hr=ModbusSequentialDataBlock(0, [0] * 50),
)

context = ModbusServerContext(devices=store, single=True)  # if this errors, tell me and we’ll swap to devices=

def start_modbus(plc_loop_fn):
    print("Starting Virtual PLC/RTU on 127.0.0.1:5020")
    t = threading.Thread(target=plc_loop_fn, daemon=True)
    t.start()
    StartTcpServer(context=context, address=("127.0.0.1", 5020))

if __name__ == "__main__":
    # ONLY if you run: python modbus_plc.py
    from main import main  # or whatever your PLC loop function is called
    start_modbus(main)
