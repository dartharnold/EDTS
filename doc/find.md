## Purpose ##
The **find** tool allows you to find systems and stations using partial matches.

## Examples ##
Once the [First Run Setup](firstrun.md) is done, the script can be used:

`python find.py 'Turd*'`

```
#!text
Matching systems:

  Turd Wu        M (red) star
  Turd Wura      L (brown dwarf) tar
  Turdet         M (red) tar
  Turdetani      M (red) tar
```

`python find.py '* b23-9'`

```
#!text
Matching systems:

  Bleia Dryiae PM-T b23-9        M (red) star
  Col 173 Sector XZ-N b23-9      M (red) star
  Col 285 Sector LP-K b23-9      M (red) star
  Col 173 Sector XU-N b23-9      M (red) star
  Col 173 Sector WU-N b23-9      M (red) star
  Col 285 Sector NK-K b23-9      M (red) star
```

`python find.py 'Futh?r?'`

```
#!text
Matching systems:

  Futhark      G (white-yellow) star
  Futhorc      G (white-yellow) star
```

`python find.py 'Enoch*'`

```
#!text
Matching stations:

  Agartha (G)   Enoch Port   888Ls   Coriolis Starport
```

## Usage ##

Required arguments:

* `search`: the system or station to search for; supported wildcards are `*` to match any number of characters, and `?` to match a single character

Optional arguments:

* `-s`/`--systems`: only search for systems
* `-t`/`--stations`: only search for stations
* `-a`/`--anagram`: assume the query is an anagram and find systems/stations which match; this is experimental and may not work as you expect