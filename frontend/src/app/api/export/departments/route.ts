import { NextResponse } from 'next/server'

// Mock departments data
const mockDepartments = [
  { department_id: 1, department_name: 'Human Resources' },
  { department_id: 2, department_name: 'IT Department' },
  { department_id: 3, department_name: 'Finance' },
  { department_id: 4, department_name: 'Operations' },
  { department_id: 5, department_name: 'Marketing' },
  { department_id: 6, department_name: 'Sales' },
  { department_id: 7, department_name: 'Customer Service' },
  { department_id: 8, department_name: 'Legal' },
  { department_id: 9, department_name: 'Research & Development' },
  { department_id: 10, department_name: 'Quality Assurance' }
]

export async function GET() {
  try {
    // In a real application, this would fetch from your database
    return NextResponse.json(mockDepartments)
  } catch (error) {
    console.error('Error fetching departments:', error)
    return NextResponse.json(
      { error: 'Failed to fetch departments' },
      { status: 500 }
    )
  }
}