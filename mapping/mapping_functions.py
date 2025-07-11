import numpy as np
import asyncio
import sys
sys.path.append("../")
from acquisition.fifo_buffer import FIFOBuffer
from utils.utils import find_nearest

def interpolate_1d(input_array: np.ndarray, output_size: int, original_indices: list[int], edge_behaviour: str = "reflect") -> np.ndarray:
    """
    Perform 1D interpolation to map input array values to a specified output size, with user-definable edge behaviour.

    Parameters
    ----------
    input_array : np.ndarray
        The input array containing values to interpolate.
    output_size : int
        The size of the output array.
    original_indices : list[int]
        The indices in the output array corresponding to the input array values.
    edge_behaviour : str, optional
        Edge behaviour when there is no original index at the edge. Options:
        - "reflect": (default) Extrapolate at the edges by reflecting the nearest value.
        - "wrap": Interpolate between the last and first value, wrapping around the array.

    Returns
    -------
    np.ndarray
        The interpolated output array.
    """
    if edge_behaviour not in ("reflect", "wrap"):
        raise ValueError(f"edge_behaviour must be 'reflect' or 'wrap', got '{edge_behaviour}'")
    original_indices = np.array(original_indices)
    input_array = np.array(input_array)
    input_size = len(input_array)

    if output_size < input_size:
        raise ValueError(f"output_size ({output_size}) must be greater than or equal to the size of input_array ({input_size})")
    if len(original_indices) != input_size:
        raise ValueError(f"original_indices must be the same size as input_array (got {len(original_indices)} and {input_size})")

    if edge_behaviour == "wrap":
        output_array = np.zeros(output_size)
        for i in range(input_size):
            output_array[original_indices[i]] = input_array[i]
        for i in range(input_size):
            start_idx = original_indices[i]
            end_idx = original_indices[(i + 1) % input_size]
            start_value = input_array[i]
            end_value = input_array[(i + 1) % input_size]
            if end_idx > start_idx:
                idx_range = range(start_idx + 1, end_idx)
                denom = end_idx - start_idx
            else:
                idx_range = list(range(start_idx + 1, output_size)) + list(range(0, end_idx))
                denom = (output_size - start_idx) + end_idx
            for j, idx in enumerate(idx_range, 1):
                weight = j / denom
                output_array[idx % output_size] = start_value + weight * (end_value - start_value)
        return output_array
    elif edge_behaviour == "reflect":
        if original_indices[0] > 0 and original_indices[-1] < output_size - 1:
            output_size = output_size + 2
            original_indices = original_indices + 1
            output_array = np.zeros(output_size)
        elif original_indices[0] > 0:
            output_size = output_size + 1
            original_indices = original_indices + 1
            output_array = np.zeros(output_size)
        elif original_indices[-1] < output_size - 1:
            output_size = output_size + 1
            output_array = np.zeros(output_size)
        else:
            output_array = np.zeros(output_size)
        for i in range(input_size):
            output_array[original_indices[i]] = input_array[i]
        for i in range(1, input_size):
            start_idx = original_indices[i-1]
            end_idx = original_indices[i]
            start_value = input_array[i-1]
            end_value = input_array[i]
            for idx in range(start_idx + 1, end_idx):
                weight = (idx - start_idx) / (end_idx - start_idx)
                output_array[idx] = start_value + weight * (end_value - start_value)
        if original_indices[0] > 0:
            start_idx = 0
            end_idx = original_indices[0]
            start_value = input_array[1]
            end_value = input_array[0]
            for idx in range(start_idx + 1, end_idx):
                weight = (idx - start_idx) / (end_idx - start_idx)
                output_array[idx] = start_value + weight * (end_value - start_value)
        if original_indices[-1] < output_size - 1:
            start_idx = original_indices[-1]
            end_idx = output_size-1
            start_value = input_array[-1]
            end_value = input_array[-2]
            for idx in range(start_idx + 1, end_idx):
                weight = (idx - start_idx) / (end_idx - start_idx)
                output_array[idx] = start_value + weight * (end_value - start_value)
        if original_indices[0] > 0 and original_indices[-1] < output_size - 1:
            return output_array[1:-1]
        elif original_indices[0] > 0:
            return output_array[1:]
        elif original_indices[-1] < output_size - 1:
            return output_array[:-1]
        else:
            return output_array
    
def fill_1d(input_array: np.ndarray, output_size: int, input_value: float) -> np.ndarray:
    """
    Fill a 1D array with a constant value.

    Parameters
    ----------
    input_value : float
        The value to fill the output array with.
    output_size : int
        The size of the output array.

    Returns
    -------
    np.ndarray
        An array filled with the specified value.
    """
    return np.full(output_size, input_value)

