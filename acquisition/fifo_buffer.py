import numpy as np
import time

class FIFOBuffer:
    """
    A fixed-size First-In-First-Out (FIFO) buffer for numeric data, supporting
    efficient enqueuing, transformation, and statistical operations.
    """
    def __init__(self, size: int):
        """
        Initialize the FIFO buffer with a given maximum size.

        Parameters
        ----------
        size : int
            The maximum size of the buffer.
        """
        self.size = size
        self.centre_index = int(np.floor(self.size * 0.5))
        self.buffer = np.array([], dtype=float)
        self._version = 0  # Tracks changes to the buffer
        self._last_transform_version = -1  # For update-based transforms
        self._last_transform_time = 0  # For time-based transforms

    def is_full(self) -> bool:
        """
        Check if the buffer is full.

        Returns
        -------
        bool
            True if the buffer is full, False otherwise.
        """
        return len(self.buffer) >= self.size

    def enqueue(self, items: int | float | list[int | float] | np.ndarray | tuple[int | float]) -> None:
        """
        Add an item or a list of items to the buffer.
        Automatically removes the oldest items if the buffer exceeds the size.

        Parameters
        ----------
        items : list or np.ndarray or int or float
            The items to add to the buffer.
        """
        if isinstance(items, (list, np.ndarray, tuple)):
            items = np.array(items).flatten()
            for item in items:
                if self.is_full():
                    self.buffer = self.buffer[1:]
                self.buffer = np.append(self.buffer, item)
                self._version += 1
        else:
            if self.is_full():
                self.buffer = self.buffer[1:]
            self.buffer = np.append(self.buffer, items)
            self._version += 1

    def get_buffer(self) -> np.ndarray:
        """
        Returns the buffer as a NumPy array.

        Returns
        -------
        np.ndarray
            The current buffer.
        """
        return self.buffer

    def get_size(self) -> int:
        """
        Returns the number of elements in the buffer.

        Returns
        -------
        int
            The number of elements in the buffer.
        """
        return len(self.buffer)
    
    def get_max_size(self) -> int:
        """
        Returns the maximum size of the buffer.

        Returns
        -------
        int
            The maximum size of the buffer.
        """
        return self.size
    
    def set_buffer(self, new_buffer: np.ndarray | list, resize_buffer=True) -> None:
        """
        Set the buffer to a new NumPy array or list.

        Parameters
        ----------
        new_buffer : np.ndarray or list
            The new buffer to set.
        resize_buffer : bool, optional
            If True, resize the buffer size to match the new buffer length.
        """
        if not isinstance(new_buffer, (np.ndarray, list)):
            raise TypeError("new_buffer must be a numpy array or a list")
        self.clear_buffer()
        if resize_buffer:
            self.size = len(new_buffer)
        if self.size < 0:
            raise ValueError("Buffer size must be at least 0")
        self.enqueue(new_buffer)
        if self.buffer.ndim > 1:
            self.buffer = self.buffer.flatten()
        self.centre_index = self._calculate_centre_index()
        self._version += 1

    def _calculate_centre_index(self) -> int:
        """
        Calculate the centre index of the buffer based on its size.

        Returns
        -------
        int
            The centre index of the buffer.
        """
        return int(np.floor(self.size * 0.5))
    
    def clear_buffer(self) -> None:
        """
        Clear the buffer by resetting it to an empty array.
        """
        self.buffer = np.array([], dtype=float)
        self._version += 1
        self._last_transform_version = -1
        self._last_transform_time = 0

    def transform(self, functions, args_list=None, kwargs_list=None, output_index=None):
        """
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

        Returns
        -------
        np.ndarray or object
            The result after applying all functions in sequence to the buffer.
        """
        if args_list is None:
            args_list = [()] * len(functions)
        if kwargs_list is None:
            kwargs_list = [{}] * len(functions)

        values = np.nan_to_num(self.buffer, nan=0, posinf=1, neginf=-1)

        for i, func in enumerate(functions):
            args = args_list[i] if i < len(args_list) else ()
            kwargs = kwargs_list[i].copy() if i < len(kwargs_list) else {}
            stats_needed = set(kwargs.values())
            finite_vals = values[np.isfinite(values)] if stats_needed else None
            if "min" in stats_needed:
                v_min = np.nanmin(finite_vals) if finite_vals.size > 0 else 0
            if "max" in stats_needed:
                v_max = np.nanmax(finite_vals) if finite_vals.size > 0 else 0
            if "mean" in stats_needed:
                v_mean = np.mean(finite_vals) if finite_vals.size > 0 else 0
            if "std" in stats_needed:
                v_std = np.std(finite_vals) if finite_vals.size > 0 else 0
            if "median" in stats_needed:
                v_median = np.median(finite_vals) if finite_vals.size > 0 else 0
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
        if output_index is not None and isinstance(values, (tuple, list)):
            values = values[output_index]
        if isinstance(values, np.ndarray):
            values = np.nan_to_num(values, nan=0, posinf=1, neginf=-1)
        return values

    def transform_tick(self, functions, args_list=None, kwargs_list=None, mode="update", interval=1000, output_index=None):
        """
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

        Returns
        -------
        np.ndarray or None
            The result of transform if triggered, else None.
        """
        now = time.perf_counter() * 1000

        if mode == "update":
            if self._version != self._last_transform_version:
                self._last_transform_version = self._version
                return self.transform(functions, args_list, kwargs_list, output_index=output_index)
        elif mode == "time":
            if now - self._last_transform_time >= interval:
                self._last_transform_time += interval
                if now - self._last_transform_time > interval:
                    self._last_transform_time = now
                return self.transform(functions, args_list, kwargs_list, output_index=output_index)
        else:
            raise ValueError("mode must be 'update' or 'time'")
        return None
