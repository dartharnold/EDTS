# EDTS - A route decision maker for Elite: Dangerous #

This script provides a way to determine optimal routes for visiting a set of stations.

### Features ###

* Given a set of stations, find an optimal way to visit some or all of them
* Includes an estimation of time taken to reach stations in supercruise
* Includes an estimation of jump range decay due to picking up cargo en-route

### How to use ###

On first run, the latest [EDDB](http://eddb.io) system and station data must be downloaded:
```
#!bash
python eddb.py --download
```

Once this is done, the script can be used:
```
#!bash
python edts.py -j 35.2 --start "Sol/Galileo" --end "Alioth/Irkutsk" "Wolf 359/Powell High" "Agartha/Enoch Port"
```
This example assumes you wish to go from Galileo in Sol, to Irkutsk in Alioth, via both Powell High and Enoch Port. All of this will be done in a ship with a 35.2Ly jump range.

The output might look similar to the following:
```
#!text
Sol, Galileo (505Ls, Ocellus Starport)
    ===   7.78Ly ===> Wolf 359, Powell High (99Ls, Coriolis Starport), SC: ~88s
    === 152.54Ly ===> Agartha, Enoch Port (878Ls, Coriolis Starport), SC: ~123s
    === 230.65Ly ===> Alioth, Irkutsk (7783Ls, Orbis Starport), SC: ~229s

Total distance: 390.97Ly; total jumps: 14; total SC distance: 8760Ls
```

### Experimental/in-progress features ###
* You may pass the "-r" flag, which generates a full route between each hop, instead of just the hop itself. This route is generated from the available EDDB data, which may be incomplete (and thus the route may not be optimal). This may also take a long time to execute (and take a lot of CPU time while it does so).