def dimensionality_expansion(x: np.ndarray, channel_functions: list[list[callable]], channel_args_list: list[list[tuple]] = None, channel_kwargs_list: list[list[dict]] = None) -> tuple:
    """
    Perform parametric expansion on an input array using multiple functions for any number of channels (e.g., RGB, RGBW, etc.).

    Parameters
    ----------
    x : np.ndarray
        The input array to be expanded.
    channel_functions : list[list[callable]]
        A list where each element is a list of functions to be applied to a channel (e.g., [r_funcs, g_funcs, b_funcs, ...]).
    channel_args_list : list[list[tuple]], optional
        A list where each element is a list of positional argument tuples for the corresponding channel's functions.
        If not provided, defaults to empty tuples for all functions.
    channel_kwargs_list : list[list[dict]], optional
        A list where each element is a list of keyword argument dicts for the corresponding channel's functions.
        If not provided, defaults to empty dicts for all functions.

    Returns
    -------
    tuple[np.ndarray, ...]
        A tuple containing arrays for each expanded channel.
    """
    n_channels = len(channel_functions)
    if channel_kwargs_list is None:
        channel_kwargs_list = [[{}] * len(funcs) for funcs in channel_functions]
    if channel_args_list is None:
        channel_args_list = [[()] * len(funcs) for funcs in channel_functions]

    for i in range(n_channels):
        if channel_kwargs_list[i] is None or len(channel_kwargs_list[i]) != len(channel_functions[i]):
            channel_kwargs_list[i] = [{}] * len(channel_functions[i])
        if channel_args_list[i] is None or len(channel_args_list[i]) != len(channel_functions[i]):
            channel_args_list[i] = [()] * len(channel_functions[i])

    def apply_functions(values: np.ndarray, functions: list[callable], args_list: list[tuple], kwargs_list: list[dict]) -> np.ndarray:
        values = np.nan_to_num(values, nan=0, posinf=1, neginf=-1)
        for i, func in enumerate(functions):
            range_values = values[np.isfinite(values)]
            v_min = np.nanmin(range_values) if range_values.size > 0 else 0
            v_max = np.nanmax(range_values) if range_values.size > 0 else 0
            v_mean = np.mean(range_values) if range_values.size > 0 else 0
            v_std = np.std(range_values) if range_values.size > 0 else 0
            v_median = np.median(range_values) if range_values.size > 0 else 0
            kwargs = kwargs_list[i] if i < len(kwargs_list) else {}
            args = args_list[i] if i < len(args_list) else ()
            for key, value in kwargs.items():
                if value == "min":
                    kwargs[key] = v_min
                elif value == "max":
                    kwargs[key] = v_max
                elif value == "mean":
                    kwargs[key] = v_mean
                elif value == "std":
                    kwargs[key] = v_std
                elif value == "median":
                    kwargs[key] = v_median
            values = func(values, *args, **kwargs)
            values = np.nan_to_num(values, nan=0, posinf=1, neginf=-1)
        return values

    expanded_channels = tuple(
        apply_functions(x, channel_functions[i], channel_args_list[i], channel_kwargs_list[i])
        for i in range(n_channels)
    )
    return expanded_channels

def identity(x: np.ndarray) -> np.ndarray:
    """
    Identity function that returns the input value.

    Parameters
    ----------
    x : np.ndarray
        The input array.

    Returns
    -------
    np.ndarray
        The input array.
    """
    return x

def sine(x: np.ndarray) -> np.ndarray:
    """
    Sine function that returns the sine of the input value.

    Parameters
    ----------
    x : np.ndarray
        The input array.

    Returns
    -------
    np.ndarray
        The sine of the input array.
    """
    return np.sin(x)

def cosine(x: np.ndarray) -> np.ndarray:
    """
    Cosine function that returns the cosine of the input value.

    Parameters
    ----------
    x : np.ndarray
        The input array.

    Returns
    -------
    np.ndarray
        The cosine of the input array.
    """
    return np.cos(x)

def offset(x: np.ndarray, offset: float) -> np.ndarray:
    """
    Offset function that returns the input value plus an offset.

    Parameters
    ----------
    x : np.ndarray
        The input array.
    offset : float
        The offset to add to the input array.

    Returns
    -------
    np.ndarray
        The input array plus the offset.
    """
    return x + offset

def scale(x: np.ndarray, scale: float) -> np.ndarray:
    """
    Scale function that returns the input value multiplied by a scale factor.

    Parameters
    ----------
    x : np.ndarray
        The input array.
    scale : float
        The scale factor to multiply the input array by.

    Returns
    -------
    np.ndarray
        The input array multiplied by the scale factor.
    """
    return x * scale

