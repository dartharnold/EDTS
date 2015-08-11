import argparse
import json
import os
import sys
import eddb
from solver import Solver
from station import Station

class Application:

  def __init__(self):
    ap = argparse.ArgumentParser(description = "Elite: Dangerous TSP Solver", fromfile_prefix_chars="@")
    ap.add_argument("-j", "--jump-distance", type=float, required=True, help="The ship's max jump distance while empty")
    ap.add_argument("-s", "--start", type=str, required=True, help="The starting station, in the form 'system/station'")
    ap.add_argument("-e", "--end", type=str, required=True, help="The end station, in the form 'system/station'")
    ap.add_argument("-n", "--num-jumps", required=True, type=int, help="The number of stations to visit, not including the start/end")
    ap.add_argument("-p", "--pad-size", default="M", type=str, help="The landing pad size of the ship (S/M/L)")
    ap.add_argument("-d", "--jump-decay", type=float, default=0.0, help="An estimate of the range decay per jump in Ly (e.g. due to taking on cargo)")
    ap.add_argument("-v", "--verbose", type=int, default=1, help="Increases the logging output")
    ap.add_argument("--jump-time", type=float, default=45.0, help="Seconds taken per hyperspace jump")
    ap.add_argument("--sc-multiplier", type=float, default=0.25, help="Seconds taken per 1Ls of supercruise travel")
    ap.add_argument("--diff-limit", type=float, default=1.5, help="The multiplier of the fastest route which a route must be over to be discounted")
    ap.add_argument("--slf", type=float, default=0.9, help="The multiplier to apply to multi-jump hops to account for imperfect system positions")
    ap.add_argument("--eddb-systems-file", type=str, default="eddb/systems.json", help="Path to EDDB systems.json")
    ap.add_argument("--eddb-stations-file", type=str, default="eddb/stations_lite.json", help="Path to EDDB stations_lite.json or stations.json")
    ap.add_argument("--download-eddb-files", nargs="?", const=True, help="Download EDDB files if not already present.")
    ap.add_argument("stations", metavar="system/station", nargs="+", help="A station to travel via, in the form 'system/station'")
    self.args = ap.parse_args()

    if not os.path.isfile(self.args.eddb_systems_file) or not os.path.isfile(self.args.eddb_stations_file):
      if self.args.download_eddb_files:
        eddb.download_eddb_files(self.args.eddb_systems_file, self.args.eddb_stations_file)
      else:
        self.log(0, "Error: EDDB system/station files not found. Run this script with '--download-eddb-files' to auto-download these.")
        sys.exit(1)

    self.eddb_systems = eddb.load_systems(self.args.eddb_systems_file)
    self.eddb_stations = eddb.load_stations(self.args.eddb_stations_file)
    

  def log(self, level, msg):
    if self.args.verbose >= level:
      print msg


  def get_station_from_string(self, statstr):
    parts = statstr.split("/", 1)
    sysname = parts[0]
    statname = parts[1]

    return self.get_station(sysname, statname)

  def get_station(self, sysname, statname):
    for sy in self.eddb_systems:
      if sy["name"].lower() == sysname.lower():
        # Found system
        sysid = sy["id"]

        for st in self.eddb_stations:
          if st["system_id"] == sysid and st["name"].lower() == statname.lower():
            # Found station
            return Station(sy["x"], sy["y"], sy["z"], st["distance_to_star"], sy["name"], st["name"], st["type"], bool(sy["needs_permit"]), bool(st["has_refuel"]), st["max_landing_pad_size"])  
    return None


  def run(self):

    start = self.get_station_from_string(self.args.start)
    end = self.get_station_from_string(self.args.end)

    if start == None:
      self.log(0, "Error: start station {0} could not be found. Stopping.".format(self.args.start))
      return
    if end == None:
      self.log(0, "Error: end station {0} could not be found. Stopping.".format(self.args.end))
      return

    stations = []
    for st in self.args.stations:
      sobj = self.get_station_from_string(st)
      if sobj != None:
        if sobj.distance != None:
          if self.args.pad_size == "L" and sobj.max_pad_size != "L":
            self.log(1, "Warning: station {0} ({1}) is not usable by the specified ship size. Discarding.".format(s["name"], s.system))
            continue
          else:
            self.log(2, "Adding station: {0} ({1}, {2}Ls)".format(sobj.name, sobj.system, sobj.distance))
            stations.append(sobj)
        else:
          self.log(1, "Warning: station {0} ({1}) is missing SC distance in EDDB. Discarding.".format(sobj.name, sobj.system))
      else:
        self.log(1, "Warning: station {0} could not be found. Discarding.".format(st))

    s = Solver(self.args)

    # Add 2 to the jump count for start + end
    route = s.solve(stations, start, end, self.args.num_jumps + 2)

    totaldist = 0.0
    totaljumps = 0
    totalsc = 0

    print ""
    print route[0].to_string()
    for i in xrange(1, len(route)):
      jumpdist = (route[i-1].position - route[i].position).length
      totaldist += jumpdist
      jumpcount = s.jump_count(route[i-1], route[i], route[0:i-1])
      totaljumps += jumpcount
      totalsc += route[i].distance
      print "    --- {0: >6.2f}Ly ({1:d} jump{2:1s}) ---> {3}".format(jumpdist, jumpcount, ("s" if jumpcount != 1 else ""), route[i].to_string())

    print ""
    print "Total distance: {0:.2f}Ly; total jumps: {1:d}; total SC distance: {2:d}Ls".format(totaldist, totaljumps, totalsc)
    print ""



if __name__ == '__main__':
  a = Application()
  a.run()


