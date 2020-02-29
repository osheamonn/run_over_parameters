import numpy as np
import pandas as pd
import os
import yaml
from typing import Tuple

from parlize.utils import merge_dataframes


def parse_yaml_file(config_file):
    # type: (str) -> Tuple[str, list, pd.DataFrame]
    with open(config_file, "r") as f:
        yml_file = yaml.load(f, Loader=yaml.FullLoader)

    # Below names can either be a tuple of strings or a single string. The wrapping of names
    # into an array followed by a flatten means both the tuple case and single string case get
    # mapped to a 1D array of strings
    dataframes = [
        pd.DataFrame(data=np.array(values), columns=np.array([names]).flatten())
        for names, values in yml_file["VariableParameters"].items()
    ]

    all_parameters = merge_dataframes(*dataframes)

    return (
        yml_file["OutputDirectory"],
        yml_file["FilesToTemplateAndCopy"],
        all_parameters,
    )


def create_runs(config_file):
    # type: (str) -> None
    output_dir, files_to_copy, df = parse_yaml_file(config_file)

    df.index.name = "Directory"
    output_dir = os.path.join(os.path.dirname(config_file), output_dir)
    os.makedirs(output_dir)
    df.to_csv(os.path.join(output_dir, "parameters.csv"), sep="\t")
    for idx, s in df.iterrows():
        run_dir = os.path.join(output_dir, "run_{}".format(idx))
        os.makedirs(run_dir)
        for f in files_to_copy:
            # To allow multiple files to act as templates we rely on the fact
            # that format will not fail if the string does not contain the parameter
            # it's trying to replace.
            infile_contents, outfile = None, None
            if isinstance(f, str):
                infile_contents = open(os.path.join(os.path.dirname(
                    config_file), f), "r").read()
                outfile = open(os.path.join(run_dir, f), "w")
            elif isinstance(f, list) and len(f) == 2:
                infile_contents = open(os.path.join(os.path.dirname(config_file),
                                                    f[0]),
                                                                    "r").read()
                outfile = open(os.path.join(run_dir, f[1]), "w")
            else:
                raise RuntimeError("Files: {} should be either a single string or "
                                   "list of size two representing input and output "
                                   "files. ")
            # If outfile is itself a python file which contains some string formatting,
            # then this script will either fail with a KeyError, for possibly do the
            # wrong thing and format a string it should not. So if a python file,
            # just copy it with no formatting
            if os.path.splitext(outfile.name)[1] == '.py':
                outfile.write(infile_contents)
            else:
                outfile.write(infile_contents.format(**s))
