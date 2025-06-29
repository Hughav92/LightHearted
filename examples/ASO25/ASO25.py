"""
LightHearted ASO25 Example Script
---------------------------------
This script sets up an asynchronous pipeline for processing ECG signals, deriving heart rates, mapping them to lighting arrays, and controlling lighting fixtures in real time.

Main features:
- Listens for OSC ECG data and simulates CSV input on demand
- Transforms ECG signals and derives heart rates
- Maps heart rates to lighting arrays for organ and baluster fixtures
- Sends lighting commands (RGB/RGBW ramps) to a lighting client
- Allows live switching of mapping functions via keyboard

Author: Hugh Alexander von Arnim (RITMO, UiO)
Date: 2025

Dependencies:
- numpy
- asyncio
- aioconsole
- keyboard
- pythonosc
- Custom LightHearted modules (see imports)

Usage:
- Run this script to start the LightHearted ASO25 lighting control pipeline.
- Press 'q' to quit, 'r' to run the CSV simulator.
- Press 'o' to toggle organ mapping, 'b' to toggle baluster mapping.
- Use left/right arrow keys or number keys to switch mapping modes.

"""
import sys
sys.path.append("../..")
import asyncio
import aioconsole
import os
import numpy as np
import keyboard
from multiprocessing import Process
from utils.utils import setup_osc_server, osc_loop, FIFOBuffer, initiate_client
from csv_simulator.csv_simulator import csv_sim
from derivation.heart_rate import heart_rate
from derivation.transforms import pan_tompkins
from derivation.mapping_array import MappingArray
from mapping.lighting_array import LightingArray
from mapping.mapping_functions import *
from mapping.mapper import ContinuousMapper, TriggerMapper
from communication.grandma3_osc import *
from examples.ASO25.ASO25_config import *

async def listen_for_commands(tasks: list[asyncio.Task]) -> None:
    """
    Asynchronously listens for user commands from the console.
    - 'q': Cancels all running tasks and stops the event loop (quits the program).
    - 'r': Starts the CSV simulator in a separate process.

    Parameters
    ----------
    tasks : list[asyncio.Task]
        List of asyncio tasks to be cancelled when quitting.
    """
    while True:
        user_input = await aioconsole.ainput("Enter 'q' to quit or 'r' to run simulator: ")
        if user_input.lower() == 'q':
            for task in tasks:
                task.cancel()
            await asyncio.sleep(0.1)
            loop = asyncio.get_running_loop()
            loop.stop()
            break
        elif user_input.lower() == 'r':
            p_csv = Process(target=csv_sim)
            p_csv.start()

async def transform_signals(ecg_buffer_dict: dict[str, FIFOBuffer], transformed_dict: dict[str, FIFOBuffer], osc_addresses: list) -> None:
    """
    Asynchronously transforms ECG signals in the FIFO buffers using the Pan-Tompkins algorithm.
    Stores the transformed results in the provided transformed_dict.

    Parameters
    ----------
    ecg_buffer_dict : dict[str, FIFOBuffer]
        Dictionary of raw ECG signal buffers keyed by OSC address.
    transformed_dict : dict[str, FIFOBuffer]
        Dictionary to store transformed ECG signals keyed by OSC address.
    osc_addresses : list
        List of OSC addresses to process.
    """
    while True:
        ecg_buffer_dict_copy = ecg_buffer_dict.copy()
        for address in osc_addresses:
            if ecg_buffer_dict_copy[address].get_size() > 21:
                result = ecg_buffer_dict_copy[address].transform_tick([pan_tompkins], [(5, 12, 0.15, 256)], [{}], mode="update")
                if result is not None:
                    transformed_dict[address].enqueue(result)
        await asyncio.sleep(0)

async def derive_heart_rate(transformed_dict: dict[str, FIFOBuffer], heart_rate_buffer_dict: dict[str, FIFOBuffer], osc_addresses: list) -> None:
    """
    Asynchronously derives heart rate from transformed ECG signals and stores the results in heart_rate_buffer_dict.

    Parameters
    ----------
    transformed_dict : dict[str, FIFOBuffer]
        Dictionary of transformed ECG signal buffers keyed by OSC address.
    heart_rate_buffer_dict : dict[str, FIFOBuffer]
        Dictionary to store derived heart rate values keyed by OSC address.
    osc_addresses : list
        List of OSC addresses to process.
    """
    while True:
        transformed_dict_copy = transformed_dict.copy()
        for address in osc_addresses:
            if transformed_dict_copy[address].is_full():
                result = transformed_dict_copy[address].transform_tick([heart_rate], [(10, 256)], [{}], mode="time", interval=1000, output_index=0)
                if result is not None:
                    heart_rate_buffer_dict[address].enqueue(result)
        await asyncio.sleep(0)

