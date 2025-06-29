import sys
sys.path.append("../")
from mapping.mapping_functions import ones, zeros, identity, flip_range, offset, scale, sine, cosine

osc_addresses = ["/aud", "/brs", "/conductor", "/vn1"]
osc_ip = "127.0.0.1"
osc_port = 13000

lighting_ip = "10.101.90.103"
lighting_port = 12000

functions_dict = {1: {"r_functions": [ones],
                    "g_functions": [flip_range, offset, scale],
                    "b_functions": [zeros],
                    "w_functions": [zeros],
                    "r_kwargs_list": [],
                    "g_kwargs_list": [{"min":0, "max":1}, {"offset":0.4}, {"scale":0.6}],
                    "b_kwargs_list": [],
                    "w_kwargs_list": []},
                2: {"r_functions": [flip_range, offset, scale],
                    "g_functions": [ones],
                    "b_functions": [zeros],
                    "w_functions": [zeros],
                    "r_kwargs_list": [{"min":0, "max":1}, {"offset":0.4}, {"scale":0.6}],
                    "g_kwargs_list": [],
                    "b_kwargs_list": [],
                    "w_kwargs_list": []},
                3: {"r_functions": [zeros],
                    "g_functions": [zeros],
                    "b_functions": [identity],
                    "w_functions": [zeros],
                    "r_kwargs_list": [],
                    "g_kwargs_list": [],
                    "b_kwargs_list": [],
                    "w_kwargs_list": []},
                4: {"r_functions": [sine],
                    "g_functions": [cosine],
                    "b_functions": [identity],
                    "w_functions": [zeros],
                    "r_kwargs_list": [],
                    "g_kwargs_list": [],
                    "b_kwargs_list": [],
                    "w_kwargs_list": []},
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