# Juco API Endpoints

Base URL: `http://localhost:8000/api` (Local) or `http://10.0.2.2:8000/api` (Android Emulator)

## Authentication
- `POST /auth/lecturers/login` - Lecturer login (email, password)
- `POST /auth/monitors/login` - Class Rep login (registration_number, password)
- `POST /auth/admin/register` - Admin self-registration (username, first_name, last_name, email, password)
- `POST /auth/admin/login` - Admin login (email, password)

## Timetables
- `GET /lecturers/{id}/timetables` - Get lecturer's timetable
- `GET /monitors/{id}/timetables` - Get monitor's timetable
- `POST /timetables` - Create new timetable entries
- `PUT /timetables/{id}` - Update timetable entry
- `PATCH /timetables/{id}/status` - Update entry status (PENDING, CONFIRMED, CANCELLED)
- `DELETE /timetables/{id}` - Delete timetable entry

## Tasks
- `GET /lecturers/{id}/tasks` - List lecturer's tasks
- `POST /lecturers/{id}/tasks` - Create new task
- `GET /monitors/{id}/tasks` - List tasks visible to CRs

## Notifications
- `GET /users/{id}/notifications` - List user notifications
- `PATCH /notifications/{id}` - Mark notification as read

## Reference Data (Admin/CR Management)
- `GET /courses` - List all courses
- `GET /programmes` - List all programmes
- `GET /semesters` - List all semesters
- `GET /years-of-study` - List all years of study
- `GET /lecturers` - List all lecturers

## Admin Specific
- `GET /admin/users` - List all users (filter by ?role=)
- `POST /admin/users` - Create new user (Lecturer/Monitor)
- `GET /admin/monitors/timetables` - Overview of all CRs and their timetables