async def hr_reduction(mapping_array: MappingArray) -> None:
    """
    Asynchronously reduces heart rate buffers to a single value per channel using np.mean and updates the mapping array.

    Parameters
    ----------
    mapping_array : MappingArray
        The mapping array to update with reduced heart rate values.

    Returns
    -------
    None
    """
    while True:
        mapping_array.update_array_ticks([np.mean], args=(), kwargs=None, mode="update")
        await asyncio.sleep(0)

async def derive_heart_rate_peaks(transformed_dict: dict[str, FIFOBuffer], peak_buffer_dict: dict[str, FIFOBuffer], osc_addresses: list) -> None:
    """
    Asynchronously derives heart rate peaks from transformed ECG signals and stores them in peak_buffer_dict.

    Parameters
    ----------
    transformed_dict : dict[str, FIFOBuffer]
        Dictionary of transformed ECG signal buffers keyed by OSC address.
    peak_buffer_dict : dict[str, FIFOBuffer]
        Dictionary to store derived heart rate peaks keyed by OSC address.
    osc_addresses : list
        List of OSC addresses to process.

    Returns
    -------
    None
    """
    while True:
        transformed_dict_copy = transformed_dict.copy()
        for address in osc_addresses:
            if transformed_dict_copy[address].is_full():
                result = transformed_dict_copy[address].transform_tick([heart_rate], [(10, 256)], [{}], mode="update", output_index=1)
                if result is not None:
                    peak_buffer_dict[address].set_buffer(result, resize_buffer=True)
        await asyncio.sleep(0)

async def organ_continuous_mapping(lighting_array: LightingArray, mapping_array: MappingArray, lighting_client, functions_container=None) -> None:
    """
    Maps heart rate data to the organ lighting array and sends RGB ramp commands when updated.
    Supports live updating of mapping functions via the functions_container.

    Parameters
    ----------
    lighting_array : LightingArray
        The organ lighting array to control.
    mapping_array : MappingArray
        The mapping array containing heart rate data.
    lighting_client : object
        The client used to send lighting commands.
    functions_container : dict, optional
        Dictionary containing mapping functions and their arguments for live updates.

    Returns
    -------
    None
    """
    if functions_container is not None:
        r_functions = functions_container["r_functions"]
        g_functions = functions_container["g_functions"]
        b_functions = functions_container["b_functions"]
        r_kwargs_list = functions_container["r_kwargs_list"]
        g_kwargs_list = functions_container["g_kwargs_list"]
        b_kwargs_list = functions_container["b_kwargs_list"]
    else:
        r_functions = [ones]
        g_functions = [flip_range, offset, scale]
        b_functions = [zeros]
        r_kwargs_list = []
        g_kwargs_list = [{"min": 0, "max": 1}, {"offset": 0.4}, {"scale": 0.6}]
        b_kwargs_list = []

    channel_functions = [r_functions, g_functions, b_functions]
    channel_kwargs_list = [r_kwargs_list, g_kwargs_list, b_kwargs_list]

    functions = [range_scaler, dimensionality_expansion, np.clip, range_scaler]
    args = [ (0, 1, 60, 120), (channel_functions, channel_kwargs_list), (0, 1), (0, 100, 0, 1)]
    kwargs = [{}, {}, {}, {}]

    organ_continuous_mapper = ContinuousMapper(mapping_array, lighting_array, functions, args, kwargs)

    if functions_container is not None:
        last_config = {
            "r_functions": r_functions,
            "g_functions": g_functions,
            "b_functions": b_functions,
            "r_kwargs_list": r_kwargs_list,
            "g_kwargs_list": g_kwargs_list,
            "b_kwargs_list": b_kwargs_list,
        }
    else:
        last_config = None

    while True:
        mapping_changed = False
        if functions_container is not None:
            mapping_changed = any(
                functions_container[key] != last_config[key]
                for key in last_config
            )
            if mapping_changed:
                r_functions = functions_container["r_functions"]
                g_functions = functions_container["g_functions"]
                b_functions = functions_container["b_functions"]
                r_kwargs_list = functions_container["r_kwargs_list"]
                g_kwargs_list = functions_container["g_kwargs_list"]
                b_kwargs_list = functions_container["b_kwargs_list"]
                channel_functions = [r_functions, g_functions, b_functions]
                channel_kwargs_list = [r_kwargs_list, g_kwargs_list, b_kwargs_list]
                functions = [range_scaler, dimensionality_expansion, np.clip, range_scaler]
                args = [ (0, 1, 60, 120), (channel_functions, channel_kwargs_list), (0, 1), (0, 100, 0, 1)]
                kwargs = [{}, {}, {}, {}]
                organ_continuous_mapper.set_functions(functions, args, kwargs)
                last_config = {
                    "r_functions": r_functions,
                    "g_functions": g_functions,
                    "b_functions": b_functions,
                    "r_kwargs_list": r_kwargs_list,
                    "g_kwargs_list": g_kwargs_list,
                    "b_kwargs_list": b_kwargs_list,
                }
        if mapping_array.updated or mapping_changed:
            mapping_array.spatial_expansion(interpolate_1d, args=(lighting_array.no_leds, lighting_array.get_anchor_positions()), expansion_name="organ")
            organ_continuous_mapper.apply_mapping("rgb", expansion_name="organ")
            await lighting_array.send_command(
                ramp_RGB,
                duration=1.0,
                step_time=0.5,
                fixtures=lighting_array.fixtures,
                r_start = lighting_array.get_previous_rgb()[0],
                g_start = lighting_array.get_previous_rgb()[1],
                b_start = lighting_array.get_previous_rgb()[2],
                r_end = lighting_array.get_rgb()[0],
                g_end = lighting_array.get_rgb()[1],
                b_end = lighting_array.get_rgb()[2],
                client = lighting_client
            )
        await asyncio.sleep(0)

