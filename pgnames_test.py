import logging
import pgdata
from pgnames import *

# Test modes
if __name__ == '__main__':
  if len(sys.argv) >= 2:
    if sys.argv[1] == "debug":
      c1_get_wtf_run(204800)
    
    elif sys.argv[1] == "c1ot":
      test_data = {
        'Mycapp': 623548, 'Lychoitl': 541608, 'Shruery': 410512, 'Phrauph': 574396,
        'Myreasp': 459657, 'Pythaics': 557994, 'Pythaipr': 803991, 'Styaill': 214060,
        'Styefs': 836644, 'Leeh': 99373, 'Keet': 99364, 'Schreang': 607155,
        'Sqeass': 263332, 'Squer': 639916, 'Cryaths': 246810, 'Phylur': 328741,
        'Slyeax': 443539, 'Mynoaw': 541610, 'Gyruenz': 459554, 'Sphuezz': 132132,
        'Spliech': 132135, 'Groec': 164896, 'Vigs': 148514, 'Tzorbs': 115616,
        'Phloiws': 115617, 'Tyrootz': 164768, 'Sigy': 148381, 'Soac': 148389,
        'Pyoer': 492698,
        # 'Isheau': 99239, 'Aowheou': 574476, 'Aochou': 492476,
        # 'Aaeyoe': 623543, 'Aaeshoa': 705543, 'Eaezi': 820396, 
        # Nasty ones
        'Chroabs': 492710, 'Kyloalz': 574382, 'Flyaulz': 574516, 'Froaphs': 492589,
        'Swoiphs': 312233, 'Cyoilz': 213923,
      }
      badcnt = 0
      for name in dict(test_data):
        actual = test_data[name]
        predicted = c1_get_offset(name)
        if actual != predicted:
          print("BAD [{0}]: predicted = {1}, actual = {2}, diff = {3}".format(name, predicted, actual, round(abs(predicted-actual)/pgdata.cx_prefix_total_run_length)))
          badcnt += 1
      print("Total: OK = {0}, bad = {1}".format(len(test_data)-badcnt, badcnt))
    
    elif sys.argv[1] == "pdiff":
      for x in range(2, len(sys.argv)-1):
        idx1 = pgdata.cx_prefixes.index(sys.argv[x])
        idx2 = pgdata.cx_prefixes.index(sys.argv[x+1])
        roll = False
        
        if idx2 < idx1:
          dif = (len(pgdata.cx_prefixes) - idx1) + idx2
          roll = True
        else:
          dif = idx2 - idx1
        
        cnt = 0
        for i in range(dif):
          idx = (idx1 + i) % len(pgdata.cx_prefixes)
          cnt += get_prefix_run_length(pgdata.cx_prefixes[idx])
        
        print("{0} --> {1}: {2} prefixes (rollover: {3}, predicted len: {4})".format(sys.argv[x], sys.argv[x+1], dif, roll, cnt))
      
    elif sys.argv[1] == "pdiff2":
      idx1 = pgdata.cx_prefixes.index(sys.argv[2])
      dif = int(sys.argv[3])
      inc = int(sys.argv[4]) if len(sys.argv) > 4 else 1
      
      cnt = 0
      for i in range(0, dif, inc):
        idx = (100 * len(pgdata.cx_prefixes) + idx1 + i) % len(pgdata.cx_prefixes)
        print("[{0}] {1}".format(cnt, pgdata.cx_prefixes[idx]))
        cnt += get_prefix_run_length(pgdata.cx_prefixes[idx])
      
      print("{0} prefixes (predicted len: {1})".format(dif, cnt))
      
    elif sys.argv[1] == "run1":
      input = sys.argv[2] # "Smooreau"
      frags = get_fragments(input)
      
      start_x = sector.base_coords.x - (39 * 1280)
      
      cur_idx = pgdata.cx_suffixes_s1.index(frags[-1])
      
      for i in range(0, int(sys.argv[3])):
        frags[-1] = pgdata.cx_suffixes_s1[cur_idx]
        print ("[{1}] {0}".format("".join(frags), start_x + (i * 1280)))
        if cur_idx + 1 == len(pgdata.cx_suffixes_s1):
          cur_idx = 0
          frags[0] = pgdata.cx_prefixes[pgdata.cx_prefixes.index(frags[0])+1]
        else:
          cur_idx += 1
        
      
    elif sys.argv[1] == "run2":
      input = sys.argv[2] # "Schuae Flye"
      limit = int(sys.argv[3]) if len(sys.argv) > 3 else None

      for idx, frags in c2_get_run(input, limit):
        x = sector.base_coords.x + (idx * sector.cube_size)
        print ("[{1}/{2}] {0}".format(format_name(frags), idx, x))
        
      
    elif sys.argv[1] == "fr1":
      limit = int(sys.argv[2]) if len(sys.argv) > 2 else 1248
      
      x = -sector.base_sector_coords[0]
      y = -8
      z = -sector.base_sector_coords[2]
      count = 0
      ok = 0
      bad = 0
      for (i, j, name) in c1_get_extended_run():
        print("[{0},{1},{2}] {3}".format(x, y, z, name))
        x += 1
        if x >= 89:
          y += 1
          if y >= 8:
            y = -8
            z += 1
        if count + 1 > limit:
          break
        count += 1
      # print("Count: {0}, OK: {1}, bad: {2}".format(count, ok, bad))
      
    elif sys.argv[1] == "fr2":
      limit = int(sys.argv[2]) if len(sys.argv) > 2 else 1248
      
      x = -sector.base_sector_coords[0]
      y = -8
      z = -sector.base_sector_coords[2]
      count = 0
      ok = 0
      bad = 0
      for ((f0, f1), (f2, f3)) in c2_get_start_points():
        extra = ""
        if y >= -3 and y <= 2:
          sect = c2_get_name(sector.PGSector(x,y,z))
          if sect == [f0, f1, f2, f3]:
            ok += 1
            # print("[{0},{1},{2}] {3}{4} {5}{6} (OK: {7})".format(x,y,z,f0,f1,f2,f3,format_name(sect)))
          elif sect is not None:
            bad += 1
            print("[{0},{1},{2}] {3}{4} {5}{6} (BAD: {7})".format(x,y,z,f0,f1,f2,f3,format_name(sect)))
          else:
            # print("[{0},{1},{2}] {3}{4} {5}{6}".format(x,y,z,f0,f1,f2,f3))
            pass
        else:
          # print("[{0},{1},{2}] {3}{4} {5}{6}".format(x,y,z,f0,f1,f2,f3))
          pass
        y += 1
        if y >= 8:
          y = -8
          z += 1
        if count + 1 > limit:
          break
        count += 1
      print("Count: {0}, OK: {1}, bad: {2}".format(count, ok, bad))
    

    elif sys.argv[1] == "search2":
      input = sys.argv[2]
      coords, relpos_confidence = get_coords_from_name(input)
      if coords is not None:
        print("Est. position of {0}: {1} (+/- {2}Ly)".format(input, coords, int(relpos_confidence)))
      else:
        sector = get_sector_from_name(input)
        if sector is not None:
          print("{0} is {1}, has origin {2}".format(input, str(sector), sector.origin))
        else:
          print("Could not find sector or system")

    elif sys.argv[1] == "eddbtest":
      import env
      env.set_verbosity(2)     
 
      ok1 = 0
      ok2 = 0
      okha = 0
      okhaname = 0
      bad1 = 0
      bad2 = 0
      badha = 0
      badhaname = 0
      none1 = 0
      none2 = 0
      noneha = 0
      notpg = 0
      
      get_sector_avg = 0.0
      get_sector_cnt = 0
      get_coords_avg = 0.0
      get_coords_cnt = 0

      for system in env.data.eddb_systems:
        m = pgdata.pg_system_regex.match(system.name)
        if m is not None and m.group("sector") not in ["Hypiae"]: # TODO: Remove when bad EDDB data is gone
          if m.group("sector") in pgdata.ha_sectors:
            sector = pgdata.ha_sectors[m.group("sector")]
            if sector.contains(system.position):
              rp, rpe = get_star_relpos(*m.group("prefix", "centre", "suffix", "mcode", "number1", "number2"))
              so = sector.get_origin(rpe * 2)
              limit = math.sqrt(rpe * rpe * 3)
              realdist = ((so + rp) - system.position).length
              if realdist <= limit:
                okha += 1
              else:
                badha += 1
                log.info("BadHA: {4}, {0} not within {1:.2f}Ly of {2}, actually {3:.2f}Ly".format((so + rp), limit, system.position, realdist, system.name))
            else:
              noneha += 1
              log.info("NoneHA: {0} @ {1} not in {2}".format(system.name, system.position, sector))
            ha_name = ha_get_name(system.position)
            if ha_name == m.group("sector"):
              okhaname += 1
            else:
              badhaname += 1
              if ha_name is not None:
                log.info("Bad HA name: {} ({}Ly) was predicted to be in {} ({}Ly)".format(system.name, sector.size, ha_name, pgdata.ha_sectors[ha_name].size))
              else:
                log.info("Bad HA name: {} ({}Ly) was predicted to not be in an HA sector)".format(system.name, sector.size))
          else:
            start = time.clock()
            sect = get_sector(m.group("sector"))
            tm = time.clock() - start
            cls = get_sector_class(m.group("sector"))
            if sect is not None and cls is not None:
              get_sector_avg = (get_sector_avg*get_sector_cnt + tm) / (get_sector_cnt + 1)
              get_sector_cnt += 1
              pos_sect = get_sector(system.position, allow_ha=False)
              if sect == pos_sect:
                start = time.clock()
                coords, dist = get_coords_from_name(system.name)
                tm = time.clock() - start
                if coords is None or dist is None:
                  log.warning("Could not parse system name {0}".format(system.name))
                  if cls == 2:
                    bad2 += 1
                  elif cls == 1:
                    bad1 += 1
                  continue
                get_coords_avg = (get_coords_avg*get_coords_cnt + tm) / (get_coords_cnt + 1)
                get_coords_cnt += 1
                realdist = (coords - system.position).length
                limit = math.sqrt(dist*dist*3)
                if realdist <= limit:
                  if cls == 2:
                    ok2 += 1
                  elif cls == 1:
                    ok1 += 1
                else:
                  if cls == 2:
                    bad2 += 1
                  elif cls == 1:
                    bad1 += 1
                  log.info("Bad position: {4}, {0} not within {1:.2f}Ly of {2}, actually {3:.2f}Ly".format(coords, limit, system.position, realdist, system.name))
              else:
                if cls == 2:
                  bad2 += 1
                elif cls == 1:
                  bad1 += 1
                log.info("Bad sector: {0} @ {1} is not in {2}".format(system.name, system.position, sect))
            else:
              if cls == 2:
                none2 += 1
                log.info("None2: {0} @ {1}".format(system.name, system.position))
              elif cls == 1:
                none1 += 1
                log.info("None1: {0} @ {1}".format(system.name, system.position))
              else:
                log.info("InvalidName: {0} @ {1}".format(system.name, system.position))
        else:
          notpg += 1

      log.info("Totals: OK1 = {}, OK2 = {}, OKHA = {}, OKHAName = {}, Bad1 = {}, Bad2 = {}, BadHA = {}, BadHAName = {}, None1 = {}, None2 = {}, NoneHA = {}, notPG = {}".format(ok1, ok2, okha, okhaname, bad1, bad2, badha, badhaname, none1, none2, noneha, notpg))
      log.info("Time: get_sector = {0:.6f}s, get_coords = {1:.6f}s".format(get_sector_avg, get_coords_avg))

    elif sys.argv[1] == "eddbspaff":
      import env
      
      with open("edsm_data.txt") as f:
        edsm_sectors = [s.strip() for s in f.readlines() if len(s) > 1]

      y_levels = {}
      
      for system in env.data.eddb_systems:
        m = pgdata.pg_system_regex.match(system.name)
        if m is not None and m.group("sector") in edsm_sectors:
          sname = m.group("sector")
          cls = get_sector_class(m.group("sector"))
          if cls != "2":
            sect = get_sector(system.position, allow_ha=False)
            if sect.y not in y_levels:
              y_levels[sect.y] = {}
            if sect.z not in y_levels[sect.y]:
              y_levels[sect.y][sect.z] = {}
            if sect.x not in y_levels[sect.y][sect.z]:
              y_levels[sect.y][sect.z][sect.x] = {}
            if sname not in y_levels[sect.y][sect.z][sect.x]:
              y_levels[sect.y][sect.z][sect.x][sname] = 0
            y_levels[sect.y][sect.z][sect.x][sname] += 1

      xcount = pgdata.c2_galaxy_size[0]
      zcount = pgdata.c2_galaxy_size[2]
      for y in y_levels:
        with open("sectors_{0}.csv".format(y), 'w') as f:
          for z in range(zcount - sector.base_sector_coords[2], -sector.base_sector_coords[2], -1):
            zvalues = ["" for _ in range(xcount)]
            if z in y_levels[y]:
              for x in range(-sector.base_sector_coords[0], xcount - sector.base_sector_coords[0], 1):
                if x in y_levels[y][z]:
                  zvalues[x + sector.base_sector_coords[0]] = max(y_levels[y][z][x], key=lambda t: y_levels[y][z][x][t])
            f.write(",".join(zvalues) + "\n")
    else:
      print("Unknown test {0}".format(sys.argv[1]))
  else:
    print("Usage: {0} <test-name> [<test-args>]".format(sys.argv[0]))
