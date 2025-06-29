import numpy as np
import time

class MappingArray:
    """
    A class for handling derived features from multiple FIFO buffers to be mapped to a lighting array.
    """

    def __init__(self, buffer_dict: dict[str, np.ndarray]):
        """
        Initialize the MappingArray with a dictionary of FIFO buffers.

        Parameters
        ----------
        buffer_dict : dict[str, np.ndarray]
            A dictionary where keys are OSC addresses and values are numpy arrays representing the buffers.
        """
        self.buffer_dict = buffer_dict
        self.array = np.zeros((len(buffer_dict)))
        self.position_dict = {key : idx for idx, key in enumerate(buffer_dict.keys())}
        self.expansions = {}
        self._buffer_versions = {key: 0 for key in buffer_dict}
        self._last_update_versions = {key: -1 for key in buffer_dict}
        self._last_update_time = 0
        self.updated = False
        
    def set_positions(self, dict):
        """
        Set the positions of the buffers in the array based on the provided dictionary.

        Parameters
        ----------
        dict : dict[str, int]
            A dictionary where keys are OSC addresses and values are their respective positions in the array.
        """
        for key, position in dict.items():
            if key in self.position_dict:
                self.position_dict[key] = position
            else:
                raise KeyError(f"Key '{key}' not found in buffer_dict.")
            
    def get_array(self):
        """
        Get the current state of the array.

        Returns
        -------
        np.ndarray
            The current state of the array.
        """
        return self.array
    
    def get_values(self, keys=None):
        """
        Get the values of the array for specified keys.

        Parameters
        ----------
        keys : list[str] or None, optional
            A list of keys to retrieve values for. If None, return all values.

        Returns
        -------
        np.ndarray
            The values corresponding to the specified keys.
        """
        if keys is None:
            return self.array
        else:
            return np.array([self.array[self.position_dict[key]] for key in keys if key in self.position_dict])
    
    def update_array(self, reduction_functions, args=(), kwargs=None, output_index=None):
        """
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
        """
        if not isinstance(reduction_functions, list):
            reduction_functions = [reduction_functions]
        if kwargs is None:
            kwargs = {}

        for key, buffer in self.buffer_dict.items():
            if hasattr(buffer, "get_buffer") and hasattr(buffer, "is_full"):
                if not buffer.is_full():
                    continue
                reduced = buffer.get_buffer()
            elif isinstance(buffer, (np.ndarray, list)):
                reduced = buffer
            else:
                raise TypeError(f"Buffer for key '{key}' is not a supported type.")
            
            for func in reduction_functions:
                reduced = func(reduced, *args, **kwargs)
            if output_index is not None and isinstance(reduced, (tuple, list)):
                reduced = reduced[output_index]
            self.array[self.position_dict[key]] = reduced

    def update_array_ticks(self, reduction_functions, args=(), kwargs=None, mode="update", interval=1000, output_index=None):
        """
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
        """
        if kwargs is None:
            kwargs = {}

        now = time.perf_counter() * 1000

        if mode == "update":
            updated = False
            for key, buffer in self.buffer_dict.items():
                version = getattr(buffer, "_version", None)
                if version is not None:
                    if version != self._last_update_versions[key]:
                        updated = True
                        break
                else:
                    updated = True
                    break
            if updated:
                self.update_array(reduction_functions, args, kwargs, output_index=output_index)
                for key, buffer in self.buffer_dict.items():
                    version = getattr(buffer, "_version", None)
                    if version is not None:
                        self._last_update_versions[key] = version
                self.updated = True
                return True
            self.updated = False
            return False

        elif mode == "time":
            if now - self._last_update_time >= interval:
                self._last_update_time += interval
                if now - self._last_update_time > interval:
                    self._last_update_time = now
                self.update_array(reduction_functions, args, kwargs, output_index=output_index)
                for key, buffer in self.buffer_dict.items():
                    version = getattr(buffer, "_version", None)
                    if version is not None:
                        self._last_update_versions[key] = version
                self.updated = True
                return True
            self.updated = False
            return False
        else:
            raise ValueError("mode must be 'update' or 'time'")
        
    def spatial_expansion(self, expansion_function, args=None, kwargs=None, return_expansion=False, expansion_name=None):
        """
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
        """
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}

        expanded = expansion_function(self.array, *args, **kwargs)
        
        if return_expansion:
            return expanded
        
        if expansion_name is not None:
            self.expansions[expansion_name] = expanded
        else:
            self.expansions[str(len(self.expansions))] = expanded
        return None

