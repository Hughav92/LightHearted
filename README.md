# LightHearted

A Python framework for generating real-time stage lighting for performing arts with ECG signals.

## Installation

Requires Python 3.10 or higher. Developed and tested on Python 3.10.16. Using Conda:

```bash
conda create --name LightHearted python==3.10.16
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Any scripts using LightHearted will be sensitive to filepaths when importing. It is therefore advised to make use of

```python
import sys
sys.path.append("path/to/LightHearted")
```
for imports.

Full usage is described in the [tutorial.ipynb](documentation\tutorial.ipynb) Jupyter Notebook.

Documentation can be found [here](documentation/documentation.md).

If using ```csv_simulator```, replace ```placeholder.csv``` in ```csv_simulator/csv/``` with the desired csv files.

## Requirements

See [requirements.txt](requirements.txt) for the full list of dependencies.

## License

CC-BY License
