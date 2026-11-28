# Author: Oliv4945
# AT commands documentation
# https://docs.rakwireless.com/Product-Categories/WisDuo/RAK3172-Module/AT-Command-Manual/

import serial
import sys
import threading
import time


class RAK3172:
    serial = None
    STATUS_CODES = ["OK", "AT_ERROR", "AT_PARAM_ERROR", "AT_BUSY_ERROR"]

    class NETWORK_MODES:
        P2P = 0
        LORAWAN = 1

    class JOIN_MODES:
        ABP = 0
        OTAA = 1

    class JOIN_STATUS:
        NOT_JOINED = 0
        JOINED = 1

    class EVENTS:
        JOINED = 0
        SEND_CONFIRMATION = 1
        RECEIVED=2
        ERROR=3
        TIMEOUT=4
        RECONNECTED=5

    class P2P_RX:
        DISABLE = 0
        CONTINUOUS = 65535

    def __init__(self, serial_port, network_mode, verbose=False, callback_events=None):
        
        self.serial_port = serial_port
        self.verbose = verbose
        self.__callback_events = callback_events
        self.__reconnecting_lock = threading.Lock()

        # Open serial port
        try:
            self.serial = serial.Serial(serial_port, 115200, timeout=1)
        except serial.SerialException as e:
            sys.exit(f"/!\\ Cannot open serial port {serial_port}: {e} "
                     "(permission denied -> add user to 'dialout' group; "
                     "busy -> another process holds the port). Aborting.")
        self.serial.reset_input_buffer()

        # Open RX thread
        self.thread_rx_handle = threading.Thread(target=self.thread_rx)
        self.data_received = threading.Event()
        self.thread_rx_ready = threading.Event()
        self.thread_rx_kill = threading.Event()
        self.thread_rx_handle.start()

        # Check chip presence
        # Retry: the port can bounce right after opening (USB-serial DTR
        # reset), during which the RX thread is busy reconnecting.
        detected = False
        for _ in range(5):
            if self.status() is True:
                detected = True
                break
            time.sleep(1)
        if not detected:
            print("ERROR - Unable to detect chip")
            self.thread_rx_kill.set()
            exit()

        # Ensure network mode
        self.network_mode = network_mode

    def thread_rx(self):
        self.thread_rx_ready.set()
        while not self.thread_rx_kill.is_set():
            try:
                rx = self.serial.read_until(b"\r\n").decode("ASCII").rstrip().upper()
            except serial.SerialException:
                self._reconnect()
                continue
            if not len(rx):
                # Drop empty lines
                continue
            self.thread_rx_ready.clear()
            if self.verbose:
                print(f"<- {rx}")
            if rx[0] == "+":
                if rx == "+EVT:JOINED":
                    self.__callback_events(RAK3172.EVENTS.JOINED, None)

                if rx.startswith("+EVT:SEND CONFIRMED"):
                    if rx == "+EVT:SEND CONFIRMED OK":
                        self.__callback_events(RAK3172.EVENTS.SEND_CONFIRMATION, True)
                    else:
                        self.__callback_events(RAK3172.EVENTS.SEND_CONFIRMATION, False)

                if "+EVT:RXP2P" in rx:
                    # Format: +EVT:RXP2P:<rssi>:<snr>:<hex_payload>
                    parts = rx.split(":")
                    if len(parts) >= 5:
                        rssi, snr, payload = parts[2].strip(), parts[3].strip(), parts[4].strip()
                        self.__callback_events(RAK3172.EVENTS.RECEIVED, f"{rssi}:{snr}:{payload}")

            elif "CURRENT WORK MODE" in rx:
                # The module reboots on its own sometimes (power/watchdog
                # reset) without the USB-serial link dropping at all - this
                # boot banner is the only sign. Radio config and RX mode
                # don't survive it, so callers must redo them.
                print(f"WARNING - {self.serial_port} reported a reboot: {rx}")
                self._notify_reconnected()
            else:
                # RUI3 firmware (e.g. RUI_4.2.0) echoes the command name in
                # query replies, e.g. "AT+NWM=0" instead of a bare "0".
                if rx.startswith("AT+") and "=" in rx:
                    rx = rx.split("=", 1)[1]
                self.data_rx = rx
                self.data_received.set()
                time_start = time.time()
                while self.data_received.is_set():
                    # Wait for data to be processed or timeout
                    if time.time() > time_start + 0.1:
                        # Timeout, prepare for next RX
                        self.data_received.clear()
                        self.data_rx = ""
            self.thread_rx_ready.set()

    def _reconnect(self):
        # The module can reboot on its own (power/watchdog reset), which
        # drops the USB-serial device node until it re-enumerates. Radio
        # config and RX mode don't survive that, so callers must redo them
        # via the RECONNECTED event once the link is back.
        print(f"WARNING - Serial port {self.serial_port} lost, reconnecting...")
        self.thread_rx_ready.clear()
        try:
            self.serial.close()
        except Exception:
            pass

        while not self.thread_rx_kill.is_set():
            time.sleep(2)
            try:
                self.serial = serial.Serial(self.serial_port, 115200, timeout=1)
                self.serial.reset_input_buffer()
                break
            except serial.SerialException:
                continue

        if self.thread_rx_kill.is_set():
            return

        print(f"Reconnected to {self.serial_port}")
        self.thread_rx_ready.set()
        self._notify_reconnected()

    def _notify_reconnected(self):
        # Runs the callback on its own thread: it typically re-sends AT
        # commands (e.g. configure_p2p), which needs this RX thread free to
        # read the responses - calling it inline here would deadlock.
        # The lock drops duplicate/overlapping triggers (e.g. a burst of
        # boot-banner lines) so only one reconfigure attempt runs at a time.
        if not self.__callback_events:
            return
        if not self.__reconnecting_lock.acquire(blocking=False):
            return

        def run():
            try:
                self.__callback_events(RAK3172.EVENTS.RECONNECTED, None)
            finally:
                self.__reconnecting_lock.release()

        threading.Thread(target=run, daemon=True).start()

    @property
    def network_mode(self):
        return self.__network_mode

    @network_mode.setter
    def network_mode(self, network_mode):
        status, data = self.send_command("AT+NWM=?")
        if status != "OK":
            print("ERROR - Unable to check network mode")
            sys.exit(1)
        if int(data) != network_mode:
            status, _ = self.send_command(f"AT+NWM={network_mode}")
            if status != "OK":
                print("ERROR - Unable to set network mode")
                sys.exit(1)
        self.__network_mode = network_mode

    @property
    def appkey(self):
        status, data = self.send_command("AT+APPKEY=?")
        if status != "OK":
            print("ERROR - Unable to get APPKEY")
            exit()
        return data

    @appkey.setter
    def appkey(self, appkey):
        status, _ = self.send_command(f"AT+APPKEY={appkey}")
        if status != "OK":
            print("status", status)
            print("ERROR - Unable to set AppKEY")
            exit()
        # RAK3172 needs to be restarted to take it into account
        self.reset_soft()

    @property
    def deveui(self):
        status, data = self.send_command("AT+DEVEUI=?")
        if status != "OK":
            print("ERROR - Unable to get devEUI")
            exit()
        return data

    @deveui.setter
    def deveui(self, deveui):
        status, _ = self.send_command(f"AT+DEVEUI={deveui}")
        if status != "OK":
            print("ERROR - Unable to set devEUI")
            exit()
        # RAK3172 needs to be restarted to take it into account
        self.reset_soft()

    @property
    def joineui(self):
        status, data = self.send_command("AT+APPEUI=?")
        if status != "OK":
            print("ERROR - Unable to get joinEUI")
            exit()
        return data

    @joineui.setter
    def joineui(self, joineui):
        status, _ = self.send_command(f"AT+APPEUI={joineui}")
        if status != "OK":
            print("ERROR - Unable to set joinEUI")
            exit()
        # RAK3172 needs to be restarted to take it into account
        self.reset_soft()

    @property
    def getdata(self):
        status,data = self.send_command("AT+RECV=?")
        if status != "OK":
            print("ERROR - Unable to get data")
            exit()
        return data

    @property
    def verbose(self):
        return self.__verbose

    @verbose.setter
    def verbose(self, verbose):
        self.__verbose = verbose

    @property
    def serial_port(self):
        return self.__serial_port

    @serial_port.setter
    def serial_port(self, port):
        self.__serial_port = port

    def close(self):
        self.thread_rx_kill.set()

    def join(self):
        status, _ = self.send_command(f"AT+NJM={RAK3172.JOIN_MODES.OTAA}")
        if status != "OK":
            print("ERROR - Unable to set join mode")
        status, _ = self.send_command("AT+JOIN=1:0:8:0")
        if status != "OK":
            print("ERROR - Unable to join")

    def join_status(self):
        status, data = self.send_command(f"AT+NJS=?")
        if status != "OK":
            print("ERROR - Unable to get join status")
        return int(data)

    def reset_soft(self):
        self.send_command(f"ATZ", ignore=True)
        # Give some time to the device to restart
        time.sleep(1.0)
        self.serial.reset_input_buffer()

    def send_command(self, cmd, ignore=False):
        # Ensure case
        cmd = cmd.upper()
        # Clear RX buffer
        self.data_rx = []
        # Send command as soon as RX thread is available
        if not self.thread_rx_ready.wait(10):
            return None, None
        self.serial.write(cmd.encode("ASCII") + b"\r\n")
        self.serial.flush()

        if self.verbose is True:
            print(f"-> {cmd}")

        if not ignore:
            if self.data_received.wait(10):
                # Get data or status code
                data = self.data_rx
                self.data_received.clear()
                if data in RAK3172.STATUS_CODES:
                    return data, None
                # Already got data, only status code remaining
                if self.data_received.wait(10):
                    status = self.data_rx
                    self.data_received.clear()
                    return status, data

        return None, None

    def send_payload(self, fport, payload, confirmed=False):
        # TODO - Implement confirm messages
        status, _ = self.send_command(f'AT+SEND={fport}:{payload.decode("ASCII")}')
        if status != "OK":
            print("ERROR - Unable to send payload")
            return False
        return True

    def status(self):
        status, _ = self.send_command("AT")
        if status == "OK":
            return True
        else:
            return False

    def configure_p2p(self, frequency, spreading_factor, bandwidth, coding_rate, preamble, tx_power):
        """
        Konfigurasi perangkat ke mode P2P dengan parameter yang diberikan
        """
        self.network_mode = RAK3172.NETWORK_MODES.P2P

        # A prior session may have left continuous RX on (e.g. crashed
        # without calling close()); radio params can't be set while it's on.
        self.send_command(f"AT+PRECV={RAK3172.P2P_RX.DISABLE}")
        time.sleep(0.2)

        p2p_params = {
            "AT+PFREQ": frequency,      # Frekuensi LoRa
            "AT+PSF": spreading_factor, # Spreading factor
            "AT+PBW": bandwidth,        # Bandwidth
            "AT+PCR": coding_rate,      # Coding rate
            "AT+PPL": preamble,         # Preamble length
            "AT+PTP": tx_power,         # TX power
        }
        for cmd, value in p2p_params.items():
            status, _ = self.send_command(f"{cmd}={value}")
            if status != "OK":
                print(f"ERROR - Unable to set {cmd}")
                exit()

        self.enable_p2p_rx()
        print("P2P mode configured successfully!")

    def enable_p2p_rx(self):
        """
        Mengaktifkan mode penerimaan P2P LoRa secara kontinu.
        """
        self.send_command(f"AT+PRECV={RAK3172.P2P_RX.DISABLE}")  # Reset buffer RX
        time.sleep(0.5)
        self.send_command(f"AT+PRECV={RAK3172.P2P_RX.CONTINUOUS}")  # Aktifkan RX terus-menerus
        time.sleep(0.5)
        print("P2P RX enabled and listening for packets...")

    def rearm_p2p_rx(self):
        """
        Re-arm RX after a received packet with minimal deaf time. Tries a
        direct AT+PRECV=65535 first (the module is already idle after RX);
        falls back to the slow disable/enable cycle if it is refused.
        """
        status, _ = self.send_command(f"AT+PRECV={RAK3172.P2P_RX.CONTINUOUS}")
        if status != "OK":
            self.enable_p2p_rx()

    @property
    def get_p2p_data(self):
        status,data = self.send_command("AT+PRECV=?")
        if status != "OK":
            print("ERROR - Unable to get data")
            exit()
        
        return data

    def send_p2p_payload(self, payload, confirmed=False):
        # TODO - Implement confirm messages
        status, _ = self.send_command(f'AT+PSEND={payload}')
        if status != "OK":
            print("ERROR - Unable to send payload")
            return False
        return True