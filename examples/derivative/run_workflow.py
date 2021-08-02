import pandas as pd
import matplotlib.pyplot as pl
import yaml
import numpy as np
from parlize.parlize import create_runs
from parlize.utils import apply_over_runs
import subprocess


@apply_over_runs("Output")
def run():
    subprocess.check_call(["bash", "run.sh"])


@apply_over_runs("Output")
def get_output():
    return float(open("error.txt", "r").read())


if __name__ == "__main__":

    hs = np.logspace(-20, 0, 10)

    # Explicitly write the hs to the yaml file
    with open("incomplete_config.yml", "r") as yml_file:
        yml = yaml.full_load(yml_file)
        if not yml["VariableParameters"]:
            yml["VariableParameters"] = {}
            # Explicitly convert from numpy types to make the yaml easier to parse
            yml["VariableParameters"]["spacing"] = [float(h) for h in hs]
    with open("config.yml", "w") as yml_file:
        yaml.dump(yml, yml_file)

    create_runs("config.yml")
    run()

    dct = get_output()

    df = pd.read_csv("Output/parameters.csv", sep="\t")
    pl.loglog(df["spacing"], [dct[i] for i in df["Directory"]], "x-")
    pl.xlabel("h")
    pl.ylabel("Error in d exp(0)/ dx")
    pl.show()
