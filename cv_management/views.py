from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, NotFound
from django.db import transaction
import logging

from .models import UserCvData, JobTitle
from .serializers import UserCvDataSerializer, JobTitleSerializer

logger = logging.getLogger(__name__)


# Response Helper Functions
def success_response(message, data=None, status_code=status.HTTP_200_OK):
    """Standardized success response"""
    response = {
        "success": True,
        "message": message
    }
    if data is not None:
        response["data"] = data
    return Response(response, status=status_code)


def error_response(message, error_code, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    """Standardized error response"""
    response = {
        "success": False,
        "message": message,
        "error": error_code
    }
    if details is not None:
        response["details"] = details
    return Response(response, status=status_code)


class JobTitleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing job titles"""
    queryset = JobTitle.objects.all().order_by('-created_at')
    serializer_class = JobTitleSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """List all job titles"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            return success_response(
                message=f"Found {len(serializer.data)} job title(s)",
                data=serializer.data
            )
        except Exception as e:
            logger.error(f"Error listing job titles: {str(e)}", exc_info=True)
            return error_response(
                message="Error retrieving job titles",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """Get single job title details"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return success_response(
                message="Job title retrieved successfully",
                data=serializer.data
            )
        except NotFound:
            return error_response(
                message="Job title not found",
                error_code="NOT_FOUND",
                details="The requested job title does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving job title: {str(e)}", exc_info=True)
            return error_response(
                message="Error retrieving job title",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """Create new job title"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            logger.info(f"Job title created: {serializer.data['title']} by user {request.user.email}")
            
            return success_response(
                message="Job title created successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            logger.warning(f"Validation error creating job title: {e.detail}")
            return error_response(
                message="Invalid data provided",
                error_code="VALIDATION_ERROR",
                details=e.detail,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating job title: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to create job title",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """Update job title"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            logger.info(f"Job title updated: {serializer.data['title']} by user {request.user.email}")
            
            return success_response(
                message="Job title updated successfully",
                data=serializer.data
            )
        except NotFound:
            return error_response(
                message="Job title not found",
                error_code="NOT_FOUND",
                details="The requested job title does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            logger.warning(f"Validation error updating job title: {e.detail}")
            return error_response(
                message="Invalid data provided",
                error_code="VALIDATION_ERROR",
                details=e.detail,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error updating job title: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to update job title",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Delete job title"""
        try:
            instance = self.get_object()
            title_name = instance.title
            self.perform_destroy(instance)
            
            logger.info(f"Job title deleted: {title_name} by user {request.user.email}")
            
            return success_response(
                message="Job title deleted successfully",
                status_code=status.HTTP_200_OK
            )
        except NotFound:
            return error_response(
                message="Job title not found",
                error_code="NOT_FOUND",
                details="The requested job title does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting job title: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to delete job title",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserCvDataViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing candidate CV data
    
    Endpoints (under /api/cv-management/cvs/):
    - GET / - List all CVs
    - GET /{id}/ - Get CV details
    - POST / - Create new CV
    - PUT/PATCH /{id}/ - Update CV
    - DELETE /{id}/ - Delete CV
    """
    queryset = UserCvData.objects.select_related('job_title', 'created_by').all().order_by('-created_at')
    serializer_class = UserCvDataSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)

    def list(self, request, *args, **kwargs):
        """List all CVs with optional filtering"""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            
            # Optional filtering by interview_status
            status_filter = request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(interview_status=status_filter)
            
            serializer = self.get_serializer(queryset, many=True)
            
            return success_response(
                message=f"Found {len(serializer.data)} CV(s)",
                data=serializer.data
            )
        except Exception as e:
            logger.error(f"Error listing CVs: {str(e)}", exc_info=True)
            return error_response(
                message="Error retrieving CV data",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """Get detailed CV information"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return success_response(
                message="CV retrieved successfully",
                data=serializer.data
            )
        except NotFound:
            return error_response(
                message="CV not found",
                error_code="NOT_FOUND",
                details="The requested CV does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving CV: {str(e)}", exc_info=True)
            return error_response(
                message="Error retrieving CV",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """
        Create new CV record
        
        Request body should include:
        - name, email, phone_number (required)
        - job_title, place, district, education, experience
        - cv_file (optional)
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            with transaction.atomic():
                self.perform_create(serializer)
            
            logger.info(
                f"CV created for {serializer.data['name']} "
                f"(email: {serializer.data['email']}) by user {request.user.email}"
            )
            
            return success_response(
                message=f"CV data created successfully for {serializer.data['name']}",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            logger.warning(f"Validation error creating CV: {e.detail}")
            return error_response(
                message="Invalid data provided",
                error_code="VALIDATION_ERROR",
                details=e.detail,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating CV: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to create CV data",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """Update CV data (PUT/PATCH)"""
        try:
            instance = self.get_object()
            partial = kwargs.get('partial', False)
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            
            with transaction.atomic():
                self.perform_update(serializer)
            
            logger.info(
                f"CV updated for {serializer.data['name']} "
                f"by user {request.user.email}"
            )
            
            return success_response(
                message="CV data updated successfully",
                data=serializer.data
            )
        except NotFound:
            return error_response(
                message="CV not found",
                error_code="NOT_FOUND",
                details="The requested CV does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            logger.warning(f"Validation error updating CV: {e.detail}")
            return error_response(
                message="Invalid data provided",
                error_code="VALIDATION_ERROR",
                details=e.detail,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error updating CV: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to update CV data",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Delete CV record"""
        try:
            instance = self.get_object()
            candidate_name = instance.name
            candidate_email = instance.email
            
            with transaction.atomic():
                self.perform_destroy(instance)
            
            logger.info(
                f"CV deleted for {candidate_name} (email: {candidate_email}) "
                f"by user {request.user.email}"
            )
            
            return success_response(
                message="CV data deleted successfully",
                status_code=status.HTTP_200_OK
            )
        except NotFound:
            return error_response(
                message="CV not found",
                error_code="NOT_FOUND",
                details="The requested CV does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting CV: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to delete CV data",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
