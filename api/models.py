from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model to support two main roles:
    - LECTURER
    - MONITOR (Class Representative)
    - ADMIN
    """

    class Role(models.TextChoices):
        LECTURER = "LECTURER", "Lecturer"
        MONITOR = "MONITOR", "Monitor"
        ADMIN = "ADMIN", "Admin"

    # We keep Django's default username field for admin/login flexibility,
    # but the API logins will use `email` (lecturers) or `registration_number` (monitors).
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=16, choices=Role.choices)
    registration_number = models.CharField(
        max_length=64, unique=True, null=True, blank=True,
        help_text="Student registration number for MONITOR users"
    )
    programme = models.ForeignKey(
        "Programme",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="monitors",
    )

    def __str__(self) -> str:
        return self.get_full_name() or self.username or self.email


class Course(models.Model):
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=255)
    programme = models.ForeignKey(
        "Programme",
        on_delete=models.CASCADE,
        related_name="courses",
        null=True,
        blank=True,
    )
    monitor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_courses",
        limit_choices_to={"role": User.Role.MONITOR},
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Semester(models.Model):
    name = models.CharField(max_length=64)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="semesters")
    year_of_study = models.ForeignKey(
        "YearOfStudy",
        on_delete=models.CASCADE,
        related_name="semesters",
        null=True,
        blank=True,
    )
    monitor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_semesters",
        limit_choices_to={"role": User.Role.MONITOR},
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f"{self.course.code} - {self.name}"


class YearOfStudy(models.Model):
    name = models.CharField(max_length=64)
    programme = models.ForeignKey(
        "Programme",
        on_delete=models.CASCADE,
        related_name="years_of_study",
        null=True,
        blank=True,
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="years_of_study"
    )
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="years_of_study"
    )
    monitor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_years_of_study",
        limit_choices_to={"role": User.Role.MONITOR},
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f"{self.course.code} - {self.name}"


class Programme(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class ClassGroup(models.Model):
    """
    Represents a teaching group like 'DIT 1A'.
    """

    name = models.CharField(max_length=128)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="class_groups")

    def __str__(self) -> str:
        return self.name


class Timetable(models.Model):
    class Day(models.TextChoices):
        MONDAY = "MONDAY", "Monday"
        TUESDAY = "TUESDAY", "Tuesday"
        WEDNESDAY = "WEDNESDAY", "Wednesday"
        THURSDAY = "THURSDAY", "Thursday"
        FRIDAY = "FRIDAY", "Friday"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    subject_code = models.CharField(max_length=32)
    subject_name = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="timetables")
    venue = models.CharField(max_length=255)
    day = models.CharField(max_length=16, choices=Day.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    color_code = models.CharField(max_length=9, default="#4285F4")
    lecturer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lecturer_timetables",
        limit_choices_to={"role": User.Role.LECTURER},
    )
    monitor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="monitor_timetables",
        limit_choices_to={"role": User.Role.MONITOR},
    )
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="timetables"
    )
    cancellation_note = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.subject_code} - {self.day} {self.start_time}"


class Task(models.Model):
    class TaskType(models.TextChoices):
        TEST = "Test", "Test"
        QUIZ = "Quiz", "Quiz"
        ASSIGNMENT = "Assignment", "Assignment"
        OTHER = "Other", "Other"

    lecturer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tasks",
        limit_choices_to={"role": User.Role.LECTURER},
    )
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=16, choices=TaskType.choices)
    class_group = models.ForeignKey(
        ClassGroup, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True
    )
    class_name = models.CharField(
        max_length=128,
        help_text="Display name such as 'DIT 1A'",
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    send_to_crs = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


class Notification(models.Model):
    class RelatedType(models.TextChoices):
        TIMETABLE = "TIMETABLE", "Timetable"
        TASK = "TASK", "Task"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    role = models.CharField(max_length=16, choices=User.Role.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    related_type = models.CharField(
        max_length=16, choices=RelatedType.choices, null=True, blank=True
    )
    related_id = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.title} -> {self.user}"

