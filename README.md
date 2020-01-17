# Separation Explorer

A repository which contains the code to generate and to 
display the NIST ISODB separation explorer.

## Data creation

All data scraping, sorting and processing performed can be found
in the Jupyter notebooks located in the `./notebooks/` folder.

* `scrape-isotherms`: downloads the latest version of the NIST database
  and stores it in a single pickled file.
* `select-isotherms`: convert NIST isotherms to a pyGAPS format, followed
  by filtering and consolidation in an SQLite database. 
* `process-isotherms`: generation of KPI and isotherm files for the explorer.
* `compare-isotherms`: comparisons between the NIST adsorption database and 
  the MADIREL data.

Notebooks should be run with Python 3.6+

## Data

In the `./data/` folder the following are found:

* `iso.db` - the complete ISODB database in a SQLite format
* `iso-madirel.db` - the complete MADIREL database in a SQLite format
* `kpi.h5` - calculated KPI DataFrame, in a HDF5 format
* `iso-packed.bak, .dat, .dir` - simple shelve dictionary to store NIST isotherms

## Dashboard

The separation explorer dashboard is built on top of a [Bokeh](https://bokeh.pydata.org/)
server. The main code is found in `./src` while auxiliary html templates,
css and javascript can be found in the `./templates/` folder.

The dashboard is running on a Heroku dyno at <https://pauliacomi.com/separation-explorer>.
Performance of this version is limited to the infrastructure and bandwidth provided by Heroku.

It is entirely possible (and faster) to run a local version of the explorer
by first cloning this repository, installing all the Python requirements in
`requirements.txt` and then starting a local Bokeh server with:

```
bokeh serve . --show
```