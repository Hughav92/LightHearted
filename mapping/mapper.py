import numpy as np
import asyncio
import inspect
import sys
sys.path.append("../")
from acquisition.fifo_buffer import FIFOBuffer
from mapping.lighting_array import LightingArray
from derivation.mapping_array import MappingArray

class ContinuousMapper:
    """
    Maps a MappingArray to a LightingArray using a configurable chain of functions.

    This class allows you to apply a sequence of transformation functions (with optional arguments) to expansions from a MappingArray, and then update the LightingArray with the result. It supports mapping to different lighting parameters (e.g., intensity, RGB, RGBW) and can use different expansions of the mapping array.
    """

    def __init__(self, mapping_array: MappingArray, lighting_array: LightingArray, functions: list[callable], args_list: list[tuple] = None, kwargs_list: list[dict] = None, output_indices: list[int | None] = None):
        """
        Initialize the ContinuousMapper with a MappingArray, LightingArray, and mapping functions.

        Parameters
        ----------
        mapping_array : MappingArray
            The MappingArray instance containing the data to be mapped.
        lighting_array : LightingArray
            The LightingArray instance to be updated.
        functions : list[callable]
            List of mapping functions to apply to the data.
        args_list : list[tuple], optional
            List of positional argument tuples for each function.
        kwargs_list : list[dict], optional
            List of keyword argument dicts for each function.
        output_indices : list[int or None], optional
            List of output indices for each function. If provided, after each function call, the corresponding output index is used.
        """
        self.mapping_array = mapping_array
        self.lighting_array = lighting_array
        self.functions = functions
        self.args_list = args_list if args_list is not None else [()] * len(functions)
        self.kwargs_list = kwargs_list if kwargs_list is not None else [{}] * len(functions)
        self.output_indices = output_indices if output_indices is not None else [None] * len(functions)

    def set_functions(self, functions: list[callable], args_list: list[tuple] = None, kwargs_list: list[dict] = None, output_indices: list[int | None] = None):
        """
        Set the mapping functions for the ContinuousMapper.

        Parameters
        ----------
        functions : list[callable]
            List of mapping functions to apply.
        args_list : list[tuple], optional
            List of positional argument tuples for each function.
        kwargs_list : list[dict], optional
            List of keyword argument dicts for each function.
        output_indices : list[int or None], optional
            List of output indices for each function. If provided, after each function call, the corresponding output index is used.
        """
        self.functions = functions
        self.args_list = args_list if args_list is not None else [()] * len(functions)
        self.kwargs_list = kwargs_list if kwargs_list is not None else [{}] * len(functions)
        self.output_indices = output_indices if output_indices is not None else [None] * len(functions)

    def apply_mapping(self, parameter: str, expansion_name: str = None):
        """
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
        """

        if expansion_name is not None:
            if expansion_name not in self.mapping_array.expansions:
                raise ValueError(f"Expansion '{expansion_name}' not found in mapping_array.expansions.")
            data = self.mapping_array.expansions[expansion_name]
        else:
            data = self.mapping_array.get_array()

        data_out = data
        for i, func in enumerate(self.functions):
            func_args = self.args_list[i] if len(self.args_list) > i else ()
            func_kwargs = self.kwargs_list[i] if len(self.kwargs_list) > i else {}
            idx = self.output_indices[i] if len(self.output_indices) > i else None
            if isinstance(data_out, (tuple, list)) and all(isinstance(arr, np.ndarray) for arr in data_out):
                data_out = tuple(func(arr, *func_args, **func_kwargs) for arr in data_out)
            else:
                data_out = func(data_out, *func_args, **func_kwargs)
            if idx is not None and isinstance(data_out, (tuple, list)):
                data_out = data_out[idx]
        data = data_out

        if parameter == "intensity":
            if not (isinstance(data, np.ndarray) and data.shape == (self.lighting_array.no_leds,)):
                raise ValueError(f"Expected one array of length {self.lighting_array.no_leds} for intensity, got shape {data.shape}")
            self.lighting_array.update_intensities(data)
        elif parameter in ("red", "green", "blue", "white"):
            if not (isinstance(data, np.ndarray) and data.shape == (self.lighting_array.no_leds,)):
                raise ValueError(f"Expected one array of length {self.lighting_array.no_leds} for {parameter}, got shape {data.shape}")
            getattr(self.lighting_array, f"update_{parameter}")(data)
        elif parameter == "rgb":
            if not (isinstance(data, (tuple, list)) and len(data) == 3 and all(isinstance(arr, np.ndarray) and arr.shape == (self.lighting_array.no_leds,) for arr in data)):
                raise ValueError(f"Expected three arrays of length {self.lighting_array.no_leds} for rgb, got {type(data)} with shapes {[arr.shape for arr in data] if isinstance(data, (tuple, list)) else 'N/A'}")
            self.lighting_array.update_rgb(*data)
        elif parameter == "rgbw":
            if not (isinstance(data, (tuple, list)) and len(data) == 4 and all(isinstance(arr, np.ndarray) and arr.shape == (self.lighting_array.no_leds,) for arr in data)):
                raise ValueError(f"Expected four arrays of length {self.lighting_array.no_leds} for rgbw, got {type(data)} with shapes {[arr.shape for arr in data] if isinstance(data, (tuple, list)) else 'N/A'}")
            self.lighting_array.update_rgbw(*data)
        else:
            raise ValueError(f"Unknown parameter '{parameter}'.")
        
