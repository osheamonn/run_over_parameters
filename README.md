
Library for running trivially parallelizable scripts over a specification of
 parameters. Implemented in python but is agnostic to how underlying scripts work.  

If we have some script we wish to run for a range of different parameters, by
 specifying which parameters we wish to vary and their values in a yaml configuration
  file, the `create_multiple_runs` executable will take that config file, and for
   each combination of parameters present, create a new directory where each script
    can be run or submit to a seperate computing resource. All of the values of the
     parameters will be output to a `parameters
    .csv` file and the run directories are named `run_0`, `run_1`, etc.
    
The example in `test_create_multiple_runs.py` works as follows: The executable which
 is to be run is a bash script `run.sh`, which itself runs a seperate python script `sample
 .py` which takes 3 integers i,j,k as input, and then concatenates them and outputs
  them to a file `output.txt`. If we only wanted to run this for the paramaters 1, 2
  , 3, then the command in `run.sh` would be:
  
 ``` shell script
  python sample.py --i 1 --j 2 --k 3
```

which would produce an `output.txt` with the only line `123`. Now if we want to vary
 the i,j,k parameters, we simply replace 1,2,3 with named placeholders, 
 ```
python sample.py --i {i} --j {j} --k {k}
```
and `create_multiple_runs` will use python string formatting to replace `i,j,k` with
 a range of values. To specify what values to use, `create_multiple_runs` takes a
  yaml config file as argument. The config file must specify 3 things:
   
  - `OutputDirectory`, name of directory to output all runs to. Will be created if it
   doesn't exist. 
  - `FilesToTemplateAndCopy`, list of all files needed for each run. If a file
   has named placeholders for string formatting as in the `run.sh` above, they will
    be replaced, otherwise the file will just be copied to each run directory. Files
     can be renamed on copying to the run directory by specifying a size 2 list of
      strings instead of a single string. e.g. - [run.sh, renamed_run.sh] instead of
       just -run.sh in the yaml. 
   - `VariableParameters`. Set of key-value pairs corresponding the names of the
    parameters to substitute in files, and a list of the values to vary over. In the
     test example for substituting `i,j,k` in run.sh, this section looks like: 
``` yaml
VariableParameters:
   i:
    - 1
    - 2
    - 3

  !!python/tuple [j, k]:
    - [4, 9]
    - [5, 8]
    - [6, 7]
```   
   What this says is: `i` will take the values `1,2,3`, and `j` and `k` will take the
    values 4 and 9 respectively, then 5 and 8, and then 6 and 7. So this will
     produce 9 different runs. The idea here is that
     each key-value pair specifies which variables vary independently, and for
      variables whose values are dependent, we specify in one key-value pair which
       maps a tuple of names to a list of list of values.    
  
  We also provide a (possibly) useful python decorator `apply_over_runs` in `parlize
  /utils.py`. This decorator takes a directory as argument, and if decorating a
   function will automatically run that function in each directory. This can be
    potentially useful for submitting runs, or doing postprocessing, and hides the
     looping over the run directories. 
     
 # Examples
 
 - `examples/test_example` uses the test example described above.  
   [`run_workflow.py`](examples/test_example/run_workflow.py) to demonstrate how a full workflow
    might be assembled using the
    `apply_over_runs` decorator. If executed, it will call `parlize.create_runs` and
     and each run
     will
     execute. Then the
     outputs are collected and the average of each output printed which should yield
      `258`.
      
 - `examples/derivative.py` contains an example to numerically differentiate `exp(x
 )` at `x=0` using a second order formula for spacings = `np.logspace(-20, 0, 10
 )`. This also has a `run_workflow.py` which has a more complicated structure
 . `run_workflow.py` specifies the spacings as a `logspace` and writes this
  as a list to the .yml file. The runs are then created and executed, and the outputs
   are gathered, and the error is plotted as a function of the spacing.    
        
 
  # Caveats
  - `parameters.csv` uses tabs as a separator instead of commas, so the sep must be
   given to read it in properly. e.g. `pd.read_csv('parameters.csv', sep='\t')`
  - Since the library depends on python string formatting to substitute in the
   template files, it will not work if one wishes to perform substitution inside of
    other python files. This is because if those files do *any* string formatting
     themselves, `create_multiple_runs` will try and format those strings and either
      fail or do the wrong thing. As such any python files in the
       `FilesToTemplateAndCopy` section of the config file are copied with no
        substitution. 
  - Any usage of `{`, `}` must be escaped by repeating them `{{`, `}}`, e.g. if a
   bash script has bash variables. This is since the code will try and format these
    strings and fail. 
  - There is a good chance I've made an error in terms of assuming file locations to
   be relative. If so this should be changed. 
