## Purpose ##
The **obscured** tool helps you to choose an alternative jump when a leg of your route is obscured, eg by the body orbited by the station at which you are docked.

## Examples ##
Suppose you are at `Robert Aitken Orbital` in `Firdaus` and you have plotted a route to `Iota Hydri` with the first jump via `ICZ FB-X c1-17`.  However the jump is currently obscured.

`python close_to.py -s Firdaus -e "Iota Hydri" "ICZ FB-X c1-17"`

This finds the closest 10 systems to Firdaus whose direction is most deviated from ICZ FB-X c1-17.

```
#!text
Alternative systems for route from Firdaus to Iota Hydri:

   System           Dev.   Dist. from   Dist. to   

   Ngurungo         100%      25.54Ly    57.63Ly   
   Caspatsuria      100%      30.08Ly    61.26Ly   
   Beta-1 Tucanae   100%      23.01Ly    54.04Ly   
   ICZ LX-T b3-0    100%      30.49Ly    62.77Ly   
   Atlantis         100%      31.01Ly    61.92Ly   
   Karadjari        100%      26.05Ly    58.12Ly   
   Fotla            100%      16.19Ly    47.23Ly   
   Cegreeth         100%      24.41Ly    54.69Ly   
   Gondul           100%      22.78Ly    53.43Ly   
   BPM 28514        100%      32.22Ly    63.15Ly   
```

To understand the `deviation`, imagine a line from Firdaus extending to ICZ FB-X c1-17 beyond.  Any system lying directly on this line would have a deviation of 0%.  A system on a line perpendicular to the imaginary line or anywhere "behind" Firdaus would have a deviation of 100%.  The higher the deviation for a given system, the less chance that a jump to that system from Firdaus will be obscured by the same body which obscures ICZ FB-X c1-17.

Since an unobscured system is no use to you if your ship lacks the range to reach it, **obscured** can take into account the range of your ship.

Suppose your range is 28Ly.

`python close_to.py -j 28 -s Firdaus -e "Iota Hydri" "ICZ FB-X c1-17"`

```
#!text
Alternative systems for route from Firdaus to Iota Hydri:

   System           Dev.   Dist. from   Dist. to   

   Ngurungo         100%      25.54Ly    57.63Ly   
   Beta-1 Tucanae   100%      23.01Ly    54.04Ly   
   Karadjari        100%      26.05Ly    58.12Ly   
   Fotla            100%      16.19Ly    47.23Ly   
   Cegreeth         100%      24.41Ly    54.69Ly   
   Gondul           100%      22.78Ly    53.43Ly   
   Jotunheim        100%      27.47Ly    56.86Ly   
   Ngadjal          100%      26.18Ly    55.29Ly   
   ICZ LX-T b3-3    100%      27.81Ly    57.89Ly   
   ICZ LX-T b3-4    100%      17.59Ly    49.13Ly   
```

By default, **obscured** will return systems sorted by maximum deviation.  You can also request that it sort by minimum distance from the start system, with `--sort=DISTANCE-FROM` or to the end system, with `--sort=DISTANCE-TO`.

`python close_to.py -j 28 --sort=DISTANCE-FROM -s Firdaus -e "Iota Hydri" "ICZ FB-X c1-17"`

```
#!text
Alternative systems for route from Firdaus to Iota Hydri:

   System                      Dev.   Dist. from   Dist. to   

   Luluwala                     16%      20.45Ly    17.45Ly   
   Sorbago                      15%      17.67Ly    17.92Ly   
   Shui Wei Sector MI-S b4-3    29%      23.17Ly    18.34Ly   
   ICZ FB-X c1-27               34%      25.49Ly    20.29Ly   
   ICZ IH-U b3-3                36%      20.42Ly    21.90Ly   
   Clayahu                      36%      24.18Ly    22.25Ly   
   Malarhones                   37%      21.08Ly    22.63Ly   
   Sowiio                       16%      21.43Ly    22.69Ly   
   Rind                         36%      17.76Ly    23.04Ly   
   ICZ FB-X c1-19               15%      19.49Ly    23.34Ly   
```

`python close_to.py -j 28 --sort=DISTANCE-TO -s Firdaus -e "Iota Hydri" "ICZ FB-X c1-17"`

```
#!text
Alternative systems for route from Firdaus to Iota Hydri:

   System                      Dev.   Dist. from   Dist. to   
                                                              
   Luluwala                     16%      20.45Ly    17.45Ly   
   Sorbago                      15%      17.67Ly    17.92Ly   
   Shui Wei Sector MI-S b4-3    29%      23.17Ly    18.34Ly   
   ICZ FB-X c1-27               34%      25.49Ly    20.29Ly   
   ICZ IH-U b3-3                36%      20.42Ly    21.90Ly   
   Clayahu                      36%      24.18Ly    22.25Ly   
   Malarhones                   37%      21.08Ly    22.63Ly   
   Sowiio                       16%      21.43Ly    22.69Ly   
   Rind                         36%      17.76Ly    23.04Ly   
   ICZ FB-X c1-19               15%      19.49Ly    23.34Ly   
```

## Usage ##
All systems must be provided as bare system names; station names are not currently allowed.

Required arguments:

* `-s SYSTEM`/`--start=SYSTEM`: the system from which you are starting
* `obscured`: the name of the system which is obscured.

Optional arguments:

* `-d N`/`--min-deviation=N`: the minimum deviation, default 15%
* `-e SYSTEM`/`--end=SYSTEM`: the ultimate destination of your route, defaults to the `obscured` system
* `-n N`/`--num=N`: the maximum number of systems to return, default 10
* `--sort=DEVIATION/DISTANCE-FROM/DISTANCE-TO`: how to order the returned systems

To specify the jump range, use either:

* `-j N`/`--jump-range=N` (optional): the current jump range of the ship, in Ly.

or all of:

* `-f F`/`--fsd=F`: the ship's fitted FSD, in the form `6A` or `A6`
* `-m N`/`--mass=N`: the ship's mass when empty of fuel and cargo
* `-t N`/`--tank=N`: the size of the ship's fuel tank
* `-T N`/`--reserve-tank=N`: the size of the ship's reserve fuel tank
