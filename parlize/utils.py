
import glob
import os
import subprocess
import pandas as pd
import functools

def merge_dataframes(df, *rest):
    # type: (pd.DataFrame, Optional[pd.DataFrame]) -> pd.DataFrame
    out = df.copy()
    out["dummy"] = 1
    for d in rest:
        d["dummy"] = 1
        out = pd.merge(out, d, on="dummy")
    return out.drop("dummy", axis=1)


def apply_over_runs(dirname):
    """ By applying this decorator to a function with the directory dirname, it will
    go over every run directory in dirname and run the function. If the function
    returns a value, the decorated function returns a dictionary from the run names
    to the return values. If the function does not return, neither does the decorated
    function.
    """
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            curdir = os.getcwd()
            return_values = {}
            for d in glob.glob(os.path.join(dirname, 'run_*')):
                localdir = os.getcwd()
                os.chdir(d)
                return_value = function(*args, **kwargs)
                return_values[int(d[-1])] = return_value
                os.chdir(localdir)
            os.chdir(curdir)
            if all(val is None for val in return_values.values()):
                return
            else:
                return return_values
        return wrapper
    return decorator
