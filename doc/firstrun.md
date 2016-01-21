On first run, the latest [EDDB](http://eddb.io) system and station data must be downloaded, as well as [Coriolis](http://coriolis.io) data for ship FSD sizes:

`python eddb.py --download`  
`python coriolis.py --download`

These commands can be re-run at any time to refresh the data (for instance, if new data has been added to EDDB which is relevant to you).