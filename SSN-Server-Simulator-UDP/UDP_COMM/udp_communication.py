import select
from socket import *
import utils.utils as utils
from MAC_utilities.MAC_utils import get_mac_bytes_from_mac_string

SSN_MessageType_to_ID = {
    'GET_MAC':               1,
    'SET_MAC':               2,
    'GET_TIMEOFDAY':         3,
    'SET_TIMEOFDAY':         4,
    'GET_CONFIG':            5,
    'SET_CONFIG':            6,
    'ACK_CONFIG':            7,
    'STATUS_UPDATE':         8,
    'RESET_MACHINE_TIME':    9,
    'DEBUG_EEPROM_CLEAR':   10,
    'DEBUG_RESET_SSN':      11
}

SSN_MessageID_to_Type = {x:y for y,x in SSN_MessageType_to_ID.items()}
SSN_ActivityLevelID_to_Type = {0: 'NORMAL', 1: 'ABNORMAL', 2: 'TREADFAIL', 3: 'TCOMMFAIL'}
offset = 12


class UDP_COMM:
    def __init__(self):
        # for multiple nodes
        self.SSN_Network_Address_Mapping = {}
        self.SSN_Network_Node_names = list()
        self.SSN_Network_Nodes = list()
        self.client_socket = None
        pass

    def __del__(self):
        # close the socket and delete it
        if self.client_socket is not None:
            self.client_socket.close()
        pass

    def udp_setup_connection(self, server_address, server_port):
        # create a udp socket and return
        self.client_socket = socket(family=AF_INET, type=SOCK_DGRAM)
        try:
            self.client_socket.bind((server_address, server_port))
        except:
            self.client_socket = None
            return None
        self.client_socket.setblocking(True)
        self.client_socket.settimeout(0.1)
        return True

    def decipher_node_message(self, node_message=None):
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
            temperature = utils.get_word_from_bytes(high_byte=node_message[7], low_byte=node_message[8]) / 10.0
            humidity = utils.get_word_from_bytes(high_byte=node_message[9], low_byte=node_message[10]) / 10.0
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
        return

    def read_udp_message(self):
        # check if we have incoming data or not, because we have a time out
        try:
            in_message, (self.node_ip, self.node_port) = self.client_socket.recvfrom(1024)
        except:
            return -1, -1, None
            pass
        # insert this into the SSN network dictionary
        # print(self.node_ip, self.node_port)
        message_id, params = self.decipher_node_message(in_message)
        node_MAC_id = params[0]
        params[0] = utils.get_MAC_id_string_from_bytes(bytes=node_MAC_id)
        if node_MAC_id not in self.SSN_Network_Address_Mapping:
            self.SSN_Network_Nodes.append(node_MAC_id)
            self.SSN_Network_Node_names.append(utils.get_MAC_id_string_from_bytes(bytes=node_MAC_id))
            self.SSN_Network_Address_Mapping[node_MAC_id] = (self.node_ip, self.node_port)
            print('\033[32m' + "Added a new SSN into the network.")
            print('\033[32m' + "SSN-{} ({}): {} @ {}".format(len(self.SSN_Network_Address_Mapping), node_MAC_id, self.node_ip, self.node_port))
        # reset the IP and Port for this current node if it changed
        if node_MAC_id in self.SSN_Network_Address_Mapping.keys() and self.SSN_Network_Address_Mapping[node_MAC_id] != (self.node_ip, self.node_port):
            self.SSN_Network_Address_Mapping[node_MAC_id] = (self.node_ip, self.node_port)
            print('\033[32m' + "Updated SSN-{} ({}): {} @ {}".format(len(self.SSN_Network_Address_Mapping), node_MAC_id, self.node_ip, self.node_port))
        return self.SSN_Network_Nodes.index(node_MAC_id), message_id, params

    def udp_communication_test(self, server_address, server_port):
        client_socket = self.udp_setup_connection(server_address, server_port)
        while True:
            ready_to_read, ready_to_write, error = select.select([client_socket], [], [])
            if client_socket in ready_to_read:
                in_message, node_address = client_socket.recvfrom(100)
                out_message = self.decipher_node_message(in_message)
                print('\033[30m' + out_message)
            else:
                print('\033[30m' + "-> Nothing to read")
            pass
        pass

    def construct_set_mac_message(self, node_id, mac_address):
        mac_address_in_bytes = get_mac_bytes_from_mac_string(mac_address=mac_address)
        set_mac_message = [*node_id, SSN_MessageType_to_ID['SET_MAC'], *mac_address_in_bytes]
        return bytearray(set_mac_message)

    def send_set_mac_message(self, node_index, mac_address):
        set_mac_message = self.construct_set_mac_message(node_id=self.SSN_Network_Nodes[node_index], mac_address=mac_address)
        self.client_socket.sendto(set_mac_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def construct_set_timeofday_message(self, node_id, current_time):
        set_timeofday_message = [*node_id, SSN_MessageType_to_ID['SET_TIMEOFDAY'], int(current_time.hour), int(current_time.minute), int(current_time.second),
                                 int(current_time.day), int(current_time.month), int(current_time.year-2000)]
        return bytearray(set_timeofday_message)

    def send_set_timeofday_message(self, node_index, current_time):
        set_timeofday_message = self.construct_set_timeofday_message(node_id=self.SSN_Network_Nodes[node_index], current_time=current_time)
        self.client_socket.sendto(set_timeofday_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def construct_set_timeofday_Tick_message(self, node_id, current_Tick):
        set_timeofday_Tick_message = [*node_id, SSN_MessageType_to_ID['SET_TIMEOFDAY'], current_Tick[0], current_Tick[1], current_Tick[2], current_Tick[3]]
        print(set_timeofday_Tick_message)
        return bytearray(set_timeofday_Tick_message)

    def send_set_timeofday_Tick_message(self, node_index, current_tick):
        set_timeofday_message = self.construct_set_timeofday_Tick_message(node_id=self.SSN_Network_Nodes[node_index], current_Tick=current_tick)
        self.client_socket.sendto(set_timeofday_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def construct_set_config_message(self, node_id, config):
        set_config_message = [*node_id, SSN_MessageType_to_ID['SET_CONFIG'], *config]
        print(set_config_message)
        return bytearray(set_config_message)

    def send_set_config_message(self, node_index, config):
        set_config_message = self.construct_set_config_message(node_id=self.SSN_Network_Nodes[node_index], config=config)
        self.client_socket.sendto(set_config_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def construct_debug_reset_eeprom_message(self, node_id):
        debug_reset_eeprom_message = [*node_id, SSN_MessageType_to_ID['DEBUG_EEPROM_CLEAR']]
        return bytearray(debug_reset_eeprom_message)

    def send_debug_reset_eeprom_message(self, node_index):
        debug_reset_eeprom_message = self.construct_debug_reset_eeprom_message(node_id=self.SSN_Network_Nodes[node_index])
        self.client_socket.sendto(debug_reset_eeprom_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def construct_debug_reset_ssn_message(self, node_id):
        debug_reset_ssn_message = [*node_id, SSN_MessageType_to_ID['DEBUG_RESET_SSN']]
        return bytearray(debug_reset_ssn_message)

    def send_debug_reset_ssn_message(self, node_index):
        debug_reset_ssn_message = self.construct_debug_reset_ssn_message(node_id=self.SSN_Network_Nodes[node_index])
        self.client_socket.sendto(debug_reset_ssn_message, self.SSN_Network_Address_Mapping[self.SSN_Network_Nodes[node_index]])
        pass

    def getNodeCountinNetwork(self):
        return len(self.SSN_Network_Address_Mapping)
    pass
