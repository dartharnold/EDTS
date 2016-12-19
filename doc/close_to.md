## Purpose ##
The **close_to** tool allows you to find out which systems and stations are close to one or more specified systems.

## Examples ##
After the [First Run Setup](firstrun.md) is complete, the script can be run:

`python close_to.py Sol -m 25`

This finds the closest 10 systems to Sol within a max distance of 25LY:

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

Use of the `-m` flag is highly recommended - it specifies the maximum distance from the reference system(s) to search at, which can significantly speed up searching.

You can also put certain other requirements on the results (more info below):

`python close_to.py Sol -m 25 -p L -n 3 -l`

This specifies that all returned systems must have at least one station with a large landing pad (`-p L`), that only three results should be shown (`-n 3`), and also returns info on stations within those systems:

```
#!text
Matching systems close to Sol:

    Barnard's Star (5.95Ly)
        Levi-Strauss Installation (7Ls, Civilian Outpost)
        Haller City (37Ls, Planetary Port)
        Kuttner's Pride (37Ls, Planetary Outpost)
        Miller Depot (38Ls, Orbis Starport)
        Boston Base (63Ls, Coriolis Starport)
        Silves' Claim (63Ls, Planetary Outpost)
    Luhman 16 (6.57Ly)
        Jenner Orbital (10Ls, Civilian Outpost)
        Heisenberg Colony (14Ls, Civilian Outpost)
        Edison Hub (14Ls, Planetary Outpost)
    Wolf 359 (7.78Ly)
        Lomas Orbiter (53Ls, Orbis Starport)
        Cayley Enterprise (53Ls, Planetary Outpost)
        Powell High (99Ls, Coriolis Starport)
        Tryggvason Installation (99Ls, Planetary Port)
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
