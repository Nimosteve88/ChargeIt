from machine import Pin, I2C, ADC, PWM, Timer
from PID import PID
import urequests as requests 
import network
import utime
import _thread as thr


##########################WIFI CONNECTION##########################
ssid = 'SteveGalaxy'
password = 'ChargeIt'

# Set WiFi to station interface
wlan = network.WLAN(network.STA_IF)
# Activate the network interface
wlan.active(True)

#Check if already connected
while not wlan.isconnected():
    print('Connecting to network...')
    wlan.connect(ssid, password)

    max_wait = 10
    # Wait for connection
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            # Connection successful
            break
        max_wait -= 1
        print('Waiting for connection... ' + str(max_wait))
        utime.sleep(1)

    # Check connection
    #if wlan.status() != 3:
        # No connection
        #raise RuntimeError('Network connection failed')
        #continue
#else:
 #   print('Already connected to network')

# Connection successful
print('WLAN connected')
status = wlan.ifconfig()
pico_ip = status[0]
print('IP = ' + status[0])

##########################WIFI CONNECTION##########################


vret_pin = ADC(Pin(26))
vout_pin = ADC(Pin(28))
vin_pin = ADC(Pin(27))
pwm = PWM(Pin(0))
pwm.freq(100000)
pwm_en = Pin(1, Pin.OUT)

pid = PID(0.0001312335958, 10, 0, setpoint = 0.2, scale='ms')
#pid = PID(0.2, 10.9, 0, setpoint=0.4, scale='ms')
#pidvout = PID(0.2, 10, 0, setpoint= 3, scale='ms')


count = 0
c2 = 0
elapsedtime = 0
pwm_out = 0
pwm_ref = 0
initsetpoint = pid.setpoint
global setpoint
setpoint = 0
delta = 0.01

ip = '192.168.217.92'


max_power = pid.setpoint
min_power = pid.setpoint

global timer_elapsed
timer_elapsed = 0
count = 0
first_run = 1

global SHUNT_OHMS
SHUNT_OHMS = 1.02

def saturate(duty):
    if duty > 62500:
        duty = 62500
    if duty < 100:
        duty = 100
    return duty

def tick(t): 
    global timer_elapsed
    timer_elapsed = 1

global demand
demand = 0
#csv_file_path = "LED_power.csv"
#with open("LED_power.csv", "w") as file:
 # file.write("Time (ms), Power (W)\n")

#loop_timer = Timer(mode=Timer.PERIODIC, freq=1000, callback=tick)

def make_request():
    #while True:
        global setpoint
        global demand
        #start_time = utime.ticks_ms()
        data = None
        ip = '192.168.217.92'
        url = 'http://'+ip+':5000/demand'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
        else:
            print('Failed to retrieve data from server')

        demand = float(data['demand'])
        #print('DEMAND', demand)
        setpoint = demand / 4
        
        #utime.sleep(2)
        
        #end_time = utime.ticks_ms()
        #duration = utime.ticks_diff(end_time, start_time)
        #print('The request took', duration, 'milliseconds')
        #count = 0
        #setpoint = setpoint + delta
    
    
    
    
while True:        
    #demand = 2.5
    if first_run:
        # for first run, set up the INA link and the loop timer settings
        first_run = 0
        
        # This starts a 1kHz timer which we use to control the execution of the control loops and sampling
        loop_timer = Timer(mode=Timer.PERIODIC, freq=1000, callback=tick)
        #thr.start_new_thread(make_request, ())
        print('asdasda')
    
        # If the timer has elapsed it will execute some functions, otherwise it skips everything and repeats until the timer elapses
    #
    if timer_elapsed == 1:
        pid.setpoint = setpoint
        pwm_en.value(1)
        timer_elapsed = 0

        vin = 1.026*(12490/2490)*3.3*(vin_pin.read_u16()/65536) # calibration factor * potential divider ratio * ref voltage * digital reading
        vout = 1.026*(12490/2490)*3.3*(vout_pin.read_u16()/65536) # calibration factor * potential divider ratio * ref voltage * digital reading
        vret = 1*3.3*((vret_pin.read_u16()-350)/65536) # calibration factor * potential divider ratio * ref voltage * digital reading
        count = count + 1
        elapsedtime = elapsedtime + 1
        c2 = c2 + 1
        #setpoint = pid.setpoint
        
        iout = vret/SHUNT_OHMS
        vled = vout - vret
        
        ledpower = vled * iout
        
        '''
        if ledpower - initsetpoint >= 0.01:
            setpoint = setpoint - delta
            
        elif initsetpoint - ledpower>= 0.01:
            setpoint = setpoint + delta
                
        pid.setpoint = setpoint
        '''
        '''
        if abs(ledpower - pid.setpoint) <= 0.0000001:
            pwm_out = saturate(pwm_out)
            pwm.duty_u16(pwm_out)
            
        else:
        
            pwm_ref = pid(ledpower)
            pwm_ref = int(pwm_ref*65536)
            pwm_out = saturate(pwm_ref)
            pwm.duty_u16(pwm_out)
            
        '''
        pwm_ref = pid(ledpower)
        pwm_ref = int(pwm_ref*65536)
        pwm_out = saturate(pwm_ref)
        pwm.duty_u16(pwm_out)
        
        
        
        if count % 5000 == 0:
            data = None
            url = 'http://'+ip+':5000/demand'
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
            else:
                print('Failed to retrieve data from server')

            demand = float(data['demand'])
            #print('DEMAND', demand)
            setpoint = demand / 4
            pwm.duty_u16(pwm_out)
            
            
       # if c2 > 1:
       #     if elapsedtime < 1000:
       #         with open("LED_power.txt", "a") as file:
       #             file.write("{:d},{:.3f}\n".format(elapsedtime, ledpower))
       #     c2 = 0
            #print("ben")
        

        
        
        
        #if count % 100 == 0:
            
            
            #print("Vin = {:.3f}".format(vin))
            #print("Vout = {:.3f}".format(vout))
            #print("Vled = {:.3f}".format(vled))
            #print("Vret = {:.3f}".format(vret))
            #print("Duty = {:.0f}".format(pwm_out))
            #print("iout = {:.3f}".format(iout))
            #print("ledpower = {:.4f}".format(ledpower), "setpoint = {:.4f}".format(pid.setpoint))
            #print("PWM_REF = {:.0f}".format(pwm_ref))
            # print("integral error = ", pid._integral)
            #print("setpoint = {:.3f}".format(pid.setpoint))
            #print(demand/4)
            
            #start_time = utime.ticks_ms()
                
            # datasend = {
            #     "Vin": vin,
            #     "Vout": vout,
            #     "Vled": vled,
            #     "Vret": vret,
            #     "Duty": pwm_out,
            #     "Iout": iout,
            #     "Ledpower": ledpower,
            #     "Setpoint": setpoint
            #     }

            # requests.post('http://' + ip +':5001', json=datasend)
            
            #end_time = utime.ticks_ms()
            #duration = utime.ticks_diff(end_time, start_time)
            #print('The Sending took', duration, 'milliseconds')
            
            
        
        
            
        
        
                    
        '''
        if ledpower - initsetpoint >= 0.01:
            setpoint = setpoint - delta
        
        elif initsetpoint - ledpower>= 0.01:
            setpoint = setpoint + delta
            
        pid.setpoint = setpoint
        '''









