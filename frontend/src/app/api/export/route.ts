import { NextRequest, NextResponse } from 'next/server'

// Mock export data for demonstration
const mockExportRecords = [
  {
    export_id: 1,
    export_type: 'Employee List',
    format: 'Excel',
    record_count: 45,
    generated_by: 'Admin User',
    generated_date: '2024-01-15',
    status: 'Completed',
    file_url: '/exports/employees_2024-01-15.xlsx',
    file_size: '245 KB'
  },
  {
    export_id: 2,
    export_type: 'Attendance Report',
    format: 'PDF',
    record_count: 120,
    generated_by: 'Jane Smith',
    generated_date: '2024-01-14',
    status: 'Completed',
    file_url: '/exports/attendance_2024-01-14.pdf',
    file_size: '1.2 MB'
  },
  {
    export_id: 3,
    export_type: 'Payroll Summary',
    format: 'CSV',
    record_count: 30,
    generated_by: 'Admin User',
    generated_date: '2024-01-13',
    status: 'Processing'
  }
]

const mockExportHistory = [
  {
    export_id: 1,
    type: 'Employee List',
    format: 'Excel',
    records: 45,
    generated_by: 'Admin User',
    generated_date: '2024-01-15',
    status: 'Completed',
    file_size: '245 KB'
  },
  {
    export_id: 2,
    type: 'Attendance Report',
    format: 'PDF',
    records: 120,
    generated_by: 'Jane Smith',
    generated_date: '2024-01-14',
    status: 'Completed',
    file_size: '1.2 MB'
  },
  {
    export_id: 3,
    type: 'Leave Report',
    format: 'Excel',
    records: 15,
    generated_by: 'Bob Johnson',
    generated_date: '2024-01-12',
    status: 'Failed'
  }
]

const mockDepartments = [
  { department_id: 1, department_name: 'Human Resources' },
  { department_id: 2, department_name: 'IT Department' },
  { department_id: 3, department_name: 'Finance' },
  { department_id: 4, department_name: 'Operations' },
  { department_id: 5, department_name: 'Marketing' }
]

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const endpoint = searchParams.get('endpoint')

    if (endpoint === 'stats') {
      // Return export statistics
      return NextResponse.json({
        total_exports: mockExportRecords.length,
        successful_exports: mockExportRecords.filter(r => r.status === 'Completed').length,
        failed_exports: mockExportRecords.filter(r => r.status === 'Failed').length,
        available_formats: ['csv', 'excel', 'pdf', 'json', 'zip'],
        available_data_types: ['employees', 'payroll', 'overtime', 'activities', 'all']
      })
    }

    // Return export records
    return NextResponse.json(mockExportRecords)
  } catch (error) {
    console.error('Error fetching export data:', error)
    return NextResponse.json(
      { error: 'Failed to fetch export data' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { data_type, format_type, start_date, end_date, department_id, user_id } = body

    // Simulate export processing
    await new Promise(resolve => setTimeout(resolve, 2000))

    // Generate mock file information
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const fileExtension = format_type === 'excel' ? 'xlsx' : format_type
    const fileName = `${data_type}_export_${timestamp}.${fileExtension}`
    const fileSize = Math.floor(Math.random() * 1000) + 100 // Random size between 100-1100 KB

    // Create a new export record
    const newExport = {
      export_id: mockExportRecords.length + 1,
      export_type: data_type.charAt(0).toUpperCase() + data_type.slice(1).replace('_', ' '),
      format: format_type.charAt(0).toUpperCase() + format_type.slice(1),
      record_count: Math.floor(Math.random() * 200) + 10, // Random record count
      generated_by: 'Current User',
      generated_date: new Date().toISOString(),
      status: 'Completed',
      file_url: `/exports/${fileName}`,
      file_size: `${fileSize} KB`
    }

    // Add to mock records
    mockExportRecords.unshift(newExport)
    mockExportHistory.unshift({
      export_id: newExport.export_id,
      type: newExport.export_type,
      format: newExport.format,
      records: newExport.record_count,
      generated_by: newExport.generated_by,
      generated_date: newExport.generated_date,
      status: newExport.status,
      file_size: newExport.file_size
    })

    return NextResponse.json({
      success: true,
      message: `Successfully exported ${data_type} data as ${format_type}`,
      file_name: fileName,
      file_path: `/exports/${fileName}`,
      file_size: fileSize
    })
  } catch (error) {
    console.error('Error generating export:', error)
    return NextResponse.json(
      {
        success: false,
        message: 'Export failed due to server error',
        error: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}