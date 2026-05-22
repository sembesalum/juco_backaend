from typing import Optional

from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    User,
    Programme,
    Course,
    Semester,
    YearOfStudy,
    ClassGroup,
    Timetable,
    Task,
    Notification,
)
from .serializers import (
    UserSerializer,
    AdminUserCreateUpdateSerializer,
    AdminMonitorWithTimetablesSerializer,
    AdminUserDetailSerializer,
    LecturerLoginSerializer,
    MonitorLoginSerializer,
    AdminLoginSerializer,
    AdminRegisterSerializer,
    ProgrammeSerializer,
    CourseSerializer,
    SemesterSerializer,
    YearOfStudySerializer,
    TimetableSerializer,
    TimetableCreateSerializer,
    TimetableStatusUpdateSerializer,
    TaskSerializer,
    SimpleTaskListSerializer,
    NotificationSerializer,
    NotificationUpdateSerializer,
    MonitorProgrammeUpdateSerializer,
    MonitorSemesterCreateSerializer,
    MonitorYearOfStudyCreateSerializer,
)


def _build_token_response(user: User):
    refresh = RefreshToken.for_user(user)
    serialized = UserSerializer(user).data
    return {
        "id": serialized["id"],
        "name": f"{user.first_name} {user.last_name}".strip() or user.email,
        "email": user.email,
        "registration_number": serialized.get("registration_number"),
        "role": serialized["role"],
        "token": str(refresh.access_token),
    }


class LecturerLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LecturerLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": "Invalid credentials.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data["user"]
        data = _build_token_response(user)
        return Response(data, status=status.HTTP_200_OK)


class MonitorLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = MonitorLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": "Invalid credentials.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data["user"]
        data = _build_token_response(user)
        return Response(data, status=status.HTTP_200_OK)


