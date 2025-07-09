import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_colour_map(r, g, b, highlight_indices=None, plot_range=None, ticks=None, labels=None, title="colour Map"):
    """
    Plots a colour map based on three arrays of RGB values and draws boxes around specified indices.

    Parameters:
        r (array-like): Array of red values (0-100).
        g (array-like): Array of green values (0-100).
        b (array-like): Array of blue values (0-100).
        highlight_indices (list): List of indices where boxes should be drawn. Default is None.

    Raises:
        ValueError: If the input arrays are not of same length.
    """
    # Validate input
    if not (len(r) == len(g) == len(b)):
        raise ValueError("All input arrays must have exactly the same number of elements.")

    # Normalize RGB values to the range [0, 1] for plotting
    r_normalized = np.array(r)# / 100.0
    g_normalized = np.array(g)# / 100.0
    b_normalized = np.array(b)# / 100.0

    # Create a colour map array
    colour_map = np.zeros((1, len(r), 3))
    colour_map[0, :, 0] = r_normalized
    colour_map[0, :, 1] = g_normalized
    colour_map[0, :, 2] = b_normalized

    # Plot the colour map
    plt.figure(figsize=(12, 2))
    plt.imshow(colour_map, aspect='auto')
    plt.axis('off')  # Turn off axes for better visualization
    plt.title(title)

    # Draw boxes around the specified indices
    if highlight_indices is not None:
        ax = plt.gca()  # Get current axes
        for idx in highlight_indices:
            rect = patches.Rectangle((idx - 0.5, -0.5), 1, 1, linewidth=2, edgecolor='k', facecolor='none')
            ax.add_patch(rect)

    if plot_range is not None and ticks is not None and labels is not None:
        plt.axis('on')
        plt.xticks(ticks=ticks, labels=labels, rotation=45)
        plt.xlabel("Value Range")
        ax = plt.gca()
        ax.set_yticks([])

    plt.show()

def plot_rgb_3d_colourmap(r, g, b):
    """
    Plots a 3D colour map with the RGB spectrum bounded by the parameter space of r, g, and b.
    """

    # Scale to the range 0 to 100
    r = r * 100
    g = g * 100
    b = b * 100

    # Filter the points within the valid parameter space (0 to 100)
    valid_mask = (r >= 0) & (r <= 100) & (g >= 0) & (g <= 100) & (b >= 0) & (b <= 100)
    r = r[valid_mask]
    g = g[valid_mask]
    b = b[valid_mask]

    # Normalize to the range 0 to 1 for colour mapping
    r_normalized = r / 100
    g_normalized = g / 100
    b_normalized = b / 100

    # Create the corresponding colours
    colours = np.stack((r_normalized, g_normalized, b_normalized), axis=1)

    # Add transparency to the colours
    alpha = 1  # Transparency level (0.0 is fully transparent, 1.0 is fully opaque)

    # Create a 3D plot
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Plot points with colours corresponding to their RGB values
    scatter = ax.scatter(r, g, b, c=colours, alpha=alpha, marker='o', s=5)

    # Set axis labels
    ax.set_xlabel('Red')
    ax.set_ylabel('Green')
    ax.set_zlabel('Blue')

    # Set axis limits
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_zlim(0, 100)

    # Set the title
    ax.set_title('3D RGB colour Map (Bounded Parameter Space)')

def plot_rgb_3d_colourmap(r, g, b):
    """
    Plots a 3D colour map with the RGB spectrum bounded by the parameter space of r, g, and b.
    """

    # Scale to the range 0 to 100
    r = r * 100
    g = g * 100
    b = b * 100

    # Filter the points within the valid parameter space (0 to 100)
    valid_mask = (r >= 0) & (r <= 100) & (g >= 0) & (g <= 100) & (b >= 0) & (b <= 100)
    r = r[valid_mask]
    g = g[valid_mask]
    b = b[valid_mask]

    # Normalize to the range 0 to 1 for colour mapping
    r_normalized = r / 100
    g_normalized = g / 100
    b_normalized = b / 100

    # Create the corresponding colours
    colours = np.stack((r_normalized, g_normalized, b_normalized), axis=1)

    # Add transparency to the colours
    alpha = 1  # Transparency level (0.0 is fully transparent, 1.0 is fully opaque)

    # Create a 3D plot
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Plot points with colours corresponding to their RGB values
    scatter = ax.scatter(r, g, b, c=colours, alpha=alpha, marker='o', s=5)

    # Set axis labels
    ax.set_xlabel('Red')
    ax.set_ylabel('Green')
    ax.set_zlabel('Blue', rotation=90)

    # Set axis limits
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_zlim(0, 100)

    # Set the title
    ax.set_title('3D RGB colour Map (Bounded Parameter Space)')

    plt.tight_layout()
    
    plt.show()

