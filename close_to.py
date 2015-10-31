import argparse
import env
import logging
from vector3 import Vector3

app_name = "close_to"

log = logging.getLogger(app_name)


class Application:

  def __init__(self, arg, hosted):
    ap_parents = [env.arg_parser] if not hosted else []
    ap = argparse.ArgumentParser(description = "Find Nearby Systems", fromfile_prefix_chars="@", parents = ap_parents, prog = app_name)
    ap.add_argument("-n", "--num", type=int, required=False, default=10, help="Show the specified number of nearby systems")
    ap.add_argument("-d", "--min-dist", type=int, required=False, help="Exclude systems less than this distance from reference")
    ap.add_argument("-m", "--max-dist", type=int, required=False, help="Exclude systems further this distance from reference")
    ap.add_argument("-a", "--allegiance", type=str, required=False, default=None, help="Only show systems with the specified allegiance")
    ap.add_argument("-s", "--stations", default=False, action='store_true', help="Only show systems with stations")
    ap.add_argument("-p", "--pad-size", default="M", type=str, help="Only show systems with stations matching the specified pad size")
    ap.add_argument("system", metavar="system", type=str, nargs=1, help="The system to find other systems near")
    self.args = ap.parse_args(arg)

    self.allow_outposts = (self.args.pad_size != "L")

  def run(self):
    if not self.args.system[0].lower() in env.eddb_systems_by_name:
      log.error("Could not find start system \"{0}\"!".format(self.args.system))
      return

    start = env.eddb_systems_by_name[self.args.system[0].lower()]
    asys = []
    
    startpos = Vector3(start["x"], start["y"], start["z"])
    maxdist = None

    for s in env.eddb_systems:
      # If we don't care about allegiance, or we do and it matches...
      if s != start and self.args.allegiance == None or (s["allegiance"] == self.args.allegiance):
        has_stns = (s["allegiance"] != None)
        # If we have stations, or we don't care...
        if has_stns or not self.args.stations:
          # If we *don't* have stations (because we don't care), or the stations match the requirements...
          if not has_stns or (s["id"] in env.eddb_stations_by_system and len([st for st in env.eddb_stations_by_system[s["id"]] if (self.allow_outposts or st["max_landing_pad_size"] == "L")])) > 0:
            dist = (Vector3(s["x"],s["y"],s["z"]) - startpos).length
            if not self.args.min_dist is None and dist < self.args.min_dist:
              continue
            if not self.args.max_dist is None and dist > self.args.max_dist:
              continue
            if len(asys) < self.args.num or dist < maxdist:
              # We have a new contender; add it, sort by distance, chop to length and set the new max distance
              asys.append(s)
              asys.sort(key=lambda t: (Vector3(t["x"],t["y"],t["z"]) - startpos).length)
              asys = asys[0:self.args.num]
              maxdist = (Vector3(asys[-1]["x"],asys[-1]["y"],asys[-1]["z"]) - startpos).length


    print ""
    print "Matching systems close to {0}:".format(self.args.system[0])
    print ""
    for i in xrange(0,len(asys)):
      print "  {0} ({1:.2f}Ly)".format(asys[i]["name"], (Vector3(asys[i]["x"],asys[i]["y"],asys[i]["z"]) - startpos).length)
    print ""

if __name__ == '__main__':
  a = Application(env.local_args, False)
  a.run()

