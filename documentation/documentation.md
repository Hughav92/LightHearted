# LightHearted Documentation

This document provides an overview of the main classes and functions in the `acquisition`, `csv_simulator`, `derivation`, `mapping`, and `utils` modules.

---

## acquisition/fifo_buffer.py

### class FIFOBuffer

A fixed-size First-In-First-Out (FIFO) buffer for numeric data, supporting
efficient enqueuing, transformation, and statistical operations.


#### Methods:
- **__init__(size: int)**
    
    Initialize the FIFO buffer with a given maximum size.

    Parameters
    ----------
    size : int
        The maximum size of the buffer.
    
- **is_full() -> bool**
    
    Check if the buffer is full.

    Returns
    -------
    bool
        True if the buffer is full, False otherwise.
    
- **enqueue(items)**
    
    Add an item or a list of items to the buffer.
    Automatically removes the oldest items if the buffer exceeds the size.

    Parameters
    ----------
    items : list or np.ndarray or int or float
        The items to add to the buffer.
    
- **get_buffer() -> np.ndarray**
    
    Returns the buffer as a NumPy array.

    Returns
    -------
    np.ndarray
        The current buffer.
    
- **get_size() -> int**
    
    Returns the number of elements in the buffer.

    Returns
    -------
    int
        The number of elements in the buffer.
    
- **get_max_size() -> int**
    
    Returns the maximum size of the buffer.

    Returns
    -------
    int
        The maximum size of the buffer.
    
- **set_buffer(new_buffer, resize_buffer=True)**
    
    Set the buffer to a new NumPy array or list.

    Parameters
    ----------
    new_buffer : np.ndarray or list
        The new buffer to set.
    resize_buffer : bool, optional
        If True, resize the buffer size to match the new buffer length.
    
- **_calculate_centre_index() -> int**
    
    Calculate the centre index of the buffer based on its size.

    Returns
    -------
    int
        The centre index of the buffer.
    
- **clear_buffer()**
    
    Clear the buffer by resetting it to an empty array.
    
- **transform(functions, args_list=None, kwargs_list=None, output_index=None)**
    
    Apply a chain of functions to the buffer and return the result.
    Supports using 'min', 'max', 'mean', 'std', 'median' as special values in kwargs.

    Parameters
    ----------
    functions : list[callable]
        The list of functions to apply in sequence.
    args_list : list[tuple], optional
        List of positional argument tuples for each function.
    kwargs_list : list[dict], optional
        List of keyword argument dicts for each function.
    output_index : int or None, optional
        Which output to use if the final function returns multiple outputs. If None, use the entire result.
    output_indices : list[int or None], optional
            List of output indices for each function. If provided, after each function call, the corresponding output index is used.

    Returns
    -------
    np.ndarray or object
        The result after applying all functions in sequence to the buffer.
    
- **transform_tick(functions, args_list=None, kwargs_list=None, mode="update", interval=1000, output_index=None)**
    
    Only perform transform if the buffer has changed since the last call ("update" mode),
    or at a fixed interval in ms ("time" mode).

    Parameters
    ----------
    functions : list[callable]
        The list of functions to apply in sequence.
    args_list : list[tuple], optional
        List of positional argument tuples for each function.
    kwargs_list : list[dict], optional
        List of keyword argument dicts for each function.
    mode : str, optional
        "update" (default): run only if buffer has changed.
        "time": run at a fixed interval (interval).
    interval : int, optional
        Interval in milliseconds for "time" mode.
    output_index : int or None, optional
        Which output to use if the final function returns multiple outputs. If None, use the entire result.
    output_indices : list[int or None], optional
            List of output indices for each function. If provided, after each function call, the corresponding output index is used.

    Returns
    -------
    np.ndarray or None
        The result of transform if triggered, else None.
    

---

## csv_simulator/csv_simulator.py

- **load_csvs(filepath=None, col=None)**
    
    Load CSV files from a directory and extract a specified column.

    Parameters
    ----------
    filepath : str, optional
        Directory containing CSV files.
    col : str, optional
        Column name to extract from each CSV.

    Returns
    -------
    dict
        Dictionary mapping filenames to column data.
    
- **read_csvs(csv_dict, clients, buffer_size=1)**
    
    Read CSV data and send it to OSC clients in buffer-sized chunks.

    Parameters
    ----------
    csv_dict : dict
        Dictionary of CSV data.
    clients : list
        List of OSC clients.
    buffer_size : int, optional
        Number of samples per message.
    
