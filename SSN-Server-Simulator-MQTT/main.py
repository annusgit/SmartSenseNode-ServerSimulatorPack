from GUI_utilities import SSN_Server_UI

# server_end = ('115.186.183.129', 36000)
# server_end = ('34.87.92.5', 1883)
server_end = ('192.168.0.120', 1883)
node_end = ('', 8888)
CURRENT_SENSOR_RATINGS = ['NONE', 5, 10, 15, 20, 25, 30, 50, 60, 100, 250]
SSN_DEFAULT_CONFIGS = [8, 50, 3, 8, 50, 3, 0, 0, 0, 0, 0, 0, 5]


def main():
    main_gui = SSN_Server_UI(window_theme="aquativo", window_title="SSN Server Simulator", window_geometry='945x735+610+120')
    main_gui.setup_input_interface(current_sensor_ratings=CURRENT_SENSOR_RATINGS, mac_addresses_filename="MAC_utilities/MAC.txt", default_configs=SSN_DEFAULT_CONFIGS)
    main_gui.setup_buttons()
    main_gui.setup_incoming_data_interface(NumOfNodes=2)
    # main_gui.setup_serial_communication(serial_port='COM29', baudrate=19200, log_file='serial_log.txt')
    # main_gui.setup_udp_communication(server_end=server_end)
    main_gui.setup_mqtt_communication(client_id="SSNBackend", remote_host=server_end[0], remote_port=server_end[1])
    # main_gui.setup_csv_data_recording(csv_file="recording/recording.csv")
    # start the main loop
    main_gui.start()
    pass


if __name__ == "__main__":
    # main(
    resistance = [1956240, 1812199, 1679700, 1557748, 1445439, 1341952, 1246540, 1158525, 1077290, 1001621, 932353, 868317, 809086, 754271, 703517, 656499, 612919, 572506, 534686, 499905,
                  467604, 437592, 409692, 383745, 359601, 337126, 316194, 296522, 278353, 261408, 245599, 230842, 217062, 204189, 192156, 180906, 170291, 160449, 151235, 142605, 134519, 126941,
                  119834, 113168, 106912, 100988, 95475, 90296, 85428, 80852, 76547, 72497, 68685, 65095, 61685, 58500, 55499, 52669, 50000, 47481, 45104, 42859, 40739, 38718, 36826, 35037, 33345,
                  31745, 30230, 28796, 27438, 26152, 24923, 23768, 22674, 21635, 20651, 19716, 18829, 17987, 17187, 16421, 15699, 15013, 14360, 13740, 13150, 12588, 12053, 11544, 11055, 10593,
                  10154, 9734, 9335, 8954, 8590, 8243, 7912, 7593, 7292, 7004, 6729, 6466, 6215, 5975, 5745, 5526, 5314, 5113, 4921, 4737, 4561, 4392]
    fahrenheit = [-39, -37, -35, -33, -31, -29, -27, -25, -23, -21, -19, -17, -15, -13, -11, -9, -7, -5, -3, -1, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39,  41,  43,
                  45,  47,  49, 51, 53, 55, 57, 59, 61, 63, 65, 67, 69, 71, 73, 75, 77, 79, 81, 83, 85, 87, 89, 91, 93, 95, 97, 99, 101, 103, 105, 107, 109, 111, 113, 115, 117, 119, 121, 123, 125,
                  127, 129, 131, 133, 135, 137, 139, 141, 143, 145, 147, 149, 151, 153, 155, 157, 159, 161, 163, 165, 167, 169, 171, 173, 175, 177, 179, 181, 183, 185, 187]
    celcius = [-39.44, -38.33, -37.22, -36.11, -35.0, -33.89, -32.78, -31.67, -30.56, -29.44, -28.33, -27.22, -26.11, -25.0, -23.89, -22.78, -21.67, -20.56, -19.44, -18.33, -17.22, -16.11, -15.0,
               -13.89, -12.78, -11.67, -10.56, -9.44, -8.33, -7.22, -6.11, -5.0, -3.89, -2.78, -1.67, -0.56, 0.56, 1.67, 2.78, 3.89, 5.0, 6.11, 7.22, 8.33, 9.44, 10.56, 11.67, 12.78, 13.89, 15.0,
               16.11, 17.22, 18.33, 19.44, 20.56, 21.67, 22.78, 23.89, 25.0, 26.11, 27.22, 28.33, 29.44, 30.56, 31.67, 32.78, 33.89, 35.0, 36.11, 37.22, 38.33, 39.44, 40.56, 41.67, 42.78, 43.89,
               45.0, 46.11, 47.22, 48.33, 49.44, 50.56, 51.67, 52.78, 53.89, 55.0, 56.11, 57.22, 58.33, 59.44, 60.56, 61.67, 62.78, 63.89, 65.0, 66.11, 67.22, 68.33, 69.44, 70.56, 71.67, 72.78,
               73.89, 75.0, 76.11, 77.22, 78.33, 79.44, 80.56, 81.67, 82.78, 83.89, 85.0, 86.11]
    # celcius = [round((x-32)*5/9, 2) for x in fahrenheit]
    print(len(resistance), len(fahrenheit))
    import matplotlib.pyplot as plt, math
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    celcius_calculated = [round(1/(0.000724+0.000244*math.log(x))-273.15, 2) for x in resistance]
    celcius_temperature_range = [c for c in range(-50, 150)]
    calculated_resistance = [round(math.exp((1/(c+273.15)-0.000724)/0.000244), 2) for c in celcius_temperature_range]
    plt.plot(calculated_resistance, celcius_temperature_range)
    plt.show()
    # Create two subplots and unpack the output array immediately
    # f, (ax1, ax2) = plt.subplots(1, 2)
    # ax1.plot(resistance, celcius)
    # ax1.set_title('Original')
    # ax2.plot(resistance_range, celcius_calculated)
    # ax2.set_title('Calculated')
    # plt.show()
    print(len(celcius_temperature_range), celcius_temperature_range)
    print(len(calculated_resistance), calculated_resistance)