# Separation Explorer

A repository which contains the code to generate and to 
display the NIST ISODB separation explorer.

## Data generation

All data processing performed can be found in the Jupyter notebooks
located in the `./notebooks/` folder.

## Dashboard

The dashboard is running on a Heroku dyno at
<https://separation-explorer.herokuapp.com/app>.
Performance of this version is limited to the infrastructure
provided by Heroku.

It is entirely possible to run a local version of the explorer
by first installing all the Python requirements in `requirements.txt`
and then starting a local Bokeh server with:

```
bokeh serve . --show
```