## Purpose ##
The **close_to** tool allows you to find out which systems and stations are close to one or more specified systems.

## Examples ##
After the [First Run Setup](firstrun.md) is complete, the script can be run:

`python close_to.py Sol`

This finds the closest 10 systems to Sol:

```
#!text
Matching systems close to Sol:

    Alpha Centauri (4.38Ly)
    Barnard's Star (5.95Ly)
    Luhman 16 (6.57Ly)
    WISE 0855-0714 (7.17Ly)
    Wolf 359 (7.78Ly)
    Lalande 21185 (8.29Ly)
    UV Ceti (8.58Ly)
    Sirius (8.59Ly)
    Ross 154 (9.69Ly)
    Yin Sector CL-Y d127 (9.86Ly)
```

You can also put certain requirements on the results (more info below):

`python close_to.py Sol -p L -n 3 -l`

This specifies that all returned systems must have at least one station with a large landing pad, that only three results should be shown, and also returns info on those stations:

```
#!text
Matching systems close to Sol:

    Barnard's Star (5.95Ly)
        Levi-Strauss Installation (7Ls, Civilian Outpost)
        Miller Depot (38Ls, Orbis Starport)
        Boston Base (63Ls, Coriolis Starport)
    Wolf 359 (7.78Ly)
        Lomas Orbiter (51Ls, Unknown Starport)
        Powell High (99Ls, Coriolis Starport)
    Sirius (8.59Ly)
        Patterson Enterprise (1028Ls, Coriolis Starport)
        O'Brien Vision (11706Ls, Civilian Outpost)
```

You can also specify multiple systems; this will result in a list of systems which are closest to all the named systems.

## Usage ##
All systems must be provided as bare system names; station names are not currently allowed.

Required arguments:

* `system`: one or more system names

Optional arguments:

* `-p [SML]`/`--pad-size=[SML]`: specifies that at least one matching station must have a pad of this size
* `-s N`/`--max-sc-distance=N`: specifies that at least one matching station must be within the given distance (in Ls) of the entry point
* `-n N`/`--num=N`: the number of results to return
* `-l`/`--list-stations`: list all stations within returned systems
* `-a A`/`--allegiance=A`: specifies that returned systems must have the specified allegiance
* `-d N`/`--min-dist=N`: the minimum distance from the provided system that results must be
* `-m N`/`--max-dist=N`: the maximum distance from the provided system that results must be
