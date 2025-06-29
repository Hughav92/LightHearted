import os
import pandas as pd
import time
import sys
sys.path.append("../")
from utils.utils import sleep, initiate_client
from acquisition.fifo_buffer import FIFOBuffer
from config import wait_time, csv_receiver_ip, csv_receiver_port, csv_visualiser_port, visualiser, audio

def load_csvs(filepath=None, col=None):

    print("Current directory:", os.getcwd())

    if filepath is None:
        filepath = "C:/Users/Hugh/Documents/GitHub/LightHearted_Private/csv_simulator/demo_csv"

    if col is None:

        col = "Lead 1"

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
    buffer_start_index = 0
    for index, data in enumerate(zip(*values)):
        start_time = time.perf_counter()  # Start time for the iteration
        combined = dict(zip(keys, data))
        for key, value in combined.items():
            buffer_dict[key].append(value)
            if len(buffer_dict[key]) == buffer_size:
                buffer_end_index = index
                for client in clients:
                    client.send_message(f"/{key}/data", buffer_dict[key])
                buffer_dict[key] = []
                buffer_start_index = index + 1
        elapsed_time = time.perf_counter() - start_time  # Elapsed time for the iteration
        sleep_time = max(0, wait_time - elapsed_time)  # Adjust sleep time
        sleep(sleep_time)


def main():

    csv_dict = load_csvs()

    clients = []
    client = initiate_client(ip=csv_receiver_ip, port=csv_receiver_port)
    clients.append(client)

    if visualiser:
        vis_client = initiate_client(ip=csv_receiver_ip, port=csv_visualiser_port)
        clients.append(vis_client)
        
    try:
        if audio and vis_client:
            vis_client.send_message("/audio", 1)

        read_csvs(csv_dict, clients, buffer_size=1)
    
    finally:
        if audio and vis_client:
            vis_client.send_message("/audio", 0)

def csv_sim():
    main()
    

if __name__ == "__main__":
    main()




