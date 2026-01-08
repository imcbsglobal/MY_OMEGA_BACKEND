from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from interview_management.models import Interview
from .models import OfferLetter
from .serializers import (
    OfferLetterSerializer,
    SelectedCandidatesSerializer
)


# --------------------------------------------------
# Common response helpers
# --------------------------------------------------
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


# --------------------------------------------------
# LIST + CREATE OFFER LETTER
# --------------------------------------------------
@api_view(['GET', 'POST'])
def offer_letter_list_create(request):
    if request.method == 'GET':
        queryset = OfferLetter.objects.select_related(
            'candidate', 'candidate__job_title', 'created_by'
        )
        serializer = OfferLetterSerializer(queryset, many=True)
        return success_response("Offer letters fetched", serializer.data)

    elif request.method == 'POST':
        print("\n" + "=" * 80)
        print("VIEW: RECEIVED POST REQUEST TO CREATE OFFER LETTER")
        print("=" * 80)
        print("Request data received:")
        print(f"  candidate: {request.data.get('candidate')}")
        print(f"  basic_pay: {request.data.get('basic_pay')}")
        print(f"  dearness_allowance: {request.data.get('dearness_allowance')}")
        print(f"  house_rent_allowance: {request.data.get('house_rent_allowance')}")
        print(f"  special_allowance: {request.data.get('special_allowance')}")
        print(f"  conveyance_earnings: {request.data.get('conveyance_earnings')}")
        print(f"  salary: {request.data.get('salary')}")
        print("=" * 80)

        # Prevent duplicate offer letters for same candidate
        candidate_id = request.data.get('candidate')
        if candidate_id:
            if OfferLetter.objects.filter(candidate_id=candidate_id).exists():
                return Response({
                    "candidate": [
                        "An offer letter already exists for this candidate. Please edit the existing one."
                    ]
                }, status=status.HTTP_400_BAD_REQUEST)

        serializer = OfferLetterSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            print("\n✅ Serializer validation PASSED")
            offer = serializer.save(created_by=request.user)

            print("\n" + "=" * 80)
            print("VIEW: OFFER LETTER CREATED SUCCESSFULLY")
            print("=" * 80)
            print(f"Offer ID: {offer.id}")
            print(f"  basic_pay: {offer.basic_pay}")
            print(f"  dearness_allowance: {offer.dearness_allowance}")
            print(f"  house_rent_allowance: {offer.house_rent_allowance}")
            print(f"  special_allowance: {offer.special_allowance}")
            print(f"  conveyance_earnings: {offer.conveyance_earnings}")
            print(f"  salary: {offer.salary}")
            print("=" * 80 + "\n")

            return success_response(
                "Offer letter created successfully",
                OfferLetterSerializer(offer).data,
                status.HTTP_201_CREATED
            )

        print("\n❌ Serializer validation FAILED")
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --------------------------------------------------
# GET / UPDATE / DELETE OFFER LETTER
# --------------------------------------------------
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def offer_letter_detail(request, pk):
    try:
        offer = OfferLetter.objects.select_related(
            'candidate', 'candidate__job_title', 'created_by'
        ).get(pk=pk)
    except OfferLetter.DoesNotExist:
        return error_response("Offer letter not found", status_code=404)

    if request.method == 'GET':
        serializer_data = OfferLetterSerializer(offer).data

        print("\n" + "=" * 80)
        print(f"VIEW: GET REQUEST FOR OFFER LETTER ID {pk}")
        print("=" * 80)
        print("Database values:")
        print(f"  basic_pay: {offer.basic_pay}")
        print(f"  dearness_allowance: {offer.dearness_allowance}")
        print(f"  house_rent_allowance: {offer.house_rent_allowance}")
        print(f"  special_allowance: {offer.special_allowance}")
        print(f"  conveyance_earnings: {offer.conveyance_earnings}")
        print(f"  salary: {offer.salary}")
        print("=" * 80 + "\n")

        return success_response("Offer letter fetched", serializer_data)

    elif request.method in ['PUT', 'PATCH']:
        print("\n" + "=" * 80)
        print(f"VIEW: {request.method} REQUEST FOR OFFER LETTER ID {pk}")
        print("=" * 80)
        print("Incoming update data:")
        print(f"  basic_pay: {request.data.get('basic_pay')}")
        print(f"  dearness_allowance: {request.data.get('dearness_allowance')}")
        print(f"  house_rent_allowance: {request.data.get('house_rent_allowance')}")
        print(f"  special_allowance: {request.data.get('special_allowance')}")
        print(f"  conveyance_earnings: {request.data.get('conveyance_earnings')}")
        print(f"  salary: {request.data.get('salary')}")
        print("=" * 80)

        serializer = OfferLetterSerializer(
            offer,
            data=request.data,
            partial=(request.method == 'PATCH'),
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            offer.refresh_from_db()

            print("\n✅ OFFER LETTER UPDATED")
            print(f"  salary: {offer.salary}")
            print("=" * 80 + "\n")

            return success_response(
                "Offer letter updated successfully",
                serializer.data
            )

        print("\n❌ Serializer validation FAILED")
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        offer.delete()
        return success_response("Offer letter deleted")


# --------------------------------------------------
# SELECTED CANDIDATES
# --------------------------------------------------
@api_view(['GET'])
def selected_candidates_list(request):
    candidates = Interview.objects.filter(status='selected')
    serializer = SelectedCandidatesSerializer(candidates, many=True)
    return success_response(
        f"Found {len(serializer.data)} selected candidate(s)",
        serializer.data
    )


# --------------------------------------------------
# OFFER STATUS ACTIONS
# --------------------------------------------------
@api_view(['POST'])
def send_offer(request, pk):
    try:
        offer = OfferLetter.objects.get(pk=pk)
    except OfferLetter.DoesNotExist:
        return error_response("Offer letter not found", status_code=404)

    if offer.candidate_status != 'draft':
        return error_response("Only draft offers can be sent")

    offer.candidate_status = 'sent'
    offer.save()

    return success_response(
        "Offer letter marked as sent",
        OfferLetterSerializer(offer).data
    )


@api_view(['POST'])
def accept_offer(request, pk):
    try:
        offer = OfferLetter.objects.get(pk=pk)
    except OfferLetter.DoesNotExist:
        return error_response("Offer letter not found", status_code=404)

    if offer.candidate_status != 'sent':
        return error_response("Only sent offers can be accepted")

    offer.candidate_status = 'willing'
    offer.save()

    return success_response(
        "Offer letter accepted successfully",
        OfferLetterSerializer(offer).data
    )


@api_view(['POST'])
def reject_offer(request, pk):
    try:
        offer = OfferLetter.objects.get(pk=pk)
    except OfferLetter.DoesNotExist:
        return error_response("Offer letter not found", status_code=404)

    if offer.candidate_status != 'sent':
        return error_response("Only sent offers can be rejected")

    offer.candidate_status = 'not_willing'
    offer.rejection_status = request.data.get('rejection_status', '')
    offer.save()

    return success_response(
        "Offer letter rejected",
        OfferLetterSerializer(offer).data
    )
