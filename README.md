## Juco Notify – Backend API

This Django project implements the backend REST API for the Juco Notify mobile app, following the contract in `BACKEND_API_SPEC.md`.

Base URL prefix for all endpoints: `/api/`

---

### 1. Authentication & Users

- **Lecturer Login**
  - **POST** `/api/auth/lecturers/login`
  - **Body**
    ```json
    {
      "email": "lecturer@example.com",
      "password": "string"
    }
    ```
  - **Success 200**
    ```json
    {
      "id": 1,
      "name": "Dr. Jane Doe",
      "email": "lecturer@example.com",
      "registration_number": null,
      "role": "LECTURER",
      "token": "jwt-access-token"
    }
    ```
  - **Errors**
    - `400 Bad Request` – invalid credentials or missing fields.
    - `500 Internal Server Error` – unexpected server error.

- **CR (Monitor) Login**
  - **POST** `/api/auth/monitors/login`
  - **Body**
    ```json
    {
      "registration_number": "DIT 092/221",
      "password": "string"
    }
    ```
  - **Success 200**
    ```json
    {
      "id": 10,
      "name": "Edger Emmanuel",
      "email": "cr@example.com",
      "registration_number": "DIT 092/221",
      "role": "MONITOR",
      "token": "jwt-access-token"
    }
    ```
  - **Errors**
    - `400 Bad Request` – invalid credentials or missing fields.
    - `500 Internal Server Error` – unexpected server error.

> All other endpoints require a valid JWT access token in the `Authorization: Bearer <token>` header unless otherwise stated.

---

### 1.1 Admin Users (Custom Admin API)

These endpoints are for users with `role = "ADMIN"` (they do not use the default Django admin panel).

- **List / Register Users (Lecturers, CRs, Admins)**
  - **GET** `/api/admin/users`
    - Optional query: `role=LECTURER|MONITOR|ADMIN`
  - **POST** `/api/admin/users`
  - **Body (example – create lecturer)**
    ```json
    {
      "first_name": "Jane",
      "last_name": "Doe",
      "email": "lecturer@example.com",
      "role": "LECTURER",
      "password": "strong-password"
    }
    ```
  - **Body (example – create CR / monitor)**
    ```json
    {
      "first_name": "Edger",
      "last_name": "Emmanuel",
      "email": "cr@example.com",
      "role": "MONITOR",
      "registration_number": "DIT 092/221",
      "password": "strong-password"
    }
    ```
  - **Success 201 (POST)**
    ```json
    {
      "id": 12,
      "first_name": "Jane",
      "last_name": "Doe",
      "email": "lecturer@example.com",
      "role": "LECTURER",
      "registration_number": null
    }
    ```
  - **Errors**
    - `400 Bad Request` – validation / unique constraint errors.
    - `403 Forbidden` – caller is not an ADMIN.

- **View / Edit / Delete Single User (with related data)**
  - **GET** `/api/admin/users/{userId}`
    - Returns full user info, plus:
      - `lecturer_timetables` (if user is a lecturer)
      - `monitor_timetables` (if user is a CR)
      - `tasks` (lecturer tasks)
  - **PUT** `/api/admin/users/{userId}`
    - Same body fields as POST; password is optional (only updated if provided).
  - **DELETE** `/api/admin/users/{userId}`
  - **Success 200 (GET/PUT)**
    ```json
    {
      "id": 1,
      "first_name": "Jane",
      "last_name": "Doe",
      "email": "lecturer@example.com",
      "role": "LECTURER",
      "registration_number": null,
      "lecturer_timetables": [ /* timetable objects */ ],
      "monitor_timetables": [],
      "tasks": [ /* task summaries */ ]
    }
    ```
  - **Success 204 (DELETE)** – no content.
  - **Errors**
    - `403 Forbidden` – caller is not an ADMIN.
    - `404 Not Found` – user not found.

---

### 2. Timetables

