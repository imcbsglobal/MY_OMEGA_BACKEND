from rest_framework import serializers
from .models import OfferLetter
from interview_management.models import Interview
from django.utils import timezone


# ============================================================
# MAIN OFFER LETTER SERIALIZER
# ============================================================
class OfferLetterSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    candidate_email = serializers.CharField(source='candidate.email', read_only=True)
    candidate_phone = serializers.CharField(source='candidate.phone_number', read_only=True)
    candidate_cv = serializers.FileField(source='candidate.cv_file', read_only=True)
    created_by_name = serializers.CharField(source='created_by.email', read_only=True)

    class Meta:
        model = OfferLetter
        fields = [
            'id',
            'candidate',
            'candidate_name',
            'candidate_email',
            'candidate_phone',

            'position',
            'department',
            'department_id',
            'job_title_id',

            'salary',
            'basic_pay',
            'dearness_allowance',
            'house_rent_allowance',
            'special_allowance',
            'conveyance_earnings',

            'joining_data',
            'notice_period',

            'work_start_time',
            'work_end_time',

            'subject',
            'body',
            'terms_condition',
            'pdf_file',

            'candidate_cv',

            'candidate_status',
            'rejection_status',

            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'candidate_cv',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_name',
        ]

    # --------------------------------------------------------
    # Candidate validation
    # --------------------------------------------------------
    def validate_candidate(self, value):
        if self.instance and self.instance.candidate_id == value.id:
            return value

        if hasattr(value, 'interview_status') and value.interview_status != 'selected':
            raise serializers.ValidationError(
                "Offer letters can only be created for candidates with 'selected' status."
            )

        qs = OfferLetter.objects.filter(candidate=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "An offer letter already exists for this candidate."
            )

        return value

    # --------------------------------------------------------
    # Joining date validation
    # --------------------------------------------------------
    def validate_joining_data(self, value):
        if not value:
            raise serializers.ValidationError("Joining date is required.")

        if value < timezone.now().date():
            raise serializers.ValidationError(
                "Joining date must be today or a future date."
            )

        return value

    # --------------------------------------------------------
    # 🔥 SALARY VALIDATION (NO ZERO FORCING)
    # --------------------------------------------------------
    def validate(self, data):
        salary_fields = [
            'basic_pay',
            'dearness_allowance',
            'house_rent_allowance',
            'special_allowance',
            'conveyance_earnings',
        ]

        for field in salary_fields:
            value = data.get(field)
            if value in ("", None):
                data[field] = None
            else:
                try:
                    data[field] = float(value)
                except (TypeError, ValueError):
                    raise serializers.ValidationError({
                        field: "Must be a valid number"
                    })

        if data.get('salary') in ("", None):
            raise serializers.ValidationError({
                "salary": "Salary is required"
            })

        try:
            data['salary'] = float(data['salary'])
        except (TypeError, ValueError):
            raise serializers.ValidationError({
                "salary": "Salary must be a valid number"
            })

        return data


# ============================================================
# CREATE SERIALIZER (🔥 FIXED)
# ============================================================
class OfferLetterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferLetter
        fields = [
            'candidate',
            'position',
            'department',
            'department_id',
            'job_title_id',

            'salary',
            'basic_pay',
            'dearness_allowance',
            'house_rent_allowance',
            'special_allowance',
            'conveyance_earnings',

            'work_start_time',
            'work_end_time',
            'joining_data',
            'notice_period',

            'subject',
            'body',
            'terms_condition',
        ]

    def validate_candidate(self, value):
        if hasattr(value, 'interview_status') and value.interview_status != 'selected':
            raise serializers.ValidationError(
                "Offer letters can only be created for candidates with 'selected' status."
            )

        if OfferLetter.objects.filter(candidate=value).exists():
            raise serializers.ValidationError(
                "An offer letter already exists for this candidate."
            )

        return value

    # 🔥 SAME salary validation here (IMPORTANT)
    def validate(self, data):
        salary_fields = [
            'basic_pay',
            'dearness_allowance',
            'house_rent_allowance',
            'special_allowance',
            'conveyance_earnings',
        ]

        for field in salary_fields:
            value = data.get(field)
            if value in ("", None):
                data[field] = None
            else:
                try:
                    data[field] = float(value)
                except (TypeError, ValueError):
                    raise serializers.ValidationError({
                        field: "Must be a valid number"
                    })

        if data.get('salary') in ("", None):
            raise serializers.ValidationError({
                "salary": "Salary is required"
            })

        try:
            data['salary'] = float(data['salary'])
        except (TypeError, ValueError):
            raise serializers.ValidationError({
                "salary": "Salary must be a valid number"
            })

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return OfferLetter.objects.create(**validated_data)


# ============================================================
# SELECTED CANDIDATES SERIALIZER
# ============================================================
class SelectedCandidatesSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='candidate.name', read_only=True)
    email = serializers.EmailField(source='candidate.email', read_only=True)
    phone_number = serializers.CharField(source='candidate.phone_number', read_only=True)
    job_title_name = serializers.CharField(
        source='candidate.job_title.title',
        read_only=True
    )
    candidate_id = serializers.UUIDField(source='candidate.id', read_only=True)

    class Meta:
        model = Interview
        fields = [
            'id',
            'candidate_id',
            'name',
            'phone_number',
            'job_title_name',
            'status',
            'email',
        ]