- **main()**
    
    Main entry point for running the CSV simulator.
    
- **csv_sim()**
    
    Alias for `main()`.
    

---

## derivation/mapping_array.py

### class MappingArray

A class for handling derived features from multiple FIFO buffers to be mapped to a lighting array.


#### Methods:
- **__init__(buffer_dict)**
    
    Initialize the MappingArray with a dictionary of FIFO buffers.

    Parameters
    ----------
    buffer_dict : dict[str, np.ndarray]
        A dictionary where keys are OSC addresses and values are numpy arrays representing the buffers.
    
- **set_positions(dict)**
    
    Set the positions of the buffers in the array based on the provided dictionary.

    Parameters
    ----------
    dict : dict[str, int]
        A dictionary where keys are OSC addresses and values are their respective positions in the array.
    
- **get_array()**
    
    Get the current state of the array.

    Returns
    -------
    np.ndarray
        The current state of the array.
    
- **get_values(keys=None)**
    
    Get the values of the array for specified keys.

    Parameters
    ----------
    keys : list[str] or None, optional
        A list of keys to retrieve values for. If None, return all values.

    Returns
    -------
    np.ndarray
        The values corresponding to the specified keys.
    
- **update_array(reduction_functions, args=(), kwargs=None, output_index=None)**
    
    Update the array by applying the same reduction function(s) to all buffers.

    Parameters
    ----------
    reduction_functions : callable or list[callable]
        A single function or list of functions to apply to each buffer.
    args : tuple, optional
        Positional arguments to pass to the function(s).
    kwargs : dict, optional
        Keyword arguments to pass to the function(s).
    output_index : int or None, optional
        Which output to use if the function returns multiple outputs. If None, use the entire result.
    
- **update_array_ticks(reduction_functions, args=(), kwargs=None, mode="update", interval=1000, output_index=None)**
    
    Update the array only if any buffer has changed ("update" mode), or at a fixed interval ("time" mode).

    Parameters
    ----------
    reduction_functions : callable or list[callable]
        Function(s) to apply to each buffer.
    args : tuple, optional
        Positional arguments for the function(s).
    kwargs : dict, optional
        Keyword arguments for the function(s).
    mode : str, optional
        "update" (default): update if any buffer changed.
        "time": update at a fixed interval (interval ms).
    interval : int, optional
        Interval in milliseconds for "time" mode.
    output_index : int or None, optional
        Which output to use if the function returns multiple outputs. If None, use the entire result.

    Returns
    -------
    bool
        True if the array was updated, False otherwise.
    
- **spatial_expansion(expansion_function, args=None, kwargs=None, return_expansion=False, expansion_name=None)**
    
    Apply a spatial expansion function to the array.

    Parameters
    ----------
    expansion_function : callable
        The function to apply for spatial expansion.
    args : tuple, optional
        Positional arguments for the function.
    kwargs : dict, optional
        Keyword arguments for the function.
    return_expansion : bool, optional
        If True, return the expansion instead of storing it.
    expansion_name : str, optional
        Name of the expansion for storage.

    Returns
    -------
    np.ndarray or None
        The expanded array if return_expansion is True, otherwise None.
    

---

## mapping/mapper.py

### class ContinuousMapper

A class for mapping derived features from a mapping array to a lighting array.


#### Methods:
- **__init__(mapping_array, lighting_array, functions, args, kwargs)**
    
    Initialize the ContinuousMapper with a dictionary of FIFO buffers and a lighting array.

    Parameters
    ----------
    buffer_dict : dict[str, FIFOBuffer]
        A dictionary where keys are OSC addresses and values are FIFOBuffers representing the buffers.
    lighting_array : LightingArray
        An instance of LightingArray to map the derived features to.
    
- **set_functions(functions, args=None, kwargs=None)**
    
    Set the mapping functions for the ContinuousMapper.

    Parameters
    ----------
    functions : dict[str, callable]
        A dictionary where keys are OSC addresses and values are functions to map the derived features.
    
- **apply_mapping(parameter, expansion_name=None)**
    
    Apply the mapper's functions to the mapping array (or chosen expansion) and set the lighting array.

    Parameters
    ----------
    parameter : str
        The parameter to set ('intensity', 'red', 'green', 'blue', 'white', 'rgb', 'rgbw').
    expansion_name : str, optional
        The name of the expansion to use. If None, use the main array.

    Raises
    ------
    ValueError
        If the number or shape of the outputs does not fit the parameter.
    