- **List Lecturer Timetables**
  - **GET** `/api/lecturers/{lecturerId}/timetables`
  - **Query params (optional)**
    - `day=MONDAY`
    - `status=PENDING|CONFIRMED|CANCELLED`
  - **Success 200**
    ```json
    [
      {
        "id": 123,
        "subject_name": "Intro to CS",
        "subject_code": "CSC101",
        "course_name": "BSc CS",
        "course_id": 5,
        "venue": "Room 101",
        "day": "MONDAY",
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "status": "PENDING",
        "color_code": "#4285F4",
        "lecturer_id": 1,
        "lecturer_name": "Dr. Jane Doe",
        "monitor_id": 10,
        "semester_id": 2,
        "cancellation_note": null
      }
    ]
    ```
  - **Errors**
    - `401 Unauthorized` – missing/invalid token.

- **Update Timetable Status**
  - **PATCH** `/api/timetables/{timetableId}/status`
  - **Body**
    ```json
    {
      "status": "CONFIRMED",
      "lecturer_id": 1,
      "cancellation_note": "Optional note for cancellation"
    }
    ```
  - **Success 200**
    ```json
    {
      "id": 123,
      "status": "CONFIRMED",
      "cancellation_note": null
    }
    ```
  - **Errors**
    - `400 Bad Request` – validation errors.
    - `403 Forbidden` – lecturer_id does not match the timetable lecturer.
    - `404 Not Found` – timetable not found.

- **Monitor Timetables (Classes View)**
  - **GET** `/api/monitors/{monitorId}/timetables`
  - **Query params (optional)**
    - `filter=today|day|date`
    - `day=MONDAY` (when `filter=day`)
    - `date=YYYY-MM-DD` (when `filter=date`)
  - **Success 200** – same item shape as lecturer timetables.

- **CR “My Timetable” – Manage**
  - **GET** `/api/monitors/{monitorId}/timetables/manage`
  - **Success 200**
    - Same shape as monitor timetables plus full timetable details (code, color, etc.).

- **Create Timetable Entries (CR Form)**
  - **POST** `/api/timetables`
  - **Body**
    ```json
    {
      "monitor_id": 10,
      "lecturer_id": 1,
      "course_id": 5,
      "semester_id": 2,
      "subject_code": "CSC101",
      "subject_name": "Intro to CS",
      "venue": "Room 101",
      "days": ["MONDAY", "WEDNESDAY"],
      "start_time": "09:00:00",
      "end_time": "10:00:00",
      "color_code": "#4285F4"
    }
    ```
  - **Success 201**
    ```json
    {
      "created": [
        { "id": 201, "day": "MONDAY" },
        { "id": 202, "day": "WEDNESDAY" }
      ]
    }
    ```
  - **Errors**
    - `400 Bad Request` – missing/invalid fields.
    - `404 Not Found` – monitor, lecturer, course, or semester not found.

- **Edit Timetable (CR Edit Dialog)**
  - **PUT** `/api/timetables/{timetableId}`
  - **Body** (any updatable fields)
    ```json
    {
      "subject_name": "Intro to Computer Science",
      "subject_code": "CSC101",
      "venue": "Room 102",
      "day": "TUESDAY"
    }
    ```
  - **Success 200** – updated timetable object (same shape as list entries).
  - **Errors**
    - `400 Bad Request` – validation errors.
    - `404 Not Found` – timetable not found.

- **Delete Timetable (CR Swipe to Delete)**
  - **DELETE** `/api/timetables/{timetableId}`
  - **Success 204** – no content.
  - **Errors**
    - `404 Not Found` – timetable not found.

---

### 3. Lecturer Tasks

- **List Lecturer Tasks**
  - **GET** `/api/lecturers/{lecturerId}/tasks`
  - **Query params (optional)**
    - `class_id=5`
    - `upcoming_only=true`
  - **Success 200**
    ```json
    [
      {
        "id": 500,
        "title": "Midterm Test",
        "type": "Test",
        "class_name": "DIT 1A",
        "scheduled_at": "2026-04-01T10:00:00Z",
        "send_to_crs": true
      }
    ]
    ```

