'use client'
import { Toaster } from "react-hot-toast"

import React, { useEffect, useState } from "react"
import { toast } from "react-hot-toast"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { LayoutWrapper } from "@/components/layout"
import api from "@/lib/api"
import { employeeService } from "@/lib/api"

const employeeSchema = z.object({
  // Personal Information (required)
  company_id: z
    .string()
    .min(1, { message: "Please enter a Company ID" })
    .regex(/^[A-Za-z0-9-]+$/, { message: "Company ID can only contain letters, numbers, or dashes" }),
  first_name: z.string().min(1, { message: "Please enter the employee's first name" }),
  middle_name: z.string().optional(),
  last_name: z.string().min(1, { message: "Please enter the employee's last name" }),
  suffix: z.string().optional(),
  nickname: z.string().optional(),
  date_of_birth: z.string().optional(),
  place_of_birth: z.string().optional(),
  gender: z.enum(["Male", "Female", "Other"]).optional(),
  civil_status: z.enum(["Single", "Married", "Widowed", "Divorced"]).optional(),
  nationality: z.string().optional(),
  blood_type: z.string().optional(),
  religion: z.string().optional(),
  // Contact & Address (optional)
  mobile_number: z.string().optional(),
  landline_number: z.string().optional(),
  personal_email: z.string().email().optional(),
  current_address: z.string().optional(),
  permanent_address: z.string().optional(),
  emergency_contact_name: z.string().optional(),
  emergency_contact_number: z.string().optional(),
  emergency_contact_relationship: z.string().optional(),
  // Employment Details (required)
  job_title: z.string().min(1, { message: "Job title is required" }).max(100, { message: "Job title must be less than 100 characters" }),
  department_id: z.string().refine((val) => {
    // Allow "placeholder" during UI state, but require actual selection for submission
    if (val === "placeholder" || val === undefined || val === "") {
      return false;
    }
    return true;
  }, {
    message: "Please select a department.",
  }),
  role_id: z.string().refine((val) => {
    // Allow "placeholder" during UI state, but require actual selection for submission
    if (val === "placeholder" || val === undefined || val === "") {
      return false;
    }
    return true;
  }, {
    message: "Please select a role.",
  }),
  employment_status: z.string().refine((val) => {
    // Allow "placeholder" during UI state, but require actual selection for submission
    if (val === "placeholder" || val === undefined || val === "") {
      return false;
    }
    return true;
  }, {
    message: "Please select an employment status.",
  }),
  date_hired: z
    .string()
    .refine((val) => val !== "", {
      message: "Date Hired is required.",
    })
    .refine((val) => val === "" || new Date(val) <= new Date(), {
      message: "Date Hired must be today or in the past.",
    }),
  date_regularised: z.string().optional(),
  office_id: z.string().refine((val) => {
    // Allow "placeholder" during UI state, but require actual selection for submission
    if (val === "placeholder" || val === undefined || val === "") {
      return false;
    }
    return true;
  }, {
    message: "Please select an office.",
  }),
  line_manager_id: z.string().refine((val) => {
    // Allow "placeholder" during UI state, but require actual selection for submission
    if (val === "placeholder" || val === undefined || val === "") {
      return false;
    }
    return true;
  }, {
    message: "Please select a line manager.",
  }),
  // Compensation & Payroll (required)
  basic_salary: z
    .string()
    .refine((val) => val !== "", {
      message: "Basic salary is required.",
    })
    .refine((val) => {
      const num = parseFloat(val);
      return !isNaN(num) && num > 0;
    }, {
      message: "Basic salary must be greater than zero",
    }),
  bank_name: z.string().optional(),
  bank_account_number: z.string().optional(),
  // Documents (optional)
  resume_path: z.string().optional(),
  government_id_paths: z.array(z.string()).optional(),
  birth_certificate_path: z.string().optional(),
  marriage_certificate_path: z.string().optional(),
  diploma_path: z.string().optional(),
})

type EmployeeForm = z.infer<typeof employeeSchema>