def range_scaler(x, new_min: float, new_max: float, old_min: float = None, old_max: float = None):
    """
    A flexible linear scaler that can scale scalars, arrays, tuples/lists of arrays, or arrays of arrays to a given range.
    The input shape and type are preserved.
    """
    import numpy as np

    # If tuple/list of scalars, treat as 1D array
    if isinstance(x, (tuple, list)):
        if all(np.isscalar(xi) for xi in x):
            arr = np.asarray(x)
            # Now arr is 1D, scale as a whole
            if old_min is None:
                old_min = arr.min()
            if old_max is None:
                old_max = arr.max()
            if old_max == old_min:
                return type(x)([new_min for _ in arr])
            output = ((arr - old_min) * (new_max - new_min)) / (old_max - old_min) + new_min
            return type(x)(output.tolist())
        else:
            # Otherwise, recurse
            return type(x)(range_scaler(xi, new_min, new_max, old_min, old_max) for xi in x)

    arr = np.asarray(x)

    # If 2D or higher, apply to each row (or sub-array) recursively
    if arr.ndim > 1:
        return np.array([range_scaler(sub, new_min, new_max, old_min, old_max) for sub in arr])

    # Now arr is 1D or scalar
    if old_min is None:
        old_min = arr.min() if hasattr(arr, "min") else arr
    if old_max is None:
        old_max = arr.max() if hasattr(arr, "max") else arr

    if old_max == old_min:
        return np.full_like(arr, new_min)

    output = ((arr - old_min) * (new_max - new_min)) / (old_max - old_min) + new_min

    if np.isscalar(x):
        return output.item()
    return output

def zeros(x: np.ndarray) -> np.ndarray:
    """
    Zero function that returns an array of zeros.

    Parameters
    ----------
    x : np.ndarray
        The input array.

    Returns
    -------
    np.ndarray
        An array of zeros with the same shape as the input array.
    """
    return np.zeros_like(x)

def ones(x: np.ndarray) -> np.ndarray:
    """
    Ones function that returns an array of ones.

    Parameters
    ----------
    x : np.ndarray
        The input array.

    Returns
    -------
    np.ndarray
        An array of ones with the same shape as the input array.
    """
    return np.ones_like(x)

def flip(x: np.ndarray) -> np.ndarray:
    """
    Flip function that returns the input array in reverse order.

    Parameters
    ----------
    x : np.ndarray
        The input array.

    Returns
    -------
    np.ndarray
        The input array in reverse order.
    """
    return np.flip(x)

def minus(x: np.ndarray) -> np.ndarray:
    """
    Negation function that returns the negative of the input array.

    Parameters
    ----------
    x : np.ndarray
        The input array.

    Returns
    -------
    np.ndarray
        The negated input array.
    """
    return -x

def flip_range(x: np.ndarray, min: float, max: float) -> np.ndarray:
    """
    Flip the range of the input array around its center.

    Parameters
    ----------
    x : np.ndarray
        The input array.
    min : float
        The minimum value of the range.
    max : float
        The maximum value of the range.

    Returns
    -------
    np.ndarray
        The input array with its range flipped around the center.
    """
    centre = max - (max - min) / 2
    distances = x - centre
    x = x - distances
    distances = distances * -1
    x = x + distances

    return x
    
class CrossesIndex:
    def __init__(self, index: int):
        self.index = index
        self.previous_dist = None

    async def __call__(self, reference: np.ndarray | FIFOBuffer, query: np.ndarray | FIFOBuffer, auto_index: bool = True) -> bool:
        """
        Returns True if the minimum distance from any value in the query to the reference index is less than the previous minimum distance.
        """
        if auto_index and isinstance(reference, FIFOBuffer):
            self.index = reference.centre_index
        elif auto_index and isinstance(query, np.ndarray):
            self.index = len(query) // 2
        else:
            self.index = self.index

        if isinstance(reference, FIFOBuffer):
            if reference.get_size() == 0:
                return False
        if isinstance(query, FIFOBuffer):
            if query.get_size() == 0:
                return False
        if isinstance(reference, np.ndarray):
            if len(reference) == 0:
                return False
        if isinstance(query, np.ndarray):
            if len(query) == 0:
                return False

        _, dist = find_nearest(self.index, query)
        triggered = False
        if dist is not None and dist >= 0:
            if self.previous_dist is not None and dist >= 0 and self.previous_dist <= 0 and dist != self.previous_dist:
                triggered = True
            self.previous_dist = dist
        else:
            self.previous_dist = dist
        return triggered
    
    def update_index(self, new_index: int):
        """
        Update the index for the trigger.
        """
        self.index = new_index
        self.previous_dist = None