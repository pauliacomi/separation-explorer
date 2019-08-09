# Separation Explorer

A repository which contains the code to generate and to 
display the NIST ISODB separation explorer.

## Data

In the `./data/` folder the following are found:

* `iso.db` - the complete ISODB database in a SQLite format
* `kpi.json` - the calculated KPI, in a JSON format
* `isotherms/` - selected isotherms for the separation explorer 

## Data generation

All data processing performed can be found in the Jupyter notebooks
located in the `./notebooks/` folder. It extracts the isotherms 
from the database, performs outlier detection and saves selected 
ones in the `./data/isotherms/` folder.

## Dashboard

The separation explorer dashboard is built on top of a Bokeh
server. The main code is found in `./src` while auxiliary html
and css templates can be found in the `./templates/` folder.

The dashboard is running on a Heroku dyno at
<https://separation-explorer.herokuapp.com/app>.
Performance of this version is limited to the infrastructure
and bandwith provided by Heroku.

It is entirely possible (and faster) to run a local version of the explorer
by first cloning this repository, installing all the Python requirements in
`requirements.txt` and then starting a local Bokeh server with:

```
bokeh serve . --show
```