async def baluster_continuous_mapping(lighting_array: LightingArray, mapping_array: MappingArray, lighting_client, functions_container=None) -> None:
    """
    Maps heart rate data to a baluster lighting array and sends RGBW ramp commands when updated.
    Supports live updating of mapping functions via the functions_container.

    Parameters
    ----------
    lighting_array : LightingArray
        The baluster lighting array to control.
    mapping_array : MappingArray
        The mapping array containing heart rate data.
    lighting_client : object
        The client used to send lighting commands.
    functions_container : dict, optional
        Dictionary containing mapping functions and their arguments for live updates.

    Returns
    -------
    None
    """
    if functions_container is not None:
        r_functions = functions_container["r_functions"]
        g_functions = functions_container["g_functions"]
        b_functions = functions_container["b_functions"]
        w_functions = functions_container["w_functions"]
        r_kwargs_list = functions_container["r_kwargs_list"]
        g_kwargs_list = functions_container["g_kwargs_list"]
        b_kwargs_list = functions_container["b_kwargs_list"]
        w_kwargs_list = functions_container["w_kwargs_list"]
    else:
        r_functions = [ones]
        g_functions = [flip_range, offset, scale]
        b_functions = [zeros]
        w_functions = [zeros]
        r_kwargs_list = []
        g_kwargs_list = [{"min": 0, "max": 1}, {"offset": 0.4}, {"scale": 0.6}]
        b_kwargs_list = []
        w_kwargs_list = []

    channel_functions = [r_functions, g_functions, b_functions, w_functions]
    channel_kwargs_list = [r_kwargs_list, g_kwargs_list, b_kwargs_list, w_kwargs_list]

    functions = [range_scaler, dimensionality_expansion, np.clip, range_scaler]
    args = [ (0, 1, 60, 120), (channel_functions, channel_kwargs_list), (0, 1), (0, 100, 0, 1)]
    kwargs = [{}, {}, {}, {}]

    baluster_continuous_mapper = ContinuousMapper(mapping_array, lighting_array, functions, args, kwargs)

    if functions_container is not None:
        last_config = {
            "r_functions": r_functions,
            "g_functions": g_functions,
            "b_functions": b_functions,
            "w_functions": w_functions,
            "r_kwargs_list": r_kwargs_list,
            "g_kwargs_list": g_kwargs_list,
            "b_kwargs_list": b_kwargs_list,
            "w_kwargs_list": w_kwargs_list,
        }
    else:
        last_config = None

    while True:
        mapping_changed = False
        if functions_container is not None:
            mapping_changed = any(
                functions_container[key] != last_config[key]
                for key in last_config
            )
            if mapping_changed:
                r_functions = functions_container["r_functions"]
                g_functions = functions_container["g_functions"]
                b_functions = functions_container["b_functions"]
                w_functions = functions_container["w_functions"]
                r_kwargs_list = functions_container["r_kwargs_list"]
                g_kwargs_list = functions_container["g_kwargs_list"]
                b_kwargs_list = functions_container["b_kwargs_list"]
                w_kwargs_list = functions_container["w_kwargs_list"]
                channel_functions = [r_functions, g_functions, b_functions, w_functions]
                channel_kwargs_list = [r_kwargs_list, g_kwargs_list, b_kwargs_list, w_kwargs_list]
                functions = [range_scaler, dimensionality_expansion, np.clip, range_scaler]
                args = [ (0, 1, 60, 120), (channel_functions, channel_kwargs_list), (0, 1), (0, 100, 0, 1)]
                kwargs = [{}, {}, {}, {}]
                baluster_continuous_mapper.set_functions(functions, args, kwargs)
                last_config = {
                    "r_functions": r_functions,
                    "g_functions": g_functions,
                    "b_functions": b_functions,
                    "w_functions": w_functions,
                    "r_kwargs_list": r_kwargs_list,
                    "g_kwargs_list": g_kwargs_list,
                    "b_kwargs_list": b_kwargs_list,
                    "w_kwargs_list": w_kwargs_list,
                }
        if mapping_array.updated or mapping_changed:
            mapping_array.spatial_expansion(fill_1d, args=(lighting_array.no_leds, mapping_array.get_values(["/conductor"])), expansion_name="baluster")
            baluster_continuous_mapper.apply_mapping("rgbw", expansion_name="baluster")
            await lighting_array.send_command(
                ramp_RGBW,
                duration=1.0,
                step_time=0.5,
                fixtures=lighting_array.fixtures,
                r_start=lighting_array.get_previous_rgbw()[0],
                g_start=lighting_array.get_previous_rgbw()[1],
                b_start=lighting_array.get_previous_rgbw()[2],
                w_start=lighting_array.get_previous_rgbw()[3],
                r_end=lighting_array.get_rgbw()[0],
                g_end=lighting_array.get_rgbw()[1],
                b_end=lighting_array.get_rgbw()[2],
                w_end=lighting_array.get_rgbw()[3],
                client=lighting_client
            )
        await asyncio.sleep(0)

