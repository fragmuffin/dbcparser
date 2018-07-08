import os
import inspect

_this_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# Sample DBC File
sample_filenme = 'sample.dbc'
sample_path = os.path.join(_this_path, sample_filenme)
