import sys
from os.path import exists

header = ['time','encoder','potentiometer']

class Point:
    time = -1
    encoder = -1
    encoder_roll_avg = -1
    pot = -1
    pot_roll_avg = -1
    pot_expected = -1
    error = -1
    error_detected = 'False'

    def print(self):
        print("\ttime = " + str(self.time) + " s")
        print("\tencoder = " + str(self.encoder))
        print("\tencoder_roll_avg = " + str(self.encoder_roll_avg))
        print("\tpot = " + str(self.pot))
        print("\tpot_roll_avg = " + str(self.pot_roll_avg))
        print("\tpot_expected = " + str(self.pot_expected))
        print("\terror = " + str(self.error) + " %")
        print("\terror_detected = " + str(self.error_detected))

    def parse(line):
        values = line.split()
        if len(values) != 3:
            print("Error - expected columns is 3 but was " + str(len(values)))
            return
        try:
            point = Point()
            point.time = float(values[0])
            point.encoder = int(values[1])
            point.pot = int(values[2])
            return point
        except ValueError:
            return

class RingBuffer:
    values = list()
    size = -1
    full = 'False'

    def __init__(self, size):
        self.size = size

    def append(self, to_append):
        self.values.append(to_append)
        if (len(self.values) > self.size):
            self.values.pop(0)
            self.full = 'True'
    
    # Allow ring buffer to be iterated like a list
    def __iter__(self):
          for each in self.values:
              yield each

# Constants
degrees = 360
roll_avg_count = 10
gear_ratio = 30
encoder_res = 2048
pot_res = 256
pot_allowed_error = 5

# Variables
pot_start = -1

# Quit program if wrong number of arguments
if len(sys.argv) != 2:
    print("Error: expected arguments is 1 but was " + str(len(sys.argv)-1))
    print("Example: main.py my-sensor-data.txt")
    quit()

# Quit program if file does not exist
file_name = sys.argv[1]
if not exists(file_name):
    print(file_name + " does not exist")
    quit()

# Quit program if file is the wrong type
if not file_name.__contains__(".txt"):
    print(file_name + " is not a .txt")
    quit()

# Main
points_ring_buffer = RingBuffer(roll_avg_count)
points = list()
encoder_sum = -1
pot_sum = -1
error_threshold = 0.0
error_count = 0

with open(file_name, "r") as sensor_data:
    # Parse each point and add to ring buffer
    for line in sensor_data:
        print(line, end='')
        raw_point = Point.parse(line)
        points.append(raw_point)
        points_ring_buffer.append(raw_point)

        # Calculate rolling averages from ring buffer
        if (points_ring_buffer.full == 'True'):
            encoder_sum = 0
            pot_sum = 0
            for point in points_ring_buffer:
                encoder_sum += point.encoder
                pot_sum += point.pot
            midpoint = points_ring_buffer.values[int(roll_avg_count/2)]
            midpoint.encoder_roll_avg = encoder_sum / roll_avg_count
            midpoint.pot_roll_avg = pot_sum / roll_avg_count

            # Initialize pot start location
            if (pot_start == -1):
                pot_start = midpoint.pot_roll_avg
                print("Potentiometer start set to " + str(pot_start))

            # Set expected pot value and check for error
            midpoint.pot_expected = pot_start + (midpoint.encoder_roll_avg*pot_res/encoder_res/gear_ratio)
            midpoint.error = float((midpoint.pot_expected - midpoint.pot_roll_avg)/pot_res*100)
            lower_limit = float(midpoint.pot_roll_avg - pot_allowed_error)
            upper_limit = float(midpoint.pot_roll_avg + pot_allowed_error)
            print("\t\tUpper Limit = " + str(upper_limit))
            print("\t\tExpected is = " + str(midpoint.pot))
            print("\t\tLower Limit = " + str(lower_limit))
            if (midpoint.pot < lower_limit or midpoint.pot> upper_limit):
                midpoint.error_detected = 'True'
                error_count += 1
            midpoint.print()
    
    # Report error percentage and pass/fail
    error_percent = float(error_count / len(points))
    print (file_name + " --> " + str(error_percent) + " % points were expected error")
    if (error_percent > error_threshold):
        print (file_name + " --> Sensor error detected")
    else:
        print (file_name + " --> Sensor is good")
    