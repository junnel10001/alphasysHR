export interface AttendanceRecord {
  attendance_id: number;
  user_id: number;
  date: string;
  time_in: string | null;
  time_out: string | null;
  hours_worked: number | null;
  status: string;
}

export interface AttendanceFormData {
  user_id: number;
  date: string;
  time_in: string | null;
  time_out: string | null;
  status: string;
}

export interface AttendanceFilters {
  user_id?: number;
  date_from?: string;
  date_to?: string;
  status?: string;
}

export interface AttendanceStats {
  total_employees: number;
  present_today: number;
  late_today: number;
  absent_today: number;
  pending_approvals: number;
}

export interface AttendanceOverview {
  total_records: number;
  present_count: number;
  late_count: number;
  absent_count: number;
  on_leave_count: number;
}