async def organ_trigger_mapping(lighting_array: LightingArray, signal_buffers: dict[str, FIFOBuffer], peak_buffers: dict[str, FIFOBuffer], lighting_client) -> None:
    """
    Maps detected peaks in ECG signals to intensity pulses in the organ lighting array using trigger-action mapping.
    Each channel is mapped independently using a TriggerMapper.

    Parameters
    ----------
    lighting_array : LightingArray
        The organ lighting array to control.
    signal_buffers : dict[str, FIFOBuffer]
        Dictionary of ECG signal buffers keyed by channel.
    peak_buffers : dict[str, FIFOBuffer]
        Dictionary of peak buffers keyed by channel.
    lighting_client : object
        The client used to send lighting commands.

    Returns
    -------
    None
    """
    trigger_functions = {key: PeakCrossesIndexTrigger(signal_buffers[key].centre_index) for key in signal_buffers.keys()}
    action_functions = {key: pulse_intensity for key in signal_buffers.keys()}
    action_args = {key: (lighting_array.anchors[i], 100, 40, 0.1, lighting_client, False) for i, key in enumerate(signal_buffers.keys())}
    trigger_mappers = {key: TriggerMapper(
        reference_buffer=signal_buffers[key],
        query_buffer=peak_buffers[key],
        trigger_functions=trigger_functions[key],
        action_function=action_functions[key],
        action_args=action_args[key]
    ) for key in signal_buffers.keys()}

    trigger_tasks = [asyncio.create_task(trigger_mapper.run()) for trigger_mapper in trigger_mappers.values()]

    try:
        while True:
            await asyncio.sleep(0)
    except asyncio.CancelledError:
        for t in trigger_tasks:
            t.cancel()
        await asyncio.gather(*trigger_tasks, return_exceptions=True)
        raise

async def initialise_lighting_parameters(lighting_array: LightingArray, lighting_client) -> None:
    """
    Initialises the lighting parameters for the lighting array by sending commands to set the initial RGB and intensity values to zero.

    Parameters
    ----------
    lighting_array : LightingArray
        The lighting array to initialise.
    lighting_client : object
        The client used to send lighting commands.

    Returns
    -------
    None
    """
    lighting_array.update_intensities(np.zeros(lighting_array.no_leds))
    lighting_array.update_rgbw(np.zeros(lighting_array.no_leds), np.zeros(lighting_array.no_leds), np.zeros(lighting_array.no_leds), np.zeros(lighting_array.no_leds))
    lighting_array.send_command(
        format_intensity,
        lighting_array.fixtures,
        lighting_array.get_intensities(),
        client=lighting_client
    )
    lighting_array.send_command(
        format_RGBW,
        lighting_array.fixtures,
        lighting_array.get_rgbw()[0],
        lighting_array.get_rgbw()[1],
        lighting_array.get_rgbw()[2],
        lighting_array.get_rgbw()[3],
        client=lighting_client
    )