### class TriggerMapper

A class for mapping temporal triggers from a reference buffer and a query buffer (FIFOBuffer, np.ndarray, or list)
to actions on a lighting array. Supports a chain of trigger functions.


#### Methods:
- **__init__(reference_buffer, query_buffer, trigger_functions, action_function, ...)**
    
    Initialize the TriggerMapper.

    Parameters
    ----------
    reference_buffer : FIFOBuffer
        The buffer to use as a reference for triggers (e.g., ECG signal).
    query_buffer : FIFOBuffer, np.ndarray, or list
        The buffer or array to use as a query for triggers (e.g., peaks).
    trigger_functions : callable or list[callable]
        A function or list of functions to process the trigger logic. The final function must return a bool.
    action_function : callable
        Async function to call when a trigger fires.
    trigger_args : list, optional
        List of positional argument tuples for each trigger function.
    trigger_kwargs : list, optional
        List of keyword argument dicts for each trigger function.
    action_args : tuple, optional
        Positional arguments for the action function.
    action_kwargs : dict, optional
        Keyword arguments for the action function.
    
- **set_trigger_functions(trigger_functions, trigger_args=None, trigger_kwargs=None)**
    
    Set the trigger function chain and its arguments. The final function must return a bool.

    Parameters
    ----------
    trigger_functions : callable or list[callable]
        A function or list of functions to process the trigger logic.
    trigger_args : list, optional
        List of positional argument tuples for each trigger function.
    trigger_kwargs : list, optional
        List of keyword argument dicts for each trigger function.
    
- **set_action_function(action_function, action_args=(), action_kwargs=None)**
    
    Set the action (mapping) function and its arguments.

    Parameters
    ----------
    action_function : callable
        Function to call when a trigger fires.
    action_args : tuple, optional
        Positional arguments for the action function.
    action_kwargs : dict, optional
        Keyword arguments for the action function.
    
- **run()**
    
    Continuously check for triggers and execute actions.
    

---

## mapping/lighting_array.py

### class LightingArray

LightingArray represents a collection of lighting fixtures (LEDs) and their color/intensity states.
Supports RGBW color channels, anchor points for mapping, and provides methods to update and retrieve channel values.


#### Methods:
- **__init__(fixtures, anchors=None)**
    
    Initialize the LightingArray with fixtures and anchors.

    Parameters
    ----------
    fixtures : list or np.ndarray
        A list or array of fixture IDs (LED indices).
    anchors : list or np.ndarray, optional
        A list or array of anchor IDs (LED indices used as mapping anchors).
    
- **set_anchors(new_anchors)**
    
    Set the anchors for the lighting array and update anchor positions.

    Parameters
    ----------
    new_anchors : list or np.ndarray
        A list or array of new anchor IDs.
    
- **get_anchor_positions()**
    
    Get the positions of the anchors in the fixture array.

    Returns
    -------
    np.ndarray
        An array of anchor positions (indices in the fixture array).
    
- **update_anchor_positions(new_anchor_positions)**
    
    Set the positions of the anchors in the fixture array.

    Parameters
    ----------
    new_anchor_positions : np.ndarray
        An array of new anchor positions (indices in the fixture array).
    
- **update_intensities(new_intensities)**
    
    Update the intensities of the fixtures (brightness for each LED).

    Parameters
    ----------
    new_intensities : np.ndarray
        An array of new intensity values for the fixtures.
    
- **update_red(new_red)**, **update_green(new_green)**, **update_blue(new_blue)**, **update_white(new_white)**
    
    Update the respective color channel values of the fixtures.

    Parameters
    ----------
    new_red/new_green/new_blue/new_white : np.ndarray
        An array of new channel values for the fixtures.
    
- **update_rgb(new_red, new_green, new_blue)**
    
    Update the RGB channel values of the fixtures.

    Parameters
    ----------
    new_red : np.ndarray
        An array of new red channel values for the fixtures.
    new_green : np.ndarray
        An array of new green channel values for the fixtures.
    new_blue : np.ndarray
        An array of new blue channel values for the fixtures.
    
