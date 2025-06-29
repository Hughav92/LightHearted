import numpy as np
import sys
sys.path.append("../")
from acquisition.fifo_buffer import FIFOBuffer
from utils.utils import filter, moving_average

def pan_tompkins(sig: np.ndarray, filter_low: int, filter_high: int, average_window: float, sr: int) -> np.ndarray:
    """
    Apply the Pan-Tompkins algorithm to detect QRS complex in ECG data.

    Parameters
    ----------
    sig : np.ndarray
        The ECG signal.
    filter_low : int
        The lower critical frequency for bandpass filtering of the ECG signal.
    filter_high : int
        The higher critical frequency for bandpass filtering the ECG signal.
    average_window : float
        The window size for the moving average window in seconds.
    sr : int
        The sampling rate of the ECG signal.

    Returns
    -------
    np.ndarray
        The QRS complex derived from the ECG signal.
    """
    filtered = filter(sig, 3, (filter_low, filter_high), "bandpass", sr)
    der = np.diff(filtered)
    squared = der**2

    moving_window = int(sr * average_window)

    qrs = moving_average(squared, moving_window)

    return qrs
