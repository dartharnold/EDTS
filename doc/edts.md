## Purpose ##
The **edts** tool is used to calculate the optimal order in which to visit a set of systems/stations. It is also capable of producing full routes between these systems, sometimes more effectively (if more slowly) than the in-game galaxy map.

## Example ##
Once the [First Run Setup](firstrun.md) is done, the script can be used:

`python edts.py -j 35.2 --start="Sol/Galileo" --end="Alioth/Golden Gate" "Wolf 359/Powell High" "Agartha/Enoch Port" "Alpha Centauri"`

This example assumes you wish to go from Galileo in Sol, to Golden Gate in Alioth, via Powell High, Enoch Port and Alpha Centauri (but not necessarily in that order). All of this will be done in a ship with a 35.2Ly jump range. Note that for the case of Alpha Centauri, we only specify the system name; this is because we definitely do not want to visit any stations in Alpha Centauri. It is a silly place.

The script will then determine the most efficient way to visit all these destinations. The output might look similar to the following:
```
#!text
  Distance   System           Cruise                                                 Hop dist.         Jumps
                                                                                                            
           > Sol               503Ls         Galileo      Ocellus Starport  <                               
  148.32Ly > Agartha           888Ls   ~118s Enoch Port   Coriolis Starport <   148.32Ly for 148.32Ly      5
  145.96Ly > Alpha Centauri                                                 <   145.96Ly for 145.96Ly      5
    8.33Ly > Wolf 359           98Ls    ~82s Powell High  Coriolis Starport <     8.33Ly for 8.33Ly        1
   78.21Ly > Alioth           7781Ls   ~223s Golden Gate  Coriolis Starport <    78.21Ly for 78.21Ly       3

Total distance: 380.82LY (380.82LY); total jumps: 14
Total SC distance: 8767Ls; ETT: 16:55
```

You can also use the tool to generate full routes:

`python edts.py -m 21.8 -f 2A -t 2 -r --start="Sol/Galileo" --end="Alioth/Golden Gate" "Wolf 359/Powell High" "Agartha/Enoch Port" "Alpha Centauri"`

```
#!text
   Distance   System                      Cruise                                            Fuel     Fuel range          Hop dist.         Jumps
                                                                                                                                                
            > Sol                          504Ls         Galileo      Ocellus Starport  <                                                       
X   32.50Ly   Core Sys Sector WO-R a4-3                                                     0.89T   0.80T (39%) +                               
    32.40Ly   LTT 183                                                                       0.82T   0.79T (39%) +                               
X   29.32Ly   ICZ EB-X c1-28                                                                0.62T   0.64T (32%) +                               
X   31.27Ly   ICZ FW-V b2-5                                                                 0.82T   0.74T (36%) +                               
X   31.13Ly > Agartha                      887Ls   ~118s Enoch Port   Coriolis Starport <   0.76T   0.73T (36%) +   156.63Ly for 148.32Ly      5
X   31.13Ly   ICZ FW-V b2-5                                                                 0.81T   0.73T (36%) +                               
X   31.75Ly   Putamasin                                                                     0.79T   0.76T (38%) +                               
X   31.80Ly   q1 Eridani                                                                    0.74T   0.76T (38%) +                               
X   30.34Ly   P Eridani                                                                     0.77T   0.69T (34%) +                               
X   24.83Ly > Alpha Centauri                                                            <   0.48T   0.45T (22%) +   149.86Ly for 145.96Ly      5
X    8.33Ly > Wolf 359                      98Ls    ~82s Powell High  Coriolis Starport <   0.06T   0.05T (2%) +      8.33Ly for 8.33Ly        1
X   30.35Ly   Ross 1003                                                                     0.77T   0.69T (34%) +                               
X   32.36Ly   LHS 2651                                                                      0.82T   0.79T (39%) +                               
X   17.61Ly > Alioth                      7781Ls   ~223s Golden Gate  Coriolis Starport <   0.23T   0.22T (11%) +    80.32Ly for 78.21Ly       3

Total distance: 395.14LY (380.82LY); total jumps: 14
Total SC distance: 8766Ls; ETT: 16:55; fuel cost: 9.38T
```

