# Employees Page – Technical Documentation

## Overview
`frontend/src/app/employees/page.tsx` implements the **Employees Management** UI for administrators.  
It displays a searchable, filterable table of employee records, summary statistic cards, and actions to add or edit employees.  
The component is currently using mock data; the next implementation step is to replace the mock with real data fetched from the backend API (`/employees` endpoint).

## Component Structure
- **React Hooks**
  - `useAuth` – provides the current authenticated user.
  - `useState` – manages `employees`, `isLoading`, and `searchTerm`.
  - `useEffect` – triggers `fetchEmployees` on mount.

- **Data Model**
  ```ts
  interface Employee {
    id: number;
    username: string;
    full_name: string;
    email: string;
    phone: string;
    department: string;
    role: 'admin' | 'manager' | 'employee';
    join_date: string; // ISO date string
    status: 'active' | 'inactive' | 'pending';
  }
  ```

- **UI Elements**
  - **Header** – page title, description, and “Add Employee” button.
  - **Search & Filter Card** – text input for live search; placeholder filter button.
  - **Statistic Cards** – total employees, active count, pending count, manager count.
  - **Employees Table** – columns: Employee (avatar + name), Contact (email & phone), Department, Role (badge), Join Date (formatted), Status (badge), Actions (ellipsis button).

- **Helper Functions**
  - `getStatusBadge(status)` – returns a colored `<Badge>` based on employee status.
  - `getRoleBadge(role)` – returns a colored `<Badge>` based on employee role.
  - `formatDate(dateString)` – formats ISO date to `MMM dd, yyyy` using `date-fns`.
  - `filteredEmployees` – derived list applying the current `searchTerm` to name, email, and department.

## Current Behaviour (Mock)
- `fetchEmployees` populates `employees` with a static array of five sample users.
- Loading spinner shown while `isLoading` is true.
- Search input filters the displayed rows in real‑time.

## Planned Enhancements
1. **API Integration**
   - Replace mock data with a call to `dashboardService.getEmployees()` (or a new endpoint in `backend/routers/employees.py`).
   - Update `fetchEmployees` to handle pagination, error handling, and loading state.
2. **Add Employee Modal**
   - Wire the “Add Employee” button to open a modal/form component.
3. **Row Actions**
   - Implement edit/delete functionality behind the ellipsis button.
4. **Filtering**
   - Expand the filter UI to allow department/role/status filters.
5. **Unit Tests**
   - Add React Testing Library tests for rendering, searching, and API error handling.

## Dependencies
- **UI Library** – Tailwind CSS, custom components from `@/components/ui/*`.
- **Icons** – `lucide-react`.
- **Date Formatting** – `date-fns`.
- **Auth Context** – `@/contexts/AuthContext`.
- **ProtectedRoute** – ensures only admins can access the page.

## File Location
`frontend/src/app/employees/page.tsx`

---

*Prepared by the Orchestrator – ready for implementation of real data fetching and UI enhancements.*