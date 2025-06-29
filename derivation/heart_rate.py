import numpy as np
from scipy.signal import find_peaks
from acquisition.fifo_buffer import FIFOBuffer
from utils.utils import *

def heart_rate(
    qrs: np.ndarray,
    window: float,
    sr: int,
    average: str = "median"
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate the heart rate from a QRS signal at specified time intervals.

    Parameters
    ----------
    qrs : np.ndarray
        The QRS-processed signal (e.g., from pan_tompkins).
    window : float
        The window size (in seconds) for heart rate calculation.
    sr : int
        The sampling rate.
    average : str
        The type of average to use for heart rate values in the window ("mean" or "median").

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
        - hr_arr: The average heart rate for each window in BPM.
        - peaks_arr: The detected peaks in the QRS signal.
        - rr_arr: The RR intervals in samples.
        - rr_sec_arr: The RR intervals in seconds.
    """
    len_chunk = int(window * sr)
    len_hr = int(np.ceil(len(qrs) / len_chunk))
    hr_arr = np.zeros(len_hr)
    index_counter = 0
    peaks_arr = []

    for i in range(len_hr):
        chunk_start = int(i * sr * window)
        chunk_end = int(chunk_start + sr * window)
        chunk = qrs[chunk_start:chunk_end]

        mean_pt = np.mean(chunk)
        peaks = find_peaks(chunk, height=mean_pt, prominence=mean_pt / 6, distance=0.2 * sr)[0]
        rr = np.diff(peaks)

        if len(rr) == 0:
            hr_arr[i] = hr_arr[i - 1] if i > 0 else 0
            rr_sec = 0
        else:
            rr_sec = rr * (1 / sr)
            hr = 60 / rr_sec
            if average == "mean":
                window_av = np.mean(hr)
            elif average == "median":
                window_av = np.median(hr)
            hr_arr[i] = window_av

        peaks_arr.append(peaks + index_counter)
        index_counter += len_chunk

    peaks_arr = np.concatenate(peaks_arr)
    rr_arr = np.diff(peaks_arr)
    rr_sec_arr = rr_arr * (1 / sr)

    return hr_arr, peaks_arr, rr_arr, rr_sec_arr