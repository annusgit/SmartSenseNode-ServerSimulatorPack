import paho.mqtt.client as mqtt
from queue import Queue
from Messages import *
import utils as utils


class MQTT:
    GetterChannel = "Getters"
    StatusUpdatesChannel = "StatusUpdates"
    ConfigurationsChannel = "Configurations"

    def __init__(self, client_id, remote_host, remote_port, keep_alive=60):
        self.client = mqtt.Client(client_id=client_id, clean_session=False)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.remote_host, self.remote_port, self.keep_alive = remote_host, remote_port, keep_alive
        self.client.connect(remote_host, remote_port, keep_alive)
        self.message_queue = Queue()
        # for multiple nodes
        self.SSN_Network_Address_Mapping = {}
        self.SSN_Network_Nodes = list()
        pass

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # this is our status update channel for all nodes
        client.subscribe(self.GetterChannel, 1)
        client.subscribe(self.StatusUpdatesChannel, 1)
        client.subscribe(self.ConfigurationsChannel, 1)

        pass

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, _, __, in_message):
        # print(f"{msg.topic}: {msg.payload.decode('utf-8')}")
        # print(in_message.payload, "hello\n",in_message.qos, "hello\n", in_message.topic, "hello\n", in_message.retain)
        message_id, params = self.decipher_node_message(in_message.payload)
        node_MAC_id = params[0]
        params[0] = utils.get_MAC_id_string_from_bytes(bytes=node_MAC_id)
        # x = ['AA:BB:CC:DD:EE:FF',   '70:B3:D5:FE:4F:E5']# '70:B3:D5:FE:4F:F4','70:B3:D5:FE:4F:F2',
        # x = ['70:B3:D5:FE:4C:DF', '70:B3:D5:FE:4F:D5','AA:BB:CC:DD:EE:FF']
        # if params[0] in x:
        if node_MAC_id not in self.SSN_Network_Nodes:
            self.SSN_Network_Nodes.append(node_MAC_id)
            print('\033[32m' + "Added a new SSN into the network.")
            print('\033[32m' + "SSN-{} ({})".format(len(self.SSN_Network_Address_Mapping), node_MAC_id))
            pass
        self.message_queue.put([self.SSN_Network_Nodes.index(node_MAC_id), message_id, params])

    def decipher_node_message(self, node_message=None):
        # print(node_message)
        # node id is in the first six bytes of the message
        node_id = utils.get_MAC_id_from_bytes(bytes=node_message)
        # message id is the seventh byte
        node_message_id = node_message[6]

        # GET MAC message is received?
        if node_message_id == SSN_MessageType_to_ID['GET_MAC']:
            return node_message_id, [node_id]

        # Get configurations message is received?
        elif node_message_id == SSN_MessageType_to_ID['GET_CONFIG']:
            return node_message_id, [node_id]

        # acknowledge configurations message is received from the SSN?
        elif node_message_id == SSN_MessageType_to_ID['ACK_CONFIG']:
            configs_received = list()
            # configurations include sensor rating, max load, threshold current and sensor voltage output
            for i in range(4):
                configs_received.append(node_message[7+4*i])
                configs_received.append(node_message[8+4*i])
                configs_received.append(node_message[9+4*i])
                configs_received.append(node_message[10+4*i])
                pass
            # configurations include min-max temperature and min-max humidity readings and a report interval
            configs_received.append(node_message[23])
            configs_received.append(node_message[24])
            configs_received.append(node_message[25])
            configs_received.append(node_message[26])
            configs_received.append(node_message[27])
            return node_message_id, [node_id, configs_received]

        # Get time of day is received from the node?
        elif node_message_id == SSN_MessageType_to_ID['GET_TIMEOFDAY']:
            return node_message_id, [node_id]

        # Status update is received?
        elif node_message_id == SSN_MessageType_to_ID['STATUS_UPDATE']:
            # get node specific information
            # ambient temperature sensor
            temperature = round(utils.get_word_from_bytes(high_byte=node_message[7], low_byte=node_message[8]) / 10.0, 2)
            # object temperature sensor
            # temperature = round(utils.get_word_from_bytes(high_byte=node_message[8], low_byte=node_message[7]) * 0.02 - 273.15, 2)
            # object temperature sensor
            humidity = round(utils.get_word_from_bytes(high_byte=node_message[9], low_byte=node_message[10]) / 10.0, 2)
            state_flags = node_message[11]
            ssn_uptime = utils.get_int_from_bytes(highest_byte=node_message[60], higher_byte=node_message[61], high_byte=node_message[62], low_byte=node_message[63])
            abnormal_activity = node_message[64]
            # get machine specific information
            machine_load_currents, machine_load_percentages, machine_status, machine_state_timestamp, machine_state_duration = list(), list(), list(), list(), list()
            # print(node_message)
            for i in range(4):
                machine_load_currents.append(utils.get_word_from_bytes(high_byte=node_message[12+i*offset], low_byte=node_message[13+i*offset]) / 100.0)
                machine_load_percentages.append(node_message[14+i*offset])
                machine_status.append(node_message[15+i*offset])
                machine_state_timestamp.append(utils.get_int_from_bytes(highest_byte=node_message[16+i*offset], higher_byte=node_message[17+i*offset],
                                                                        high_byte=node_message[18+i*offset], low_byte=node_message[19+i*offset]))
                machine_state_duration.append(utils.get_int_from_bytes(highest_byte=node_message[20+i*offset], higher_byte=node_message[21+i*offset],
                                                                       high_byte=node_message[22+i*offset], low_byte=node_message[23+i*offset]))
                pass
            return node_message_id, [node_id, temperature, humidity, ssn_uptime, abnormal_activity, *machine_load_currents, *machine_load_percentages, *machine_status,
                                     *machine_state_timestamp, *machine_state_duration, state_flags]
        elif node_message_id == SSN_MessageType_to_ID['RETRIEVE_SSN_CONFIG']:
            current_configs = list()
            # configurations include sensor rating, max load, threshold current and sensor voltage output
            for i in range(4):
                current_configs.append(node_message[7+4*i])
                current_configs.append(node_message[8+4*i])
                current_configs.append(node_message[9+4*i])
                current_configs.append(node_message[10+4*i])
                pass
            # configurations include min-max temperature and min-max humidity readings and a report interval
            current_configs.append(node_message[23])
            current_configs.append(node_message[24])
            current_configs.append(node_message[25])
            current_configs.append(node_message[26])
            current_configs.append(node_message[27])
            print(current_configs)
            print("Received Sensor Configurations: \n"
                   "     >> S1-Rating: {} Arms".format(current_configs[0]) + "| M1-Threshold: {:.2f} Arms".format(current_configs[1]/10.0)+ "| M1-Maxload: {} Arms |\n".format(current_configs[2]) + "| S1-Scalar: {} Vrms" .format(current_configs[3])+
                   "     >> S2-Rating: {} Arms".format(current_configs[4]) + "| M2-Threshold: {:.2f} Arms" .format(current_configs[5]/10.0) + " | M2-Maxload: {} Arms |\n" .format(current_configs[6]) + "| S1-Scalar: {} Vrms" .format(current_configs[7]) +
                   "     >> S3-Rating: {} Arms".format(current_configs[8]) + "| M3-Threshold: {:.2f} Arms" .format(current_configs[9]/10.0) + " | M3-Maxload: {} Arms |\n" .format(current_configs[10]) +"| S1-Scalar: {} Vrms" .format(current_configs[11]) +
                   "     >> S4-Rating: {} Arms".format(current_configs[12]) + "| M4-Threshold: {:.2f} Arms" .format(current_configs[13]/10.0) + " | M4-Maxload: {} Arms |\n".format(current_configs[14]) + "| S1-Scalar: {} Vrms" .format(current_configs[15]) +
                   "     >> MIN TEMP : {} C".format(current_configs[16]) + "    | MAX TEMP : {} C    |\n".format(current_configs[17]) +
                   "     >> MIN RH   : {} %".format(current_configs[18]) + "    | MIN RH   : {} %    |\n".format(current_configs[19]) +
                   "     >> Report   : {} seconds\n".format(current_configs[20]))

            return node_message_id, [node_id, current_configs]
        return

    def send_set_mac_message(self, node_index, mac_address):
        set_mac_message = construct_set_mac_message(node_id=self.SSN_Network_Nodes[node_index], mac_address=mac_address)
        self.client.publish(topic=utils.get_MAC_id_string_from_bytes(bytes=self.SSN_Network_Nodes[node_index]), payload=set_mac_message, qos=1)
        pass

    def send_set_timeofday_message(self, node_index, current_time):
        set_timeofday_message = construct_set_timeofday_message(node_id=self.SSN_Network_Nodes[node_index], current_time=current_time)
        self.client.publish(topic=utils.get_MAC_id_string_from_bytes(bytes=self.SSN_Network_Nodes[node_index]), payload=set_timeofday_message, qos=1)
        pass

    def send_set_timeofday_Tick_message(self, node_index, current_tick):
        set_timeofday_message = construct_set_timeofday_Tick_message(node_id=self.SSN_Network_Nodes[node_index], current_Tick=current_tick)
        self.client.publish(topic=utils.get_MAC_id_string_from_bytes(bytes=self.SSN_Network_Nodes[node_index]), payload=set_timeofday_message, qos=1)
        pass

    def send_set_config_message(self, node_index, config):
        set_config_message = construct_set_config_message(node_id=self.SSN_Network_Nodes[node_index], config=config)
        self.client.publish(topic=utils.get_MAC_id_string_from_bytes(bytes=self.SSN_Network_Nodes[node_index]), payload=set_config_message, qos=1)
        pass

    def send_debug_reset_eeprom_message(self, node_index):
        print(node_index)
        debug_reset_eeprom_message = construct_debug_reset_eeprom_message(node_id=self.SSN_Network_Nodes[node_index])
        self.client.publish(topic=utils.get_MAC_id_string_from_bytes(bytes=self.SSN_Network_Nodes[node_index]), payload=debug_reset_eeprom_message, qos=1)
        pass

    def send_debug_reset_ssn_message(self, node_index):
        print(node_index)
        debug_reset_ssn_message = construct_debug_reset_ssn_message(node_id=self.SSN_Network_Nodes[node_index])
        self.client.publish(topic=utils.get_MAC_id_string_from_bytes(bytes=self.SSN_Network_Nodes[node_index]), payload=debug_reset_ssn_message, qos=1)
        pass

    def send_retrieve_ssn_config_message(self, node_index):
        print(node_index)
        retrieve_ssn_config_message = construct_retrieve_ssn_config_message(node_id=self.SSN_Network_Nodes[node_index])
        self.client.publish(topic=utils.get_MAC_id_string_from_bytes(bytes=self.SSN_Network_Nodes[node_index]), payload=retrieve_ssn_config_message, qos=1)
        pass
    pass











































