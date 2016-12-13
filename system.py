import env
import pgnames
from system_internal import System, KnownSystem, PGSystem, PGSystemPrototype, _calculate_from_id64


def from_id64(id, allow_ha = True):
  coords, cube_width, n2 = _calculate_from_id64(id)
  # Get a system prototype to steal its name
  sys_proto = pgnames.get_system(coords, cube_width, allow_ha)
  name = sys_proto.name + str(n2)
  x, y, z = sys_proto.position
  return PGSystem(x, y, z, name, sector=sys_proto.sector, uncertainty=cube_width/2.0)


def from_name(name, allow_ha = True):
  with env.use() as data:
    known_sys = data.get_system(name)
    if known_sys is not None:
      return known_sys
  return pgnames.get_system(name, allow_ha=allow_ha)