async def listen_for_organ_key(organ_lighting_array: LightingArray, background_lighting_array: LightingArray, hr_map: MappingArray, background_map: MappingArray, ecg_buffer_dict: dict[str, FIFOBuffer], peak_buffer_dict: dict[str, FIFOBuffer], background_buffer_dict: dict[str, FIFOBuffer], functions_container: dict[int, dict[str, list]], lighting_client) -> None:
    """
    Listens for the 'o' key press to toggle organ lighting mapping and background mapping.
    Starts or stops the relevant mapping and trigger tasks, and ramps lighting up or down accordingly.

    Parameters
    ----------
    organ_lighting_array : LightingArray
        The organ lighting array to control.
    background_lighting_array : LightingArray
        The background lighting array to control.
    hr_map : MappingArray
        Mapping array for heart rate data.
    background_map : MappingArray
        Mapping array for background data.
    ecg_buffer_dict : dict[str, FIFOBuffer]
        Dictionary of ECG signal buffers.
    peak_buffer_dict : dict[str, FIFOBuffer]
        Dictionary of peak buffers.
    background_buffer_dict : dict[str, FIFOBuffer]
        Dictionary of background signal buffers.
    functions_container : dict[int, dict[str, list]]
        Container for mapping functions and arguments.
    lighting_client : object
        The client used to send lighting commands.

    Returns
    -------
    None
    """
    organ_triggered = False
    task_organ_continuous_mapping = None
    task_organ_trigger_mapping = None
    task_background_mapping = None

    while True:
        if keyboard.is_pressed('o'):
            if not organ_triggered:
                
                task_organ_continuous_mapping = asyncio.create_task(
                    organ_continuous_mapping(organ_lighting_array, hr_map, lighting_client)
                )
                task_background_mapping = asyncio.create_task(
                    set_background(background_buffer_dict, background_map, background_lighting_array, lighting_client, functions_container)
                )
                await asyncio.gather(
                    organ_lighting_array.send_command(
                        ramp_intensity,
                        duration=5,
                        step_time=0.5,
                        fixtures=organ_lighting_array.fixtures,
                        values_start=0,
                        values_end=100,
                        client=lighting_client
                    ),
                    background_lighting_array.send_command(
                        ramp_intensity,
                        duration=5,
                        step_time=0.5,
                        fixtures=background_lighting_array.fixtures,
                        values_start=0,
                        values_end=100,
                        client=lighting_client
                    )
                )
                task_organ_trigger_mapping = asyncio.create_task(
                    organ_trigger_mapping(organ_lighting_array, ecg_buffer_dict, peak_buffer_dict, lighting_client)
                )
                organ_triggered = True
            else:
                if task_organ_trigger_mapping:
                    task_organ_trigger_mapping.cancel()
                if task_organ_continuous_mapping:
                    task_organ_continuous_mapping.cancel()
                if task_background_mapping:
                    task_background_mapping.cancel()
                await asyncio.gather(
                    organ_lighting_array.send_command(
                        ramp_intensity,
                        duration=5,
                        step_time=0.5,
                        fixtures=organ_lighting_array.fixtures,
                        values_start=100,
                        values_end=0,
                        client=lighting_client
                    ),
                    background_lighting_array.send_command(
                        ramp_intensity,
                        duration=5,
                        step_time=0.5,
                        fixtures=background_lighting_array.fixtures,
                        values_start=100,
                        values_end=0,
                        client=lighting_client
                    )
                )
                organ_triggered = False
        await asyncio.sleep(0.1)

async def listen_for_baluster_key(lighting_arrays: list[LightingArray], hr_map: MappingArray, lighting_client) -> None:
    """
    Listens for the 'b' key press to toggle baluster lighting mapping.
    All baluster lighting arrays ramp up or down concurrently.

    Parameters
    ----------
    lighting_arrays : list[LightingArray]
        List of baluster lighting arrays to control.
    hr_map : MappingArray
        Mapping array for heart rate data.
    lighting_client : object
        The client used to send lighting commands.

    Returns
    -------
    None
    """
    baluster_triggered = False
    task_baluster_mappings = []

    while True:
        if keyboard.is_pressed('b'):
            if not baluster_triggered:
                task_baluster_mappings = [
                    asyncio.create_task(baluster_continuous_mapping(lighting_array, hr_map, lighting_client))
                    for lighting_array in lighting_arrays
                ]
                await asyncio.gather(*[
                    lighting_array.send_command(
                        ramp_intensity,
                        duration=5,
                        step_time=0.5,
                        fixtures=lighting_array.fixtures,
                        values_start=0,
                        values_end=100,
                        client=lighting_client
                    ) for lighting_array in lighting_arrays
                ])
                baluster_triggered = True
            else:
                for task in task_baluster_mappings:
                    task.cancel()
                await asyncio.gather(*[
                    lighting_array.send_command(
                        ramp_intensity,
                        duration=5,
                        step_time=0.5,
                        fixtures=lighting_array.fixtures,
                        values_start=100,
                        values_end=0,
                        client=lighting_client
                    ) for lighting_array in lighting_arrays
                ])
                baluster_triggered = False
        await asyncio.sleep(0.1)

