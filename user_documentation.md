# Employee Invitation System - User Documentation

## Table of Contents
1. [Overview](#overview)
2. [For Administrators/Managers](#for-administratorsmanagers)
   - [Inviting Employees](#inviting-employees)
   - [Managing Invitations](#managing-invitations)
   - [Invitation Status](#invitation-status)
3. [For Employees](#for-employees)
   - [Receiving an Invitation](#receiving-an-invitation)
   - [First-Time Login](#first-time-login)
   - [Security Best Practices](#security-best-practices)
4. [Troubleshooting](#troubleshooting)
5. [FAQ](#faq)

## Overview

The Employee Invitation System allows administrators and managers to invite existing employees to create user accounts in the AlphaHR system. This feature streamlines the process of granting system access while maintaining security and proper role-based permissions.

### Key Features
- Secure invitation system with unique tokens
- Role-based access control
- Email notifications with login credentials
- Invitation status tracking
- Resend and revoke functionality
- Password security requirements

---

## For Administrators/Managers

### Inviting Employees

#### Prerequisites
- You must have Admin, Manager, or HR role
- Employee must exist in the system without a user account
- Valid email address must be on file for the employee

#### Step-by-Step Guide

1. **Navigate to Employees Page**
   - Log into AlphaHR with your admin/manager account
   - Click on "Employees" in the navigation menu
   - You'll see a list of all employees in the system

2. **Identify Employees Without User Accounts**
   - Look for employees with "Can be Invited" status in the "User Status" column
   - Or use the filter to show only invitable employees

3. **Initiate Invitation**
   - Click the "Actions" menu (three dots) next to the employee you want to invite
   - Select "Invite as User" from the dropdown menu

4. **Fill Invitation Form**
   - **Username**: Create a unique username for the employee
     - Must be unique across all users
     - Recommended format: firstname.lastname or firstnamelastname
   - **Password**: Set an initial password
     - Minimum 8 characters
     - Should include uppercase, lowercase, numbers, and special characters
   - **Confirm Password**: Re-enter the password for verification
   - **Role**: Select the appropriate role for the employee
     - **Employee**: Standard employee access
     - **Manager**: Department management capabilities
     - **HR**: Human resources functions
   - **Send Email**: Keep checked to send automatic invitation email

5. **Send Invitation**
   - Review all entered information
   - Click "Send Invitation"
   - Wait for confirmation message

#### Example Invitation Form

```
┌─────────────────────────────────────┐
│ Invite John Doe                     │
├─────────────────────────────────────┤
│ Username: [john.doe________]       │
│ Password: [•••••••••••••]       │
│ Confirm Password: [•••••••••••••] │
│ Role: [Employee ▼]                │
│ ☑ Send invitation email           │
│                                     │
│ [Cancel]        [Send Invitation]   │
└─────────────────────────────────────┘
```

### Managing Invitations

#### Viewing Invitation History
1. Go to Employees → Invitation Management
2. View all invitations with their current status
3. Filter by status: Pending, Accepted, Expired, Revoked

#### Resending Invitations
- Find the pending invitation in the list
- Click "Resend" to send a new email
- Expiration date will be extended by 7 days
- Use when employee reports not receiving the email

#### Revoking Invitations
- Find the invitation you want to cancel
- Click "Revoke" to cancel the invitation
- Employee will not be able to accept the invitation
- Use when employee should not receive access

### Invitation Status Guide

| Status | Meaning | Action Required |
|--------|---------|----------------|
| **Pending** | Invitation sent but not yet accepted | Monitor or resend if needed |
| **Accepted** | Employee has created account and logged in | No action needed |
| **Expired** | Invitation expired (7 days old) | Send new invitation |
| **Revoked** | Invitation was cancelled | Send new invitation if still needed |

---

## For Employees

### Receiving an Invitation

#### Email Notification
When invited, you'll receive an email with the following information:

```
Subject: Welcome to AlphaHR - Your Account Details

Dear [Employee Name],

You have been invited to join the AlphaHR system as a [Role].

Your login credentials are:
Username: [username]
Password: [password]

Please login at: [company-url]/login

For security reasons, we recommend changing your password after your first login.

If you have any questions, please contact your HR administrator.

Best regards,
AlphaHR Team
```

#### Security Information
- The email contains your unique login credentials
- Store this information securely
- Do not share your credentials with anyone
- Change your password after first login

### First-Time Login

#### Step-by-Step Guide

1. **Access Login Page**
   - Go to the URL provided in the email
   - Or directly to: `[company-url]/login`

2. **Enter Credentials**
   - Username: As provided in the email
   - Password: As provided in the email

3. **Login Successfully**
   - You'll be redirected to your dashboard
   - You'll see features based on your assigned role

4. **Change Password (Recommended)**
   - Go to Profile → Security Settings
   - Click "Change Password"
   - Enter your current password
   - Create a new password that meets security requirements
   - Confirm the new password
   - Click "Update Password"

#### Password Requirements
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one number (0-9)
- At least one special character (!@#$%^&*)

### Security Best Practices

#### Password Security
- **Never share** your login credentials
- **Change password** immediately after first login
- **Use strong passwords** that are hard to guess
- **Avoid using** common information (birthdays, names, etc.)
- **Update password** regularly (every 90 days)

#### Account Security
- **Log out** when finished using the system
- **Don't save** passwords in browsers on shared computers
- **Report suspicious activity** to IT/HR immediately
- **Use different passwords** for different systems

#### Email Security
- **Verify sender** - invitations come from your company domain
- **Check legitimacy** - confirm with HR if unsure about invitation
- **Report phishing** - forward suspicious emails to IT department

---

## Troubleshooting

### For Administrators/Managers

#### Common Issues and Solutions

**Issue: "Employee already has a user account"**
- Solution: Employee already has access. Check existing user accounts.

**Issue: "Username already exists"**
- Solution: Choose a different username. Try variations like:
  - john.doe2
  - john.doe.department
  - johndoe2024

**Issue: "Email failed to send"**
- Solution: 
  1. Check employee email address for typos
  2. Verify email server configuration
  3. Try resending the invitation
  4. Contact IT if problem persists

**Issue: "Not authorized to create invitations"**
- Solution: Your account doesn't have the required permissions.
  - Contact your system administrator
  - Request appropriate role assignment

#### Debugging Steps

1. **Check Employee Data**
   - Verify employee exists in the system
   - Confirm email address is correct
   - Ensure no existing user account

2. **Check System Configuration**
   - Verify email server settings
   - Check role permissions
   - Confirm database connectivity

3. **Review Error Logs**
   - Check system logs for detailed error messages
   - Look for email delivery failures
   - Review authentication logs

### For Employees

#### Common Issues and Solutions

**Issue: "Invalid username or password"**
- Solutions:
  - Check for typos in username and password
  - Copy and paste credentials from email
  - Verify invitation hasn't expired
  - Contact your administrator if problems persist

**Issue: "Invitation expired"**
- Solutions:
  - Contact your administrator for a new invitation
  - Check if you missed the original email (spam folder)

**Issue: "Account already exists"**
- Solutions:
  - You may already have an account
  - Try password recovery if you forgot credentials
  - Contact IT for account assistance

**Issue: "Email not received"**
- Solutions:
  - Check spam/junk folder
  - Add sender to safe senders list
  - Verify email address with HR
  - Request invitation resend

#### Getting Help

**Contact Information:**
- **IT Helpdesk**: it-support@company.com / ext. 1234
- **HR Department**: hr@company.com / ext. 5678
- **System Administrator**: admin@company.com / ext. 9999

**When Requesting Help:**
1. Provide your employee ID and full name
2. Describe the issue in detail
3. Include any error messages
4. Mention when the issue started
5. Screenshot of error (if possible)

---

## FAQ

### For Administrators

**Q: Can I invite multiple employees at once?**
A: Currently, invitations are sent individually. Bulk invitation feature may be added in future updates.

**Q: What happens if an employee leaves the company?**
A: Their user account should be deactivated by an administrator. The invitation status shows their access history.

**Q: Can I change an employee's role after inviting them?**
A: Yes, administrators can modify user roles through the user management section.

**Q: How long are invitations valid?**
A: Invitations expire after 7 days. You can resend expired invitations.

**Q: Can I customize the invitation email template?**
A: Contact your system administrator to customize email templates.

### For Employees

**Q: I forgot my password. What should I do?**
A: Use the "Forgot Password" link on the login page or contact IT support.

**Q: Can I change my username?**
A: Usernames cannot be changed by employees. Contact IT for username changes.

**Q: What if I don't receive the invitation email?**
A: Check your spam folder, then contact your administrator to resend the invitation.

**Q: Is the system secure?**
A: Yes, the system uses industry-standard encryption and security measures.

**Q: Can I access the system from mobile devices?**
A: Yes, AlphaHR is mobile-responsive and works on smartphones and tablets.

**Q: What features do I have access to?**
A: Your access level depends on your assigned role. Contact your manager for details.

---

## System Requirements

### Browser Compatibility
- **Chrome**: Version 90 or higher
- **Firefox**: Version 88 or higher  
- **Safari**: Version 14 or higher
- **Edge**: Version 90 or higher

### Mobile Access
- Responsive design works on all modern smartphones
- Recommended to use official mobile app (if available)
- Desktop experience recommended for complex tasks

### Network Requirements
- Stable internet connection
- Minimum 2 Mbps download speed
- JavaScript must be enabled
- Cookies must be enabled

---

## Contact Support

### Technical Support
- **Email**: support@alphahr.com
- **Phone**: 1-800-ALPHAAHR
- **Hours**: Monday-Friday, 8 AM - 6 PM EST

### Training Resources
- **Online Help**: Available in-system via Help menu
- **Video Tutorials**: Available at company.training.com
- **User Manuals**: Downloadable from company intranet

### Feedback
We welcome your feedback on the invitation system:
- **Feature Requests**: feedback@alphahr.com
- **Bug Reports**: bugs@alphahr.com
- **User Experience**: ux@alphahr.com

---

*This documentation is updated regularly. Check for the latest version at company intranet → Documentation → Employee Invitation System.*