- **Create Task**
  - **POST** `/api/lecturers/{lecturerId}/tasks`
  - **Body**
    ```json
    {
      "title": "Quiz 1",
      "type": "Quiz",
      "class_id": 5,
      "class_name": "DIT 1A",
      "scheduled_at": "2026-03-25T14:00:00Z",
      "notes": "Short quiz on week 2 material",
      "send_to_crs": true
    }
    ```
  - **Success 201**
    ```json
    {
      "id": 501,
      "lecturer": 1,
      "title": "Quiz 1",
      "type": "Quiz",
      "class_group": 5,
      "class_name": "DIT 1A",
      "scheduled_at": "2026-03-25T14:00:00Z",
      "notes": "Short quiz on week 2 material",
      "send_to_crs": true,
      "created_at": "2026-03-20T09:00:00Z",
      "updated_at": "2026-03-20T09:00:00Z"
    }
    ```

- **Update Task**
  - **PUT** `/api/lecturers/{lecturerId}/tasks/{taskId}`
  - **Body**
    ```json
    {
      "title": "Quiz 1 (Updated)",
      "type": "Quiz",
      "class_id": 5,
      "scheduled_at": "2026-03-26T10:00:00Z",
      "notes": "Rescheduled due to public holiday",
      "send_to_crs": false
    }
    ```
  - **Success 200**
    ```json
    {
      "id": 501,
      "title": "Quiz 1 (Updated)",
      "send_to_crs": false
    }
    ```
  - **Errors**
    - `404 Not Found` – task not found for given lecturer.

- **Delete Task**
  - **DELETE** `/api/lecturers/{lecturerId}/tasks/{taskId}`
  - **Success 204** – no content.

- **CR View Tasks (optional)**
  - **GET** `/api/monitors/{monitorId}/tasks`
  - **Query params**
    - `class_id=5`
  - **Success 200**
    ```json
    [
      {
        "id": 500,
        "title": "Midterm Test",
        "type": "Test",
        "scheduled_at": "2026-04-01T10:00:00Z",
        "class_name": "DIT 1A"
      }
    ]
    ```

---

### 4. Notifications

- **List Notifications for User**
  - **GET** `/api/users/{userId}/notifications`
  - **Query params (optional)**
    - `unread_only=true`
  - **Success 200**
    ```json
    [
      {
        "id": 900,
        "title": "Class Cancelled",
        "message": "Today's Database class has been cancelled.",
        "created_at": "2026-03-20T09:30:00Z",
        "is_read": false,
        "related_type": "TIMETABLE",
        "related_id": 123
      }
    ]
    ```

- **Mark Notification as Read**
  - **PATCH** `/api/notifications/{notificationId}`
  - **Body**
    ```json
    { "is_read": true }
    ```
  - **Success 200**
    ```json
    { "id": 900, "is_read": true }
    ```

---

### 5. Reference Data

- **List Courses**
  - **GET** `/api/courses`
  - **Success 200**
    ```json
    [
      { "id": 5, "code": "DIT", "name": "Diploma in Information Technology" }
    ]
    ```

- **List Semesters**
  - **GET** `/api/semesters`
  - **Success 200**
    ```json
    [
      { "id": 2, "name": "Semester 2", "course": 5 }
    ]
    ```

- **List Lecturers**
  - **GET** `/api/lecturers`
  - **Success 200**
    ```json
    [
      { "id": 1, "first_name": "Jane", "last_name": "Doe", "email": "lecturer@example.com", "role": "LECTURER", "registration_number": null }
    ]
    ```

---

### 6. Common Status Codes

- **200 OK** – Successful GET, PUT, PATCH operations.
- **201 Created** – Successful resource creation (timetables, tasks).
- **204 No Content** – Successful deletion (timetables, tasks).
- **400 Bad Request** – Validation errors, malformed JSON, or invalid credentials.
- **401 Unauthorized** – Missing or invalid JWT token.
- **403 Forbidden** – Authenticated but not allowed for this action (e.g. lecturer mismatch).
- **404 Not Found** – Resource not found for provided ID.
- **500 Internal Server Error** – Unexpected server-side error.

---

### 7. Running the Project

1. Install dependencies (inside your virtualenv):
   ```bash
   pip install django djangorestframework djangorestframework-simplejwt
   ```
2. Run migrations:
   ```bash
   python manage.py migrate
   ```
3. Create a superuser (optional, for admin):
   ```bash
   python manage.py createsuperuser
   ```
4. Start the development server:
   ```bash
   python manage.py runserver
   ```

