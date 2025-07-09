import os
import pandas as pd
import time
import sys
sys.path.append("../")
from utils.utils import sleep, initiate_client
from acquisition.fifo_buffer import FIFOBuffer
from csv_simulator.sim_config import wait_time, csv_receiver_ip, csv_receiver_port, csv_visualiser_port, visualiser, filepath, column

def load_csvs(filepath=None, col=None):

    print("Current directory:", os.getcwd())

    if filepath is None:
        filepath = "./csv/"

    if col is None:

        raise ValueError("Column name must be specified.")

    csv_dict = {}

    for file in os.listdir(filepath):

        if ".csv" in file.lower():

            csv = pd.read_csv(os.path.join(filepath, file))

            ecg = csv[col]

            filename = file.split(".")[0]

            csv_dict[filename] = ecg

    print(f"CSV Files Found: {[file for file in os.listdir(filepath)]}")

    return csv_dict

def read_csvs(csv_dict, clients, buffer_size=1):
    keys = list(csv_dict.keys())
    values = csv_dict.values()
    print(f"OSC Addresses {keys}")
    buffer_dict = {}
    for key in keys:
        buffer_dict[key] = []
    for index, data in enumerate(zip(*values)):
        start_time = time.perf_counter()
        combined = dict(zip(keys, data))
        for key, value in combined.items():
            buffer_dict[key].append(value)
            if len(buffer_dict[key]) == buffer_size:
                for client in clients:
                    client.send_message(f"/{key}/data", buffer_dict[key])
                buffer_dict[key] = []
        elapsed_time = time.perf_counter() - start_time
        sleep_time = max(0, wait_time - elapsed_time)
        sleep(sleep_time)


def main(column=None, filepath=None):

    csv_dict = load_csvs(filepath=filepath, col=column)

    clients = []
    client = initiate_client(ip=csv_receiver_ip, port=csv_receiver_port)
    clients.append(client)

    if visualiser:
        vis_client = initiate_client(ip=csv_receiver_ip, port=csv_visualiser_port)
        clients.append(vis_client)
        
    read_csvs(csv_dict, clients, buffer_size=1)


def csv_sim(column=None, filepath=None):
    main(column=column, filepath=filepath)


if __name__ == "__main__":
    main()




