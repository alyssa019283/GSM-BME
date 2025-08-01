"""
Raspberry Pi Pico (MicroPython) with SIM868 GSM/GPRS/GNSS Module
Some of the below is from the code which came with SIM868 Module
"""
import machine
import os
import utime
import binascii
import bme680


# using pin defined
led_pin = 25  # onboard led
pwr_en = 14  # pin to control the power of the module
uart_port = 0
uart_baute = 115200
bme_i2c_address = 0x77
bme_PinSDA=8
bme_PinSCL=9

APN = "prepay.tesco-mobile.com"

reading = 0
temperature = 0

# uart setting
uart = machine.UART(uart_port, uart_baute)
print(os.uname())
# Part for BME280
i2c=machine.I2C(0,sda=machine.Pin(bme_PinSDA),scl=machine.Pin(bme_PinSCL), freq=10000)    #initializing the I2C method 
#bme = bme280.BME280(i2c=i2c,address=bme_i2c_address)
bme = bme680.BME680_I2C(i2c=i2c)

# LED indicator on Raspberry Pi Pico
led_onboard = machine.Pin(led_pin, machine.Pin.OUT)

# HTTP Get Post Parameter - change API key
http_post_server = ['http://alyssamarie.co.uk/other', '/post-data-new.php', 'api_key=API_KEY']
http_post_tmp = 'api_key=API_KEY&value1=23.04&value2=58.13&value3=1004.93'
http_content_type = 'application/x-www-form-urlencoded'

def led_blink():
    led_onboard.value(1)
    utime.sleep(1)
    led_onboard.value(0)
    utime.sleep(1)
    led_onboard.value(1)
    utime.sleep(1)
    led_onboard.value(0)

# power on/off the module
def power_on_off():
    pwr_key = machine.Pin(pwr_en, machine.Pin.OUT)
    pwr_key.value(1)
    utime.sleep(2)
    pwr_key.value(0)

def hexstr_to_str(hex_str):
    hex_data = hex_str.encode('utf-8')
    str_bin = binascii.unhexlify(hex_data)
    return str_bin.decode('utf-8')

def str_to_hexstr(string):
    str_bin = string.encode('utf-8')
    return binascii.hexlify(str_bin).decode('utf-8')

def wait_resp_info(timeout=2000):
    prvmills = utime.ticks_ms()
    info = b""
    while (utime.ticks_ms()-prvmills) < timeout:
        if uart.any():
            info = b"".join([info, uart.read(1)])
    print(info.decode())
    return info

# Send AT command
def send_at(cmd, back, timeout=2000):
    rec_buff = b''
    uart.write((cmd+'\r\n').encode())
    prvmills = utime.ticks_ms()
    while (utime.ticks_ms()-prvmills) < timeout:
        if uart.any():
            rec_buff = b"".join([rec_buff, uart.read(1)])
    if rec_buff != '':
        if back not in rec_buff.decode():
            print(cmd + ' back:\t' + rec_buff.decode())
            return 0
        else:
            print(rec_buff.decode())
            return 1
    else:
        print(cmd + ' no responce')

# Send AT command and return response information
def send_at_wait_resp(cmd, back, timeout=2000):
    rec_buff = b''
    uart.write((cmd + '\r\n').encode())
    prvmills = utime.ticks_ms()
    while (utime.ticks_ms() - prvmills) < timeout:
        if uart.any():
            rec_buff = b"".join([rec_buff, uart.read(1)])
    if rec_buff != '':
        if back not in rec_buff.decode():
            print(cmd + ' back:\t' + rec_buff.decode())
        else:
            print(rec_buff.decode())
    else:
        print(cmd + ' no responce')
    # print("Response information is: ", rec_buff)
    return rec_buff

# Module startup detection
def check_start():
    while True:
        # simcom module uart may be fool,so it is better to send much times when it starts.
        uart.write(bytearray(b'ATE1\r\n'))
        utime.sleep(2)
        uart.write(bytearray(b'AT\r\n'))
        rec_temp = wait_resp_info()
        if 'OK' in rec_temp.decode():
            print('SIM868 is ready\r\n' + rec_temp.decode())
            break
        else:
            power_on_off()
            print('SIM868 is starting up, please wait...\r\n')
            utime.sleep(8)


