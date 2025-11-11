"""
Router module initialization
"""

# Import all routers
from . import attendance
from . import lookup
from . import dashboard
from . import employee_dashboard
from . import employees
from . import export
from . import leave
from . import overtime
from . import payroll
from . import permissions
from . import roles
from . import departments
from . import invitations

# Make all routers available
__all__ = [
    'attendance',
    'lookup',
    'dashboard',          # ensured inclusion
    'employee_dashboard',
    'employees',
    'export',
    'leave',
    'overtime',
    'payroll',
    'permissions',
    'roles',
    'departments',
    'invitations',
]