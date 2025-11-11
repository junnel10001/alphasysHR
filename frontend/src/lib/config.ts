/**
 * Centralized API configuration
 * This file contains all API-related configuration settings
 */

// API base URL configuration
export const API_CONFIG = {
  // Base URL for API calls
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
  // Request timeout in milliseconds
  timeout: 10000,
  
  // Default headers for all requests
  headers: {
    'Content-Type': 'application/json',
  },
  
  // API version
  version: 'v1',
}

// API endpoints configuration
export const API_ENDPOINTS = {
  // Authentication
  auth: {
    login: '/token',
    register: '/register',
    currentUser: '/users/me',
    permissions: '/me/permissions'
  },
  
  // Employees
  employees: {
    list: '/employees/',
    detail: (id: number) => `/employees/${id}`,
    create: '/employees/',
    update: (id: number) => `/employees/${id}`,
    delete: (id: number) => `/employees/${id}`
  },
  
  // Attendance
  attendance: {
    list: '/attendance/',
    detail: (id: number) => `/attendance/${id}`,
    create: '/attendance/',
    update: (id: number) => `/attendance/${id}`,
    delete: (id: number) => `/attendance/${id}`
  },
  
  // Leave
  leave: {
    list: '/leaves/',
    detail: (id: number) => `/leaves/${id}`,
    create: '/leaves/',
    update: (id: number) => `/leaves/${id}`,
    delete: (id: number) => `/leaves/${id}`,
    approve: (id: number) => `/dashboard/leaves/${id}/approve`,
    reject: (id: number) => `/dashboard/leaves/${id}/reject`
  },
  
  // Payroll
  payroll: {
    list: '/payroll/',
    detail: (id: number) => `/payroll/${id}`,
    create: '/payroll/',
    update: (id: number) => `/payroll/${id}`,
    delete: (id: number) => `/payroll/${id}`,
    generatePayslip: (id: number) => `/payroll/${id}/generate-payslip`,
    payslips: '/payslips/',
    downloadPayslip: (id: number) => `/payslips/${id}/download`
  },
  
  // Overtime
  overtime: {
    list: '/overtime/',
    detail: (id: number) => `/overtime/${id}`,
    create: '/overtime/',
    update: (id: number) => `/overtime/${id}`,
    delete: (id: number) => `/overtime/${id}`,
    approve: (id: number) => `/dashboard/overtime/${id}/approve`,
    reject: (id: number) => `/dashboard/overtime/${id}/reject`
  },
  
  // Dashboard
  dashboard: {
    kpi: '/dashboard/kpi',
    employeesPresent: '/dashboard/kpi/employees-present',
    lateAbsent: '/dashboard/kpi/late-absent',
    pendingLeave: '/dashboard/kpi/pending-leave',
    pendingOvertime: '/dashboard/kpi/pending-overtime',
    attendanceOverview: '/dashboard/kpi/attendance-overview',
    todayAttendance: '/dashboard/kpi/today-attendance',
    payrollSummary: '/dashboard/kpi/payroll-summary',
    leaveStats: '/dashboard/kpi/leave-stats',
    overtimeStats: '/dashboard/kpi/overtime-stats'
  },
  
  // Export
  export: {
    data: (type: string) => `/export/${type}`,
    history: '/export/history'
  }
}

// File upload configuration
export const UPLOAD_CONFIG = {
  maxSize: 10 * 1024 * 1024, // 10MB
  allowedTypes: [
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'text/csv'
  ]
}

// API response helpers
export const API_RESPONSES = {
  success: (data: any, message = 'Success') => ({
    success: true,
    message,
    data
  }),
  
  error: (message: string, details?: any) => ({
    success: false,
    message,
    ...(details && { details })
  }),
  
  paginated: (data: any, page: number, limit: number, total: number) => ({
    success: true,
    data,
    pagination: {
      page,
      limit,
      total,
      pages: Math.ceil(total / limit)
    }
  })
}