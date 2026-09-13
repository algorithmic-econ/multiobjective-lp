# MUlti OBjective Linear Programming (MUOBLP)

This package contains core model used to define MUOB linear programs and some utility methods.

---

### Installation
See  [PyPi](https://pypi.org/project/muoblp/) project page for details

```shell
pip install muoblp
```

### Example
Example instance of PB election defined as multi objective linear program [source](./example/define_pb.py)

```shell
python example/define_pb.py
```

### Known limitations
`muoblp.utils.lp_reader_utils.read_lp_file` only parses the dialect written by
`MultiObjectiveLpProblem.write_lp` (pulp's `writeLP` plus OBJECTIVES/WEIGHTS
sections):

- coefficients and right-hand sides are coerced with `int()`
- terms are split on `"+"` only, so negative coefficients do not round-trip
- the section markers must appear on their own lines, in pulp's order
- variables are rebuilt as binary; bounds and expression constants are ignored

`write_lp` raises `ValueError` on a non-integer objective coefficient rather
than truncating it silently.
