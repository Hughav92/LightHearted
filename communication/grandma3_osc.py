import time
import asyncio
from config import *
import sys
sys.path.append("../")
from utils.utils import sleep, ramp_value
import numpy as np

def format_RGB(fixtures: list, r: list = None, g: list = None, b: list = None, client=None) -> str:
    """
    Format RGB values for fixtures, including only the non-None values.

    Parameters
    ----------
    fixtures : list
        List of fixtures.
    r : list, optional
        List of red channel values.
    g : list, optional
        List of green channel values.
    b : list, optional
        List of blue channel values.
    client : object, optional
        The client object to send messages to. If not provided, the formatted strings will be returned.

    Returns
    -------
    str
        A formatted string containing fixtures and the corresponding non-None RGB values.
    """

    fixtures = fixtures.tolist()
    values = [fixtures]

    labels = []
    if r is not None:
        values.append(r)
        labels.append('R')
    if g is not None:
        values.append(g)
        labels.append('G')
    if b is not None:
        values.append(b)
        labels.append('B')

    result = []
    for items in zip(*values):
        fixture = items[0]
        formatted_values = ";".join(f'Attribute ColorRGB_{label} At {value}' for label, value in zip(labels, items[1:]))
        result.append(f"{fixture}; {formatted_values};")

    if client is not None:
        client.send_message(client, "".join(result))
    else:
        return "".join(result)

async def ramp_RGB(duration: float, step_time: float, fixtures: list, r_start: list = None, r_end: list = None, g_start: list = None, g_end: list = None, b_start: list = None, b_end: list = None, client=None) -> str:
    """
    Ramp RGB values for fixtures over a given duration.

    Parameters
    ----------
    duration : float
        The duration over which to ramp the RGB values in seconds.
    step_time : float
        The time interval between each step in output in seconds.
    fixtures : list
        List of fixtures.
    r_start : list, optional
        List of starting red channel values.
    r_end : list, optional
        List of ending red channel values.
    g_start : list, optional
        List of starting green channel values.
    g_end : list, optional
        List of ending green channel values.
    b_start : list, optional
        List of starting blue channel values.
    b_end : list, optional
        List of ending blue channel values.
    client : object, optional
        The client object to send messages to. If not provided, the formatted strings will be returned.

    Returns
    -------
    str
        A formatted string containing the final RGB values.
    """
    if r_start is None and r_end is None and g_start is None and g_end is None and b_start is None and b_end is None:
        pass

    start_time = time.perf_counter()
    result = []
    while True:
        elapsed_time = time.perf_counter() - start_time
        if elapsed_time >= duration:
            break

        r_values = [ramp_value(start, end, elapsed_time, duration) for start, end in zip(r_start, r_end)] if r_start is not None and r_end is not None else None
        g_values = [ramp_value(start, end, elapsed_time, duration) for start, end in zip(g_start, g_end)] if g_start is not None and g_end is not None else None
        b_values = [ramp_value(start, end, elapsed_time, duration) for start, end in zip(b_start, b_end)] if b_start is not None and b_end is not None else None

        formatted_string = format_RGB(fixtures, r_values, g_values, b_values)

        if client is not None:
            client.send_message(lighting_address, formatted_string)
        else:
            result.append(formatted_string)

        await asyncio.sleep(step_time)

    if client is not None:
        client.send_message(lighting_address, formatted_string)
    else:
        formatted_string = format_RGB(fixtures, r_end, g_end, b_end)
        result.append(formatted_string)
        return "".join(result)
    
def format_RGBW(fixtures: list, r: list = None, g: list = None, b: list = None, w: list = None, client=None) -> str:
    """
    Format RGBW values for fixtures, including only the non-None values.

    Parameters
    ----------
    fixtures : list
        List of fixtures.
    r : list, optional
        List of red channel values.
    g : list, optional
        List of green channel values.
    b : list, optional
        List of blue channel values.
    w : list, optional
        List of white channel values.
    client : object, optional
        The client object to send messages to. If not provided, the formatted strings will be returned.

    Returns
    -------
    str
        A formatted string containing fixtures and the corresponding non-None RGBW values.
    """
    fixtures = fixtures.tolist()
    values = [fixtures]

    labels = []
    if r is not None:
        values.append(r)
        labels.append('R')
    if g is not None:
        values.append(g)
        labels.append('G')
    if b is not None:
        values.append(b)
        labels.append('B')
    if w is not None:
        values.append(w)
        labels.append('W')

    result = []
    for items in zip(*values):
        fixture = items[0]
        formatted_values = ";".join(f'Attribute ColorRGB_{label} At {value}' for label, value in zip(labels, items[1:]))
        result.append(f"{fixture}; {formatted_values};")

    if client is not None:
        client.send_message(lighting_address, "".join(result))
    else:
        return "".join(result)

