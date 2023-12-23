from cc.scpi import Keysight36311A, Keysight33600A
import utils
import os
import time
import serial
import threading
import subprocess
import signal

# Current limit is a constant, do not change
CURRENT = 0.3
TIMEOUT = 30
POWER_CHANNEL = Keysight36311A.Channel.CH3
CLOCK_CHANNEL = Keysight33600A.Channel.CH1

# Unit in mVolt
VOLTAGE_LOW = 550
VOLTAGE_HIGH = 1100
VOLTAGE_STEP = 50

# Unit in MHz
BASE_BAUD = 115200
FREQUENCY_LOW = 10
FREQUENCY_HIGH = 100
FREQUENCY_STEP = 10

def toggle_reset():
    resetter.write(b"l")
    # read for acknowledgement
    retval = resetter.read_until(b"r")
    return

def monitor_dut(voltage, frequency):
    # try to read from serial port, and meanwhile get a power reading
    start_time = time.time()
    end_time = time.time()
    current_arr = []
    while end_time - start_time < TIMEOUT:
        # utils.debug_print(end_time - start_time)
        retval = ser.read_all()
        if retval != b"":
            utils.debug_print(retval)
            # success datapoint
            current_arr.append(power.getCurrent(POWER_CHANNEL))
            # compute energy used
            power_meas = sum(current_arr) / len(current_arr) * voltage / 1000
            energy = power_meas * (end_time - start_time) * 1000
            # write to log csv by power source voltage, frequency, energy
            log_file.write(str(voltage) + "," + str(frequency) + "," + str(energy) + "\n")
            # save the write
            log_file.flush()
            print("success: " + str(voltage) + "," + str(frequency) + "," + str(energy))
            return
        else:
            current_arr.append(power.getCurrent(POWER_CHANNEL))
            end_time = time.time()
            time.sleep(0.1)
    # failed
    log_file.write(str(voltage) + "," + str(frequency) + "," + str(-1) + "\n")
    log_file.flush()
    #TODO: reset the dut
    toggle_reset()
    return

# Main Loop, sweep voltage and frequency
if __name__ == "__main__":
    power = Keysight36311A("169.254.110.102")
    power.connect()

    clock = Keysight33600A("128.32.62.101")
    clock.connect()

    print(power.getInstrumentIdentification())
    print(clock.getInstrumentIdentification())
    utils.debug_print("Connected to power and clock source, ready to sweep...")

    ser = serial.Serial('/dev/ttyUSB0', BASE_BAUD)
    resetter = serial.Serial('/dev/ttyUSB3', BASE_BAUD)

    #create log file based on timestamp
    log_file = open("../logs/log_" + str(int(time.time())) + ".csv", "w")

    power.setVoltageCurrent(VOLTAGE_LOW, CURRENT, POWER_CHANNEL)
    power.enableOutput(POWER_CHANNEL)
    # power.enableCurrentProtection(POWER_CHANNEL)

    clock.setFunction(Keysight33600A.Function.SQUARE, CLOCK_CHANNEL)
    clock.setVoltageHigh(1.8, CLOCK_CHANNEL)
    clock.setVoltageLow(0, CLOCK_CHANNEL)
    clock.enableOutput(CLOCK_CHANNEL)

    toggle_reset()

    # sweep voltage and frequency
    for voltage in range(VOLTAGE_LOW, VOLTAGE_HIGH+1, VOLTAGE_STEP):
        for frequency in range(FREQUENCY_LOW, FREQUENCY_HIGH+1, FREQUENCY_STEP):
            power.setVoltageCurrent(voltage/1000, CURRENT, POWER_CHANNEL)
            clock.setFrequency(frequency*1000000, CLOCK_CHANNEL)
            ser.baudrate = BASE_BAUD * (frequency / 10)
            time.sleep(1)
            utils.debug_print("Voltage: " + str(voltage) + "mV, Frequency: " + str(frequency) + "MHz")
            openocd = subprocess.Popen("bash ~/scratch/bora/scripts/openocd.sh", shell=True)
            time.sleep(1)
            returncode = openocd.poll()
            if returncode is not None:
                print("openocd terminated with exit code: " + str(returncode))
                log_file.write(str(voltage) + "," + str(frequency) + "," + str(-1) + "\n")
                log_file.flush()
                toggle_reset()
                continue
            gdb = subprocess.Popen("bash ~/scratch/bora/scripts/program_dut.sh", shell=True)
            time.sleep(1)
            returncode = gdb.poll()
            if returncode is not None:
                print("gdb terminated with exit code: " + str(returncode))
                log_file.write(str(voltage) + "," + str(frequency) + "," + str(-1) + "\n")
                log_file.flush()
                toggle_reset()
                continue
            # start monitoring thread
            t = threading.Thread(target=monitor_dut, args=(voltage, frequency))
            t.start()
            t.join()
            time.sleep(3)
            # print("iteration completed")
            gdb.send_signal(signal.SIGINT)
            subprocess.call("killall riscv64-unknown-elf-gdb", shell=True)
            subprocess.call("killall openocd", shell=True)
            print("waiting for openocd to terminate")
            openocd.send_signal(signal.SIGINT)
            time.sleep(3)
            toggle_reset()
