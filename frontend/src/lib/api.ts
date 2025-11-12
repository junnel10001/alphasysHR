import axios from 'axios'
import { API_CONFIG } from './config'

// Create axios instance with default config
const api = axios.create({
  baseURL: API_CONFIG.baseURL,
  timeout: API_CONFIG.timeout,
  headers: API_CONFIG.headers,
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token')
      // Only redirect if not already on login page to avoid infinite loops
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    } else if (error.response?.status === 403) {
      // Permission denied - show appropriate error
      console.error('Access denied: Insufficient permissions')
      // You could redirect to an unauthorized page here
      // window.location.href = '/unauthorized'
    }
    return Promise.reject(error)
  }
)

// API service methods
export const authService = {
  async login(username: string, password: string) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    try {
      const response = await api.post('/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
      return response.data
    } catch (error: any) {
      if (error.response?.status === 401) {
        throw new Error('Invalid username or password')
      } else if (error.response?.status === 403) {
        throw new Error('Access denied: Insufficient permissions')
      } else {
        throw new Error('Login failed. Please try again.')
      }
    }
  },

  async getCurrentUser() {
    try {
      const response = await api.get('/users/me')
      return response.data
    } catch (error: any) {
      if (error.response?.status === 401) {
        throw new Error('Session expired. Please login again.')
      } else if (error.response?.status === 403) {
        throw new Error('Access denied: Insufficient permissions')
      } else {
        throw new Error('Failed to get user information')
      }
    }
  },

  async getPermissions() {
    try {
      const response = await api.get('/me/permissions')
      return response.data
    } catch (error: any) {
      if (error.response?.status === 401) {
        throw new Error('Session expired. Please login again.')
      } else if (error.response?.status === 403) {
        throw new Error('Access denied: Insufficient permissions')
      } else {
        throw new Error('Failed to get permissions')
      }
    }
  },
}

export const employeeService = {
  async getEmployees(params?: any) {
    const response = await api.get('/employees/', { params })
    return response.data
  },

  async getEmployee(id: number) {
    const response = await api.get(`/employees/${id}`)
    return response.data
  },

  async getEmployeeByUserId(id: number) {
    const response = await api.get(`/employees/by-user/${id}`)
    return response.data
  },

  async createEmployee(data: any) {
    const response = await api.post('/employees/', data)
    return response.data
  },

  async updateEmployee(id: number, data: any) {
    const response = await api.put(`/employees/${id}`, data)
    return response.data
  },

  async deleteEmployee(id: number) {
    const response = await api.delete(`/employees/${id}`)
    return response.data
  },
}

export const departmentService = {
  async getDepartments(params?: any) {
    const response = await api.get('/lookup/departments', { params })
    return response.data
  },

  async getDepartment(id: number) {
    const response = await api.get(`/departments/${id}`)
    return response.data
  },

  async createDepartment(data: any) {
    const response = await api.post('/departments/', data)
    return response.data
  },

  async updateDepartment(id: number, data: any) {
    const response = await api.put(`/departments/${id}`, data)
    return response.data
  },

  async deleteDepartment(id: number) {
    const response = await api.delete(`/departments/${id}`)
    return response.data
  },

  async getOffices(params?: any) {
    const response = await api.get('/lookup/offices', { params })
    return response.data
  },

  async createOffice(data: any) {
    const response = await api.post('/offices/', data)
    return response.data
  },

  async updateOffice(id: number, data: any) {
    const response = await api.put(`/offices/${id}`, data)
    return response.data
  },

  async deleteOffice(id: number) {
    const response = await api.delete(`/offices/${id}`)
    return response.data
  },
}

export const roleService = {
  async getRoles(params?: any) {
    const response = await api.get('/roles/', { params })
    return response.data
  },

  async getRole(id: number) {
    const response = await api.get(`/roles/${id}`)
    return response.data
  },

  async createRole(data: any) {
    const response = await api.post('/roles/', data)
    return response.data
  },

  async updateRole(id: number, data: any) {
    const response = await api.put(`/roles/${id}`, data)
    return response.data
  },

  async deleteRole(id: number) {
    const response = await api.delete(`/roles/${id}`)
    return response.data
  },

  async assignPermissionsToRole(roleId: number, permissionIds: number[]) {
    const response = await api.post(`/roles/${roleId}/permissions`, { permission_ids: permissionIds })
    return response.data
  },

  async getRolePermissions(roleId: number) {
    const response = await api.get(`/roles/${roleId}/permissions`)
    return response.data
  }
}

export const permissionService = {
  async getPermissions(params?: any) {
    const response = await api.get('/permissions/', { params })
    return response.data
  }
}

