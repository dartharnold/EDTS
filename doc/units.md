## Purpose ##
The **units** tool allows you to convert distances.

## Examples ##
Hutton Orbital is famous for being 0.22 lightyears from Alpha Centauri.
To determine how far that is in lightseconds:

`python units.py 0.22 Ly Ls`

This outputs `6942672Ls`

But just how far is one lightsecond in kilometres anyway?

`python units.py 1Ls km`

This outputs `299792km`

## Usage ##
The first argument to **units** is the distance to convert.
It can be specified as a single string comprised of a number followed by a suffix or as two separate arguments; number and suffix.

The last argument is a suffix.  The distance will be converted and printed to the scale specified.

Valid suffices are:

* m

* km

* Mm

* Ls

* Ly
