## Purpose ##
The **fuel_usage** tool allows you to calculate how much fuel jumps between systems will require, and track how much fuel you will have left from a given starting amount.

## Examples ##
Once the [First Run Setup](firstrun.md) is done, the script can be used:

`python fuel_usage.py -f 6A -m 521.8 -t 32 Alioth Loucetios Eranin "LP 98-132" Aulin Altair Sol`

```
#!text

   Distance  System            Fuel cost  Remaining  
             Alioth (Star)                   32.00T  
    21.61Ly  Loucetios (Star)      1.65T     30.35T  
    23.37Ly  Eranin (Star)         2.01T     28.34T  
     5.23Ly  LP 98-132 (Star)      0.04T     28.30T  
    12.51Ly  Aulin (Star)          0.39T     27.90T  
    36.73Ly  Altair (Star)         6.44T     21.46T  
    16.74Ly  Sol (Star)            0.81T     20.65T  
```

The output will show a warning if the given jump is impossible due to insufficient range:

`python fuel_usage.py -f 6A -m 521.8 -t 32 Alioth Loucetios Eranin Altair`

```
#!text

   Distance  System            Fuel cost  Remaining  
             Alioth (Star)                   32.00T  
    21.61Ly  Loucetios (Star)      1.65T     30.35T  
    23.37Ly  Eranin (Star)         2.01T     28.34T  
 !  42.46Ly  Altair (Star)         9.40T     18.93T  
```

Similarly if you would have run out of fuel (here we set the starting fuel amount to 8T):

`python fuel_usage.py -f 6A -m 525.8 -t 32 Pandemonium Jotunheim Cemiess Achenar Agartha -s 8`

```
#!text

   Distance  System           Fuel cost  Remaining  
             Pandemonium (G)                 8.00T  
    32.73Ly  Jotunheim (K)        4.42T      3.58T  
    26.18Ly  Cemiess (G)          2.42T      1.16T  
    14.38Ly  Achenar (B)          0.50T      0.65T  
 !  17.29Ly  Agartha (G)          0.81T     -0.16T  
```

You can specify that the ship was refueled by giving the amount of added fuel as a percentage of the full tank size.

`python fuel_usage.py -f 6a -m 525.8 -t 32 Pandemonium Jotunheim Cemiess 10% Achenar Agartha -s 8`

```
#!text

   Distance  System           Refuel  Percent  Fuel cost  Remaining  
             Pandemonium (G)                                  8.00T  
    32.73Ly  Jotunheim (K)                         4.42T      3.58T  
    26.18Ly  Cemiess (G)                           2.42T      1.16T  
                               3.20T   10.00%                 4.36T  
    14.38Ly  Achenar (B)                           0.51T      3.85T  
    17.29Ly  Agartha (G)                           0.82T      3.02T  
```

In practice a 10% refuel at a station also takes into account the ship's reserve fuel tank size.  If you know it, use the `--reserve-tank` flag to specify the reserve size in tonnes.

## Usage ##
All names must be given as refuel percentages or bare system names; station names are not currently supported.

Required arguments:

* `-f F`/`--fsd=F`: the ship's fitted FSD, in the form `6A` or `A6`
* `-m N`/`--mass=N`: the ship's mass when empty of fuel and cargo
* `-t N`/`--tank=N`: the size of the ship's fuel tank
* `system`: two or more system names to calculate usage between

Optional arguments:

* `-T N`/`--reserve-tank=N`: the size of the ship's reserve fuel tank
* `-b N`/`--boost N`: level `1`-`3` FSD boost or `D` for white dwarf, `N` for neutron star); default: no boost
* `-B N`/`--range-boost N` (optional): Range bonus from a Guardian FSD booster.
* `-s N`/`--starting-fuel=N`: the amount of fuel to start the journey with; default: tank size
* `-c N`/`--cargo=N`: the amount of cargo on board the ship
