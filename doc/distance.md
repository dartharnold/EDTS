## Purpose ##
The **distance** tool is used to determine the distance between two or more systems.

## Examples ##
Once the [First Run Setup](firstrun.md) is done, the script can be used:

`python distance.py Sol Alioth`

```
#!text

   Sol (G) > 82.53Ly > Alioth (A)
```

This variant creates a "Raikogram" providing the distances between all systems provided:

`python distance.py Sol Alioth Achenar "Beta-1 Tucanae"`

```
#!text

                  Achenar     Alioth   Beta-1 Tucanae        Sol
       Achenar          -   221.68Ly           24.3Ly   139.45Ly
        Alioth   221.68Ly          -         217.13Ly    82.53Ly
Beta-1 Tucanae     24.3Ly   217.13Ly                -   135.05Ly
           Sol   139.45Ly    82.53Ly         135.05Ly          -
```

This variant specifies that you want to know the distances from a particular system to all others:

`python distance.py -s Sol Alioth Achenar "Beta-1 Tucanae"`

```
#!text

   Sol (G) >  82.53Ly > Alioth (A)         
   Sol (G) > 135.05Ly > Beta-1 Tucanae (B) 
   Sol (G) > 139.45Ly > Achenar (B)        
```

## Usage ##
All names must be bare system names; station names are not currently supported.

Required arguments:

* `system`: two or more system names to calculate distances between

Optional arguments:

* `-s S`/`--start=S`: specifies that the given system should be considered the start point
* `-o`/`--ordered`: do not sort Raikogram systems into alphabetical order
* `-f`/`--full-width`: do not truncate Raikogram heading names for readability
* `c`/`--csv`: output results as CSV rather than human-readable text