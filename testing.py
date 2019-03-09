from functools import partial
from random import random
from threading import Thread
import time

from bokeh.models import ColumnDataSource
from bokeh.plotting import curdoc, figure

from tornado import gen

# this must only be modified from a Bokeh session callback
source = ColumnDataSource(data=dict(x=[0], y=[0]))

# This is important! Save curdoc() to make sure all threads
# see the same document.
doc = curdoc()


@gen.coroutine
def update(x, y):
    source.stream(dict(x=[x], y=[y]))


def blocking_task():
    while True:
        # do some blocking computation
        time.sleep(0.1)
        x, y = random(), random()

        # but update the document from callback
        doc.add_next_tick_callback(partial(update, x=x, y=y))


p = figure(x_range=[0, 1], y_range=[0, 1])
l = p.circle(x='x', y='y', source=source)

doc.add_root(p)

thread = Thread(target=blocking_task)
thread.start()
