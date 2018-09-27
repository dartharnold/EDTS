## Calling EDTS library methods programmatically ##

Individual tools can be invoked programatically as well as via the command line.

First instantiate the `Application` class in the appropriate namespace.

```
#!text
from edtslib import edts
app = edts.Application(start = 'Sol', end = 'Alioth', jump_range = 30)
```

Refer to the source code for each tool to see which arguments are accepted.

Each application has a `run()` method which `yield`s `Result` objects.  `Result`s are treated as opaque types and their content may vary depending on the parameters passed to the `Application`.  For instance, if you provide a `jump_range` to `edts` the `Result`s will include origin and destination systems for each leg.  If you instead provide a `ship` object the `Result`s will additionally include fuel use estimates.

```
#!text
for leg in app.run():
  print('From {} to {} is {}'.format(
    leg.origin.system.name,
    leg.destination.system.name,
    leg.distance
  ))
```

## Calling the API.
`close_t`
```
#!text
curl -s -d '{"systems":[{"system":"Alioth", "max_dist": 10}]}' http://localhost:8080/api/v3/close_to
```

`coords`
```
#!text
curl -s -d '{"systems":["Alioth"]}' http://localhost:8080/api/v3/coords
```

`direction`
```
#!text
curl -s -d '{"reference":"Alioth", "systems":["Achenar", "Wyrd"]}' http://localhost:8080/api/v3/direction
```

`distance`
```
#!text
curl -s -d '{"systems":["Alioth", "Achenar", "Sol"]}' http://localhost:8080/api/v3/distance
```

`edts`
```
#!text
curl -s -d '{"start":"Sol/Galileo", "end":"Alioth/Golden Gate", "stations":["Wolf 359/Powell High", "Agartha/Enoch Port", "Alpha Centauri"], "ship": {"fsd":"2A", "mass": 21.8, "tank": 2}, "route": true}' http://localhost:8080/api/v3/edts
```

`find`
```
#!text
curl -s -d '{"pattern": "Jameson Memorial"}' http://localhost:8080/api/v3/galmath
```

`fuel_usage`
```
#!text
curl -s -d '{"systems":["Alioth", "Loucetios", "Eranin", "LP 98-132", "Aulin", "Altair", "Sol"], "ship":{"fsd": "6A", "mass": 521.8, "tank": 32}}' http://localhost:8080/api/v3/fuel_usage
```

`galmath`
```
#!text
curl -s -d '{"jump_range": 30, "core_distance": 1000}' http://localhost:8080/api/v3/galmath
```

`units`
```
#!text
curl -s -d '{"distance":0.22, "result": "Ls", "suffix":"Ly"}' http://localhost:8080/api/v3/units
```