# Check the network status
def check_network():
    for i in range(1, 3):
        if send_at("AT+CGREG?", "0,1") == 1:
            print('SIM868 is online\r\n')
            break
        else:
            print('SIM868 is offline, please wait...\r\n')
            utime.sleep(5)
            continue
    send_at("AT+CPIN?", "OK")
    send_at("AT+CSQ", "OK")
    send_at("AT+COPS?", "OK")
    send_at("AT+CGATT?", "OK")
    send_at("AT+CGDCONT?", "OK")
    send_at("AT+CSTT?", "OK")
    send_at("AT+CSTT=\""+APN+"\"", "OK")
    send_at("AT+CIICR", "OK")
    send_at("AT+CIFSR", "OK")


# Get the gps info
def get_gps_info():
    count = 0
    print('Start GPS session...')
    send_at('AT+CGNSPWR=1', 'OK')
    utime.sleep(2)
    for i in range(1, 10):
        uart.write(bytearray(b'AT+CGNSINF\r\n'))
        rec_buff = wait_resp_info()
        if ',,,,' in rec_buff.decode():
            print('GPS is not ready')
#            print(rec_buff.decode())
            if i >= 9:
                print('GPS positioning failed, please check the GPS antenna!\r\n')
                send_at('AT+CGNSPWR=0', 'OK')
            else:
                utime.sleep(2)
                continue
        else:
            if count <= 3:
                count += 1
                print('GPS info:')
                print(rec_buff.decode())
            else:
                send_at('AT+CGNSPWR=0', 'OK')
                break


# Bearer Configure
def bearer_config():
    send_at('AT+SAPBR=3,1,\"Contype\",\"GPRS\"', 'OK')
    send_at('AT+SAPBR=3,1,\"APN\",\"'+APN+'\"', 'OK')
    send_at('AT+SAPBR=1,1', 'OK')
    send_at('AT+SAPBR=2,1', 'OK')
#   send_at('AT+SAPBR=0,1', 'OK')


# HTTP GET TEST
def http_get():
    send_at('AT+HTTPINIT', 'OK')
    send_at('AT+HTTPPARA=\"CID\",1', 'OK')
    send_at('AT+HTTPPARA=\"URL\",\"'+http_get_server[0]+http_get_server[1]+'\"', 'OK')
    if send_at('AT+HTTPACTION=0', '200', 5000):
        uart.write(bytearray(b'AT+HTTPREAD\r\n'))
        rec_buff = wait_resp_info(8000)
        print("resp is :", rec_buff.decode())
    else:
        print("Get HTTP failed, please check and try again\n")
    send_at('AT+HTTPTERM', 'OK')


# HTTP POST TEST
# parameters: temperature, humidity, pressure for BME280
def http_post(temperature, humidity, pressure, gas):
    send_at('AT+SAPBR=3,1,"Contype","GPRS"','OK')
    send_at('AT+SAPBR=3,1,"APN","'+APN+'"', 'OK')
    send_at('AT+SAPBR=1,1', 'OK')

    http_post_tmp = 'api_key=API_KEY' + temperature + '&value2=' + humidity + '&value3=' + pressure + '&value4=' + gas
    print(http_post_tmp)
    send_at('AT+HTTPINIT', 'OK')
    send_at('AT+HTTPPARA=\"CID\",1', 'OK')
    send_at('AT+HTTPPARA=\"URL\",\"'+http_post_server[0]+http_post_server[1]+'\"', 'OK')
    send_at('AT+HTTPPARA=\"CONTENT\",\"' + http_content_type + '\"', 'OK')
    if send_at('AT+HTTPDATA=75,8000', 'DOWNLOAD', 3000):
        uart.write(bytearray(http_post_tmp.encode()))
        utime.sleep(5)
        rec_buff = wait_resp_info()
        print(rec_buff)
        if 'OK' in rec_buff.decode():
            print("UART data is read!\n")
        # Errors on this part:
        if send_at('AT+HTTPACTION=1', '200', 8000):
            print("POST successfully!\n")
        else:
            print("POST failed\n")
        send_at('AT+HTTPTERM', 'OK')
    else:
        print("HTTP Post failed，please try again!\n")


