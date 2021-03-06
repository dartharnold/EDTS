## Purpose ##
The **edi** tool allows all the other tools to be run more quickly within a simple interactive interpreter.

## Example ##
`python edi.py`

```
#!text
EDI> distance Sol Alioth

   Sol (G) > 82.53Ly > Alioth (A)

EDI> set_ship -f 6A -m 521.8 -t 16

Ship [FSD: 6A, mass: 521.8T, fuel: 16T]: jump range 40.81LY (41.43LY)

EDI> fuel_usage Sol Sirius Altair Aulin "LP 98-132" Sobek

   Distance  System         Fuel cost  Remaining  
             Sol (G)                      15.86T  
     8.59Ly  Sirius (A)         0.14T     15.86T  
    25.05Ly  Altair (A)         2.25T     13.75T  
    36.73Ly  Aulin (K)          6.08T      9.92T  
    12.51Ly  LP 98-132 (M)      0.37T     15.63T  
    35.73Ly  Sobek (G)          5.66T     10.34T  

EDI> 
```

## Usage ##

Optional Arguments:

* `-v N`/`--verbose=N`: sets the output level (0-3, with 3 being debug output)

Note that these arguments can also be used with any of the individual commands when run standalone (but not within EDI).

## Additional Commands ##

### set_ship ###
This command allows you to store the ship to use for future commands; this means you no longer have to include these options in commands which require ship stats or jump range, such as `edts`, `fuel_usage` and `galmath`.

e.g. `set_ship -f 5A -m 703 -t 16`

Required arguments:

* `-f F`/`--fsd=F`: set the FSD of the ship, in the form "6A" or "A6"
* `-m N`/`--mass=N`: set the mass of the ship with no fuel or cargo on board
* `-B N`/`--range-boost N` (optional): Range bonus from a Guardian FSD booster.
* `-t N`/`--tank=N`: set the full fuel tank size of the ship
* `-T N`/`--reserve-tank=N`: the size of the ship's reserve fuel tank

### ship ###
This command shows the saved ship, if any.

### set_verbosity ###
This command allows you to set the verbosity level from within EDI; it's equivalent to running edi.py with the `-v` flag.

e.g. `set_verbosity 3`

### help ###
Lists commands if used with no arguments, or provides help for a particular command if provided.

e.g. `help`, `help close_to`

### quit / exit ###
Does exactly what it says on the tin :)