export const attendanceService = {
  async getAttendance(params?: any) {
    const response = await api.get('/attendance/', { params })
    return response.data
  },

  async getAttendanceById(id: number) {
    const response = await api.get(`/attendance/${id}`)
    return response.data
  },

  async createAttendance(data: any) {
    const response = await api.post('/attendance/', data)
    return response.data
  },

  async updateAttendance(id: number, data: any) {
    const response = await api.put(`/attendance/${id}`, data)
    return response.data
  },

  async deleteAttendance(id: number) {
    const response = await api.delete(`/attendance/${id}`)
    return response.data
  },
}

export const leaveService = {
  async getLeaves(params?: any) {
    const response = await api.get('/leaves/', { params })
    return response.data
  },

  async getLeaveById(id: number) {
    const response = await api.get(`/leaves/${id}`)
    return response.data
  },

  async createLeave(data: any) {
    const response = await api.post('/leaves/', data)
    return response.data
  },

  async updateLeave(id: number, data: any) {
    const response = await api.put(`/leaves/${id}`, data)
    return response.data
  },

  async deleteLeave(id: number) {
    const response = await api.delete(`/leaves/${id}`)
    return response.data
  },

  async approveLeave(id: number) {
    const response = await api.post(`/dashboard/leaves/${id}/approve`)
    return response.data
  },

  async rejectLeave(id: number) {
    const response = await api.post(`/dashboard/leaves/${id}/reject`)
    return response.data
  },
}

export const payrollService = {
  async getPayrolls(params?: any) {
    const response = await api.get('/payroll/', { params })
    return response.data
  },

  async getPayrollById(id: number) {
    const response = await api.get(`/payroll/${id}`)
    return response.data
  },

  async createPayroll(data: any) {
    const response = await api.post('/payroll/', data)
    return response.data
  },

  async updatePayroll(id: number, data: any) {
    const response = await api.put(`/payroll/${id}`, data)
    return response.data
  },

  async deletePayroll(id: number) {
    const response = await api.delete(`/payroll/${id}`)
    return response.data
  },

  async generatePayslip(id: number) {
    const response = await api.post(`/payroll/${id}/generate-payslip`)
    return response.data
  },

  async getPayslips(params?: any) {
    const response = await api.get('/payslips/', { params })
    return response.data
  },

  async downloadPayslip(id: number) {
    const response = await api.get(`/payslips/${id}/download`, {
      responseType: 'blob'
    })
    return response.data
  },
}

export const overtimeService = {
  async getOvertimeRequests(params?: any) {
    const response = await api.get('/overtime/', { params })
    return response.data
  },

  async getOvertimeById(id: number) {
    const response = await api.get(`/overtime/${id}`)
    return response.data
  },

  async createOvertime(data: any) {
    const response = await api.post('/overtime/', data)
    return response.data
  },

  async updateOvertime(id: number, data: any) {
    const response = await api.put(`/overtime/${id}`, data)
    return response.data
  },

  async deleteOvertime(id: number) {
    const response = await api.delete(`/overtime/${id}`)
    return response.data
  },

  async approveOvertime(id: number) {
    const response = await api.post(`/dashboard/overtime/${id}/approve`)
    return response.data
  },

  async rejectOvertime(id: number) {
    const response = await api.post(`/dashboard/overtime/${id}/reject`)
    return response.data
  },
}

export const getCurrentUser = async () => {
  const response = await api.get('/users/me')
  return response.data
}

export const getPermissions = async () => {
  const response = await api.get('/me/permissions')
  return response.data
}
export const dashboardService = {
  async getKPIs() {
    const response = await api.get('/dashboard/kpi')
    return response.data
  },

  async getEmployeesPresent() {
    const response = await api.get('/dashboard/kpi/employees-present')
    return response.data
  },

  async getLateAbsent() {
    const response = await api.get('/dashboard/kpi/late-absent')
    return response.data
  },

  async getPendingLeave() {
    const response = await api.get('/dashboard/kpi/pending-leave')
    return response.data
  },

  async getPendingOvertime() {
    const response = await api.get('/dashboard/kpi/pending-overtime')
    return response.data
  },

  async getAttendanceOverview() {
    const response = await api.get('/dashboard/kpi/attendance-overview')
    return response.data
  },

  async getTodayAttendance() {
    const response = await api.get('/dashboard/kpi/today-attendance')
    return response.data
  },

  async getPayrollSummary() {
    const response = await api.get('/dashboard/kpi/payroll-summary')
    return response.data
  },

  async getLeaveStats() {
    const response = await api.get('/dashboard/kpi/leave-stats')
    return response.data
  },

  async getOvertimeStats() {
    const response = await api.get('/dashboard/kpi/overtime-stats')
    return response.data
  },

  // New method for top‑leave statistics
  async getTopLeave() {
    const response = await api.get('/dashboard/kpi/top-leave')
    return response.data
  },

  // New methods for top‑employee statistics
  async getTopSickLeave() {
    const response = await api.get('/dashboard/kpi/top-sick-leave')
    return response.data
  },

  async getTopAbsent() {
    const response = await api.get('/dashboard/kpi/top-absent')
    return response.data
  },

  async getTopTardy() {
    const response = await api.get('/dashboard/kpi/top-tardy')
    return response.data
  },

}