# Get the gps info
def phone_call(phone_num='10000', keep_time=10):
    send_at('AT+CHFA=1', 'OK')
    send_at('ATD'+phone_num+';', 'OK')
    utime.sleep(keep_time)
    send_at('AT+CHUP;', 'OK')

def answer_call():
    send_at('AT', 'OK')
    send_at('AT+CLIP=1', 'OK')
    # Main loop to wait for incoming calls
    while True:
        response = uart.readline()
        if response:
            response = response.decode().strip()
            if 'RING' in response:  # Incoming call detected
                print("Incoming call detected!")
                # Answer the call
                send_at('ATA', 'OK')
                break  

# SMS test
def sms_test(phone_num, sms_info=""):
    #send_at('AT+SAPBR=0,1', 'OK')
    send_at('AT+CMGF=1', 'OK')
    if send_at('AT+CMGS=\"'+phone_num+'\"', '>'):
        uart.write((sms_info).encode())
        uart.write(b'\x1A')


# Bluetooth scan
def bluetooth_scan():
    send_at('AT+BTPOWER=1', 'OK', 3000)
    send_at('AT+BTHOST?', 'OK', 3000)
    send_at('AT+BTSTATUS?', 'OK', 3000)
    send_at('AT+BTSCAN=1,10', 'OK', 8000)
    send_at('AT+BTPOWER=0', 'OK')


# AT test
def at_test():
    print("---------------------------SIM868 TEST---------------------------")
    while True:
        try:
            command_input = str(input('Please input the AT command,press Ctrl+C to exit: '))
            send_at(command_input, 'OK', 2000)
        except KeyboardInterrupt:
            print("\r\nExit AT command test!\n")
            power_on_off()
            print("Power off the module!\n")
            break

def calculate_gas_score(hum, gas):
    # Humiidity contribution to IAQ Index
    hum_score = 0
    if (hum >= 38 and hum <= 42):
        hum_score = 0.25*100
    else:
        if (hum < 38):
            hum_score = 0.25/40*hum*100
        else:
            hum_score = ((-0.25/(100-40)*hum)+0.416666)*100
    # Gas contribution to IAQ Index
    if (gas > 50000):
        gas_ref = 50000
    if (gas < 5000):
        gas_ref = 5000
    gas_score = (0.75/(50000-5000)*gas_ref -(5000*(0.75/(50000-5000))))*100
     # 100% is good air quality 
    air_quality_score = hum_score + gas_score
    score = (100-air_quality_score)*5
    return score
    

def iaq_description(score):
    print("AQI:")
    if (score >= 301):
        print("Hazardous")
        return 1
    elif (score >= 201 and score <= 300 ):
        print("Very Unhealthy")
        return 2
    elif (score >= 176 and score <= 200 ):
        print("Unhealthy")
        return 3
    elif (score >= 151 and score <= 175 ):
        print("Unhealthy for Sensitive Groups")
        return 4
    elif (score >= 51 and score <= 150 ):
        print("Moderate")
        return 5
    elif (score >= 00 and score <= 50 ):
        print("Good")
        return 6
    else:
        return 7
    


# main program

while True:
  try:
    temp = str(round(bme.temperature, 2))
    hum_1 = bme.humidity
    hum = str(round(hum_1, 2))
    
    pres = str(round(bme.pressure, 2))
    gas_1 = bme.gas
    gas = str(round(gas_1/1000, 2))
    
    # Calculation of AQI Score
    aqi_score = calculate_gas_score(hum_1, gas_1)
    # 
    quality_num = iaq_description(aqi_score)
    aqi = str(round(aqi_score, 2))
    
    http_post(temp, hum, pres, aqi)

    print('Temperature:', temp, ' C')
    print('Humidity:', hum, ' %')
    print('Pressure:', pres, ' hPa')
    print('Gas:', gas, ' KOhms')
    print('AQI:', aqi)

    
    if quality_num == 1:
        sms_test("MOBILE_NUM", "Hazardous AQI")
    elif quality_num == 2:
        sms_test("MOBILE_NUM", "Very Unhealthy")
    elif quality_num == 3:
        sms_test("MOBILE_NUM", "Unhealthy")
    elif quality_num == 4:
        sms_test("MOBILE_NUM", "Unhealthy for Sensitive Groups")    
    print('-------')
  except OSError as e:
    print('Failed to read sensor.')
 
  utime.sleep(10)