class TriggerMapper:
    """
    A class for mapping temporal triggers from a reference buffer and a query buffer (FIFOBuffer, np.ndarray, or list)
    to actions on a lighting array. Supports a chain of trigger functions.
    """

    def __init__(
        self,
        reference_buffer,
        query_buffer,
        trigger_functions,
        action_function: callable,
        trigger_args: list = None,
        trigger_kwargs: list = None,
        action_args: tuple = (),
        action_kwargs: dict = None,
    ):
        """
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
        """
        self.reference_buffer = reference_buffer
        self.query_buffer = query_buffer
        if isinstance(trigger_functions, (list, tuple)):
            self.trigger_functions = list(trigger_functions)
        else:
            self.trigger_functions = [trigger_functions]
        if isinstance(trigger_args, (list, tuple)):
            self.trigger_args = list(trigger_args)
        else:
            self.trigger_args = [trigger_args if trigger_args is not None else ()]

        if isinstance(trigger_kwargs, (list, tuple)):
            self.trigger_kwargs = list(trigger_kwargs)
        else:
            self.trigger_kwargs = [trigger_kwargs if trigger_kwargs is not None else {}]
        self.action_function = action_function
        self.action_args = action_args or ()
        self.action_kwargs = action_kwargs or {}

    def set_trigger_functions(self, trigger_functions, trigger_args: list = None, trigger_kwargs: list = None):
        """
        Set the trigger function chain and its arguments.

        Parameters
        ----------
        trigger_functions : callable or list[callable]
            A function or list of functions to process the trigger logic.
        trigger_args : list, optional
            List of positional argument tuples for each trigger function.
        trigger_kwargs : list, optional
            List of keyword argument dicts for each trigger function.
        """
        if isinstance(trigger_functions, (list, tuple)):
            self.trigger_functions = list(trigger_functions)
        else:
            self.trigger_functions = [trigger_functions]
        if isinstance(trigger_args, (list, tuple)):
            self.trigger_args = list(trigger_args)
        else:
            self.trigger_args = [trigger_args if trigger_args is not None else ()]

        if isinstance(trigger_kwargs, (list, tuple)):
            self.trigger_kwargs = list(trigger_kwargs)
        else:
            self.trigger_kwargs = [trigger_kwargs if trigger_kwargs is not None else {}]

    def set_action_function(self, action_function: callable, action_args: tuple = (), action_kwargs: dict = None):
        """
        Set the action (mapping) function and its arguments.

        Parameters
        ----------
        action_function : callable
            Function to call when a trigger fires.
        action_args : tuple, optional
            Positional arguments for the action function.
        action_kwargs : dict, optional
            Keyword arguments for the action function.
        """
        self.action_function = action_function
        self.action_args = action_args or ()
        self.action_kwargs = action_kwargs or {}

    async def run(self):
        """
        Continuously check for triggers and execute actions.
        """
        while True:
            if hasattr(self.query_buffer, "get_buffer"):
                query = self.query_buffer.get_buffer()
            else:
                query = self.query_buffer

            value = (self.reference_buffer, query)
            for i, func in enumerate(self.trigger_functions):
                func_args = self.trigger_args[i] if len(self.trigger_args) > i else ()
                func_kwargs = self.trigger_kwargs[i] if len(self.trigger_kwargs) > i else {}
                if i == 0:
                    result = func(*value, *func_args, **func_kwargs)
                else:
                    result = func(value, *func_args, **func_kwargs)
                if inspect.isawaitable(result):
                    result = await result
                value = result

            trigger_result = value

            if not isinstance(trigger_result, bool):
                raise TypeError(
                    f"Trigger function chain must return a bool, got {type(trigger_result).__name__}: {trigger_result}"
                )

            if trigger_result:
                if inspect.iscoroutinefunction(self.action_function):
                    await self.action_function(
                        *self.action_args,
                        **self.action_kwargs
                    )
                else:
                    self.action_function(
                        *self.action_args,
                        **self.action_kwargs
                    )
            await asyncio.sleep(0)

