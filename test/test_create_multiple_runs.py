import filecmp
from string import Template
import os
import pandas as pd
import glob
import subprocess
import contextlib
from parlize.parlize import create_runs
from parlize.utils import apply_over_runs


def relative_to_absolute_path(d):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), d)


@contextlib.contextmanager
def create_test_workflow():
    try:
        create_runs(relative_to_absolute_path("config.yml"), False)
        yield
    except Exception as e:
        raise e
    finally:
        subprocess.call(["rm", "-r", "TestOutput"])


@apply_over_runs(relative_to_absolute_path("TestOutput"))
def submit():
    subprocess.check_call(["bash", "run.sh"])


@apply_over_runs(relative_to_absolute_path("TestOutput"))
def check():
    # This function is applied for every directory, and when called returns a
    # dictionary of ints, one for each run.
    return int(open("output.txt").read())


def test_create_runs():
    with create_test_workflow():
        run_dirs = glob.glob(relative_to_absolute_path("TestOutput/run_*"))
        parameters = pd.read_csv(
            relative_to_absolute_path("TestOutput/parameters.csv"), sep="\t"
        )

        assert len(run_dirs) == 9
        assert len(parameters) == 9

        assert filecmp.cmp(
            relative_to_absolute_path("test_files/expected_parameters.csv"),
            os.path.join(relative_to_absolute_path("TestOutput/parameters.csv")),
            shallow=False,
        )

        for d in run_dirs:
            i = int(d[-1])
            current_parameters = parameters.iloc[i]
            expected = Template(
                open(relative_to_absolute_path("test_files/run.sh"), "r").read()
            ).substitute(current_parameters)
            received = open(
                relative_to_absolute_path(os.path.join(d, "run.sh")), "r"
            ).read()
            assert expected == received
            assert filecmp.cmp(
                relative_to_absolute_path(
                    relative_to_absolute_path("test_files/sample.py")
                ),
                relative_to_absolute_path(os.path.join(d, "renamed_sample.py")),
            )
        # Test submission
        submit()

        for d in run_dirs:
            assert os.path.exists(
                relative_to_absolute_path(os.path.join(d, "output.txt"))
            )
        results = check()
        for dirname, result in results.items():
            assert str(result) == "{i}{j}{k}".format(**parameters.iloc[dirname])
