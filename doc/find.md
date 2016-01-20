## Purpose ##
The **find** tool allows you to find systems and stations using partial matches.

## Examples ##
Once the [First Run Setup](firstrun.md) is done, the script can be used:

`python find.py 'Turd*'`

```
#!text
Matching systems:

  Turd Wu
  Turdetani
  Turd Wura
  Turdet
```

`python find.py '* b23-9'`

```
#!text
Matching systems:

  Bleia Dryiae PM-T b23-9
  Col 173 Sector XZ-N b23-9
  Col 285 Sector LP-K b23-9
  Col 173 Sector XU-N b23-9
  Col 173 Sector WU-N b23-9
  Col 285 Sector NK-K b23-9
```

`python find.py 'Futh?r?'`

```
#!text
Matching systems:

  Futhark
  Futhorc
```

`python find.py 'Enoch*'`

```
#!text
Matching stations:

  Agartha, Enoch Port (878Ls, Coriolis Starport)
```

## Usage ##

Required arguments:

* `search`: the system or station to search for; supported wildcards are `*` to match any number of characters, and `?` to match a single character

Optional arguments:

* `-s`/`--systems`: only search for systems
* `-t`/`--stations`: only search for stations
* `-a`/`--anagram`: assume the query is an anagram and find systems/stations which match; this is experimental and may not work as you expect