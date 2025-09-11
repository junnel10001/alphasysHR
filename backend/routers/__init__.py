"""
Router module initialization
"""

# Import all routers
from . import activity
from . import attendance
from . import dashboard
from . import employee_dashboard
from . import employees
from . import export
from . import leave
from . import overtime
from . import payroll
from . import permissions
from . import roles

# Make all routers available
__all__ = [
    'activity',
    'attendance',
    'dashboard',
    'employee_dashboard',
    'employees',
    'export',
    'leave',
    'overtime',
    'payroll',
    'permissions',
    'roles'
]