async def set_background(background_buffer_dict: dict[int, FIFOBuffer], background_map: MappingArray, lighting_array: LightingArray, lighting_client, functions_container: dict) -> None:
    """
    Continuously maps background buffer values to the background lighting array using the current mapping functions.
    Supports live updating of mapping functions via the functions_container.

    Parameters
    ----------
    background_buffer_dict : dict[int, FIFOBuffer]
        Dictionary of background signal buffers.
    background_map : MappingArray
        Mapping array for background data.
    lighting_array : LightingArray
        The background lighting array to control.
    lighting_client : object
        The client used to send lighting commands.
    functions_container : dict
        Container for mapping functions and arguments.

    Returns
    -------
    None
    """
    values = np.linspace(60, 120, len(background_buffer_dict))
    for i, val in enumerate(values):
        background_buffer_dict[i].set_buffer([val], resize_buffer=True)
    
    r_functions = functions_container["r_functions"]
    g_functions = functions_container["g_functions"]
    b_functions = functions_container["b_functions"]
    w_functions = functions_container["w_functions"]
    r_kwargs_list = functions_container["r_kwargs_list"]
    g_kwargs_list = functions_container["g_kwargs_list"]
    b_kwargs_list = functions_container["b_kwargs_list"]
    w_kwargs_list = functions_container["w_kwargs_list"]

    channel_functions = [r_functions, g_functions, b_functions, w_functions]
    channel_kwargs_list = [r_kwargs_list, g_kwargs_list, b_kwargs_list, w_kwargs_list]

    functions = [range_scaler, dimensionality_expansion, np.clip, range_scaler]
    args = [ (0, 1, 60, 120), (channel_functions, channel_kwargs_list), (0, 1), (0, 100, 0, 1)]
    kwargs = [{}, {}, {}, {}]
    
    background_continuous_mapper = ContinuousMapper(background_map, lighting_array, functions, args, kwargs)

    last_config = {
        "r_functions": r_functions,
        "g_functions": g_functions,
        "b_functions": b_functions,
        "w_functions": w_functions,
        "r_kwargs_list": r_kwargs_list,
        "g_kwargs_list": g_kwargs_list,
        "b_kwargs_list": b_kwargs_list,
        "w_kwargs_list": w_kwargs_list,
    }

    while True:
        mapping_changed = any(
            functions_container[key] != last_config[key]
            for key in last_config
        )
        if mapping_changed:
            r_functions = functions_container["r_functions"]
            g_functions = functions_container["g_functions"]
            b_functions = functions_container["b_functions"]
            w_functions = functions_container["w_functions"]
            r_kwargs_list = functions_container["r_kwargs_list"]
            g_kwargs_list = functions_container["g_kwargs_list"]
            b_kwargs_list = functions_container["b_kwargs_list"]
            w_kwargs_list = functions_container["w_kwargs_list"]

            channel_functions = [r_functions, g_functions, b_functions, w_functions]
            channel_kwargs_list = [r_kwargs_list, g_kwargs_list, b_kwargs_list, w_kwargs_list]

            functions = [range_scaler, dimensionality_expansion, np.clip, range_scaler]
            args = [ (0, 1, 60, 120), (channel_functions, channel_kwargs_list), (0, 1), (0, 100, 0, 1)]
            kwargs = [{}, {}, {}, {}]

            background_continuous_mapper.set_functions(functions, args, kwargs)

            last_config = {
                "r_functions": r_functions,
                "g_functions": g_functions,
                "b_functions": b_functions,
                "w_functions": w_functions,
                "r_kwargs_list": r_kwargs_list,
                "g_kwargs_list": g_kwargs_list,
                "b_kwargs_list": b_kwargs_list,
                "w_kwargs_list": w_kwargs_list,
            }
        background_map.update_array_ticks([identity], args=(), kwargs=None, mode="update")
        if background_map.updated or mapping_changed:
            background_continuous_mapper.apply_mapping("rgbw")
            await lighting_array.send_command(
                ramp_RGBW,
                duration=1.0,
                step_time=0.5,
                fixtures=lighting_array.fixtures,
                r_start=lighting_array.get_previous_rgbw()[0],
                g_start=lighting_array.get_previous_rgbw()[1],
                b_start=lighting_array.get_previous_rgbw()[2],
                w_start=lighting_array.get_previous_rgbw()[3],
                r_end=lighting_array.get_rgbw()[0],
                g_end=lighting_array.get_rgbw()[1],
                b_end=lighting_array.get_rgbw()[2],
                w_end=lighting_array.get_rgbw()[3],
                client=lighting_client
            )
            mapping_changed = False
        await asyncio.sleep(0)

