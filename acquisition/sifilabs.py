import sifi_bridge_py as sbp
from multiprocessing import Process
import time
from pythonosc.udp_client import SimpleUDPClient
import keyboard
import sys
import numpy as np
from sifi_config import mac_dict, sifi_receiver_ip, sifi_receiver_port, sifi_visualiser_ip, sifi_visualiser_port, sifi_filter, sifi_filter_low, sifi_filter_high

def connect_device(bridge: sbp.SifiBridge, device_name: str, mac_address: str) -> None:
    """
    Attempts to connect a device to the given MAC address, retrying until successful.

    Parameters
    ----------
    bridge : sbp.SifiBridge
        The SiFi bridge instance.
    device_name : str
        The name of the device to connect.
    mac_address : str
        The MAC address of the device.
    """
    bridge.select_device(device_name)
    connected = False
    while not connected:
        connected = bridge.connect(mac_address)
        if not connected:
            print(f"Failed to connect {device_name}. Retrying in 1 second...")
            time.sleep(1)
    print(f"{device_name} connected.")

def configure_channels(bridge: sbp.SifiBridge, ECG: bool = True, EMG: bool = False, EDA: bool = False, IMU: bool = False, PPG: bool = False, filter: bool = True) -> None:
    """
    Configures the channels for the SiFi device.

    Parameters
    ----------
    bridge : sbp.SifiBridge
        The SiFi bridge instance.
    ECG : bool
        Enable ECG channel. Default is True.
    EMG : bool
        Enable EMG channel. Default is False.
    EDA : bool
        Enable EDA channel. Default is False.
    IMU : bool
        Enable IMU channel. Default is False.
    PPG : bool
        Enable PPG channel. Default is False.
    filter : bool
        Enable filtering. Default is True.
    """
    bridge.set_channels(ECG, EMG, EDA, IMU, PPG)
    if filter:
        bridge.set_filters(True)
    else:
        bridge.set_filters(False)

def configure_ecg(bridge: sbp.SifiBridge, sifi_filter_low: float, sifi_filter_high: float) -> None:
    """
    Configures the ECG settings for the SiFi device.

    Parameters
    ----------
    bridge : sbp.SifiBridge
        The SiFi bridge instance.
    sifi_filter_low : float
        Low cutoff frequency for the bandpass filter.
    sifi_filter_high : float
        High cutoff frequency for the bandpass filter.
    """
    bridge.configure_emg(bandpass_freqs=(sifi_filter_low, sifi_filter_high), notch_freq=60)

def initialise_sifi_client(ip: str, port: int) -> SimpleUDPClient:
    """
    Initialises the SiFi client with the given IP and port.

    Parameters
    ----------
    ip : str
        The IP address of the SiFi client.
    port : int
        The port number of the SiFi client.

    Returns
    -------
    SimpleUDPClient
        An instance of the UDP client.
    """
    return SimpleUDPClient(ip, port)

def initialise_visualiser_client(ip: str, port: int) -> SimpleUDPClient:
    """
    Initialises the visualiser client with the given IP and port.

    Parameters
    ----------
    ip : str
        The IP address of the visualiser client.
    port : int
        The port number of the visualiser client.

    Returns
    -------
    SimpleUDPClient
        An instance of the UDP client.
    """
    return SimpleUDPClient(ip, port)

def main_sifibridge() -> None:
    """
    Main function to run the SiFi bridge and connect to devices.

    Parameters
    ----------
    None
    """
    sifi_client = initialise_sifi_client(sifi_receiver_ip, sifi_receiver_port)
    visualiser_client = initialise_visualiser_client(sifi_visualiser_ip, sifi_visualiser_port)

    sb = sbp.SifiBridge(data_transport="stdout")

    for device_name, mac_address in mac_dict.items():
        sb.create_device(device_name)

    for device_name, mac_address in mac_dict.items():
        connect_device(sb, device_name, mac_address)
        configure_channels(sb, ECG=True, EMG=False, EDA=False, IMU=False, PPG=False, filter=sifi_filter)
        configure_ecg(sb, sifi_filter_low, sifi_filter_high)

        print(f"SiFi Configuration: {sb.show()}")

    for device_name, mac_address in mac_dict.items():
        sb.select_device(device_name)
        print(sb.start())
        print(f"Started acquisition for {device_name}.")

    while True:
        packet = sb.get_data()
        if packet is None:
            continue

        osc_address = packet["id"]

        if packet["packet_type"] == "ecg":

            for key in packet["data"]:
                if key == "ecg":
                    ecg_data = packet["data"][key]
                    sifi_client.send_message(osc_address, ecg_data)
                    visualiser_client.send_message(f"{osc_address}/data", ecg_data)
    

def main() -> None:
    """
    Main function to run the SiFi bridge and connect to devices.

    Parameters
    ----------
    None
    """
    sifi_process = Process(target=main_sifibridge)
    sifi_process.start()

    while True:
        if keyboard.is_pressed('q'):
            print("Stopping data acquisition as 'q' was pressed.")
            break
        time.sleep(0.1)

    sifi_process.terminate()

if __name__ == "__main__":
    main()