class AdminRegisterView(APIView):
    """
    Public endpoint for creating an ADMIN account.
    You might want to restrict this in production (e.g., first admin only).
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AdminRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = _build_token_response(user)
        return Response(data, status=status.HTTP_201_CREATED)


class AdminLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": "Invalid credentials.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data["user"]
        data = _build_token_response(user)
        return Response(data, status=status.HTTP_200_OK)


class LecturerTimetableListView(generics.ListAPIView):
    serializer_class = TimetableSerializer

    def get_queryset(self):
        lecturer_id = self.kwargs["lecturer_id"]
        qs = Timetable.objects.filter(lecturer_id=lecturer_id)

        day = self.request.query_params.get("day")
        status_param = self.request.query_params.get("status")
        if day:
            qs = qs.filter(day=day.upper())
        if status_param:
            qs = qs.filter(status=status_param.upper())
        return qs


class MonitorTimetableListView(generics.ListAPIView):
    serializer_class = TimetableSerializer

    def get_queryset(self):
        monitor_id = self.kwargs["monitor_id"]
        qs = Timetable.objects.filter(monitor_id=monitor_id)

        filter_param = self.request.query_params.get("filter")
        day = self.request.query_params.get("day")
        date = self.request.query_params.get("date")

        # For simplicity, treat "today" and "date" as filters on created_at date.
        if filter_param == "day" and day:
            qs = qs.filter(day=day.upper())
        elif filter_param == "date" and date:
            qs = qs.filter(created_at__date=date)
        elif filter_param == "today":
            from django.utils.timezone import now

            today = now().date()
            qs = qs.filter(created_at__date=today)
        return qs


class MonitorManageTimetableListView(generics.ListAPIView):
    serializer_class = TimetableSerializer

    def get_queryset(self):
        monitor_id = self.kwargs["monitor_id"]
        return Timetable.objects.filter(monitor_id=monitor_id)


class TimetableCreateView(APIView):
    def post(self, request):
        serializer = TimetableCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        monitor = get_object_or_404(User, id=data["monitor_id"], role=User.Role.MONITOR)
        lecturer = get_object_or_404(
            User, id=data["lecturer_id"], role=User.Role.LECTURER
        )
        course = get_object_or_404(Course, id=data["course_id"])
        semester = get_object_or_404(Semester, id=data["semester_id"])

        created = []
        for day in data["days"]:
            timetable = Timetable.objects.create(
                monitor=monitor,
                lecturer=lecturer,
                course=course,
                semester=semester,
                subject_code=data["subject_code"],
                subject_name=data["subject_name"],
                venue=data["venue"],
                day=day.upper(),
                start_time=data["start_time"],
                end_time=data["end_time"],
                color_code=data["color_code"],
            )
            created.append({"id": timetable.id, "day": timetable.day})

        return Response({"created": created}, status=status.HTTP_201_CREATED)


class TimetableDetailView(APIView):
    """
    Handles:
    - PUT     /api/timetables/{timetableId}
    - DELETE  /api/timetables/{timetableId}
    """

    def get_object(self, timetable_id: int) -> Timetable:
        return get_object_or_404(Timetable, id=timetable_id)

    def put(self, request, timetable_id):
        timetable = self.get_object(timetable_id)
        serializer = TimetableSerializer(
            timetable, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, timetable_id):
        timetable = self.get_object(timetable_id)
        timetable.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TimetableStatusUpdateView(APIView):
    """
    PATCH /api/timetables/{timetableId}/status
    """

    def patch(self, request, timetable_id):
        timetable = get_object_or_404(Timetable, id=timetable_id)
        serializer = TimetableStatusUpdateSerializer(
            timetable, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        lecturer_id = serializer.validated_data.pop("lecturer_id", None)
        if lecturer_id is not None and lecturer_id != timetable.lecturer_id:
            return Response(
                {"detail": "Lecturer mismatch for this timetable."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save()
        return Response(
            {
                "id": timetable.id,
                "status": timetable.status,
                "cancellation_note": timetable.cancellation_note,
            },
            status=status.HTTP_200_OK,
        )


class LecturerTaskListCreateView(APIView):
    """
    GET  /api/lecturers/{lecturerId}/tasks
    POST /api/lecturers/{lecturerId}/tasks
    """

    def get(self, request, lecturer_id):
        qs = Task.objects.filter(lecturer_id=lecturer_id)
        class_id = request.query_params.get("class_id")
        upcoming_only = request.query_params.get("upcoming_only")
        if class_id:
            qs = qs.filter(class_group_id=class_id)
        if upcoming_only == "true":
            from django.utils.timezone import now

            qs = qs.filter(scheduled_at__gte=now())
        data = SimpleTaskListSerializer(qs, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, lecturer_id):
        lecturer = get_object_or_404(
            User, id=lecturer_id, role=User.Role.LECTURER
        )
        serializer = TaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(lecturer=lecturer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LecturerTaskDetailView(APIView):
    """
    PUT    /api/lecturers/{lecturerId}/tasks/{taskId}
    DELETE /api/lecturers/{lecturerId}/tasks/{taskId}
    """

    def get_object(self, lecturer_id, task_id):
        return get_object_or_404(Task, id=task_id, lecturer_id=lecturer_id)

    def put(self, request, lecturer_id, task_id):
        task = self.get_object(lecturer_id, task_id)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "id": task.id,
                "title": task.title,
                "send_to_crs": task.send_to_crs,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, lecturer_id, task_id):
        task = self.get_object(lecturer_id, task_id)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MonitorTaskListView(generics.ListAPIView):
    """
    GET /api/monitors/{monitorId}/tasks
    """

    serializer_class = SimpleTaskListSerializer

    def get_queryset(self):
        # Simple implementation: tasks visible to CRs
        class_id = self.request.query_params.get("class_id")
        qs = Task.objects.filter(send_to_crs=True)
        if class_id:
            qs = qs.filter(class_group_id=class_id)
        return qs


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        qs = Notification.objects.filter(user_id=user_id).order_by("-created_at")
        unread_only = self.request.query_params.get("unread_only")
        if unread_only == "true":
            qs = qs.filter(is_read=False)
        return qs


class NotificationUpdateView(APIView):
    def patch(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id)
        serializer = NotificationUpdateSerializer(
            notification, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"id": notification.id, "is_read": notification.is_read},
            status=status.HTTP_200_OK,
        )


class CourseListView(generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class ProgrammeListView(generics.ListAPIView):
    queryset = Programme.objects.all()
    serializer_class = ProgrammeSerializer


class SemesterListView(generics.ListAPIView):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer


class YearOfStudyListView(generics.ListAPIView):
    queryset = YearOfStudy.objects.all()
    serializer_class = YearOfStudySerializer


class LecturerListView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(role=User.Role.LECTURER)


class IsAdminUserRole(permissions.BasePermission):
    """
    Custom permission: only allow authenticated users with role ADMIN.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == User.Role.ADMIN
        )


