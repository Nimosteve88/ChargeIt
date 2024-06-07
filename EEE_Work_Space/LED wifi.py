from machine import Pin, I2C, ADC, PWM
from PID import PID

vret_pin = ADC(Pin(26))
vout_pin = ADC(Pin(28))
vin_pin = ADC(Pin(27))
pwm = PWM(Pin(0))
pwm.freq(100000)
pwm_en = Pin(1, Pin.OUT)

pid = PID(0.15, 11, 0, setpoint=0.19, scale='ms')
#pidvout = PID(0.2, 10, 0, setpoint= 3, scale='ms')

count = 0
c2 = 0
elapsedtime = 0
pwm_out = 0
pwm_ref = 0
initsetpoint = pid.setpoint
setpoint = pid.setpoint
delta = 0.01

demand = 0
pid.setpoint = demand / 5

global SHUNT_OHMS
SHUNT_OHMS = 1.02

def saturate(duty):
    if duty > 62500:
        duty = 62500
    if duty < 100:
        duty = 100
    return duty

#csv_file_path = "LED_power.csv"
with open("LED_power.txt", "w") as file:
    file.write("Time (ms), Power (W)\n")

while True:
    
    pwm_en.value(1)

    vin = 1.026*(12490/2490)*3.3*(vin_pin.read_u16()/65536) # calibration factor * potential divider ratio * ref voltage * digital reading
    vout = 1.026*(12490/2490)*3.3*(vout_pin.read_u16()/65536) # calibration factor * potential divider ratio * ref voltage * digital reading
    vret = 1*3.3*((vret_pin.read_u16()-350)/65536) # calibration factor * potential divider ratio * ref voltage * digital reading
    count = count + 1
    elapsedtime = elapsedtime + 1
    c2 = c2 + 1
    
    
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
    if abs(ledpower - pid.setpoint) <= 0.01:
        pwm_ref = pwm_out
        
    else:
        pwm_ref = pid(ledpower)
        pwm_ref = int(pwm_ref*65536)
        pwm_out = saturate(pwm_ref)
        pwm.duty_u16(pwm_out)
        
   

        
    if c2 > 9:
        if elapsedtime < 10000:
            with open("LED_power.txt", "a") as file:
                file.write("{:d},{:.3f}\n".format(elapsedtime, ledpower))
        c2 = 0
        #print("ben")

    if count > 100:
        print("Vin = {:.3f}".format(vin))
        print("Vout = {:.3f}".format(vout))
        print("Vled = {:.3f}".format(vled))
        print("Vret = {:.3f}".format(vret))
        print("Duty = {:.0f}".format(pwm_out))
        print("iout = {:.3f}".format(iout))
        print("ledpower = {:.3f}".format(ledpower))
        print("setpoint = {:.3f}".format(setpoint))
        
        

        count = 0
        #setpoint = setpoint + delta
                
        '''
        if ledpower - initsetpoint >= 0.01:
            setpoint = setpoint - delta
        
        elif initsetpoint - ledpower>= 0.01:
            setpoint = setpoint + delta
            
        pid.setpoint = setpoint
        '''


