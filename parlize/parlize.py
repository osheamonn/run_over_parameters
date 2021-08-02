import numpy as np
import pandas as pd
import os
import yaml
from typing import Tuple
import subprocess
import shutil
from string import Template

from parlize.utils import merge_dataframes


class PartialFormatDict(dict):
    """
    This is a dict which can be used to perform partial formatting. For example,

    "{A} {B}".format(A=1)
    throws an exception in normal python. If we wanted to have behaviour such that the above snippet does not throw but instead return "1 {B}" we can make use of this class along with str.format_map. E.g.

    "{A} {B}".format_map(PartialFormatDict(A=1))

    will return "1 {B}"

    """

    def __missing__(self, key):
        return "{" + key + "}"


def parse_yaml_file(config_file):
    # type: (str) -> Tuple[str, list, pd.DataFrame]
    with open(config_file, "r") as f:
        yml_file = yaml.load(f, Loader=yaml.FullLoader)

    # Below names can either be a tuple of strings or a single string. The wrapping of names
    # into an array followed by a flatten means both the tuple case and single string case get
    # mapped to a 1D array of strings
    def get_dfs(d):
        return [
            pd.DataFrame(data=np.array(values), columns=np.array([names]).flatten())
            for names, values in d.items()
        ]

    all_vars = yml_file["VariableParameters"]
    root = {k: v for k, v in all_vars.items() if type(v) != dict}
    subvars = {k: v for k, v in all_vars.items() if type(v) == dict}

    root_parameters = get_dfs(root)
    subparameters = [get_dfs(s) for s in subvars.values()]

    from itertools import chain

    if subparameters:
        all_parameters_dataframes = [
            merge_dataframes(*chain(root_parameters, subframes))
            for subframes in subparameters
        ]
    else:
        all_parameters_dataframes = [merge_dataframes(*root_parameters)]
    all_parameters = pd.concat(all_parameters_dataframes, ignore_index=True)

    return (
        yml_file["OutputDirectory"],
        yml_file["FilesToTemplateAndCopy"],
        yml_file.get("PostCreationCommands", []),
        all_parameters,
    )


def create_runs(config_file, force):
    # type: (str) -> None
    output_dir, files_to_copy, post_creation_commands, df = parse_yaml_file(config_file)

    root_dir = os.path.abspath(os.curdir)

    df.index.name = "Directory"
    output_dir = os.path.join(os.path.dirname(config_file), output_dir)

    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(os.path.join(output_dir, "parameters.csv"), sep="\t")

    # Must use itertuples instead of iterrows since iterrows will silently convert integers to floats.
    for tpl in df.itertuples():
        s = tpl._asdict()
        idx = tpl.Index
        s["Directory"] = idx
        run_dir = os.path.join(output_dir, "run_{}".format(idx))
        os.makedirs(run_dir, exist_ok=True)
        for f in files_to_copy:
            # To allow multiple files to act as templates we rely on the fact
            # that format will not fail if the string does not contain the parameter
            # it's trying to replace.
            infile_contents, outfile = None, None
            if isinstance(f, str):
                f_base = os.path.basename(f)
                infile_contents = open(
                    os.path.join(os.path.dirname(config_file), f), "r"
                ).read()
                outfile_name = os.path.join(run_dir, f_base)
                if os.path.exists(outfile_name) and not force:
                    raise RuntimeError(
                        f"{outfile_name} exists. Pass --force to force overwrite"
                    )
                outfile = open(outfile_name, "w")
            elif isinstance(f, list) and len(f) == 2:
                infile_contents = open(
                    os.path.join(os.path.dirname(config_file), f[0]), "r"
                ).read()
                outfile_name = os.path.join(run_dir, f[1])
                if os.path.exists(outfile_name) and not force:
                    raise RuntimeError(
                        f"{outfile_name} exists. Pass --force to force overwrite"
                    )
                outfile = open(outfile_name, "w")
            else:
                raise RuntimeError(
                    "Files: {} should be either a single string or "
                    "list of size two representing input and output "
                    "files. "
                )
            try:
                outfile.write(
                    Template(infile_contents).safe_substitute(s)
                    #    infile_contents.format_map(PartialFormatDict(**s))
                )
            except TypeError as e:
                print(
                    "Exception raised. Most likely a variable specified in the .yml file for replacement does not exist in the file given. \n\n Replacement dict: \n {} \n\n File: \n {} \n".format(
                        s, infile_contents
                    )
                )
                raise
        os.chdir(run_dir)
        for command in post_creation_commands:
            try:
                subprocess.check_output(command.split())
            except subprocess.CalledProcessError as e:
                os.chdir(root_dir)
                raise
        os.chdir(root_dir)
