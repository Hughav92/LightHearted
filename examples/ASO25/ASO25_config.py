import sys
sys.path.append("../")
from mapping.mapping_functions import ones, zeros, identity, flip_range, offset, scale, sine, cosine

### OSC Configuration ###

osc_addresses = ["/aud", "/brs", "/conductor", "/vn1"]
osc_ip = "127.0.0.1"
osc_port = 13000

lighting_ip = "10.101.90.103"
lighting_port = 12000

### RGBW Mapping Functions ###

functions_dict = {1: {"r_functions": [ones],
                    "g_functions": [flip_range, offset, scale],
                    "b_functions": [zeros],
                    "w_functions": [zeros],
                    "r_kwargs_list": [{}],
                    "g_kwargs_list": [{"min":0, "max":1}, {"offset":0.05}, {"scale":0.6}],
                    "b_kwargs_list": [{}],
                    "w_kwargs_list": [{}]},
                2: {"r_functions": [zeros],
                    "g_functions": [sine, flip_range, offset],
                    "b_functions": [cosine],
                    "w_functions": [zeros],
                    "r_kwargs_list": [{}],
                    "g_kwargs_list": [{}, {"min":0, "max":1}, {"offset":-0.1}],
                    "b_kwargs_list": [{}],
                    "w_kwargs_list": [{}]},
                3: {"r_functions": [ones],
                    "g_functions": [flip_range, offset],
                    "b_functions": [cosine, flip_range],
                    "w_functions": [zeros],
                    "r_kwargs_list": [{}],
                    "g_kwargs_list": [{"min":0.01265, "max":1}, {"offset":-0.2}],
                    "b_kwargs_list": [{}, {"min":0.56142, "max":1}],
                    "w_kwargs_list": [{}]},
                4: {"r_functions": [sine, scale, offset],
                    "g_functions": [offset, cosine],
                    "b_functions": [zeros],
                    "w_functions": [zeros],
                    "r_kwargs_list": [{}, {"scale":1.5}, {"offset":0.6}],
                    "g_kwargs_list": [{"offset": 0.1}, {}],
                    "b_kwargs_list": [{}],
                    "w_kwargs_list": [{}]},
                }

function_index = 1

functions_container = {
    "r_functions": [ones],
    "g_functions": [flip_range, offset, scale],
    "b_functions": [zeros],
    "w_functions": [zeros],
    "r_kwargs_list": [],
    "g_kwargs_list": [{"min": 0, "max": 1}, {"offset": 0.4}, {"scale": 0.6}],
    "b_kwargs_list": [],
    "w_kwargs_list": []
}

### ECG Configuration ###

ecg_sr = 256
ecg_filt_low = 5
ecg_filt_high = 12
ecg_window = 0.15

hr_window = 10

mapping_hr_low = 60
mapping_hr_high = 120