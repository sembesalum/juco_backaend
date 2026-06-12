from django.contrib.auth import authenticate
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

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


class UserSerializer(serializers.ModelSerializer):
    programme_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "role",
            "registration_number",
            "programme",
            "programme_name",
        ]

    def get_programme_name(self, obj):
        if not obj.programme:
            return None
        return obj.programme.name


class AdminUserCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'role', 'email', 'password', 'registration_number', 'programme']

    def validate(self, attrs):
        role = attrs.get("role", getattr(self.instance, "role", None))
        programme = attrs.get("programme", getattr(self.instance, "programme", None))
        if role == User.Role.MONITOR and not programme:
            raise serializers.ValidationError(
                {"programme": "Programme is required for class representatives."}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        registration_number = validated_data.get("registration_number")
        email = validated_data.get("email")
        base_username = registration_number or email or f"user-{User.objects.count() + 1}"
        username = base_username
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base_username}-{suffix}"
        validated_data["username"] = username
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        new_registration_number = validated_data.get("registration_number")
        new_email = validated_data.get("email")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if new_registration_number or new_email:
            base_username = new_registration_number or new_email
            if base_username:
                username = base_username
                suffix = 1
                while User.objects.filter(username=username).exclude(id=instance.id).exists():
                    suffix += 1
                    username = f"{base_username}-{suffix}"
                instance.username = username
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LecturerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        # First, try to get by email. If that fails, try by username.
        user = User.objects.filter(email=email, role=User.Role.LECTURER).first()
        if not user:
            user = User.objects.filter(username=email, role=User.Role.LECTURER).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials.", code="authorization")

        attrs["user"] = user
        return attrs


class MonitorLoginSerializer(serializers.Serializer):
    registration_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        reg = attrs.get("registration_number")
        password = attrs.get("password")

        # Try to get by registration_number. If that fails, try by username.
        user = User.objects.filter(registration_number=reg, role=User.Role.MONITOR).first()
        if not user:
            user = User.objects.filter(username=reg, role=User.Role.MONITOR).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials.", code="authorization")

        attrs["user"] = user
        return attrs


class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email, role=User.Role.ADMIN)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials.", code="authorization")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials.", code="authorization")

        attrs["user"] = user
        return attrs



class AdminRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password']
        extra_kwargs = {
            'username': {'required': True},  # ← Make username required
            'email': {'required': True},
        }

    def validate_username(self, value):
        """Check if username already exists"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(role=User.Role.ADMIN, **validated_data)
        user.set_password(password)
        user.save()
        return user


class CourseSerializer(serializers.ModelSerializer):
    programme_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Course
        fields = ["id", "code", "name", "programme", "programme_name"]

    def get_programme_name(self, obj):
        if not obj.programme:
            return None
        return obj.programme.name


class SemesterSerializer(serializers.ModelSerializer):
    programme_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Semester
        fields = ["id", "name", "course", "year_of_study", "programme_name"]

    def get_programme_name(self, obj):
        programme = None
        if obj.year_of_study and obj.year_of_study.programme:
            programme = obj.year_of_study.programme
        elif obj.course and obj.course.programme:
            programme = obj.course.programme
        if not programme:
            return None
        return programme.name


class YearOfStudySerializer(serializers.ModelSerializer):
    programme_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = YearOfStudy
        fields = ["id", "name", "programme", "course", "semester", "programme_name"]

    def get_programme_name(self, obj):
        if not obj.programme:
            return None
        return obj.programme.name


class ProgrammeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Programme
        fields = ["id", "name"]


class TimetableSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.name", read_only=True)
    lecturer_name = serializers.SerializerMethodField()
    monitor_id = serializers.IntegerField(source="monitor.id", read_only=True)
    lecturer_id = serializers.IntegerField(source="lecturer.id", read_only=True)
    course_id = serializers.IntegerField(source="course.id", read_only=True)
    semester_id = serializers.IntegerField(source="semester.id", read_only=True)

    class Meta:
        model = Timetable
        fields = [
            "id",
            "subject_code",
            "subject_name",
            "course_name",
            "course_id",
            "venue",
            "day",
            "start_time",
            "end_time",
            "status",
            "color_code",
            "lecturer_id",
            "lecturer_name",
            "monitor_id",
            "semester_id",
            "cancellation_note",
        ]

    def get_lecturer_name(self, obj):
        return obj.lecturer.get_full_name() or obj.lecturer.email


class AdminMonitorWithTimetablesSerializer(serializers.ModelSerializer):
    """Admin overview: one CR (monitor) row with all timetables they created."""

    programme_name = serializers.SerializerMethodField()
    monitor_timetables = TimetableSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "registration_number",
            "programme",
            "programme_name",
            "monitor_timetables",
        ]

    def get_programme_name(self, obj):
        if not obj.programme:
            return None
        return obj.programme.name


class AdminUserDetailSerializer(serializers.ModelSerializer):
    lecturer_timetables = TimetableSerializer(many=True, read_only=True)
    monitor_timetables = TimetableSerializer(many=True, read_only=True)
    tasks = serializers.SerializerMethodField()
    programme_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "role",
            "registration_number",
            "programme",
            "programme_name",
            "lecturer_timetables",
            "monitor_timetables",
            "tasks",
        ]

    def get_tasks(self, obj):
        qs = getattr(obj, "tasks", None)
        if qs is None:
            return []
        return SimpleTaskListSerializer(qs.all(), many=True).data

    def get_programme_name(self, obj):
        if not obj.programme:
            return None
        return obj.programme.name


class TimetableCreateSerializer(serializers.Serializer):
    monitor_id = serializers.IntegerField()
    lecturer_id = serializers.IntegerField()
    course_id = serializers.IntegerField()
    semester_id = serializers.IntegerField()
    subject_code = serializers.CharField()
    subject_name = serializers.CharField()
    venue = serializers.CharField()
    days = serializers.ListField(child=serializers.CharField())
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    color_code = serializers.CharField()


class TimetableStatusUpdateSerializer(serializers.ModelSerializer):
    lecturer_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Timetable
        fields = ["status", "lecturer_id", "cancellation_note"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "lecturer",
            "monitor",
            "title",
            "type",
            "class_group",
            "class_name",
            "scheduled_at",
            "notes",
            "send_to_crs",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["lecturer", "created_at", "updated_at"]


class SimpleTaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["id", "title", "type", "class_name", "scheduled_at", "send_to_crs"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "created_at",
            "is_read",
            "related_type",
            "related_id",
        ]


class NotificationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["is_read"]


class MonitorProgrammeUpdateSerializer(serializers.Serializer):
    programme_id = serializers.IntegerField(required=False, allow_null=True)


class MonitorSemesterCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=64)


class MonitorYearOfStudyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=64)
    semester_id = serializers.IntegerField()

