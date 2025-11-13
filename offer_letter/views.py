from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from cv_management.models import UserCvData
from .models import OfferLetter
from .serializers import (
    OfferLetterSerializer, 
    OfferLetterCreateSerializer, 
    SelectedCandidatesSerializer
)


def success_response(message, data=None, status_code=status.HTTP_200_OK):
    return Response({
        'success': True,
        'message': message,
        'data': data
    }, status=status_code)


def error_response(message, error_code='ERROR', details=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({
        'success': False,
        'message': message,
        'error': error_code,
        'details': details
    }, status=status_code)


class OfferLetterViewSet(viewsets.ModelViewSet):
    queryset = OfferLetter.objects.select_related('candidate', 'candidate__job_title', 'created_by')
    serializer_class = OfferLetterSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OfferLetterCreateSerializer
        return OfferLetterSerializer
    
    def list(self, request):
        """List all offer letters with optional filtering"""
        queryset = self.get_queryset()
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by candidate
        candidate_id = request.query_params.get('candidate')
        if candidate_id:
            queryset = queryset.filter(candidate_id=candidate_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            message=f"Found {len(serializer.data)} offer letter(s)",
            data=serializer.data
        )
    
    def create(self, request):
        """Create a new offer letter"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                offer_letter = serializer.save()
                return success_response(
                    message=f"Offer letter created successfully for {offer_letter.candidate.name}",
                    data=OfferLetterSerializer(offer_letter).data,
                    status_code=status.HTTP_201_CREATED
                )
        return error_response(
            message="Invalid data provided",
            error_code="VALIDATION_ERROR",
            details=serializer.errors
        )
    
    def retrieve(self, request, pk=None):
        """Get a specific offer letter"""
        try:
            offer_letter = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(offer_letter)
            return success_response(
                message="Offer letter retrieved successfully",
                data=serializer.data
            )
        except OfferLetter.DoesNotExist:
            return error_response(
                message="Offer letter not found",
                error_code="NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    def update(self, request, pk=None):
        """Update an offer letter"""
        try:
            offer_letter = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(offer_letter, data=request.data, partial=True)
            if serializer.is_valid():
                with transaction.atomic():
                    updated_offer = serializer.save()
                    return success_response(
                        message="Offer letter updated successfully",
                        data=OfferLetterSerializer(updated_offer).data
                    )
            return error_response(
                message="Invalid data provided",
                error_code="VALIDATION_ERROR",
                details=serializer.errors
            )
        except OfferLetter.DoesNotExist:
            return error_response(
                message="Offer letter not found",
                error_code="NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    def destroy(self, request, pk=None):
        """Delete an offer letter"""
        try:
            offer_letter = self.get_queryset().get(pk=pk)
            candidate_name = offer_letter.candidate.name
            offer_letter.delete()
            return success_response(
                message=f"Offer letter for {candidate_name} deleted successfully"
            )
        except OfferLetter.DoesNotExist:
            return error_response(
                message="Offer letter not found",
                error_code="NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def selected_candidates(self, request):
        """Get all candidates with 'selected' status available for offer letters"""
        # Get candidates with selected status who don't have offer letters yet
        candidates = UserCvData.objects.filter(
            interview_status='selected'
        ).exclude(
            offer_letter__isnull=False
        ).select_related('job_title')
        
        serializer = SelectedCandidatesSerializer(candidates, many=True)
        return success_response(
            message=f"Found {len(serializer.data)} selected candidate(s) available for offer letters",
            data=serializer.data
        )
    
    @action(detail=True, methods=['post'])
    def send_offer(self, request, pk=None):
        """Mark offer letter as sent"""
        try:
            offer_letter = self.get_queryset().get(pk=pk)
            if offer_letter.status != 'draft':
                return error_response(
                    message="Only draft offers can be sent",
                    error_code="INVALID_STATUS"
                )
            
            offer_letter.status = 'sent'
            offer_letter.sent_at = timezone.now()
            offer_letter.save()
            
            return success_response(
                message="Offer letter marked as sent",
                data=OfferLetterSerializer(offer_letter).data
            )
        except OfferLetter.DoesNotExist:
            return error_response(
                message="Offer letter not found",
                error_code="NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def accept_offer(self, request, pk=None):
        """Accept the offer letter"""
        try:
            offer_letter = self.get_queryset().get(pk=pk)
            if offer_letter.status != 'sent':
                return error_response(
                    message="Only sent offers can be accepted",
                    error_code="INVALID_STATUS"
                )
            
            offer_letter.status = 'accepted'
            offer_letter.accepted_at = timezone.now()
            offer_letter.save()
            
            return success_response(
                message="Offer letter accepted successfully",
                data=OfferLetterSerializer(offer_letter).data
            )
        except OfferLetter.DoesNotExist:
            return error_response(
                message="Offer letter not found",
                error_code="NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def reject_offer(self, request, pk=None):
        """Reject the offer letter"""
        rejection_reason = request.data.get('rejection_reason', '')
        
        try:
            offer_letter = self.get_queryset().get(pk=pk)
            if offer_letter.status != 'sent':
                return error_response(
                    message="Only sent offers can be rejected",
                    error_code="INVALID_STATUS"
                )
            
            offer_letter.status = 'rejected'
            offer_letter.rejected_at = timezone.now()
            offer_letter.rejection_reason = rejection_reason
            offer_letter.save()
            
            return success_response(
                message="Offer letter rejected",
                data=OfferLetterSerializer(offer_letter).data
            )
        except OfferLetter.DoesNotExist:
            return error_response(
                message="Offer letter not found",
                error_code="NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND
            )

