import numpy as np
from scipy import signal
import time
from pythonosc.udp_client import SimpleUDPClient
from osc4py3.as_eventloop import osc_startup, osc_udp_server, osc_process, osc_terminate, osc_method
from osc4py3 import oscmethod as osm
import asyncio
from acquisition.fifo_buffer import FIFOBuffer

def find_nearest(query: int | float, reference: np.ndarray | list | FIFOBuffer) -> tuple[int, float]:
    """
    Find the nearest value in a reference array to a query value.

    Parameters
    ----------
    query : int or float
        The value to find the nearest match for.
    reference : np.ndarray | list | FIFOBuffer
        The array to search for the nearest value.

    Returns
    -------
    tuple[int, float]
        A tuple containing the index of the nearest value and the distance to it.
    """

    if isinstance(reference, FIFOBuffer):
        reference = reference.get_buffer()
    elif isinstance(reference, list):
        reference = np.array(reference)
    elif not isinstance(reference, np.ndarray):
        raise TypeError("reference must be a numpy array, list, or FIFOBuffer")
    
    if reference.size == 0:
        raise ValueError("Reference array is empty")

    distances = np.zeros(len(reference))

    for i, r in enumerate(reference):
        distances[i] = query - r

    min_distance_i = np.argmin(np.abs(distances))

    return min_distance_i, distances[min_distance_i]

def sectosamp(sec: int | float, sr: int) -> int:
    """
    Calculates the number of samples in a given number of seconds provided a sample rate.

    Parameters
    ----------
    sec : float
        The number of seconds to convert to samples.
    sr : int
        The sample rate in Hz.

    Returns
    -------
    int
        The number of samples, rounded down to the nearest integer.
    """
    samp = int(sec * sr)
    return samp

def scaler(array: np.ndarray, new_min: float, new_max: float, old_min: float = None, old_max: float = None) -> np.ndarray:
    """
    A simple linear scaler that scales an array to a given range.

    Parameters
    ----------
    array : np.ndarray
        The array to be scaled.
    new_min : float
        The minimum value of the output array.
    new_max : float
        The maximum value of the output array.
    old_min : float, optional
        The minimum value of the input array. If not provided, it will be calculated automatically.
    old_max : float, optional
        The maximum value of the input array. If not provided, it will be calculated automatically.

    Returns
    -------
    np.ndarray
        The scaled array.
    """
    if old_min is None:
        old_min = array.min()

    if old_max is None:
        old_max = array.max()

    output = ((array - old_min) * (new_max - new_min)) / (old_max - old_min) + new_min
    return output

def filter(sig: np.ndarray, order: int, cf: float | list, type: str, fs: int) -> np.ndarray:
    """
    Apply a Butterworth filter to a signal.

    Parameters
    ----------
    sig : np.ndarray
        The signal to filter.
    order : int
        The filter order.
    cf : float or list
        The critical frequencies for the filter.
    type : str
        The filter type - 'high', 'low', 'bandpass', or 'bandstop'.
    fs : int
        The sampling rate in Hz.

    Returns
    -------
    np.ndarray
        The filtered signal.
    """
    b, a = signal.butter(N=order, Wn=cf, btype=type, fs=fs)
    filtered = signal.filtfilt(b, a, sig)
    return filtered

def moving_average(sig: np.ndarray, window: int) -> np.ndarray:
    """
    Apply a moving average filter to a signal.

    Parameters
    ----------
    sig : np.ndarray
        The signal to filter.
    window : int
        The window size for the moving average filter in samples.

    Returns
    -------
    np.ndarray
        The filtered signal.
    """
    v = np.ones(window) / window
    average = np.convolve(sig, v, "same")
    return average

def vector_magnitude(coords: np.ndarray) -> float:
    """
    Calculate the magnitude of a vector representing points in Cartesian coordinate space.

    Parameters
    ----------
    coords : np.ndarray
        The coordinates of the points.

    Returns
    -------
    float
        The vector magnitude.
    """
    if not isinstance(coords, np.ndarray):
        coords = np.array(coords)

    squared = coords ** 2
    squared_sum = np.sum(squared)
    magnitude = squared_sum ** 0.5
    return magnitude

def initiate_client(ip: str = None, port: int = None) -> SimpleUDPClient:
    """
    Initialize a UDP client for sending OSC messages.

    Parameters
    ----------
    ip : str, optional
        The IP address of the client.
    port : int, optional
        The port number of the client.

    Returns
    -------
    SimpleUDPClient
        The initialized UDP client.
    """
    client = SimpleUDPClient(ip, port)
    return client

def sleep(duration: float, get_now=time.perf_counter):
    """
    Chustom sleep function with high accuracy.

    Parameters
    ----------
    duration : float
        The duration to sleep in seconds.
    get_now : callable, optional
        A function to get the current time. Defaults to time.perf_counter.
    """
    now = get_now()
    end = now + duration
    while now < end:
        now = get_now()

def ramp_value(start: float, end: float, elapsed_time: float, duration: float) -> float:
    """
    Calculate the ramped value based on elapsed time and duration.

    Parameters
    ----------
    start : float
        The starting value.
    end : float
        The target value.
    elapsed_time : float
        The elapsed time since the start of the ramp.
    duration : float
        The total duration of the ramp.

    Returns
    -------
    float
        The ramped value.
    """
    return int(start + (end - start) * min(elapsed_time / duration, 1))

def osc_to_buffer_handler_factory(buffer_dict: dict[str, FIFOBuffer]) -> callable:
    """
    Create a handler function to enqueue OSC messages into a FIFO buffer.

    Parameters
    ----------
    buffer_dict : dict
        A dictionary mapping OSC addresses to FIFOBuffer objects.

    Returns
    -------
    callable
        A handler function for OSC messages.
    """
    def osc_to_buffer_handler(address, *args):
        address = address.split("/")[1]
        address = "/" + address
        buffer_dict[address].enqueue(args)

    return osc_to_buffer_handler

def setup_osc_server(ip: str, port: int, osc_addresses: list[str], buffer_dict: dict[str, FIFOBuffer]) -> None:
    """
    Set up an OSC server to receive messages and enqueue them into buffers.

    Parameters
    ----------
    ip : str
        The IP address of the OSC server.
    port : int
        The port number of the OSC server.
    osc_addresses : list[str]
        A list of OSC addresses to listen to.
    buffer_dict : dict
        A dictionary mapping OSC addresses to FIFOBuffer objects.
    """
    osc_startup()
    osc_udp_server(ip, port, "server")
    handler = osc_to_buffer_handler_factory(buffer_dict)
    for address in osc_addresses:
        osc_method(address, handler, argscheme=osm.OSCARG_ADDRESS + osm.OSCARG_DATAUNPACK)

def process_osc():
    osc_process()

def terminate_osc():
    osc_terminate()

async def osc_loop() -> None:
    """
    Continuously process OSC messages.

    Parameters
    ----------
    None
    """
    while True:
        process_osc()
        await asyncio.sleep(0)