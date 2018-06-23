# =========================== Package Information ===========================
# Version Planning:
#   0.1.x               - Development Status :: 2 - Pre-Alpha
#   0.2.x               - Development Status :: 3 - Alpha
#   0.3.x               - Development Status :: 4 - Beta
#   1.x                 - Development Status :: 5 - Production/Stable
#   <any above>.y       - developments on that version (pre-release)
#   <any above>*.dev*   - development release (intended purely to test deployment)
__version__ = '0.2.0'

__title__ = 'dbcparser'
__description__ = 'Controller Area Network (CAN) DBC file parser'
__url__ = 'https://github.com/fragmuffin/dbcparser'

__author__ = 'Peter Boin'
__email__ = 'peter.boin+dbcparser@gmail.com'

__license__ = 'MIT'

__keywords__ = ['can', 'network', 'dbc']

# Copyright
import datetime
_now = datetime.date.today()
__copyright__ = "Copyright {year} {author}".format(year=_now.year, author=__author__)
