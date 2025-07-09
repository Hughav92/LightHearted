import numpy as np
import time

class MappingArray:
    """
    A class for handling data from multiple FIFO buffers to be mapped to a lighting array.
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
            
    def get_positions(self):
        """
        Get the current positions of the buffers in the array.

        Returns
        -------
        list[str]
            A list of keys representing the current positions of the buffers in the array.
        """
        return [key for key, idx in sorted(self.position_dict.items(), key=lambda x: x[1])]

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
    
    def update_array(self, reduction_functions, args_list=None, kwargs_list=None, output_index=None, output_indices=None):
        """
        Update the array by applying the same reduction function(s) to all buffers.

        Parameters
        ----------
        reduction_functions : callable or list[callable]
            A single function or list of functions to apply to each buffer.
        args_list : list[tuple], optional
            List of positional argument tuples for each function.
        kwargs_list : list[dict], optional
            List of keyword argument dicts for each function.
        output_index : int or None, optional
            Which output to use if the function returns multiple outputs. If None, use the entire result.
        output_indices : list[int or None], optional
            List of output indices for each function. If provided, after each function call, the corresponding output index is used.
        """
        if not isinstance(reduction_functions, list):
            reduction_functions = [reduction_functions]
        n_funcs = len(reduction_functions)
        if args_list is None:
            args_list = [()] * n_funcs
        if kwargs_list is None:
            kwargs_list = [{}] * n_funcs
        if output_indices is None:
            output_indices = [None] * n_funcs

        for key, buffer in self.buffer_dict.items():
            if hasattr(buffer, "get_buffer") and hasattr(buffer, "is_full"):
                if not buffer.is_full():
                    continue
                reduced = buffer.get_buffer()
            elif isinstance(buffer, (np.ndarray, list)):
                reduced = buffer
            else:
                raise TypeError(f"Buffer for key '{key}' is not a supported type.")

            for i, func in enumerate(reduction_functions):
                args = args_list[i] if i < len(args_list) else ()
                kwargs = kwargs_list[i].copy() if i < len(kwargs_list) else {}
                reduced = func(reduced, *args, **kwargs)
                idx = output_indices[i] if i < len(output_indices) else None
                if idx is not None and isinstance(reduced, (tuple, list)):
                    reduced = reduced[idx]
            if output_index is not None and isinstance(reduced, (tuple, list)):
                reduced = reduced[output_index]
            if isinstance(reduced, (np.ndarray, list, tuple)) and len(reduced) == 1:
                reduced = reduced[0]
            if not (isinstance(reduced, (int, float)) and not isinstance(reduced, bool)):
                raise TypeError(f"Reduced value for key '{key}' must be a single int or float, got {type(reduced)} with value {reduced}")
            self.array[self.position_dict[key]] = reduced

    def update_array_tick(self, reduction_functions, args_list=None, kwargs_list=None, mode="update", interval=1000, output_index=None, output_indices=None):
        """
        Update the array only if any buffer has changed ("update" mode), or at a fixed interval ("time" mode).

        Parameters
        ----------
        reduction_functions : callable or list[callable]
            Function(s) to apply to each buffer.
        args_list : list[tuple], optional
            List of positional argument tuples for each function.
        kwargs_list : list[dict], optional
            List of keyword argument dicts for each function.
        mode : str, optional
            "update" (default): update if any buffer changed.
            "time": update at a fixed interval (interval ms).
        interval : int, optional
            Interval in milliseconds for "time" mode.
        output_index : int or None, optional
            Which output to use if the function returns multiple outputs. If None, use the entire result.
        output_indices : list[int or None], optional
            List of output indices for each function. If provided, after each function call, the corresponding output index is used.

        Returns
        -------
        bool
            True if the array was updated, False otherwise.
        """
        
        if output_indices is None:
            output_indices = [None] * (len(reduction_functions) if isinstance(reduction_functions, list) else 1)
        n_funcs = len(reduction_functions) if isinstance(reduction_functions, list) else 1
        if args_list is None:
            args_list = [()] * n_funcs
        if kwargs_list is None:
            kwargs_list = [{}] * n_funcs

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
                self.update_array(reduction_functions, args_list, kwargs_list, output_index=output_index, output_indices=output_indices)
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
                self.update_array(reduction_functions, args_list, kwargs_list, output_index=output_index, output_indices=output_indices)
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
        
    def spatial_expansion(self, expansion_functions, args_list=None, kwargs_list=None, output_indices=None, return_expansion=False, expansion_name=None):
        """
        Apply a chain of spatial expansion functions to the array.

        Parameters
        ----------
        expansion_functions : callable or list[callable]
            The function(s) to apply for spatial expansion.
        args_list : list[tuple], optional
            List of positional argument tuples for each function.
        kwargs_list : list[dict], optional
            List of keyword argument dicts for each function.
        output_indices : list[int or None], optional
            List of output indices for each function. If provided, after each function call, the corresponding output index is used.
        return_expansion : bool, optional
            If True, return the expansion instead of storing it.
        expansion_name : str, optional
            Name of the expansion for storage.

        Returns
        -------
        np.ndarray or None
            The expanded array if return_expansion is True, otherwise None.
        """
        # Handle single function
        if not isinstance(expansion_functions, list):
            expansion_functions = [expansion_functions]
        n_funcs = len(expansion_functions)
        if args_list is None:
            args_list = [()] * n_funcs
        if kwargs_list is None:
            kwargs_list = [{}] * n_funcs
        if output_indices is None:
            output_indices = [None] * n_funcs

        expanded = self.array
        for i, func in enumerate(expansion_functions):
            args = args_list[i] if i < len(args_list) else ()
            kwargs = kwargs_list[i].copy() if i < len(kwargs_list) else {}
            expanded = func(expanded, *args, **kwargs)
            idx = output_indices[i] if i < len(output_indices) else None
            if idx is not None and isinstance(expanded, (tuple, list)):
                expanded = expanded[idx]

        if return_expansion:
            return expanded
        if expansion_name is not None:
            self.expansions[expansion_name] = expanded
        else:
            self.expansions[str(len(self.expansions))] = expanded
        return None
    
    def get_expansion(self, expansion_name):
        """
        Get the expansion by name.

        Parameters
        ----------
        expansion_name : str
            The name of the expansion to retrieve.

        Returns
        -------
        np.ndarray
            The expanded array corresponding to the given name.
        """
        if expansion_name in self.expansions:
            return self.expansions[expansion_name]
        else:
            raise KeyError(f"Expansion '{expansion_name}' not found.")
        
    def get_expansion_names(self):
        """
        Get the names of all expansions.

        Returns
        -------
        list[str]
            A list of expansion names.
        """
        return list(self.expansions.keys())

