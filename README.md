![musco-logo](./logo.svg)

![Python application](https://github.com/g-raffy/pymusco/workflows/Python%20application/badge.svg)

# pymusco

a python library to ease creation of digitised orchestral musical scores  

A stub is a pdf file which contains a single sheet music for each instrument, but unlike the scan, also contains a table of contents.

## examples

### build a stub from a scan

The following command builds `$PYMUSCO_WORKSPACE_ROOT/stubs/007-captain-future-galaxy-drift-1.pdf` from `$PYMUSCO_WORKSPACE_ROOT/scans/007-captain-future-galaxy-drift-1.pdf` and `$PYMUSCO_WORKSPACE_ROOT/scans/007-captain-future-galaxy-drift-1.desc`:
```
PYTHONPATH=./src ./src/pymusco.py build-stub --scan-desc-file-path ./samples/scans/007-captain-future-galaxy-drift-1.desc
```
