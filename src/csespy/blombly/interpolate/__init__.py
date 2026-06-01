
import numpy as np
from scipy.interpolate import make_interp_spline

def spline_interpolate(x, f, x_new, order=3):
    """
    Perform spline interpolation of f(x) at new points x_new.

    Parameters:
        x (array-like): 1D array of original x-values (must be sorted and unique)
        f (array-like): 1D array of function values at x (same length as x)
        x_new (array-like): 1D array of new x-values to interpolate at
        order (int): Degree of the spline (default: 3 for cubic)

    Returns:
        np.ndarray: Interpolated values at x_new
    """
    x = np.asarray(x)
    f = np.asarray(f)
    x_new = np.asarray(x_new)

    # Ensure x is sorted
    sort_idx = np.argsort(x)
    x_sorted = x[sort_idx]
    f_sorted = f[sort_idx]

    # Create and evaluate spline
    spline = make_interp_spline(x_sorted, f_sorted, k=order)
    return spline(x_new)
