from setuptools import setup

setup(
    name="parlize",
    version="1.0",
    description="Tools for generating runs over multiple configurations. ",
    author="Eamonn O'Shea",
    packages=["parlize"],  # same as name
    scripts=[
        "bin/parlize_create_multiple_runs",
        "bin/parlize_generate_sample_config",
        "bin/parlize_run_command",
    ],
)
