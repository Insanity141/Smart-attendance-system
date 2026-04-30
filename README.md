# Smart Attendance System (QR-Based)
A comprehensive web-based solution for automated attendance tracking. This system leverages unique QR code generation to streamline the attendance process for instructors and students alike, replacing manual logs with a digital, report-driven workflow.

# Features
## For Students 
- Sign-Up Access: The only user role with self-registration capabilities.
- Personal Dashboard: View overall attendance records filtered by section.
- Real-time Tracking: Monitor attendance status relative to total classes held.

## For Instructors 
- Instant QR Generation: Generate unique QR codes for sections to capture attendance in seconds.
- Advanced Reporting: Export section-wise attendance reports in PDF and SVG formats.
- Analytics: View average attendance per section and compare individual student performance against class totals.
- Section Management: Create or drop sections and manage student rosters (removing a student only affects the specific section, not their system account).

## For Admins
- User Management: Exclusively add instructors and manage all user credentials.
- System Oversight: Full authority to add/delete any user from the system.
- Global Access: Generate reports across all sections and manage site-wide data.

# Tech Stack
- Backend: Python (Flask)
- Frontend: HTML, CSS, JavaScript (Vanilla)
- Database: MySql
- Data Handeling: Report generation in pdf/svg formats. 