# EDTS - A route decision maker for Elite: Dangerous #

This script provides a way to determine good routes for visiting a set of stations.

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

### Usage ###
All station arguments are provided in the form `System/Station`.

Required arguments:

* `-s S`/`--start S`: the station to start from
* `-e S`/`--end S`: the station to end at
* `-j N`/`--jump-range N`: the current jump range of the ship, in Ly

Optional arguments:

* `-n N`/`--num-jumps N`: the number of hops, excluding the start and end, to be visited. Default: the number of stations provided (i.e. visit all the hops)
* `-p [SML]`/`--pad-size [SML]`: the pad size of the ship. Default: `M` (medium pad).
* `-d N`/`--jump-decay N`: the jump range, in Ly, to lower the effective jump range by per hop. This allows estimation of a route with cargo being picked up at each hop along the way. Default: `0`
* `-v N`/`--verbose N`: causes more logging output to be provided
* `-o`/`--ordered`: indicates that the provided stations are already in order; generally used either to provide informational output only, or in conjunction with `-r`.
* `--jump-time N`: the time taken to perform a single hyperspace jump (used as part of the route estimation). Default: `45`
* `--diff-limit N`: the multiplier of the fastest route beyond which a route is considered "bad" and discounted. Default: `1.5`
* `--slf N`: the multiplier to apply to multi-jump hops to account for imperfect system positions. Default: `0.9`
* `--buffer-ly-route N`: The distance away from the optimal straight-line route to cache candidate stars for full routes. Default: `25`
* `--buffer-ly-hop N`: The distance away from the optimal straight-line route to search the cache for viable jumps. Default: `20`
* `--eddb-systems-file F`: The file to use as the EDDB systems.json. Default: `eddb/systems.json`
* `--eddb-stations-file F`: The file to use as the EDDB stations.json or stations_lite.json. Default: `eddb/stations_lite.json`
* `--download-eddb-files`: Download the EDDB systems and stations files before executing.
* `-r`/`--route`: **experimental** - causes a full route to be computed (every jump, not just the hops). The route is generated from the available EDDB data, and thus may not be optimal. May take a long time to execute, and eat CPU time while it does so.
* `station ...` - additional stations to travel via

### Experimental/in-progress features ###
* You may pass the "-r" flag, which generates a full route between each hop, instead of just the hop itself. This route is generated from the available EDDB data, which may be incomplete (and thus the route may not be optimal). This may also take a long time to execute (and take a lot of CPU time while it does so).