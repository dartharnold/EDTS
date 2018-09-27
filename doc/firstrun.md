EDTS uses a local database which must be initialised on first run.

The easiest - and recommended - way to get started is to run

`python update.py`

to download the latest [EDSM](http://edsm.net) system and station data, as well as [Coriolis](http://coriolis.io) data for ship FSD sizes.

Because the dataset is so large - multiple gigabytes for the system data alone - EDTS can update its database dynamically from EDSM when needed.

To use dynamic mode, initialise the database and fetch the FSD data:

`python update.py --steps clean,fsds`

Thereafter remember to add `--use-edsm` to command invocations.  See the [EDSM API cache](edsm.md) documentation for more details.

These commands can be re-run at any time to refresh the data (for instance, if new data has been added to EDSM which is relevant to you).
