## Purpose ##
The **coords** tool is a simple script to tell you the coordinates of specified systems.

## Example ##
Once the [First Run Setup](firstrun.md) is done, the script can be used:

`python coords.py Sol "Beta-1 Tucanae" Alioth Achenar`

```
#!text

             Sol: [    0.00,     0.00,     0.00]
  Beta-1 Tucanae: [   63.38,  -109.72,    46.72]
          Alioth: [  -33.66,    72.47,   -20.66]
         Achenar: [   67.50,  -119.47,    24.84]

```

## Usage ##
All names must be provided as bare system names; station names are not currently supported.

Required arguments:

* `system`: the names of one or more systems to retrieve coordinates for