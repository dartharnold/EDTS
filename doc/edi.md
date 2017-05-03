## Purpose ##
The **edi** tool allows all the other tools to be run more quickly within a simple interactive interpreter.

## Example ##
`python edi.py`

```
#!text
EDI> distance Sol Alioth

Sol
    ===   82.53Ly ===> Alioth

EDI> set_ship -f 6A -m 521.8 -t 16
EDI> fuel_usage Sol Sirius Altair Aulin "LP 98-132" Sobek

Sol
    ===  8.59Ly / 0.14T / 15.86T ===> Sirius
    === 25.05Ly / 2.25T / 13.61T ===> Altair
    === 36.73Ly / 6.01T /  7.60T ===> Aulin
    === 12.51Ly / 0.35T /  7.25T ===> LP 98-132
    === 35.73Ly / 5.43T /  1.82T ===> Sobek

EDI> 
```

## Usage ##

Optional Arguments:

* `-v N`/`--verbose=N`: sets the output level (0-3, with 3 being debug output)
* `--eddb-systems-file=F`: sets the systems.json file to use (default: `eddb/systems.json`)
* `--eddb-stations-file=F`: sets the stations.json file to use (default: `eddb/stations.json`)
* `--coriolis-fsd-file=F`: sets the frame_shift_drive.json file to use (default: `coriolis/frame_shift_drive.json`)

Note that these arguments can also be used with any of the individual commands when run standalone (but not within EDI).

## Additional Commands ##

### set_ship ###
This command allows you to store the ship to use for future commands; this means you no longer have to include these options in commands which require ship stats or jump range, such as `edts`, `fuel_usage` and `galmath`.

e.g. `set_ship -f 5A -m 703 -t 16`

Required arguments:

* `-f F`/`--fsd=F`: set the FSD of the ship, in the form "6A" or "A6"
* `-m N`/`--mass=N`: set the mass of the ship with no fuel or cargo on board
* `-t N`/`--tank=N`: set the full fuel tank size of the ship

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