class AdminMonitorTimetablesListView(APIView):
    """
    Admin: list every class representative (MONITOR) with timetables they created.
    """

    permission_classes = [IsAdminUserRole]

    def get(self, request):
        timetable_qs = Timetable.objects.select_related(
            "lecturer", "course", "semester"
        ).order_by("day", "start_time", "id")
        monitors = (
            User.objects.filter(role=User.Role.MONITOR)
            .select_related("programme")
            .prefetch_related(Prefetch("monitor_timetables", queryset=timetable_qs))
            .order_by("last_name", "first_name", "id")
        )
        data = AdminMonitorWithTimetablesSerializer(monitors, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class AdminUserListCreateView(APIView):
    """
    Admin: register and list lecturers/CRs (and optionally admins).
    """

    permission_classes = [IsAdminUserRole]

    def get(self, request):
        role = request.query_params.get("role")
        qs = User.objects.all()
        if role:
            qs = qs.filter(role=role.upper())
        serializer = UserSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AdminUserCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class AdminUserDetailView(APIView):
    """
    Admin: view, edit and delete lecturers/CRs/admins with related data.
    """

    permission_classes = [IsAdminUserRole]

    def get_object(self, user_id):
        return get_object_or_404(User, id=user_id)

    def get(self, request, user_id):
        user = self.get_object(user_id)
        serializer = AdminUserDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, user_id):
        user = self.get_object(user_id)
        serializer = AdminUserCreateUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def delete(self, request, user_id):
        user = self.get_object(user_id)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminCourseListCreateView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        data = CourseSerializer(Course.objects.all(), many=True).data
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        if "programme" not in request.data:
            return Response(
                {"detail": "programme is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CourseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminCourseDetailView(APIView):
    permission_classes = [IsAdminUserRole]

    def get_object(self, course_id):
        return get_object_or_404(Course, id=course_id)

    def put(self, request, course_id):
        course = self.get_object(course_id)
        serializer = CourseSerializer(course, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, course_id):
        course = self.get_object(course_id)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminSemesterListCreateView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        data = SemesterSerializer(Semester.objects.all(), many=True).data
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SemesterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminSemesterDetailView(APIView):
    permission_classes = [IsAdminUserRole]

    def get_object(self, semester_id):
        return get_object_or_404(Semester, id=semester_id)

    def put(self, request, semester_id):
        semester = self.get_object(semester_id)
        serializer = SemesterSerializer(semester, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, semester_id):
        semester = self.get_object(semester_id)
        semester.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminYearOfStudyListCreateView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        data = YearOfStudySerializer(YearOfStudy.objects.all(), many=True).data
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = YearOfStudySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if "programme" not in request.data:
            return Response(
                {"detail": "programme is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if serializer.validated_data["semester"].course_id != serializer.validated_data["course"].id:
            return Response(
                {"detail": "Selected semester does not belong to the selected course."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminYearOfStudyDetailView(APIView):
    permission_classes = [IsAdminUserRole]

    def get_object(self, year_id):
        return get_object_or_404(YearOfStudy, id=year_id)

    def put(self, request, year_id):
        year = self.get_object(year_id)
        serializer = YearOfStudySerializer(year, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        course = serializer.validated_data.get("course", year.course)
        semester = serializer.validated_data.get("semester", year.semester)
        if semester.course_id != course.id:
            return Response(
                {"detail": "Selected semester does not belong to the selected course."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, year_id):
        year = self.get_object(year_id)
        year.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminProgrammeListCreateView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        data = ProgrammeSerializer(Programme.objects.all(), many=True).data
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProgrammeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminProgrammeDetailView(APIView):
    permission_classes = [IsAdminUserRole]

    def get_object(self, programme_id):
        return get_object_or_404(Programme, id=programme_id)

    def put(self, request, programme_id):
        programme = self.get_object(programme_id)
        serializer = ProgrammeSerializer(programme, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, programme_id):
        programme = self.get_object(programme_id)
        programme.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _ensure_monitor_self(request, monitor_id: int) -> Optional[Response]:
    user = request.user
    if not user.is_authenticated:
        return Response(
            {"detail": "Authentication required."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if user.id != monitor_id or getattr(user, "role", None) != User.Role.MONITOR:
        return Response(
            {"detail": "You may only manage your own monitor profile."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


def get_or_create_programme_anchor_course(programme: Programme, monitor: User) -> Course:
    """
    Semesters require a Course FK. Per programme we keep one anchor course created by the CR
    so they only interact with programme + semester + year in the app.
    """
    sentinel_code = f"__PRG_{programme.pk}__"
    course, _ = Course.objects.get_or_create(
        programme=programme,
        code=sentinel_code,
        defaults={"name": programme.name, "monitor": monitor},
    )
    if course.monitor_id is None:
        course.monitor = monitor
        course.save(update_fields=["monitor"])
    return course


class MonitorProgrammeUpdateView(APIView):
    """PATCH: assign programme created by admin to this CR."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, monitor_id):
        bad = _ensure_monitor_self(request, monitor_id)
        if bad is not None:
            return bad
        serializer = MonitorProgrammeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        monitor = get_object_or_404(User, id=monitor_id, role=User.Role.MONITOR)
        pid = serializer.validated_data.get("programme_id")
        if pid is None:
            monitor.programme = None
        else:
            monitor.programme = get_object_or_404(Programme, id=pid)
        monitor.save(update_fields=["programme"])
        return Response(UserSerializer(monitor).data, status=status.HTTP_200_OK)


class MonitorAcademicOverviewView(APIView):
    """GET: semesters and years of study this CR added for their programme."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, monitor_id):
        bad = _ensure_monitor_self(request, monitor_id)
        if bad is not None:
            return bad
        monitor = get_object_or_404(User, id=monitor_id, role=User.Role.MONITOR)
        programme = monitor.programme
        if programme is None:
            return Response(
                {
                    "programme_id": None,
                    "programme_name": None,
                    "semesters": [],
                    "years_of_study": [],
                },
                status=status.HTTP_200_OK,
            )
        course_ids = Course.objects.filter(programme_id=programme.id).values_list(
            "id", flat=True
        )
        semesters = Semester.objects.filter(
            course_id__in=course_ids, monitor_id=monitor_id
        ).order_by("id")
        years = YearOfStudy.objects.filter(
            programme_id=programme.id, monitor_id=monitor_id
        ).order_by("id")
        return Response(
            {
                "programme_id": programme.id,
                "programme_name": programme.name,
                "semesters": [
                    {"id": s.id, "name": s.name, "course_id": s.course_id}
                    for s in semesters
                ],
                "years_of_study": [
                    {
                        "id": y.id,
                        "name": y.name,
                        "semester_id": y.semester_id,
                        "course_id": y.course_id,
                    }
                    for y in years
                ],
            },
            status=status.HTTP_200_OK,
        )


class MonitorSemesterCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, monitor_id):
        bad = _ensure_monitor_self(request, monitor_id)
        if bad is not None:
            return bad
        monitor = get_object_or_404(User, id=monitor_id, role=User.Role.MONITOR)
        if not monitor.programme_id:
            return Response(
                {"detail": "Select a programme first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = MonitorSemesterCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = get_or_create_programme_anchor_course(monitor.programme, monitor)
        name = serializer.validated_data["name"].strip()
        if not name:
            return Response(
                {"detail": "Semester name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        sem = Semester.objects.create(name=name, course=course, monitor=monitor)
        return Response(
            {"id": sem.id, "name": sem.name, "course_id": sem.course_id},
            status=status.HTTP_201_CREATED,
        )


class MonitorYearOfStudyCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, monitor_id):
        bad = _ensure_monitor_self(request, monitor_id)
        if bad is not None:
            return bad
        monitor = get_object_or_404(User, id=monitor_id, role=User.Role.MONITOR)
        if not monitor.programme_id:
            return Response(
                {"detail": "Select a programme first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = MonitorYearOfStudyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        semester = get_object_or_404(
            Semester, id=serializer.validated_data["semester_id"]
        )
        if semester.monitor_id != monitor.id:
            return Response(
                {"detail": "Semester not found for this account."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if semester.course.programme_id != monitor.programme_id:
            return Response(
                {"detail": "Semester does not belong to your programme."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        yname = serializer.validated_data["name"].strip()
        if not yname:
            return Response(
                {"detail": "Year of study name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        year = YearOfStudy.objects.create(
            name=yname,
            programme=monitor.programme,
            course=semester.course,
            semester=semester,
            monitor=monitor,
        )
        return Response(
            {"id": year.id, "name": year.name, "semester_id": year.semester_id},
            status=status.HTTP_201_CREATED,
        )

