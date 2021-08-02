import numpy as np
from parlize.parlize import create_runs
from parlize.utils import apply_over_runs
import subprocess


@apply_over_runs("Output")
def run():
    subprocess.check_call(["bash", "run.sh"])


@apply_over_runs("Output")
def get_average():
    return int(open("output.txt", "r").read())


if __name__ == "__main__":

    create_runs("config.yml")
    run()

    d = get_average()

    print(
        "Average of {} is {}".format(d, np.mean(np.fromiter(d.values(), dtype=float)))
    )
