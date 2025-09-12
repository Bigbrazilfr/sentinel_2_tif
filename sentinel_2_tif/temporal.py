## imports ##
from datetime import datetime, timedelta
import pandas as pd
from collections.abc import Iterable
import numbers


## time_wrapper ##
def time_wrapper(event_date, weeks=1):
    """
    Creates a symmetric time window around an event date.
    
    PARAMETERS
    ----------
    event_date : datetime or datetime-convertible object (int, float, str...)
        The central event date. See pd.to_datetime() for more details on
        acceptable formats.
    
    weeks : int or float, default 1
        Number of weeks to wrap before and after the event date. For example,
        weeks=2 will generate a window from two weeks before to two weeks
        after the event date (total of four weeks).
    
    RETURNS
    -------
    str
        A STAC-compliant date range string: 'YYYY-MM-DD/YYYY-MM-DD'
    
    EXAMPLES
    --------
    >>> time_wrapper("2024-07-01", weeks=3)
    '2024-06-10/2024-07-22'
    
    SEE ALSO
    --------
    time_windows : Creates multiple time windows.
    pd.to_datetime : Converts input into a pandas datetime object.
    """
    
    # converting event to datetime object
    try:
        event_date = pd.to_datetime(event_date)
        
    # throwing error if event is not a datetime object
    except (ValueError, TypeError):
        raise ValueError("Invalid event_date. Must be convertible to datetime.")

    # calculating time wrapper
    delta = timedelta(weeks=float(weeks))

    start = event_date - delta
    end = event_date + delta
    
    # returning time window in STAC-compliant format
    return f"{start.date()}/{end.date()}"


## time_windows ##
def time_windows(event_date, wrap_sizes, verbose=False):
    """
    Creates multiple symmetric time windows around a central event date.

    PARAMETERS
    ----------
    event_date : datetime or datetime-convertible object (int, float, str...)
        The central event date. See pd.to_datetime() for more details on
        acceptable formats.

    wrap_sizes : iterable of int or float
        A list, range, or other iterable of values representing the number of
        weeks to buffer before and after the event. For example, a value of 2
        will generate a window from two weeks before to two weeks after the
        event (total of four weeks).

    verbose : bool, default False
        If True, prints each generated time window.

    RETURNS
    -------
    List[str]
        A list of STAC-compliant date range strings: ['YYYY-MM-DD/YYYY-MM-DD', ...]
        
    EXAMPLES
    --------
    >>> time_windows("2025-01-01", wrap_sizes=[1, 2, 4])
    ['2024-12-25/2025-01-08', '2024-12-18/2025-01-15', '2024-12-04/2025-01-29']
    
    SEE ALSO
    --------
    time_wrapper : Creates a single time window.
    pd.to_datetime : Converts input into a pandas datetime object.
    """

    # throwing error if wrap_sizes is not iterable
    if not isinstance(wrap_sizes, Iterable):
        raise ValueError("`wrap_sizes` must be an iterable of numeric values.")
        
    # placeholder list
    windows = []
    
    # developing time wraps
    for w in wrap_sizes:
        
        # throwing error if wraps are not numeric 
        if not isinstance(w, numbers.Real):
            raise ValueError(f"Wrap size '{w}' is not a number.")
        
        # instantiating wraps and storing results
        window = time_wrapper(event_date=event_date, weeks=w)
        windows.append(window)
        
        # optional feedback while processing
        if verbose:
            print(f"Generated window: {window}")
            
    # returning time windows in STAC-compliant format 
    return windows
