# GSM-BME
SIM868 GSM module which sends air quality data from BME sensor over SMS.  

The hardware design of this project consists of a Raspberry Pi Pico with the SIM868 Module hat and a BME680 sensor. Initially, female headers were soldered to the SIM868 module so the Pi Pico can easily be inserted. Then the antennas are clipped onto the module board. The BME680 sensor is connected to the Pico on the I2C clock, I2C data, ground, and VIN pins.
