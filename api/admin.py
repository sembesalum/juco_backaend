from django.contrib import admin
from .models import (
    User,
    Course,
    Semester,
    YearOfStudy,
    Programme,
    ClassGroup,
    Timetable,
    Task,
    Notification
)

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    search_fields = ('username', 'email', 'registration_number')
    list_filter = ('role', 'is_staff', 'is_superuser')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'programme', 'monitor')
    search_fields = ('code', 'name')

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'year_of_study', 'monitor')

@admin.register(YearOfStudy)
class YearOfStudyAdmin(admin.ModelAdmin):
    list_display = ('name', 'programme', 'course', 'semester', 'monitor')

@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'course')

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('subject_code', 'subject_name', 'day', 'start_time', 'end_time', 'status', 'lecturer')
    list_filter = ('day', 'status', 'lecturer')
    search_fields = ('subject_code', 'subject_name', 'venue')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'lecturer', 'class_name', 'scheduled_at')
    list_filter = ('type', 'lecturer')
    search_fields = ('title', 'class_name')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'role', 'created_at', 'is_read')
    list_filter = ('is_read', 'role', 'created_at')
