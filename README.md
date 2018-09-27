# EDTS - A suite of routing, fuel and distance tools for Elite: Dangerous #

### Tools ###

* **[edts](doc/edts.md)**: finds the optimal order to visit a set of stations, and can produce full routes between systems
* **[close_to](doc/close_to.md)**: finds systems close to others, optionally with constraints
* **[coords](doc/coords.md)**: returns the coordinates of given systems
* **[distance](doc/distance.md)**: finds the distance between two or more systems
* **[find](doc/find.md)**: searches for systems and stations by name, including wildcards
* **[fuel_usage](doc/fuel_usage.md)**: determines the amount of fuel used by a series of jumps
* **[galmath](doc/galmath.md)**: gives an estimate of good plot distances in the galactic core

* **[edi](doc/edi.md)**: an interactive interpreter to run all the above tools more quickly (without reloading the EDSM/Coriolis data)

### Features ###

The main **edts** script provides a way to determine good routes for visiting a set of systems and/or stations.

* Given a set of systems and/or stations, find an optimal way to visit some or all of them
* Includes an estimation of time taken to reach stations in supercruise
* Includes an estimation of jump range decay due to picking up cargo en-route

### Requirements ###

A Python 2.7/3.x interpreter, and enough disk space for the data (currently around 500MB-1GB).

Please note that versions of Python 2.7 earlier than 2.7.9 may have problems initially retrieving data.

### How to use ###

On first run, the latest [EDSM](http://edsm.net) system and station data must be downloaded, as well as [Coriolis](http://coriolis.io) data for ship FSD sizes:

`python update.py`  

Once this is done, the script can be used:

`python edts.py -j 35.2 --start="Sol/Galileo" --end="Alioth/Golden Gate" "Wolf 359/Powell High" "Agartha/Enoch Port" "Alpha Centauri"`

This example assumes you wish to go from Galileo in Sol, to Golden Gate in Alioth, via Powell High, Enoch Port and Alpha Centauri. All of this will be done in a ship with a 35.2Ly jump range. Note that for the case of Alpha Centauri, we only specify the system name; this is because we definitely do not want to visit any stations in Alpha Centauri. It is a silly place.

The output might look similar to the following:
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

### Contact ###

[EDCD](http://edcd.github.io) has a [Discord server](https://discord.gg/0uwCh6R62aQ0eeAX) with a channel for EDTS. Feel free to drop by and chat or ask for help!

There is also a [thread on the Frontier forums](https://forums.frontier.co.uk/showthread.php/197847) for the project.

### Thanks ###

* CMDR furrycat - for significant additions and improvements to the project
* CMDR Jackie Silver - without whose excellent work the pgnames functionality wouldn't exist!
