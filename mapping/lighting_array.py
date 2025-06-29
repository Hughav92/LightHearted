import numpy as np

class LightingArray:
    """
    LightingArray represents a collection of lighting fixtures (LEDs) and their color/intensity states.
    Supports RGBW color channels, anchor points for mapping, and provides methods to update and retrieve channel values.
    """

    def __init__(self, fixtures, anchors=None):
        """
        Initialize the LightingArray with fixtures and anchors.

        Parameters
        ----------
        fixtures : list or np.ndarray
            A list or array of fixture IDs (LED indices).
        anchors : list or np.ndarray, optional
            A list or array of anchor IDs (LED indices used as mapping anchors).
        """
        self.fixtures = np.array(fixtures)
        self.anchors = np.array([] if anchors is None else anchors)
        self.anchor_positions = np.where(np.isin(self.fixtures, self.anchors))[0]
        self.no_leds = len(self.fixtures)
        self.intensities = np.zeros(self.no_leds)
        self.previous_intensities = np.zeros(self.no_leds)
        self.red = np.zeros(self.no_leds)
        self.previous_red = np.zeros(self.no_leds)
        self.green = np.zeros(self.no_leds)
        self.previous_green = np.zeros(self.no_leds)
        self.blue = np.zeros(self.no_leds)
        self.previous_blue = np.zeros(self.no_leds)
        self.white = np.zeros(self.no_leds)
        self.previous_white = np.zeros(self.no_leds)

    def set_anchors(self, new_anchors):
        """
        Set the anchors for the lighting array and update anchor positions.

        Parameters
        ----------
        new_anchors : list or np.ndarray
            A list or array of new anchor IDs.
        """
        self.anchors = np.array(new_anchors)
        self.update_anchor_positions(np.where(np.isin(self.fixtures, self.anchors))[0])

    def get_anchor_positions(self):
        """
        Get the positions of the anchors in the fixture array.

        Returns
        -------
        np.ndarray
            An array of anchor positions (indices in the fixture array).
        """
        return self.anchor_positions
    
    def update_anchor_positions(self, new_anchor_positions):
        """
        Set the positions of the anchors in the fixture array.

        Parameters
        ----------
        new_anchor_positions : np.ndarray
            An array of new anchor positions (indices in the fixture array).
        """
        if len(new_anchor_positions) != len(self.anchor_positions):
            raise ValueError(f"Length of new_anchor_positions ({len(new_anchor_positions)}) does not match number of anchors ({len(self.anchor_positions)})")
        self.anchor_positions = new_anchor_positions
    
    def update_intensities(self, new_intensities):
        """
        Update the intensities of the fixtures (brightness for each LED).

        Parameters
        ----------
        new_intensities : np.ndarray
            An array of new intensity values for the fixtures.
        """
        if len(new_intensities) != self.no_leds:
            raise ValueError(f"Length of new_intensities ({len(new_intensities)}) does not match number of LEDs ({self.no_leds})")
        self.previous_intensities = self.intensities.copy()
        self.intensities = new_intensities
    
    def update_red(self, new_red):
        """
        Update the red channel values of the fixtures.

        Parameters
        ----------
        new_red : np.ndarray
            An array of new red channel values for the fixtures.
        """
        if len(new_red) != self.no_leds:
            raise ValueError(f"Length of new_red ({len(new_red)}) does not match number of LEDs ({self.no_leds})")
        self.previous_red = self.red.copy()
        self.red = new_red

    def update_green(self, new_green):
        """
        Update the green channel values of the fixtures.

        Parameters
        ----------
        new_green : np.ndarray
            An array of new green channel values for the fixtures.
        """
        if len(new_green) != self.no_leds:
            raise ValueError(f"Length of new_green ({len(new_green)}) does not match number of LEDs ({self.no_leds})")
        self.previous_green = self.green.copy()
        self.green = new_green
    
    def update_blue(self, new_blue):
        """
        Update the blue channel values of the fixtures.

        Parameters
        ----------
        new_blue : np.ndarray
            An array of new blue channel values for the fixtures.
        """
        if len(new_blue) != self.no_leds:
            raise ValueError(f"Length of new_blue ({len(new_blue)}) does not match number of LEDs ({self.no_leds})")
        self.previous_blue = self.blue.copy()
        self.blue = new_blue

    def update_white(self, new_white):
        """
        Update the white channel values of the fixtures.

        Parameters
        ----------
        new_white : np.ndarray
            An array of new white channel values for the fixtures.
        """
        if len(new_white) != self.no_leds:
            raise ValueError(f"Length of new_white ({len(new_white)}) does not match number of LEDs ({self.no_leds})")
        self.previous_white = self.white.copy()
        self.white = new_white

    def update_rgb(self, new_red, new_green, new_blue):
        """
        Update the RGB channel values of the fixtures.

        Parameters
        ----------
        new_red : np.ndarray
            An array of new red channel values for the fixtures.
        new_green : np.ndarray
            An array of new green channel values for the fixtures.
        new_blue : np.ndarray
            An array of new blue channel values for the fixtures.
        """
        self.update_red(new_red)
        self.update_green(new_green)
        self.update_blue(new_blue)

    def update_rgbw(self, new_red, new_green, new_blue, new_white):
        """
        Update the RGBW channel values of the fixtures.

        Parameters
        ----------
        new_red : np.ndarray
            An array of new red channel values for the fixtures.
        new_green : np.ndarray
            An array of new green channel values for the fixtures.
        new_blue : np.ndarray
            An array of new blue channel values for the fixtures.
        new_white : np.ndarray
            An array of new white channel values for the fixtures.
        """
        self.update_rgb(new_red, new_green, new_blue)
        self.update_white(new_white)

    def get_intensities(self):
        """
        Get the current intensities of the fixtures.

        Returns
        -------
        np.ndarray
            An array of current intensity values for the fixtures.
        """
        return self.intensities
    
    def get_rgb(self):
        """
        Get the current RGB channel values of the fixtures.

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray]
            A tuple containing arrays of red, green, and blue channel values for the fixtures.
        """
        return self.red, self.green, self.blue
    
    def get_rgbw(self):
        """
        Get the current RGBW channel values of the fixtures.

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
            A tuple containing arrays of red, green, blue, and white channel values for the fixtures.
        """
        return self.red, self.green, self.blue, self.white
    
    def get_previous_intensities(self):
        """
        Get the previous intensities of the fixtures.

        Returns
        -------
        np.ndarray
            An array of previous intensity values for the fixtures.
        """
        return self.previous_intensities
    
    def get_previous_rgb(self):
        """
        Get the previous RGB channel values of the fixtures.

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray]
            A tuple containing arrays of previous red, green, and blue channel values for the fixtures.
        """
        return self.previous_red, self.previous_green, self.previous_blue
    
    def get_previous_rgbw(self):
        """
        Get the previous RGBW channel values of the fixtures.

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
            A tuple containing arrays of previous red, green, blue, and white channel values for the fixtures.
        """
        return self.previous_red, self.previous_green, self.previous_blue, self.previous_white

    def send_command(self, func, *args, **kwargs):
        """
        Send a command to the lighting system using a function from a lighting API.

        Parameters
        ----------
        func : callable
            A function from the lighting API to be called (e.g., format_RGB, format_intensity, etc.).
        *args
            Positional arguments to pass to the function.
        fixtures : list or np.ndarray, optional
            The list of fixtures to use. If None, uses self.fixtures.
        **kwargs
            Keyword arguments to pass to the function.

        Returns
        -------
        The result of the called function.
        """
        
        return func(*args, **kwargs)


