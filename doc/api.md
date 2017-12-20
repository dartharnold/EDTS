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
