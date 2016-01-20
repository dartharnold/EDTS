## Purpose ##
The **fuel_usage** tool allows you to calculate how much fuel jumps between systems will require, and track how much fuel you will have left from a given starting amount.

## Examples ##
`python fuel_usage.py -f 6A -m 521.8 -t 32 Alioth Loucetios Eranin "LP 98-132" Aulin Altair Sol`

```
#!text
Alioth
    === 21.61Ly / 1.65T / 30.35T ===> Loucetios
    === 23.37Ly / 2.01T / 28.34T ===> Eranin
    ===  5.23Ly / 0.04T / 28.30T ===> LP 98-132
    === 12.51Ly / 0.39T / 27.90T ===> Aulin
    === 36.73Ly / 6.44T / 21.46T ===> Altair
    === 16.74Ly / 0.81T / 20.65T ===> Sol
```

The output will show a warning if the given jump is impossible due to insufficient range:

`python fuel_usage.py -f 6A -m 521.8 -t 32 Alioth Loucetios Eranin Altair`

```
#!text
Alioth
    === 21.61Ly / 1.65T / 30.35T ===> Loucetios
    === 23.37Ly / 2.01T / 28.34T ===> Eranin
    =!= 42.46Ly / 9.40T / 18.93T =!=> Altair
```

Similarly if you would have run out of fuel (here we set the starting fuel amount to 8T):

`python fuel_usage.py -f 6A -m 525.8 -t 32 Pandemonium Jotunheim Cemiess Achenar Agartha -s 8`

```
#!text
Pandemonium
    === 32.73Ly / 4.42T /  3.58T ===> Jotunheim
    === 26.18Ly / 2.42T /  1.16T ===> Cemiess
    === 14.38Ly / 0.50T /  0.65T ===> Achenar
    =!= 17.29Ly / 0.81T / -0.16T =!=> Agartha
```

## Usage ##
All names must be given as bare system names; station names are not currently supported.

Required arguments:

* `-f F`/`--fsd=F`: the ship's fitted FSD, in the form `6A` or `A6`
* `-m N`/`--mass=N`: the ship's mass when empty of fuel and cargo
* `-t N`/`--tank=N`: the size of the ship's fuel tank
* `system`: two or more system names to calculate usage between

Optional arguments:

* `-s N`/`--starting-fuel=N`: the amount of fuel to start the journey with; default: tank size
* `-c N`/`--cargo=N`: the amount of cargo on board the ship