## Usage ##
All station arguments are provided in the form `System/Station` or simply `System` to specify a system only.  
The script can be run in Simple Mode (just provide the ship's jump range) or Ship Mode (provide the FSD size, empty ship mass and fuel tank size).

Start/end arguments:

* `-s S`/`--start=S`: the system/station to start from.
* `-e S`/`--end=S`: the system/station to end at.

If either or both of `--start` and `--end` are omitted, the script will choose them from the list of destinations.

Simple Mode arguments:

* `-j N`/`--jump-range=N` (optional): the current jump range of the ship, in Ly.
* `-d N`/`--jump-decay=N` (optional): the jump range, in Ly, to lower the effective jump range by per leg. This allows modelling of picking up cargo at each leg along the route. Default: `0`

Ship Mode arguments:

* `-f N[A-E]`/`--fsd=N[A-E]` (required): the FSD fitted to the ship, e.g. `5A`.
* `-m N`/`--mass=N` (required): the mass of the ship, in tonnes, with an empty fuel tank.
* `-t N`/`--tank=N` (required): the size of the ship's fuel tank, in tonnes.
* `-c N`/`--cargo=N` (optional): the amount of cargo to pick up at each stop. Default: `0`
* `-C N`/`--initial-cargo=N` (optional): the amount of cargo carried at the start of the journey. Default: `0`

Common optional arguments:

* `-n N`/`--num-jumps=N`: the number of legs, excluding the start and end, to be visited. Default: the number of stations provided (i.e. visit all the hops)
* `-b N`/`--boost N` (optional): level `1`-`3` FSD boost or `D` for white dwarf, `N` for neutron star); default: no boost
* `-B N`/`--range-boost N` (optional): Range bonus from a Guardian FSD booster.
* `-p [SML]`/`--pad-size=[SML]`: the pad size of the ship. Default: `M` (medium pad).
* `-r`/`--route`: causes a full route to be computed (for every jump, not just the legs). The route is generated from the available EDSM data, and thus may not be optimal.  Can only be used in conjunction with `-j` or `-f`.
* `-a`/`--accurate`: only used with `-r`; makes routing use a different algorithm (`trunkle`) which produces more accurate and efficient routes, but sometimes is slightly slower and may be unable to calculate some routes.
* `-o`/`--ordered`: indicates that the provided systems/stations are already in order; generally used either to provide informational output only, or in conjunction with `-r`
* `-O`/`--tour`: partial ordered, for calculating the optimal route for passenger tours; each time this flag appears any subsequent system[/station] arguments will be routed in order.
* `system[/station] ...` - additional systems/stations to travel via

Other optional arguments:

* `--jump-time=N`: the time taken to perform a single hyperspace jump (used as part of the route estimation). Default: `45`
* `--diff-limit=N`: the multiplier of the fastest route beyond which a route is considered "bad" and discounted. Default: `1.5`
* `--slf=N`: the multiplier to apply to multi-jump legs to account for imperfect system positions. Default: `0.9`
* `--rbuffer=N`: The distance away from the optimal straight-line route to build a cache of viable stars from. Default: `40`
* `--hbuffer=N`: The minimum distance away from the optimal straight-line route to search the cache for viable jumps. Default: `10`
* `--route-strategy=R`: The method to use when searching for optimal routes. Default: `trunkle`. Valid options:
    - `trundle`: a custom algorithm, very slow in many cases but usually very accurate
    - `trunkle`: a hybrid algorithm using trundle, but chunking the route to speed up execution; relatively fast and quite accurate
    - `astar`: the A* algorithm, fast and reliable but sometimes produces suboptimal and less well-balanced routes
* `--avoid=SYSTEM`: Specify a system to route around, for instance because the next jump would be obscured or would have too high a fuel cost.  You can use `--avoid` multiple times to avoid multiple systems.
* `--route-set system[/station] ...`: Specify a set of systems of which at least one but not necessarily all should be visited.  Implies --solve-mode=basic.
* `--route-set-min=N`: Override the minimum number of systems in the route set which must be visited.  Default: `1`
* `--route-set-max=N`: Override the maximum number of systems in the route set which can be visited.  Default: `1`
* `--route-filters=FILTERS`: List of filters which systems must match to be included in the plot.  Ignored if `--route` is not used.

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
