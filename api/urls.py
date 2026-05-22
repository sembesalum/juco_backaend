from django.urls import path

from . import views

urlpatterns = [
    # Authentication
    path("auth/lecturers/login", views.LecturerLoginView.as_view(), name="lecturer-login"),
    path("auth/monitors/login", views.MonitorLoginView.as_view(), name="monitor-login"),
    path("auth/admin/register", views.AdminRegisterView.as_view(), name="admin-register"),
    path("auth/admin/login", views.AdminLoginView.as_view(), name="admin-login"),

    # Timetables
    path(
        "lecturers/<int:lecturer_id>/timetables",
        views.LecturerTimetableListView.as_view(),
        name="lecturer-timetables",
    ),
    path(
        "monitors/<int:monitor_id>/timetables",
        views.MonitorTimetableListView.as_view(),
        name="monitor-timetables",
    ),
    path(
        "monitors/<int:monitor_id>/timetables/manage",
        views.MonitorManageTimetableListView.as_view(),
        name="monitor-manage-timetables",
    ),
    path(
        "monitors/<int:monitor_id>/programme",
        views.MonitorProgrammeUpdateView.as_view(),
        name="monitor-programme-update",
    ),
    path(
        "monitors/<int:monitor_id>/academic",
        views.MonitorAcademicOverviewView.as_view(),
        name="monitor-academic-overview",
    ),
    path(
        "monitors/<int:monitor_id>/semesters",
        views.MonitorSemesterCreateView.as_view(),
        name="monitor-semester-create",
    ),
    path(
        "monitors/<int:monitor_id>/years-of-study",
        views.MonitorYearOfStudyCreateView.as_view(),
        name="monitor-year-of-study-create",
    ),
    path("timetables", views.TimetableCreateView.as_view(), name="timetable-create"),
    path(
        "timetables/<int:timetable_id>",
        views.TimetableDetailView.as_view(),
        name="timetable-detail",
    ),
    path(
        "timetables/<int:timetable_id>/status",
        views.TimetableStatusUpdateView.as_view(),
        name="timetable-status-update",
    ),

    # Tasks
    path(
        "lecturers/<int:lecturer_id>/tasks",
        views.LecturerTaskListCreateView.as_view(),
        name="lecturer-tasks",
    ),
    path(
        "lecturers/<int:lecturer_id>/tasks/<int:task_id>",
        views.LecturerTaskDetailView.as_view(),
        name="lecturer-task-detail",
    ),
    path(
        "monitors/<int:monitor_id>/tasks",
        views.MonitorTaskListView.as_view(),
        name="monitor-tasks",
    ),

    # Notifications
    path(
        "users/<int:user_id>/notifications",
        views.NotificationListView.as_view(),
        name="user-notifications",
    ),
    path(
        "notifications/<int:notification_id>",
        views.NotificationUpdateView.as_view(),
        name="notification-update",
    ),

    # Reference data
    path("courses", views.CourseListView.as_view(), name="courses-list"),
    path("programmes", views.ProgrammeListView.as_view(), name="programmes-list"),
    path("semesters", views.SemesterListView.as_view(), name="semesters-list"),
    path("years-of-study", views.YearOfStudyListView.as_view(), name="years-of-study-list"),
    path("lecturers", views.LecturerListView.as_view(), name="lecturers-list"),

    # Admin management (custom admin API, not Django admin site)
    path(
        "admin/monitors/timetables",
        views.AdminMonitorTimetablesListView.as_view(),
        name="admin-monitors-timetables",
    ),
    path("admin/users", views.AdminUserListCreateView.as_view(), name="admin-users"),
    path("admin/users/<int:user_id>", views.AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("admin/courses", views.AdminCourseListCreateView.as_view(), name="admin-courses"),
    path("admin/programmes", views.AdminProgrammeListCreateView.as_view(), name="admin-programmes"),
    path("admin/programmes/<int:programme_id>", views.AdminProgrammeDetailView.as_view(), name="admin-programme-detail"),
    path("admin/courses/<int:course_id>", views.AdminCourseDetailView.as_view(), name="admin-course-detail"),
    path("admin/semesters", views.AdminSemesterListCreateView.as_view(), name="admin-semesters"),
    path("admin/semesters/<int:semester_id>", views.AdminSemesterDetailView.as_view(), name="admin-semester-detail"),
    path("admin/years-of-study", views.AdminYearOfStudyListCreateView.as_view(), name="admin-years-of-study"),
    path("admin/years-of-study/<int:year_id>", views.AdminYearOfStudyDetailView.as_view(), name="admin-year-of-study-detail"),
]