export const exportService = {
  async exportData(type: string, format: string, params?: any) {
    const response = await api.get(`/export/${type}`, {
      params: { format, ...params },
      responseType: 'blob'
    })
    return response.data
  },

  async getExportHistory() {
    const response = await api.get('/export/history')
    return response.data
  },
}

// Invitation Service
export const invitationService = {
  async getInvitations(params?: any) {
    const response = await api.get('/invitations/', { params })
    return response.data
  },

  async getInvitation(id: number) {
    const response = await api.get(`/invitations/${id}`)
    return response.data
  },

  async createInvitation(data: any) {
    console.log('invitationService.createInvitation called with data:', data)
    const response = await api.post('/invitations/', data)
    console.log('invitationService.createInvitation response:', response)
    return response.data
  },

  async validateInvitationToken(token: string) {
    const response = await api.post('/invitations/validate', null, {
      params: { token }
    })
    return response.data
  },

  async acceptInvitation(data: any) {
    const response = await api.post('/invitations/accept', data)
    return response.data
  },

  async resendInvitation(data: any) {
    const response = await api.post('/invitations/resend', data)
    return response.data
  },

  async revokeInvitation(data: any) {
    const response = await api.post('/invitations/revoke', data)
    return response.data
  },

  async getInvitationStatistics() {
    const response = await api.get('/invitations/statistics')
    return response.data
  },

  async cleanupExpiredInvitations() {
    const response = await api.post('/invitations/cleanup-expired')
    return response.data
  },

  async getMyInvitations(params?: any) {
    const response = await api.get('/invitations/my-invitations', { params })
    return response.data
  },
}

export const leaveTypesService = {
  async getLeaveTypes(params?: any) {
    const response = await api.get('/leave-types/', { params })
    return response.data
  },

  async getLeaveType(id: number) {
    const response = await api.get(`/leave-types/${id}`)
    return response.data
  },

  async createLeaveType(data: any) {
    const response = await api.post('/leave-types/', data)
    return response.data
  },

  async updateLeaveType(id: number, data: any) {
    const response = await api.put(`/leave-types/${id}`, data)
    return response.data
  },

  async deleteLeaveType(id: number) {
    const response = await api.delete(`/leave-types/${id}`)
    return response.data
  },
}

export const positionsService = {
  async getPositions(params?: any) {
    const response = await api.get('/positions/', { params })
    return response.data
  },

  async getPosition(id: number) {
    const response = await api.get(`/positions/${id}`)
    return response.data
  },

  async createPosition(data: any) {
    const response = await api.post('/positions/', data)
    return response.data
  },

  async updatePosition(id: number, data: any) {
    const response = await api.put(`/positions/${id}`, data)
    return response.data
  },

  async deletePosition(id: number) {
    const response = await api.delete(`/positions/${id}`)
    return response.data
  },
}

export const employmentStatusesService = {
  async getEmploymentStatuses(params?: any) {
    const response = await api.get('/employment-statuses/', { params })
    return response.data
  },

  async getEmploymentStatus(id: number) {
    const response = await api.get(`/employment-statuses/${id}`)
    return response.data
  },

  async createEmploymentStatus(data: any) {
    const response = await api.post('/employment-statuses/', data)
    return response.data
  },

  async updateEmploymentStatus(id: number, data: any) {
    const response = await api.put(`/employment-statuses/${id}`, data)
    return response.data
  },

  async deleteEmploymentStatus(id: number) {
    const response = await api.delete(`/employment-statuses/${id}`)
    return response.data
  },
}

export const systemStatusService = {
  async getSystemInfo() {
    const response = await api.get('/system-status/info')
    return response.data
  },

  async getHealthCheck() {
    const response = await api.get('/system-status/health')
    return response.data
  },

  async getSystemMetrics() {
    const response = await api.get('/system-status/metrics')
    return response.data
  }
}

// User Management API
export const userManagementService = {
  async listUsers(params?: any) {
    const response = await api.get('/user-management/users', { params })
    return response.data
  },

  async getUserRoles(userId: number) {
    const response = await api.get(`/user-management/users/${userId}/roles`)
    return response.data
  },

  async assignUserRoles(assignment: { user_id: number; role_ids: number[] }) {
    const response = await api.post('/user-management/users/assign-roles', assignment)
    return response.data
  },

  async deactivateUser(data: { user_id: number; reason: string }) {
    const response = await api.post('/user-management/users/deactivate', data)
    return response.data
  },

  async activateUser(userId: number) {
    const response = await api.post(`/user-management/users/${userId}/activate`)
    return response.data
  },

  async getRolesSummary() {
    const response = await api.get('/user-management/roles/summary')
    return response.data
  }
}

export default api