async def ramp_RGBW(
    duration: float,
    step_time: float,
    fixtures: list,
    r_start: list = None, r_end: list = None,
    g_start: list = None, g_end: list = None,
    b_start: list = None, b_end: list = None,
    w_start: list = None, w_end: list = None,
    client=None
) -> str:
    """
    Ramp RGBW values for fixtures over a given duration.

    Parameters
    ----------
    duration : float
        The duration over which to ramp the RGBW values in seconds.
    step_time : float
        The time interval between each step in output in seconds.
    fixtures : list
        List of fixtures.
    r_start : list, optional
        List of starting red channel values.
    r_end : list, optional
        List of ending red channel values.
    g_start : list, optional
        List of starting green channel values.
    g_end : list, optional
        List of ending green channel values.
    b_start : list, optional
        List of starting blue channel values.
    b_end : list, optional
        List of ending blue channel values.
    w_start : list, optional
        List of starting white channel values.
    w_end : list, optional
        List of ending white channel values.
    client : object, optional
        The client object to send messages to. If not provided, the formatted strings will be returned.

    Returns
    -------
    str
        A formatted string containing the final RGBW values.
    """
    if (r_start is None and r_end is None and
        g_start is None and g_end is None and
        b_start is None and b_end is None and
        w_start is None and w_end is None):
        pass

    start_time = time.perf_counter()
    result = []
    while True:
        elapsed_time = time.perf_counter() - start_time
        if elapsed_time >= duration:
            break

        r_values = [ramp_value(start, end, elapsed_time, duration) for start, end in zip(r_start, r_end)] if r_start is not None and r_end is not None else None
        g_values = [ramp_value(start, end, elapsed_time, duration) for start, end in zip(g_start, g_end)] if g_start is not None and g_end is not None else None
        b_values = [ramp_value(start, end, elapsed_time, duration) for start, end in zip(b_start, b_end)] if b_start is not None and b_end is not None else None
        w_values = [ramp_value(start, end, elapsed_time, duration) for start, end in zip(w_start, w_end)] if w_start is not None and w_end is not None else None

        formatted_string = format_RGBW(fixtures, r_values, g_values, b_values, w_values)

        if client is not None:
            client.send_message(lighting_address, formatted_string)
        else:
            result.append(formatted_string)

        await asyncio.sleep(step_time)

    if client is not None:
        client.send_message(lighting_address, formatted_string)
    else:
        formatted_string = format_RGBW(fixtures, r_end, g_end, b_end, w_end)
        result.append(formatted_string)
        return "".join(result)

def format_intensity(fixtures: list | np.ndarray | int | float, values: list | np.ndarray | int | float, concurrent: bool = True, client=None) -> str:
    """
    Format intensity values for fixtures.

    Parameters
    ----------
    fixtures : list | np.ndarray | int | float
        List of fixtures or a single fixture ID.
    values : list | np.ndarray | int | float
        List of intensity values or a single intensity value.
        If a single value is provided, it will be applied to all fixtures if `concurrent` is True.
    concurrent : bool, optional
        Whether to apply the same intensity to all fixtures concurrently. Default is True.
    client : object, optional
        The client object to send messages to. If not provided, the formatted strings will be returned.

    Returns
    -------
    str
        A formatted string containing the intensity values for the fixtures.
    """

    if fixtures is None or values is None:
        raise ValueError("Both 'fixtures' and 'values' must be provided.")
    if isinstance(fixtures, np.ndarray):
        fixtures = fixtures.tolist()
    if isinstance(values, np.ndarray):
        values = values.tolist()
    if not isinstance(fixtures, (list, tuple)):
        fixtures = [fixtures]
    if not isinstance(values, (list, tuple)):
        values = [values]
    if len(fixtures) == 0:
        raise ValueError("'fixtures' must not be empty.")
    if not concurrent and len(fixtures) != len(values):
        raise ValueError("Length of 'fixtures' and 'values' must match when 'concurrent' is False.")
    if isinstance(fixtures, (int, float)):
        fixtures = [fixtures]
    if isinstance(values, (int, float)):
        values = [values]
        fixtures = [fixtures]
    if not isinstance(values, (list, np.ndarray)):
        values = [values]
    
    if concurrent:
        formatted_values = f'{fixtures[0]} thru {fixtures[-1]} at {values[0]}'
    else:
        formatted_values = ";".join(f'{fixture} At {value}' for fixture, value in zip(fixtures, values))

    if client is not None:
        client.send_message(lighting_address, "".join(formatted_values))
    else:
        return "".join(formatted_values)