export default function EmployeeWizard() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const {
    register,
    handleSubmit,
    reset,
    clearErrors,
    setError,
    trigger,
    setValue,
    watch,
    formState: { errors },
  } = useForm<EmployeeForm>({
    resolver: zodResolver(employeeSchema),
    mode: "onChange", // Keep onChange for real-time validation feedback
    defaultValues: {
      company_id: "",
      department_id: "placeholder",
      role_id: "placeholder",
      office_id: "placeholder",
      line_manager_id: "placeholder",
      employment_status: "placeholder",
      basic_salary: "0",
      date_hired: "",
      job_title: "",
    },
  })

  const onError = (formErrors: any) => {
    // Consolidate all error messages into a single toast, each on its own line
    const messages = Object.values(formErrors)
      .map((err: any) => err?.message)
      .filter(Boolean) as string[];
    if (messages.length > 0) {
      const combined = messages.join("\n");
      toast.error(combined, { position: "top-center" });
    }
  }

  const [departments, setDepartments] = useState<
    Array<{ department_id: number; department_name: string }>
  >([])
  const [roles, setRoles] = useState<
    Array<{ role_id: number; role_name: string }>
  >([])
  const [offices, setOffices] = useState<
    Array<{ office_id: number; office_name: string; location: string }>
  >([])
  const [lineManagers, setLineManagers] = useState<
    Array<{ user_id: number; first_name: string; last_name: string }>
  >([])

  useEffect(() => {
    api.get("/lookup/departments").then((res: any) => setDepartments(res.data))
    api.get("/lookup/roles").then((res: any) => setRoles(res.data))
    api.get("/lookup/offices").then((res: any) => setOffices(res.data))
    api.get("/lookup/line-managers").then((res: any) => setLineManagers(res.data))
  }, [])

  const onSubmit = async (data: any) => {
    setIsSubmitting(true)
    try {
      // Filter out placeholder values before submission
      const sanitizedData = {
        ...data,
        department_id: data.department_id === "placeholder" ? "" : data.department_id,
        role_id: data.role_id === "placeholder" ? "" : data.role_id,
        employment_status: data.employment_status === "placeholder" ? "" : data.employment_status,
        office_id: data.office_id === "placeholder" ? "" : data.office_id,
        line_manager_id: data.line_manager_id === "placeholder" ? "" : data.line_manager_id,
      };
      
      // Check if any required fields are still empty after sanitization
      const hasEmptyRequiredFields =
        !sanitizedData.department_id ||
        !sanitizedData.role_id ||
        !sanitizedData.employment_status ||
        !sanitizedData.office_id ||
        !sanitizedData.line_manager_id ||
        !sanitizedData.job_title ||
        !sanitizedData.date_hired ||
        !sanitizedData.basic_salary;
      
      if (hasEmptyRequiredFields) {
        // Clear all errors first to prevent duplicate error messages
        clearErrors()
        
        // Trigger validation errors manually for required fields
        if (!sanitizedData.department_id) {
          setError("department_id", { message: "Please select a department." });
        }
        if (!sanitizedData.role_id) {
          setError("role_id", { message: "Please select a role." });
        }
        if (!sanitizedData.employment_status) {
          setError("employment_status", { message: "Please select an employment status." });
        }
        if (!sanitizedData.office_id) {
          setError("office_id", { message: "Please select an office." });
        }
        if (!sanitizedData.line_manager_id) {
          setError("line_manager_id", { message: "Please select a line manager." });
        }
        if (!sanitizedData.job_title) {
          setError("job_title", { message: "Job title is required." });
        }
        if (!sanitizedData.date_hired) {
          setError("date_hired", { message: "Date Hired is required." });
        }
        if (!sanitizedData.basic_salary) {
          setError("basic_salary", { message: "Basic salary is required." });
        }
        setIsSubmitting(false)
        return;
      }
      
      // Convert data to match backend expectations
      console.log('Sanitized data before conversion:', sanitizedData); // Debug log
      
      const convertedEmploymentStatus = convertEmploymentStatus(sanitizedData.employment_status);
      console.log('Converted employment status:', convertedEmploymentStatus); // Debug log
      
      const convertedData = {
        ...sanitizedData,
        // Keep company_id as string (alphanumeric with dashes) - backend should handle this
        company_id: sanitizedData.company_id,
        // Convert other string IDs to integers
        department_id: parseInt(sanitizedData.department_id, 10),
        role_id: parseInt(sanitizedData.role_id, 10),
        office_id: parseInt(sanitizedData.office_id, 10),
        line_manager_id: parseInt(sanitizedData.line_manager_id, 10),
        // Convert employment_status numeric values to enum strings
        employment_status: convertedEmploymentStatus,
        // Convert basic_salary to number
        basic_salary: parseFloat(sanitizedData.basic_salary),
        // Handle date fields - convert empty strings to null
        date_of_birth: sanitizedData.date_of_birth === "" ? null : sanitizedData.date_of_birth,
        date_regularised: sanitizedData.date_regularised === "" ? null : sanitizedData.date_regularised,
        // Handle other optional string fields - convert empty strings to null
        place_of_birth: sanitizedData.place_of_birth || null,
        nationality: sanitizedData.nationality || null,
        blood_type: sanitizedData.blood_type || null,
        religion: sanitizedData.religion || null,
        mobile_number: sanitizedData.mobile_number || null,
        landline_number: sanitizedData.landline_number || null,
        personal_email: sanitizedData.personal_email || null,
        current_address: sanitizedData.current_address || null,
        permanent_address: sanitizedData.permanent_address || null,
        emergency_contact_name: sanitizedData.emergency_contact_name || null,
        emergency_contact_number: sanitizedData.emergency_contact_number || null,
        emergency_contact_relationship: sanitizedData.emergency_contact_relationship || null,
        bank_name: sanitizedData.bank_name || null,
        bank_account_number: sanitizedData.bank_account_number || null,
      };
      
      console.log('Final converted data:', convertedData); // Debug log
      
      await employeeService.createEmployee(convertedData)
      toast.success("Employee created successfully")
      reset()
    } catch (err) {
      console.error(err)
      toast.error("Failed to create employee. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  // Helper function to convert employment_status numeric values to enum strings
  const convertEmploymentStatus = (status: string): string => {
    console.log('Converting employment status:', status); // Debug log
    const statusMap: { [key: string]: string } = {
      "1": "Regular",
      "2": "Probationary",
      "3": "Contractual",
      "4": "Project-Based",
      "5": "Part-time"
    };
    return statusMap[status] || status; // Return converted value or original if not found
  }

  return (
    <LayoutWrapper>
        <h2 className="text-2xl font-bold mb-4">Create / Edit Employee</h2>
        <form onSubmit={handleSubmit(onSubmit, onError)} className="space-y-6 bg-white p-6 rounded-md">
          <Tabs defaultValue="personal">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="personal">Personal Info</TabsTrigger>
              <TabsTrigger value="contact">Contact & Address</TabsTrigger>
              <TabsTrigger value="employment">Employment Details</TabsTrigger>
              <TabsTrigger value="compensation">Compensation</TabsTrigger>
              <TabsTrigger value="documents">Documents</TabsTrigger>
            </TabsList>

            {/* Personal Information */}
            <TabsContent value="personal" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Company ID <span className="text-red-600">*</span></label>
                  <Input placeholder="Company ID" type="text" {...register("company_id")} />
                  {errors.company_id && <p className="text-sm text-red-600 mt-1">{errors.company_id.message}</p>}
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">First Name <span className="text-red-600">*</span></label>
                  <Input placeholder="First Name" {...register("first_name")} />
                  {errors.first_name && <p className="text-sm text-red-600 mt-1">{errors.first_name.message}</p>}
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Middle Name</label>
                  <Input placeholder="Middle Name" {...register("middle_name")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Last Name <span className="text-red-600">*</span></label>
                  <Input placeholder="Last Name" {...register("last_name")} />
                  {errors.last_name && <p className="text-sm text-red-600 mt-1">{errors.last_name.message}</p>}
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Suffix</label>
                  <Input placeholder="Suffix" {...register("suffix")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Nickname</label>
                  <Input placeholder="Nickname" {...register("nickname")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Date of Birth</label>
                  <Input placeholder="Date of Birth" type="date" {...register("date_of_birth")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Place of Birth</label>
                  <Input placeholder="Place of Birth" type="text" {...register("place_of_birth")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Gender</label>
                  <Select
                    value={watch("gender")}
                    onValueChange={(value) => setValue("gender", value as "Male" | "Female" | "Other")}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Gender" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Male">Male</SelectItem>
                      <SelectItem value="Female">Female</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.gender && <p className="text-sm text-red-600 mt-1">{errors.gender.message}</p>}
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Civil Status</label>
                  <Select
                    value={watch("civil_status")}
                    onValueChange={(value) => setValue("civil_status", value as "Single" | "Married" | "Widowed" | "Divorced")}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Civil Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Single">Single</SelectItem>
                      <SelectItem value="Married">Married</SelectItem>
                      <SelectItem value="Widowed">Widowed</SelectItem>
                      <SelectItem value="Divorced">Divorced</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.civil_status && <p className="text-sm text-red-600 mt-1">{errors.civil_status.message}</p>}
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Nationality</label>
                  <Input placeholder="Nationality" {...register("nationality")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Blood Type</label>
                  <Input placeholder="Blood Type" {...register("blood_type")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Religion</label>
                  <Input placeholder="Religion" {...register("religion")} />
                </div>
              </div>
            </TabsContent>

            {/* Contact & Address */}
            <TabsContent value="contact" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Mobile Number</label>
                  <Input placeholder="Mobile Number" {...register("mobile_number")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Landline Number</label>
                  <Input placeholder="Landline Number" {...register("landline_number")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Personal Email</label>
                  <Input placeholder="Personal Email" type="email" {...register("personal_email")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Current Address</label>
                  <Input placeholder="Current Address" {...register("current_address")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Permanent Address</label>
                  <Input placeholder="Permanent Address" {...register("permanent_address")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Emergency Contact Name</label>
                  <Input placeholder="Emergency Contact Name" {...register("emergency_contact_name")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Emergency Contact Number</label>
                  <Input placeholder="Emergency Contact Number" {...register("emergency_contact_number")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Relationship</label>
                  <Input placeholder="Relationship" {...register("emergency_contact_relationship")} />
                </div>
              </div>
            </TabsContent>

            {/* Employment Details */}
            <TabsContent value="employment" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Job Title <span className="text-red-600">*</span></label>
                  <Input placeholder="Job Title" {...register("job_title")} />
                  {errors.job_title && <p className="text-sm text-red-600 mt-1">{errors.job_title.message}</p>}
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Department <span className="text-red-600">*</span></label>
                  <Select
                    value={watch("department_id")}
                    onValueChange={(value) => {
                      setValue("department_id", value);
                      if (value !== "placeholder" && value !== "") {
                        clearErrors("department_id");
                      }
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select Department" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="placeholder">Select Department</SelectItem>
                      {departments.map((d) => (
                        <SelectItem key={d.department_id} value={d.department_id.toString()}>
                          {d.department_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.department_id && <p className="text-sm text-red-600 mt-1">{errors.department_id.message}</p>}
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Role <span className="text-red-600">*</span></label>
                  <Select
                    value={watch("role_id")}
                    onValueChange={(value) => {
                      setValue("role_id", value);
                      if (value !== "placeholder" && value !== "") {
                        clearErrors("role_id");
                      }
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select Role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="placeholder">Select Role</SelectItem>
                      {roles.map((r) => (
                        <SelectItem key={r.role_id} value={r.role_id.toString()}>
                          {r.role_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.role_id && <p className="text-sm text-red-600 mt-1">{errors.role_id.message}</p>}
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Employment Status <span className="text-red-600">*</span></label>
                  <Select
                    value={watch("employment_status")}
                    onValueChange={(value) => {
                      setValue("employment_status", value);
                      if (value !== "placeholder" && value !== "") {
                        clearErrors("employment_status");
                      }
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select Employment Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="placeholder">Select Employment Status</SelectItem>
                      <SelectItem value="1">Regular</SelectItem>
                      <SelectItem value="2">Probationary</SelectItem>
                      <SelectItem value="3">Contractual</SelectItem>
                      <SelectItem value="4">Project-Based</SelectItem>
                      <SelectItem value="5">Part-time</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.employment_status && <p className="text-sm text-red-600 mt-1">{errors.employment_status.message}</p>}
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Date Hired <span className="text-red-600">*</span></label>
                  <Input placeholder="Date Hired" type="date" {...register("date_hired")} />
                  {errors.date_hired && <p className="text-sm text-red-600 mt-1">{errors.date_hired.message}</p>}
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Date Regularised</label>
                  <Input placeholder="Date Regularised" type="date" {...register("date_regularised")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Office <span className="text-red-600">*</span></label>
                  <Select
                    value={watch("office_id")}
                    onValueChange={(value) => {
                      setValue("office_id", value);
                      if (value !== "placeholder" && value !== "") {
                        clearErrors("office_id");
                      }
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select Office" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="placeholder">Select Office</SelectItem>
                      {offices.map((o) => (
                        <SelectItem key={o.office_id} value={o.office_id.toString()}>
                          {o.office_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.office_id && <p className="text-sm text-red-600 mt-1">{errors.office_id.message}</p>}
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Line Manager <span className="text-red-600">*</span></label>
                  <Select
                    value={watch("line_manager_id")}
                    onValueChange={(value) => {
                      setValue("line_manager_id", value);
                      if (value !== "placeholder" && value !== "") {
                        clearErrors("line_manager_id");
                      }
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select Line Manager" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="placeholder">Select Line Manager</SelectItem>
                      {lineManagers.map((lm) => (
                        <SelectItem key={lm.user_id} value={lm.user_id.toString()}>
                          {lm.first_name} {lm.last_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.line_manager_id && <p className="text-sm text-red-600 mt-1">{errors.line_manager_id.message}</p>}
                </div>
              </div>
            </TabsContent>

            {/* Compensation & Payroll */}
            <TabsContent value="compensation" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Basic Salary <span className="text-red-600">*</span></label>
                  <Input placeholder="Basic Salary" type="number" step="0.01" {...register("basic_salary")} />
                  {errors.basic_salary && <p className="text-sm text-red-600 mt-1">{errors.basic_salary.message}</p>}
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Bank Name</label>
                  <Input placeholder="Bank Name" {...register("bank_name")} />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Bank Account Number</label>
                  <Input placeholder="Bank Account Number" {...register("bank_account_number")} />
                </div>
              </div>
            </TabsContent>

            {/* Documents & Records */}
            <TabsContent value="documents" className="space-y-4">
              <div className="grid grid-cols-1 gap-4">
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Resume</label>
                  <input type="file" {...register("resume_path")} className="w-full border rounded p-2" />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Government IDs (multiple files)</label>
                  <input type="file" multiple {...register("government_id_paths")} className="w-full border rounded p-2" />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Birth Certificate</label>
                  <input type="file" {...register("birth_certificate_path")} className="w-full border rounded p-2" />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Marriage Certificate</label>
                  <input type="file" {...register("marriage_certificate_path")} className="w-full border rounded p-2" />
                </div>
                <div className="space-y-1">
                  <label className="block text-sm font-medium">Diploma / Transcript</label>
                  <input type="file" {...register("diploma_path")} className="w-full border rounded p-2" />
                </div>
              </div>
            </TabsContent>
          </Tabs>

          <div className="flex justify-end">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save Employee"}
            </Button>
            <Toaster position="top-center" />
          </div>
        </form>
    </LayoutWrapper>
  )
}