async def listen_for_map_switch(functions_container: dict[str, list], function_index: int, functions_dict: dict[int, dict[str, list]]) -> None:
    """
    Listens for left/right arrow key or number key presses to switch between mapping modes.
    Updates the functions_container in-place to reflect the selected mapping mode.

    Parameters
    ----------
    functions_container : dict
        A dictionary containing the current mapping functions and their arguments.
    function_index : int
        The current index of the mapping mode.
    functions_dict : dict[int, dict[str, list]]
        Dictionary of all available mapping function sets.

    Returns
    -------
    None
    """
    print("Listening for left and right arrow key presses to switch colourmaps.")

    def on_key_event(event):
        nonlocal function_index
        if event.name == 'left':
            if function_index > 1:
                function_index -= 1
                functions_container["r_functions"] = functions_dict[function_index]["r_functions"]
                functions_container["g_functions"] = functions_dict[function_index]["g_functions"]
                functions_container["b_functions"] = functions_dict[function_index]["b_functions"]
                functions_container["w_functions"] = functions_dict[function_index]["w_functions"]
                functions_container["r_kwargs_list"] = functions_dict[function_index]["r_kwargs_list"]
                functions_container["g_kwargs_list"] = functions_dict[function_index]["g_kwargs_list"]
                functions_container["b_kwargs_list"] = functions_dict[function_index]["b_kwargs_list"]
                functions_container["w_kwargs_list"] = functions_dict[function_index]["w_kwargs_list"]
                print(f"Current mapping mode: {function_index}")
                print(f"r_functions: {functions_container['r_functions']}")
                print(f"g_functions: {functions_container['g_functions']}")
                print(f"b_functions: {functions_container['b_functions']}")
                print(f"w_functions: {functions_container['w_functions']}")
        elif event.name == 'right':
            if function_index < len(functions_dict):
                function_index += 1
                functions_container["r_functions"] = functions_dict[function_index]["r_functions"]
                functions_container["g_functions"] = functions_dict[function_index]["g_functions"]
                functions_container["b_functions"] = functions_dict[function_index]["b_functions"]
                functions_container["w_functions"] = functions_dict[function_index]["w_functions"]
                functions_container["r_kwargs_list"] = functions_dict[function_index]["r_kwargs_list"]
                functions_container["g_kwargs_list"] = functions_dict[function_index]["g_kwargs_list"]
                functions_container["b_kwargs_list"] = functions_dict[function_index]["b_kwargs_list"]
                functions_container["w_kwargs_list"] = functions_dict[function_index]["w_kwargs_list"]
                print(f"Current mapping mode: {function_index}")
                print(f"r_functions: {functions_container['r_functions']}")
                print(f"g_functions: {functions_container['g_functions']}")
                print(f"b_functions: {functions_container['b_functions']}")
                print(f"w_functions: {functions_container['w_functions']}")
        elif event.name in map(str, range(1, 10)):
            function_index = int(event.name)
            if function_index in functions_dict.keys():
                functions_container["r_functions"] = functions_dict[function_index]["r_functions"]
                functions_container["g_functions"] = functions_dict[function_index]["g_functions"]
                functions_container["b_functions"] = functions_dict[function_index]["b_functions"]
                functions_container["w_functions"] = functions_dict[function_index]["w_functions"]
                functions_container["r_kwargs_list"] = functions_dict[function_index]["r_kwargs_list"]
                functions_container["g_kwargs_list"] = functions_dict[function_index]["g_kwargs_list"]
                functions_container["b_kwargs_list"] = functions_dict[function_index]["b_kwargs_list"]
                functions_container["w_kwargs_list"] = functions_dict[function_index]["w_kwargs_list"]
                print(f"Current mapping mode: {function_index}")
                print(f"r_functions: {functions_container['r_functions']}")
                print(f"g_functions: {functions_container['g_functions']}")
                print(f"b_functions: {functions_container['b_functions']}")
                print(f"w_functions: {functions_container['w_functions']}")

    keyboard.on_press(on_key_event)

    try:
        while True:
            await asyncio.sleep(0)
    finally:
        keyboard.unhook_all()


