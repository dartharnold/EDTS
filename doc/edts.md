## Purpose ##
The **edts** tool is used to calculate the optimal order in which to visit a set of systems/stations. It is also capable of producing full routes between these systems, sometimes more effectively (if more slowly) than the in-game galaxy map.

## Example ##
Once the [First Run Setup](firstrun.md) is done, the script can be used:

`python edts.py -j 35.2 --start="Sol/Galileo" --end="Alioth/Golden Gate" "Wolf 359/Powell High" "Agartha/Enoch Port" "Alpha Centauri"`

This example assumes you wish to go from Galileo in Sol, to Golden Gate in Alioth, via Powell High, Enoch Port and Alpha Centauri (but not necessarily in that order). All of this will be done in a ship with a 35.2Ly jump range. Note that for the case of Alpha Centauri, we only specify the system name; this is because we definitely do not want to visit any stations in Alpha Centauri. It is a silly place.

The script will then determine the most efficient way to visit all these destinations. The output might look similar to the following:
```
#!text
Sol, Galileo (505Ls, Ocellus Starport)
    === 148.32Ly (5 jumps) ===> Agartha, Enoch Port (878Ls, Coriolis Starport), SC: ~118s
    === 145.96Ly (5 jumps) ===> Alpha Centauri
    ===   8.33Ly (1 jump ) ===> Wolf 359, Powell High (99Ls, Coriolis Starport), SC: ~83s
    ===  78.21Ly (3 jumps) ===> Alioth, Golden Gate (7783Ls, Unknown Starport), SC: ~224s

Total distance: 380.82Ly; total jumps: 14; total SC distance: 8760Ls; ETT: 23:25
```

You can also use the tool to generate full routes:

`python edts.py -m 21.8 -f 2A -t 2 -r --start="Sol/Galileo" --end="Alioth/Golden Gate" "Wolf 359/Powell High" "Agartha/Enoch Port" "Alpha Centauri"`

```
#!text
Sol, Galileo (505Ls, Ocellus Starport)
    --- 26.56Ly ---> P Eridani
    --- 30.34Ly ---> q1 Eridani
    --- 31.80Ly ---> Putamasin
    --- 31.75Ly ---> ICZ FW-V b2-5
    === 31.13Ly ===> Agartha, Enoch Port (878Ls, Coriolis Starport) -- 151.59Ly for 148.32Ly
    --- 31.13Ly ---> ICZ FW-V b2-5
    --- 24.40Ly ---> ICZ CB-W b2-2
    --- 29.01Ly ---> Cocijo
    --- 30.33Ly ---> Sanuku
    === 32.75Ly ===> Alpha Centauri -- 147.62Ly for 145.96Ly
    ===  8.33Ly ===> Wolf 359, Powell High (99Ls, Coriolis Starport) -- 8.33Ly for 8.33Ly
    --- 21.73Ly ---> LHS 316
    --- 24.24Ly ---> BD+55 1519
    === 32.65Ly ===> Alioth, Golden Gate (7783Ls, Unknown Starport) -- 78.62Ly for 78.21Ly

Total distance: 380.82Ly; total jumps: 14; total SC distance: 8760Ls; ETT: 23:25
```

## Usage ##
All station arguments are provided in the form `System/Station` or simply `System` to specify a system only.  
The script can be run in Simple Mode (just provide the ship's jump range) or Ship Mode (provide the FSD size, empty ship mass and fuel tank size).

Required arguments:

* `-s S`/`--start=S`: the system/station to start from.
* `-e S`/`--end=S`: the system/station to end at.

Simple Mode arguments:

* `-j N`/`--jump-range=N` (required): the current jump range of the ship, in Ly.
* `-d N`/`--jump-decay=N` (optional): the jump range, in Ly, to lower the effective jump range by per hop. This allows modelling of picking up cargo at each hop along the route. Default: `0`

Ship Mode arguments:

* `-f N[A-E]`/`--fsd=N[A-E]` (required): the FSD fitted to the ship, e.g. `5A`.
* `-m N`/`--mass=N` (required): the mass of the ship, in tonnes, with an empty fuel tank.
* `-t N`/`--tank=N` (required): the size of the ship's fuel tank, in tonnes.
* `-c N`/`--cargo=N` (optional): the amount of cargo to pick up at each stop. Default: `0`

Common optional arguments:

* `-n N`/`--num-jumps=N`: the number of hops, excluding the start and end, to be visited. Default: the number of stations provided (i.e. visit all the hops)
* `-p [SML]`/`--pad-size=[SML]`: the pad size of the ship. Default: `M` (medium pad).
* `-r`/`--route`: causes a full route to be computed (for every jump, not just the hops). The route is generated from the available EDDB data, and thus may not be optimal.
* `-a`/`--accurate`: only used with `-r`; makes routing use a different algorithm (`trunkle`) which produces more accurate and efficient routes, but sometimes is slightly slower and may be unable to calculate some routes.
* `-o`/`--ordered`: indicates that the provided systems/stations are already in order; generally used either to provide informational output only, or in conjunction with `-r`
* `system[/station] ...` - additional systems/stations to travel via

Other optional arguments:

* `--jump-time=N`: the time taken to perform a single hyperspace jump (used as part of the route estimation). Default: `45`
* `--diff-limit=N`: the multiplier of the fastest route beyond which a route is considered "bad" and discounted. Default: `1.5`
* `--slf=N`: the multiplier to apply to multi-jump hops to account for imperfect system positions. Default: `0.9`
* `--rbuffer=N`: The distance away from the optimal straight-line route to build a cache of viable stars from. Default: `40`
* `--hbuffer=N`: The minimum distance away from the optimal straight-line route to search the cache for viable jumps. Default: `10`
* `--route-strategy=R`: The method to use when searching for optimal routes. Default: `trunkle`. Valid options:
    - `trundle`: a custom algorithm, very slow in many cases but usually very accurate
    - `trunkle`: a hybrid algorithm using trundle, but chunking the route to speed up execution; relatively fast and quite accurate
    - `astar`: the A* algorithm, fast and reliable but sometimes produces suboptimal and less well-balanced routes

### File arguments ###

You may also read arguments from files using the syntax `@filename` in place of arguments; within the file, arguments are one per line. In the case of the example above:

`python edts.py -j 35.2 --start "Sol/Galileo" --end "Alioth/Irkutsk" "Wolf 359/Powell High" "Agartha/Enoch Port" "Alpha Centauri"`

... you could instead have a file called `sol-alioth.txt` containing the following:

```
#!text
--start=Sol/Galileo
--end=Alioth/Golden Gate
Wolf 359/Powell High
Agartha/Enoch Port
Alpha Centauri
```

... allowing for the following command to be run instead:

`python edts.py -j 35.2 @sol-alioth.txt`

This allows for easy recalculating of the same route with different parameters such as jump range.

You could also make a file containing the Accurate Mode parameters for a particular ship, allowing you to do similar to the following:

`python edts.py @asp.txt @sol-alioth.txt`

### Future improvements ###

* Making the cost algorithms aware of most in-system SC travel being slow (having to escape the start object's gravity well)