- **update_rgbw(new_red, new_green, new_blue, new_white)**
    
    Update the RGBW channel values of the fixtures.

    Parameters
    ----------
    new_red : np.ndarray
        An array of new red channel values for the fixtures.
    new_green : np.ndarray
        An array of new green channel values for the fixtures.
    new_blue : np.ndarray
        An array of new blue channel values for the fixtures.
    new_white : np.ndarray
        An array of new white channel values for the fixtures.
    
- **get_intensities()**, **get_rgb()**, **get_rgbw()**
    
    Get the current channel values of the fixtures.

    Returns
    -------
    np.ndarray or tuple
        The current channel values.
    
- **get_previous_intensities()**, **get_previous_rgb()**, **get_previous_rgbw()**
    
    Get the previous channel values of the fixtures.

    Returns
    -------
    np.ndarray or tuple
        The previous channel values.
    
- **send_command(func, *args, **kwargs)**
    
    Send a command to the lighting system using a function from a lighting API.

    Parameters
    ----------
    func : callable
        A function from the lighting API to be called (e.g., format_RGB, format_intensity, etc.).
    *args
        Positional arguments to pass to the function.
    fixtures : list or np.ndarray, optional
        The list of fixtures to use. If None, uses self.fixtures.
    **kwargs
        Keyword arguments to pass to the function.

    Returns
    -------
    The result of the called function.
    

---

## mapping/mapping_functions.py

- **interpolate_1d(input_array, output_size, original_indices)**
    
    Perform 1D interpolation to map input array values to a specified output size.

    Parameters
    ----------
    input_array : np.ndarray
        The input array containing values to interpolate.
    output_size : int
        The size of the output array.
    original_indices : list[int]
        The indices in the output array corresponding to the input array values.

    Returns
    -------
    np.ndarray
        The interpolated output array.
    
- **fill_1d(input_array, output_size, input_value)**
    
    Fill a 1D array to a specified size with a given value.
    
- **dimensionality_expansion(x, channel_functions, channel_kwargs_list=None)**
    
    Expand the dimensionality of an array using channel functions.
    
- **identity(x)**, **sine(x)**, **cosine(x)**, **offset(x, offset)**, **scale(x, scale)**, **range_scaler(x, new_min, new_max, old_min=None, old_max=None)**, **zeros(x)**, **ones(x)**, **flip(x)**, **minus(x)**, **flip_range(x, min, max)**
    
    Various array transformation utilities.
    

### class PeakCrossesIndexTrigger
- **__init__(index)**
    
    Initialize with an index.
    
- **__call__(signal_buffer, peaks, auto_index=True)**
    
    Returns True if the minimum distance from any peak to the index is less than the previous minimum distance.
    
- **update_index(new_index)**
    
    Update the index for the trigger.
    

---

## utils/utils.py

- **find_nearest(query, reference)**
    
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
    
- **sectosamp(sec, sr)**
    
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
    
- **scaler(array, new_min, new_max, old_min=None, old_max=None)**
    
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
    
- **filter(sig, order, cf, type, fs)**
    
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
    
- **moving_average(sig, window)**
    
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
    
- **vector_magnitude(coords)**
    
    Calculate the magnitude of a vector representing points in Cartesian coordinate space.

    Parameters
    ----------
    coords : np.ndarray
        The coordinates of the points.

    Returns
    -------
    float
        The vector magnitude.
    
- **initiate_client(ip=None, port=None)**
    
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
    
- **sleep(duration, get_now=time.perf_counter)**
    
    Custom sleep function with high accuracy.

    Parameters
    ----------
    duration : float
        The duration to sleep in seconds.
    get_now : callable, optional
        A function to get the current time. Defaults to time.perf_counter.
    
- **ramp_value(start, end, elapsed_time, duration)**
    
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
    
- **osc_to_buffer_handler_factory(buffer_dict)**
    
    Create a handler function to enqueue OSC messages into a FIFO buffer.

    Parameters
    ----------
    buffer_dict : dict
        A dictionary mapping OSC addresses to FIFOBuffer objects.

    Returns
    -------
    callable
        A handler function for OSC messages.
    
- **setup_osc_server(ip, port, osc_addresses, buffer_dict)**
    
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
    
- **process_osc()**
    
    Process OSC messages.
    
- **terminate_osc()**
    
    Terminate the OSC server.
    
- **osc_loop()**
    
    Continuously process OSC messages.
    

---

For usage and parameter information, refer to the [tutorial notebook](tutorial.ipynb).