async def main():
    """
    Main entry point: sets up OSC, lighting arrays, and launches all async tasks for signal processing and lighting control.
    Creates and starts all required asyncio tasks, and manages their lifecycle.

    Returns
    -------
    None
    """
    
    ecg_buffer_dict = {address: FIFOBuffer(256) for address in osc_addresses}
    transformed_dict = {address: FIFOBuffer(256) for address in osc_addresses}
    heart_rate_buffer_dict = {address: FIFOBuffer(10) for address in osc_addresses}
    peak_buffer_dict = {address: FIFOBuffer(1) for address in osc_addresses}
    hr_map = MappingArray(heart_rate_buffer_dict)

    organ_leds = LightingArray(np.arange(401, 415), np.array([403, 406, 409, 412]))
    baluster_leds_1l = LightingArray(np.arange(301, 304))
    baluster_leds_1r = LightingArray(np.arange(304, 307))
    baluster_leds_2l = LightingArray(np.arange(307, 314))
    baluster_leds_2r = LightingArray(np.arange(314, 321))
    baluster_leds_3l = LightingArray(np.arange(321, 329))
    baluster_leds_3r = LightingArray(np.arange(329, 337))

    background_leds = LightingArray(np.arange(501, 516))
    background_buffer_dict = {i: FIFOBuffer(1) for i in range(background_leds.no_leds)}
    background_map = MappingArray(background_buffer_dict)

    setup_osc_server(osc_ip, osc_port, osc_addresses, ecg_buffer_dict)
    lighting_client = initiate_client(lighting_ip, lighting_port)

    task_organ_initialisation = asyncio.create_task(initialise_lighting_parameters(organ_leds, lighting_client))
    task_baluster_initialisation_1l = asyncio.create_task(initialise_lighting_parameters(baluster_leds_1l, lighting_client))
    task_baluster_initialisation_1r = asyncio.create_task(initialise_lighting_parameters(baluster_leds_1r, lighting_client))
    task_baluster_initialisation_2l = asyncio.create_task(initialise_lighting_parameters(baluster_leds_2l, lighting_client))
    task_baluster_initialisation_2r = asyncio.create_task(initialise_lighting_parameters(baluster_leds_2r, lighting_client))
    task_baluster_initialisation_3l = asyncio.create_task(initialise_lighting_parameters(baluster_leds_3l, lighting_client))
    task_baluster_initialisation_3r = asyncio.create_task(initialise_lighting_parameters(baluster_leds_3r, lighting_client))

    task_osc = asyncio.create_task(osc_loop())
    
    task_transform = asyncio.create_task(transform_signals(ecg_buffer_dict, transformed_dict, osc_addresses))
    task_derive_hr = asyncio.create_task(derive_heart_rate(transformed_dict, heart_rate_buffer_dict, osc_addresses))
    task_map_hr = asyncio.create_task(hr_reduction(hr_map))
    task_derive_peaks = asyncio.create_task(derive_heart_rate_peaks(transformed_dict, peak_buffer_dict, osc_addresses))

    task_listen_for_organ = asyncio.create_task(
        listen_for_organ_key(
            organ_leds,
            background_leds,
            hr_map,
            background_map,
            ecg_buffer_dict,
            peak_buffer_dict,
            background_buffer_dict,
            lighting_client
        )
    )
    task_listen_for_baluster = asyncio.create_task(listen_for_baluster_key(
        [baluster_leds_1l, baluster_leds_1r, baluster_leds_2l, baluster_leds_2r, baluster_leds_3l, baluster_leds_3r],
        hr_map,
        lighting_client
    ))

    task_map_switch = asyncio.create_task(listen_for_map_switch(functions_container, function_index, functions_dict))

    all_tasks = [
        task_osc, task_transform, task_derive_hr, task_map_hr, task_derive_peaks, task_listen_for_organ, task_listen_for_baluster, task_map_switch
    ]

    task_commands = asyncio.create_task(listen_for_commands(all_tasks))

    try:
        await asyncio.gather(*all_tasks, task_commands)
    except Exception as e:
        print(f"Exception in main: {e}")
    finally:
        for task in all_tasks:
            task.cancel()
        await asyncio.gather(*all_tasks, return_exceptions=True)
        print("Exiting...")
        os._exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Exiting...")