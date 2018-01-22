## EDSM API cache ##

EDTS can query the [EDSM](https://www.edsm.net/) API for system and station information on an ad-hoc basis.  Doing so ensures that its database is updated without having to download the (large) data dumps over and over again.  Indeed all tools can be used without ever downloading a dump file, albeit with certain limitations.


## Prerequisites ##

EDSM dynamic mode requires using EDSM as the definitive data source, which is not the default.  If you have previously downloaded system data from EDDB you will need to reinitialise the local database.

`python update.py --systems-source edsm --steps clean,fsds`

No further steps are necessary to start from a clean database.  You may, however, wish to obtain the latest full dataset by running:

`python update.py --steps systems,stations`


# Cache usage

When enabled, EDTS will query the EDSM API for data pertaining to queries it is about to run, thus ensuring that its local database is up-to-date.

For instance, suppose you ran `edts.py -j 30 Sol Alioth Achenar`.  EDTS would fetch the data for Sol, Alioth and Achenar from EDSM and add them to the local database.  The actual routing calculations are still carried out using that local data.

Similarly, if you ran `edts.py -r -j 30 Sol Alioth Achenar`, the API would be queried for systems in the vicinity of the three waypoints, so that the local database has enough entries to caluclate a route.

Note, however, that a limit is placed on the radius of the search query for nearby systems.  This is to avoid placing too much load on EDSM.  Consequently there may be a better route which could be found if more systems were available in the database.  Only fetching a full system dump will guarantee best results.

Surrounding system information is only queried when necessary.  It won't be fetched for a simple distance calculation, for instance.


## Cache modes ##

By default the EDSM API is _never_ queried.  That may change in future releases of EDTS.  Add `--use-edsm never` to tool invocations to ensure you do not use the API.

With the `--use-edsm when-missing` flag, EDTS will fetch data for systems which are not already in the local database.  It will not hit the EDSM API if any record of a system is found locally and it will never query for surrounding systems.  Thus `when-missing` has the lowest network impact.  It is best suited for use in conjunction with a full data dump.

With the `--use-edsm periodically` flag, EDTS will refresh data for systems even if they are already in the local database and will query for surrounding systems.  However it will not send the same query to EDSM more than once every seven days.

With the `--use-edsm always` flag, EDTS will always query EDSM for the latest data and will query for surrounding systems.  Use with caution, as EDSM imposes rate limits on the use of its API.


## Examples ##

Start from a clean database.

`python update.py --steps clean,fsds`

Note that no information is available.

`python find.py Lave`

```
#!text
No matches
```

Query again, allowing EDSM download.

`python find.py --use-edsm when-missing Lave`

```
#!text
Matching systems:

Lave      K (yellow-orange) star
```

Note that no stations are known.

`python find.py -l Lave`

```
#!text

Matching systems:

Lave      K (yellow-orange) star
```

Query again, allowing EDSM download (for stations).

`python find.py --use-edsm when-missing -l Lave`

```
#!text

Matching systems:

Lave                                    K (yellow-orange) star
        Lave Station          (298Ls)   Coriolis Starport     
        Warinus               (862Ls)   Asteroid base         
        Chern Terminal       (2600Ls)   Planetary Outpost     
        Navigator Terminal   (2600Ls)   Planetary Outpost     
        Watts Survey         (2616Ls)   Planetary Outpost     
        Castellan Station    (2957Ls)   Outpost               
```

Estimate a route between Lave and Alioth.

`python edts.py -j 30 -s Lave -e Alioth`

```
#text
  Distance   System          Hop dist.         Jumps
                                                    
           > Lave   <                               
  144.52Ly > Alioth <   144.52Ly for 144.52Ly  5 - 6

Total distance: 144.52LY (144.52LY); total jumps: 5 - 6
Total SC distance: 0Ls; ETT: 3:35 - 4:20
```

Note that no surrounding systems are known.

`python close_to.py -m 150 Lave`

```
#text

Matching systems close to Lave:

    Alioth   144.52Ly    A (blue-white) star
```

Plot the route, allowing EDSM download of nearby systems.

`python edts.py --use-edsm periodically -j 30 -s Lave -e Alioth`

```
#text
   Distance   System                     Hop dist.         Jumps
                                                                
            > Lave              <                               
X   29.94Ly   Oresqu                                            
X   28.39Ly   VZ Corvi                                          
X   27.91Ly   LHS 2657                                          
X   29.55Ly   BF Canis Venatici                                 
X   28.25Ly   Tiethay                                           
X    6.72Ly > Alioth            <   150.77Ly for 144.52Ly      6

Total distance: 150.77LY (144.52LY); total jumps: 6
Total SC distance: 0Ls; ETT: 4:20
```
