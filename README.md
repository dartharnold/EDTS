# EDTS - A route decision maker for Elite: Dangerous #

This script provides a way to determine good routes for visiting a set of stations.

### Features ###

* Given a set of stations, find an optimal way to visit some or all of them
* Includes an estimation of time taken to reach stations in supercruise
* Includes an estimation of jump range decay due to picking up cargo en-route

### How to use ###

On first run, the latest [EDDB](http://eddb.io) system and station data must be downloaded:

`python eddb.py --download`

Once this is done, the script can be used:

`python edts.py -j 35.2 --start="Sol/Galileo" --end="Alioth/Golden Gate" "Wolf 359/Powell High" "Agartha/Enoch Port"`

This example assumes you wish to go from Galileo in Sol, to Golden Gate in Alioth, via both Powell High and Enoch Port. All of this will be done in a ship with a 35.2Ly jump range.

The output might look similar to the following:
```
#!text
Sol, Galileo (505Ls, Ocellus Starport)
    ===   7.78Ly ===> Wolf 359, Powell High (99Ls, Coriolis Starport), SC: ~88s
    === 152.54Ly ===> Agartha, Enoch Port (878Ls, Coriolis Starport), SC: ~123s
    === 230.65Ly ===> Alioth, Golden Gate (7783Ls, Unknown Starport), SC: ~229s

Total distance: 390.97Ly; total jumps: 14; total SC distance: 8760Ls
```

### Usage ###
All station arguments are provided in the form `System/Station`.

Required arguments:

* `-s S`/`--start=S`: the station to start from
* `-e S`/`--end=S`: the station to end at
* `-j N`/`--jump-range=N`: the current jump range of the ship, in Ly

Common optional arguments:

* `-n N`/`--num-jumps=N`: the number of hops, excluding the start and end, to be visited. Default: the number of stations provided (i.e. visit all the hops)
* `-p [SML]`/`--pad-size=[SML]`: the pad size of the ship. Default: `M` (medium pad).
* `-d N`/`--jump-decay=N`: the jump range, in Ly, to lower the effective jump range by per hop. This allows modelling of picking up cargo at each hop along the route. Default: `0`
* `-r`/`--route`: causes a full route to be computed (for every jump, not just the hops). The route is generated from the available EDDB data, and thus may not be optimal. May take a long time to complete, and eat CPU time while it does so. To make it faster (but potentially slightly less optimal), use a lower `--buffer-ly-hop` value.
* `-o`/`--ordered`: indicates that the provided stations are already in order; generally used either to provide informational output only, or in conjunction with `-r`
* `station ...` - additional stations to travel via

Other optional arguments:

* `-v N`/`--verbose=N`: causes more logging output to be provided
* `--jump-time=N`: the time taken to perform a single hyperspace jump (used as part of the route estimation). Default: `45`
* `--diff-limit=N`: the multiplier of the fastest route beyond which a route is considered "bad" and discounted. Default: `1.5`
* `--slf=N`: the multiplier to apply to multi-jump hops to account for imperfect system positions. Default: `0.9`
* `--rbuffer-base=N`: The minimum distance away from the optimal straight-line route to build a cache of viable stars from. Default: `10`
* `--rbuffer-mult=N`: The multiplier of the hop distance to add to rbuffer_base to determine the cache distance. Default: `0.15`
* `--hbuffer-base=N`: The minimum distance away from the optimal straight-line route to search the cache for viable jumps. Default: `5`
* `--hbuffer-mult=N`: The multiplier of a jump's distance to add to hbuffer_base to determine the valid stars to search with. Default: `0.3`
* `--route-strategy=R`: The method to use when searching for optimal routes. Valid options: `trundle` (custom algorithm, slow in many cases but usually quite accurate), `astar` (A*, fast but sometimes produces less well-balanced routes). Default: `astar`
* `--solve-full` - **experimental**: When enabled, uses the routing strategy to solve the optimal set of hops as well. **Very slow** and may not be effective.
* `--eddb-systems-file=F`: The file to use as the EDDB systems.json. Default: `eddb/systems.json`
* `--eddb-stations-file=F`: The file to use as the EDDB stations.json or stations_lite.json. Default: `eddb/stations_lite.json`
* `--download-eddb-files`: Download the EDDB systems and stations files before executing.

### File arguments ###

You may also read arguments from files using the syntax `@filename` in place of arguments; within the file, arguments are one per line. In the case of the example above:

`python edts.py -j 35.2 --start "Sol/Galileo" --end "Alioth/Irkutsk" "Wolf 359/Powell High" "Agartha/Enoch Port"`

... you could instead have a file called `sol-alioth.txt` containing the following:

```
#!text
--start=Sol/Galileo
--end=Alioth/Golden Gate
Wolf 359/Powell High
Agartha/Enoch Port
```

... allowing for the following command to be run instead:

`python edts.py -j 35.2 @sol-alioth.txt`

This allows for easy recalculating of the same route with different parameters such as jump range.

### Future improvements ###

* Making the cost algorithms aware of most in-system SC travel being slow (having to escape the start object's gravity well)
* Supporting start/end/hops just being systems rather than stations