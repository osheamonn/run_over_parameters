
This library aims to solve the common problem of having a single run of a script/program,
and then creating an array of runs where some set of parameters from the original vary
over a set of values. For example, taking some simulation and wanting to investigate
how varying the grid resolution affects results, or running a gravitational wave analysis
for several events. It does not aim to solve the problem of actually _running_ the runs, aggregating their results or similar problem which is usually solved by a DAG within some framework such as HTCondor.

The gist of this library is to have a script such as this which prints `1 a`
```
#! /bin/bash

echo 1 a
```
If one then wants to have scripts which print every combination of the numbers
and letters (1,2,3) and (a,b,c), this can be achieved by converting the file
to a template file:
```
#! /bin/bash

echo $number $letter
```
specifying the ranges in a yaml file, and then running the commands described below to create the 9 runs corresponding to all combinations of the parameters.

# Installation
```
python setup.py install
```

# Usage

Two executables are installed: `parlize_create_multiple_runs` which is the main executable and `parlize_generate_sample_config` which will generate a sample `config.yml` file which can be edited. Running `parlize_create_multiple_runs --config-file config.yml` will create a run directory for each set of parameters, with the names `run_0, run_1, run_2, ...` along with a `.csv` file `parameters.csv` which has the list of parameters and the run directory to which it corresponds.

The options specified in the config file are:
- `OutputDirectory`: Where the run directories will be created
- `FilesToTemplateAndCopy`: List of files for which instances of $variable_name will be substituted. If no such string exists, the file will simply be copied. Note: Only the basename is copied, the directory structure is not preserved. If instead of a filename, one uses a list of size 2 such as `[old, new]` the file `old` will be templated/copied but with the newname `new`.

- `VariableParameters`: This is where the variable names and ranges are specified. In the simplest case, this is a yaml dict from names to a list of values. For example, in this case:

    ``` yaml
  VariableParameters:
    root_1:
      - 10.
      - 20.
    root_2:
      - 'foo'
      - 'bar'
    ```

  all instances of `$root_1` and `$root_2` in the files specified in `FilesToTemplateAndCopy` will be replaced with the combinations (10, 'foo'), (20, 'foo'), (10, 'bar'), (20, 'bar') resulting in 4 runs.

  It may also be desirable to replace the values of two variables which don't vary independently. This can be achieved using the awkward `!!python/tuple` syntax to specify the dependent variables, and then a list of pairs of values. For instance:

  ``` yaml
  VariableParameters:
    !!python/tuple [country, capital_city]:
      - [Ireland, Dublin]
      - [Chile, Santiago]
  ```
  will result in 2 runs where the strings `$country` and `$capital_city` have been replaced by (Ireland, Dublin) and (Chile, Santiago).

  It is also possible to have subgroups by having an extra layer in the yaml dictionary. For example:

  ``` yaml
  VariableParameters:
    root_1:
      - 10
      - 20
    Batch1:
      parameter_for_batch_1:
        - 'a'
        - 'b'
    Batch2:
      parameter_for_batch_2:
        - 4
        - 6
  ```
  will create 8 runs where in all 8 `$root_1` is replaced by either 10 or 20, but for the first 4 `$parameter_for_batch_1` is replaced by 'a' or 'b', and in the second 4 `$parameter_for_batch_2` is replaced by 4 or 6.

- `PostCreationCommands`: is a list of bash commands that will be run _within_ each run directory after the files are  templated and copied. This
can be done to create a directory such as `log`, edit permissions, or perhaps also actually launch each run.

In addition there are some helper functions/scripts. `parlize_run_command` can be run in the root directory which contains the `run_*` dirs.
```
parlize_run_command --command COMMAND --filter SQL_FILTER --dry-run --debug-single-run INT
```
will run the string COMMAND in each run directory. The optional SQL_FILTER will apply a SQL style filter to the values in `parameters.csv` and only run the command for runs which satisfy the filter. `--dry-run` will not actually run the command but output what command will be run and in which directories. `--debug-single-run` will run the command in only that run directory.

In `parlize.utils` there is the decorator `apply_over_runs` which can be useful in creating post-analysis scripts in python. It can decorate a function which returns either `None` or something else

``` python
@apply_over_runs("Directory")
def return_none():
  subprocess.check_call(['ls', '-l'])

@apply_over_runs("Directory")
def return_some():
  with open("output.txt", 'r') as f:
    x = f.read()
  return x
```

The decorator takes as argument the directory name which contains the `run_*` directories. If the decorated function returns `None`, it will simply be run inside of each directory `run_*` (so make sure commands are called relative to the `run_x` directory).

If the function returns not-`None`, calling the decorated function returns a dictionary with the run number as key, and the the value of the function as value. If `Directory` contained `run_0` and `run_1`, and output.txt contained the number of the run multiplied by 2, then calling `return_some()` would return

``` python
{
  '0': '0',
  '1': '2'
}
```


  # Caveats
  - `parameters.csv` uses tabs as a separator instead of commas, so the sep must be
   given to read it in properly. e.g. `pd.read_csv('parameters.csv', sep='\t')`

