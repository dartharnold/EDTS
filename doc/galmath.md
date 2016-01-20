## Purpose ##
The **galmath** script allows you to find estimates for good jump distances in the galactic core.

## Examples ##

`python galmath.py -j 40.81 -c 5`

```
#!text
Travelling 1000.0Ly with a 40.81Ly jump range, at around 5000Ly from the core centre:

  Maximum jump in range: 979.4Ly
  Plot between 959.0Ly and 963.9Ly
```

`python galmath.py -j 35.2 -c 0 -d 400`

```
#!text
Travelling 400.0Ly with a 35.20Ly jump range, at around 0Ly from the core centre:

  Maximum jump in range: 387.2Ly
  Plot between 381.5Ly and 383.4Ly
```

## Usage ##

Required arguments:

`-j N`/`--jump-range=N`: the jump range of the ship
`-c N`/`--core-distance=N`: the approximate current distance in kLy from the centre of the core

Optional arguments:

`-d N`/`--distance=N`: the distance to travel; default: `1000`