async def ramp_intensity(
    duration: float,
    step_time: float,
    fixtures: list,
    values_start: list | int | float,
    values_end: list | int | float,
    concurrent: bool = True,
    client=None
) -> str:
    """
    Ramp intensity values for fixtures over a given duration.

    Parameters
    ----------
    duration : float
        The duration over which to ramp the intensity values in seconds.
    step_time : float
        The time interval between each step in output in seconds.
    fixtures : list
        List of fixtures.
    values_start : list | int | float
        List of starting intensity values or a single value to apply to all fixtures.
    values_end : list | int | float
        List of ending intensity values or a single value to apply to all fixtures.
    concurrent : bool, optional
        Whether to apply the same intensity to all fixtures concurrently. Default is True.
    client : object, optional
        The client object to send messages to. If not provided, the formatted strings will be returned.

    Returns
    -------
    str
        A formatted string containing the final intensity values.
    """
    
    if isinstance(fixtures, (int, float)):
        fixtures = [fixtures]

    num_fixtures = len(fixtures)

    # Expand scalar values to lists
    if isinstance(values_start, (int, float)):
        values_start = [values_start] * num_fixtures
    if isinstance(values_end, (int, float)):
        values_end = [values_end] * num_fixtures

    start_time = time.perf_counter()
    result = []

    while True:
        elapsed_time = time.perf_counter() - start_time
        if elapsed_time >= duration:
            formatted_string = format_intensity(
                fixtures, [int(x) for x in values_end], concurrent=concurrent
            )
            if client is not None:
                client.send_message(lighting_address, formatted_string)
            else:
                result.append(formatted_string)
            break

        values = [
            ramp_value(start, end, elapsed_time, duration)
            for start, end in zip(values_start, values_end)
        ]

        formatted_string = format_intensity(fixtures, values, concurrent=concurrent)

        if client is not None:
            client.send_message(lighting_address, formatted_string)
        else:
            result.append(formatted_string)

        await asyncio.sleep(step_time)

    if client is not None:
        client.send_message(lighting_address, formatted_string)
    else:
        formatted_string = format_intensity(fixtures, values_end, concurrent=concurrent)
        result.append(formatted_string)
        return ";".join(result)

async def pulse_intensity(fixtures: list, on: int, off: int, wait_time: float, client: object, concurrent: bool = True, off_first: bool = True) -> None:
    """
    Perform a pulse effect on a fixture by setting its intensity to an "on" value, waiting, then setting it to an "off" value.

    Parameters
    ----------
    fixtures : list
        List of fixture IDs to pulse.
    on : int
        The intensity value to set for the "on" state.
    off : int
        The intensity value to set for the "off" state.
    wait_time : float
        The time in seconds to wait between the "on" and "off" states.
    client : object
        The lighting client to send messages to.
    concurrent : bool
        Whether to apply the same intensity to all fixtures concurrently.
        
    Returns
    -------
    None
    """
    if off_first:
        format_intensity(fixtures, off, concurrent=concurrent, client=client)
        await asyncio.sleep(wait_time)
        format_intensity(fixtures, on, concurrent=concurrent, client=client)
    else:
        format_intensity(fixtures, on, concurrent=concurrent, client=client)
        await asyncio.sleep(wait_time)
        format_intensity(fixtures, off, concurrent=concurrent, client=client)