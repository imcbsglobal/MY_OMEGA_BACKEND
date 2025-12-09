from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, NotFound
from django.db import transaction
from django.shortcuts import get_object_or_404
import logging

from .models import Interview, InterviewEvaluation
from cv_management.models import UserCvData
from .serializers import (
    UserCvDropSerializer,
    StartInterviewSerializer,
    InterviewTableSerializer,
    OngoingInterviewSerializer,
    InterviewEvaluationSerializer,
    InterviewStatusUpdateSerializer,
    InterviewDetailSerializer
)

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


class InterviewManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing interviews

    Endpoints (under /api/interview-management/):
    - GET /cvs-for-interview/ - Get all CVs available for interview (dropdown)
    - POST /start-interview/ - Start interview (change CV status to ongoing and add CV details to Interview table)
    - GET / - List all interviews
    - GET /ongoing-interviews/ - List only ongoing interviews (with complete CV data)
    - GET /{id}/ - Get interview details
    - PATCH /{id}/update-status/ - Update interview status
    - POST/PUT/PATCH /{id}/evaluation/ - Create/Update evaluation
    - DELETE /{id}/ - Delete interview
    """
    queryset = Interview.objects.select_related(
        'candidate', 'candidate__job_title', 'interviewer'
    ).prefetch_related('evaluation').all()
    permission_classes = [IsAuthenticated]
    serializer_class = InterviewTableSerializer

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'cvs_for_interview':
            return UserCvDropSerializer
        elif self.action == 'ongoing_interviews':
            return OngoingInterviewSerializer
        elif self.action == 'retrieve':
            return InterviewDetailSerializer
        return InterviewTableSerializer

    @action(detail=False, methods=['get'], url_path='cvs-for-interview')
    def cvs_for_interview(self, request):
        """
        Get all CVs available for interview selection (dropdown data)
        Returns CVs with status 'selected' that don't have an active interview
        """
        try:
            # Get CVs with 'selected' status that haven't been added to interview yet
            # OR have been added but interview was deleted/completed
            selected_cvs = UserCvData.objects.filter(
                interview_status='selected'
            ).select_related('job_title')
            
            # Exclude CVs that already have an active (non-completed) interview
            active_interview_cv_ids = Interview.objects.filter(
                status__in=['pending', 'ongoing']
            ).values_list('candidate_id', flat=True)
            
            available_cvs = selected_cvs.exclude(id__in=active_interview_cv_ids)
            
            serializer = self.get_serializer(available_cvs, many=True)
            
            return success_response(
                message=f"Found {len(serializer.data)} CV(s) available for interview",
                data=serializer.data
            )
        except Exception as e:
            logger.error(f"Error fetching CVs for interview: {str(e)}", exc_info=True)
            return error_response(
                message="Error retrieving CV data",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='start-interview')
    def start_interview(self, request):
        """
        Start an interview - Select a user from CV data and change status to ongoing
        
        Request body:
        {
            "candidate_id": "uuid",
            "scheduled_at": "2025-11-15T10:00:00Z",
            "interviewer_id": 1  // optional
        }
        """
        try:
            serializer = StartInterviewSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            candidate_id = serializer.validated_data['candidate_id']
            scheduled_at = serializer.validated_data['scheduled_at']
            interviewer_id = serializer.validated_data.get('interviewer_id')

            with transaction.atomic():
                # Get the candidate
                candidate = UserCvData.objects.select_for_update().get(id=candidate_id)
                
                # Verify candidate is in 'selected' status
                if candidate.interview_status != 'selected':
                    return error_response(
                        message=f"Cannot start interview. Candidate status is '{candidate.interview_status}'",
                        error_code="INVALID_STATUS",
                        details="Only candidates with 'selected' status can be added to interviews",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                # Change CV status to ongoing (now in interview process)
                candidate.interview_status = 'ongoing'
                candidate.save()

                # Create interview record
                interview = Interview.objects.create(
                    candidate=candidate,
                    scheduled_at=scheduled_at,
                    interviewer_id=interviewer_id,
                    status='pending'
                )

                # Create empty evaluation record
                InterviewEvaluation.objects.create(interview=interview)

                logger.info(
                    f"Interview started for candidate {candidate.name} (ID: {candidate_id}) "
                    f"by user {request.user.email}"
                )

                # Return full interview details
                response_serializer = InterviewDetailSerializer(interview)
                return success_response(
                    message=f"Interview started successfully for {candidate.name}",
                    data=response_serializer.data,
                    status_code=status.HTTP_201_CREATED
                )

        except UserCvData.DoesNotExist:
            return error_response(
                message="Candidate not found",
                error_code="NOT_FOUND",
                details=f"No candidate found with the provided ID",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            logger.warning(f"Validation error starting interview: {e.detail}")
            return error_response(
                message="Invalid data provided",
                error_code="VALIDATION_ERROR",
                details=e.detail,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error starting interview: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to start interview",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request, *args, **kwargs):
        """List all interviews"""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            
            return success_response(
                message=f"Found {len(serializer.data)} interview(s)",
                data=serializer.data
            )
        except Exception as e:
            logger.error(f"Error listing interviews: {str(e)}", exc_info=True)
            return error_response(
                message="Error retrieving interviews",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='ongoing-interviews')
    def ongoing_interviews(self, request):
        """
        Get all interviews with ongoing status
        Shows only interviews where CV status is 'ongoing'
        Returns complete CV data including CV file URLs and all candidate details
        """
        try:
            # Get CVs with ongoing status
            ongoing_cvs = UserCvData.objects.filter(interview_status='ongoing')
            
            if not ongoing_cvs.exists():
                return success_response(
                    message="No ongoing interviews found",
                    data=[]
                )
            
            # Get interviews for ongoing CVs
            ongoing_interviews = self.get_queryset().filter(
                candidate__in=ongoing_cvs
            ).order_by('-scheduled_at')
            serializer = self.get_serializer(ongoing_interviews, many=True)
            
            return success_response(
                message=f"Found {len(serializer.data)} ongoing interview(s)",
                data=serializer.data
            )
        except Exception as e:
            logger.error(f"Error fetching ongoing interviews: {str(e)}", exc_info=True)
            return error_response(
                message="Error retrieving ongoing interviews",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """Get detailed interview information"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            return success_response(
                message="Interview retrieved successfully",
                data=serializer.data
            )
        except NotFound:
            return error_response(
                message="Interview not found",
                error_code="NOT_FOUND",
                details="The requested interview does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving interview: {str(e)}", exc_info=True)
            return error_response(
                message="Error retrieving interview",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        Update interview status (selected/rejected/pending) and sync with CV status
        
        Request body:
        {
            "status": "selected" | "rejected" | "pending",
            "remark": "optional remark"
        }
        """
        try:
            interview = self.get_object()
            serializer = InterviewStatusUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            new_status = serializer.validated_data['status']
            remark = serializer.validated_data.get('remark', '')

            with transaction.atomic():
                # Update interview status
                old_status = interview.status
                interview.status = new_status
                interview.save()

                # Update CV status accordingly
                candidate = interview.candidate
                candidate.interview_status = new_status
                if remark:
                    candidate.remarks = remark
                candidate.save()

                logger.info(
                    f"Interview status updated from '{old_status}' to '{new_status}' "
                    f"for candidate {candidate.name} by user {request.user.email}"
                )

                response_serializer = InterviewDetailSerializer(interview)
                return success_response(
                    message=f"Interview status updated to '{new_status}' successfully",
                    data=response_serializer.data
                )

        except NotFound:
            return error_response(
                message="Interview not found",
                error_code="NOT_FOUND",
                details="The requested interview does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            logger.warning(f"Validation error updating status: {e.detail}")
            return error_response(
                message="Invalid data provided",
                error_code="VALIDATION_ERROR",
                details=e.detail,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error updating interview status: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to update status",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post', 'put', 'patch'], url_path='evaluation')
    def evaluation(self, request, pk=None):
        """
        Create or update interview evaluation
        
        Request body:
        {
            "appearance": 8,
            "knowledge": 9,
            "confidence": 7,
            "attitude": 8,
            "communication": 9,
            "languages": "English, Malayalam",
            "expected_salary": "50000.00",
            "experience": "5 years experience",
            "remark": "Good candidate",
            "voice_note": <file>  // optional
        }
        """
        try:
            interview = self.get_object()
            
            # Get or create evaluation
            try:
                eval_instance = interview.evaluation
                # Update existing evaluation
                serializer = InterviewEvaluationSerializer(
                    eval_instance, 
                    data=request.data, 
                    partial=True
                )
                action_message = "updated"
            except InterviewEvaluation.DoesNotExist:
                # Create new evaluation
                serializer = InterviewEvaluationSerializer(data=request.data)
                action_message = "created"

            serializer.is_valid(raise_exception=True)
            
            if action_message == "created":
                eval_instance = serializer.save(interview=interview)
            else:
                eval_instance = serializer.save()

            logger.info(
                f"Interview evaluation {action_message} for candidate "
                f"{interview.candidate.name} by user {request.user.email}"
            )

            return success_response(
                message=f"Interview evaluation {action_message} successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED if action_message == "created" else status.HTTP_200_OK
            )

        except NotFound:
            return error_response(
                message="Interview not found",
                error_code="NOT_FOUND",
                details="The requested interview does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            logger.warning(f"Validation error in evaluation: {e.detail}")
            return error_response(
                message="Invalid evaluation data",
                error_code="VALIDATION_ERROR",
                details=e.detail,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error managing evaluation: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to save evaluation",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Delete an interview and reset CV status if ongoing"""
        try:
            interview = self.get_object()
            candidate_name = interview.candidate.name
            
            with transaction.atomic():
                # Reset CV status back to 'selected' if it's ongoing
                if interview.candidate.interview_status == 'ongoing':
                    interview.candidate.interview_status = 'selected'
                    interview.candidate.save()
                
                self.perform_destroy(interview)
            
            logger.info(f"Interview deleted for candidate {candidate_name} by user {request.user.email}")
            
            return success_response(
                message="Interview deleted successfully. Candidate status reset to 'selected'.",
                status_code=status.HTTP_200_OK
            )

        except NotFound:
            return error_response(
                message="Interview not found",
                error_code="NOT_FOUND",
                details="The requested interview does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting interview: {str(e)}", exc_info=True)
            return error_response(
                message="Failed to delete interview",
                error_code="INTERNAL_ERROR",
                details="Please try again later",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )