from machine import Pin, I2C, ADC, PWM, Timer
import usocket as socket
import uselect as select
import json
import utime
import network
import math
import time

# Set up some pin allocations for the Analogues and switches
va_pin = ADC(Pin(28))
vb_pin = ADC(Pin(26))
vpot_pin = ADC(Pin(27))
OL_CL_pin = Pin(12, Pin.IN, Pin.PULL_UP)
BU_BO_pin = Pin(2, Pin.IN, Pin.PULL_UP)

# Set up the I2C for the INA219 chip for current sensing
ina_i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=2400000)

# Some PWM settings
pwm = PWM(Pin(9))
pwm.freq(100000)
min_pwm = 1000
max_pwm = 64536
pwm_out = min_pwm
pwm_ref = 30000

# Some error signals
trip = 0
OC = 0

# The potentiometer is prone to noise so we are filtering the value using a moving average
v_pot_filt = [0] * 100
v_pot_index = 0

# Gains etc for the PID controller
i_ref = 0  # Voltage reference for the CL modes
i_err = 0  # Voltage error
i_err_int = 0  # Voltage error integral
i_pi_out = 0  # Output of the voltage PI controller
kp = 100  # Boost Proportional Gain
ki = 300  # Boost Integral Gain

#parameters for MPPT
previous_power = 0
step_size = 1000
duty_cycle =  1000
# Basic signals to control logic flow
timer_elapsed = 0
count = 0
first_run = 1

# Need to know the shunt resistance
SHUNT_OHMS = 0.10

# Function to send to server
def send_message_to_server(message):
    start_time = time.time()
    server_name = '192.168.194.92'  # Replace with current IP Address
    server_port = 12001
    client_port = 10001  # Change this to 11000 for the second client
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(('', client_port))
    print("UDP client running...")
    print("Connecting to server at IP:", server_name, "PORT:", server_port)

    if type(message) == str:
        msg = message.encode()
    elif type(message) in [float, int]:
        msg = str(message).encode()
    elif type(message) == dict:
        msg = json.dumps(message).encode()
    else:
        print("Invalid message type. Please provide a string, float, integer or dictionary.")
        return

    client_socket.sendto(msg, (server_name, server_port))
    poll = select.poll()
    poll.register(client_socket, select.POLLIN)
    events = poll.poll(2000)

    if events:
        for event in events:
            if event[1] & select.POLLIN:
                data, server_address = client_socket.recvfrom(2048)
                if data:
                    print("Message from Server:", data.decode())
    else:
        print("No response from server within timeout period.")
    
    client_socket.close()
    print("Message has been successfully sent in", time.time() - start_time, "seconds")

# Saturation function
def saturate(signal, upper, lower):
    if signal > upper:
        signal = upper
    if signal < lower:
        signal = lower
    return signal

# Timer tick function
def tick(t):
    global timer_elapsed
    timer_elapsed = 1

# INA219 Current sensor class
class INA219:
    REG_CONFIG = 0x00
    REG_SHUNTVOLTAGE = 0x01
    REG_BUSVOLTAGE = 0x02
    REG_POWER = 0x03
    REG_CURRENT = 0x04
    REG_CALIBRATION = 0x05

    def __init__(self, sr, address, maxi):
        self.address = address
        self.shunt = sr

    def vshunt(self):
        reg_bytes = ina_i2c.readfrom_mem(self.address, self.REG_SHUNTVOLTAGE, 2)
        reg_value = int.from_bytes(reg_bytes, 'big')
        if reg_value > 2**15:  # negative
            sign = -1
            for i in range(16):
                reg_value = (reg_value ^ (1 << i))
        else:
            sign = 1
        return float(reg_value) * 1e-5 * sign

    def vbus(self):
        reg_bytes = ina_i2c.readfrom_mem(self.address, self.REG_BUSVOLTAGE, 2)
        reg_value = int.from_bytes(reg_bytes, 'big') >> 3
        return float(reg_value) * 0.004

    def configure(self):
        ina_i2c.writeto_mem(self.address, self.REG_CONFIG, b'\x19\x9F')
        ina_i2c.writeto_mem(self.address, self.REG_CALIBRATION, b'\x00\x00')

# Main function
while True:
    if first_run:
        ina = INA219(SHUNT_OHMS, 64, 5)
        ina.configure()
        first_run = 0

        loop_timer = Timer(mode=Timer.PERIODIC, freq=1000, callback=tick)

    if timer_elapsed == 1:
        va = 1.017 * (12490 / 2490) * 3.3 * (va_pin.read_u16() / 65536)
        vb = 1.015 * (12490 / 2490) * 3.3 * (vb_pin.read_u16() / 65536)
        vpot_in = 1.026 * 3.3 * (vpot_pin.read_u16() / 65536)
        v_pot_filt[v_pot_index] = vpot_in
        v_pot_index = (v_pot_index + 1) % 100
        vpot = sum(v_pot_filt) / 100

        Vshunt = ina.vshunt()
        CL = OL_CL_pin.value()  # Are we in closed or open loop mode
        BU = BU_BO_pin.value()  # Are we in buck or boost mode?
                
        Vbus = ina.vbus()
        Ipv = Vshunt / SHUNT_OHMS
        PpV = vb * Ipv
        
        min_pwm = 1000
        max_pwm = 65000
        iL = Vshunt / SHUNT_OHMS

        #MPPT P&O
        if PpV > previous_power:
            duty_cycle += step_size
        else:
            direction = -1
            duty_cycle += direction*step_size
        
        
        #set the new value of the power
        previous_power = PpV

        #set the duty  cycle of the circuit to the current duty to obtain new power
        duty_cycle = saturate(duty_cycle, pwm_ref, min_pwm)
        duty = 65356 - duty_cycle
        pwm.duty_u16(duty)

        #delay to reduce oscillations in measurements
        utime.sleep_ms(10)

        
        count += 1
        timer_elapsed = 0
        
        #calculate the approximmate power
        Power = va * iL
        PowerIN = vb * -iL

        if count > 100:
            print(f"Power = {Power:.3f}")
            print(f"PowerIn = {PowerIN:.3f}")
            print(f"Va = {va:.3f}")
            print(f"Vb = {vb:.3f}")
            print(f"Vpot = {vpot:.3f}")
            print(f"iL = {iL:.3f}")
            print(f"OC = {OC}")
            print(f"CL = {CL}")
            print(f"BU = {BU}")
            print(f"duty = {duty}")
            print(f"duty% = {duty/655.36:.3f}")
            print(f"i_err = {i_err:.3f}")
            print(f"i_ref = {i_ref:.3f}")
            #print(f"Vref = {Vref:.3f}")
            count = 0
