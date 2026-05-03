import jwt
import requests as http_requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decouple import config
from .models import Reservation
from .serializers import ReservationSerializer, ReservationCreateSerializer
from .rabbitmq_publisher import publier_message


def valider_token(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ', 1)[1]
    try:
        secret = config('JWT_SECRET_KEY', default='secret-auth')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verifier_conflit(table_id, date, heure, exclude_id=None):
    qs = Reservation.objects.filter(
        table_id=table_id,
        date=date,
        heure=heure,
        statut__in=['EN_ATTENTE', 'CONFIRMEE']
    )
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    return qs.exists()


def get_client_email(request):
    # Extraire l'email directement du token JWT (plus fiable)
    try:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            secret = config('JWT_SECRET_KEY', default='secret-auth')
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            email = payload.get('email', '')
            if email:
                return email
    except Exception:
        pass

    # Fallback : appeler auth_service
    try:
        token_header = request.headers.get('Authorization', '')
        res = http_requests.get(
            'http://auth_service:8081/auth/me',
            headers={'Authorization': token_header},
            timeout=3
        )
        if res.status_code == 200:
            return res.json().get('data', {}).get('email', '')
    except Exception:
        pass

    return ''


class CreerReservationView(APIView):
    def post(self, request):
        user = valider_token(request)
        if not user:
            return Response(
                {'status': 'error', 'message': 'Non autorisé'},
                status=401
            )

        serializer = ReservationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'data': serializer.errors},
                status=400
            )

        data = serializer.validated_data

        if verifier_conflit(data['table_id'], data['date'], data['heure']):
            return Response(
                {'status': 'error', 'message': 'Cette table est déjà réservée pour ce créneau.'},
                status=409
            )

        reservation = Reservation.objects.create(**data, statut='CONFIRMEE')

        # Récupérer l'email du client
        email = get_client_email(request)

        publier_message({
            'type': 'CONFIRMATION',
            'client_id': reservation.client_id,
            'table_id': reservation.table_id,
            'date': str(reservation.date),
            'heure': str(reservation.heure),
            'reservation_id': reservation.id,
            'email': email
        })

        return Response(
            {'status': 'success', 'data': ReservationSerializer(reservation).data},
            status=201
        )


class DetailReservationView(APIView):
    def get(self, request, id):
        user = valider_token(request)
        if not user:
            return Response(
                {'status': 'error', 'message': 'Non autorisé'},
                status=401
            )
        try:
            reservation = Reservation.objects.get(id=id)
        except Reservation.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Réservation introuvable'},
                status=404
            )
        return Response(
            {'status': 'success', 'data': ReservationSerializer(reservation).data}
        )

    def put(self, request, id):
        user = valider_token(request)
        if not user:
            return Response(
                {'status': 'error', 'message': 'Non autorisé'},
                status=401
            )
        try:
            reservation = Reservation.objects.get(id=id)
        except Reservation.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Réservation introuvable'},
                status=404
            )

        if reservation.statut == 'ANNULEE':
            return Response(
                {'status': 'error', 'message': 'Impossible de modifier une réservation annulée'},
                status=400
            )

        nouvelle_date  = request.data.get('date', reservation.date)
        nouvelle_heure = request.data.get('heure', reservation.heure)
        nouveau_table  = request.data.get('table_id', reservation.table_id)

        if verifier_conflit(nouveau_table, nouvelle_date, nouvelle_heure, exclude_id=id):
            return Response(
                {'status': 'error', 'message': 'Créneau indisponible'},
                status=409
            )

        serializer = ReservationSerializer(reservation, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data})
        return Response(
            {'status': 'error', 'data': serializer.errors},
            status=400
        )

    def delete(self, request, id):
        user = valider_token(request)
        if not user:
            return Response(
                {'status': 'error', 'message': 'Non autorisé'},
                status=401
            )
        try:
            reservation = Reservation.objects.get(id=id)
        except Reservation.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'Réservation introuvable'},
                status=404
            )

        reservation.statut = 'ANNULEE'
        reservation.save()

        # Récupérer l'email du client
        email = get_client_email(request)

        publier_message({
            'type': 'ANNULATION',
            'client_id': reservation.client_id,
            'table_id': reservation.table_id,
            'date': str(reservation.date),
            'heure': str(reservation.heure),
            'reservation_id': reservation.id,
            'email': email
        })

        return Response(
            {'status': 'success', 'message': 'Réservation annulée'}
        )


class ReservationsClientView(APIView):
    def get(self, request, clientId):
        user = valider_token(request)
        if not user:
            return Response(
                {'status': 'error', 'message': 'Non autorisé'},
                status=401
            )
        reservations = Reservation.objects.filter(client_id=clientId)
        return Response(
            {'status': 'success', 'data': ReservationSerializer(reservations, many=True).data}
        )


class ReservationsTableView(APIView):
    def get(self, request, tableId):
        date  = request.query_params.get('date')
        heure = request.query_params.get('heure')
        qs = Reservation.objects.filter(
            table_id=tableId,
            statut__in=['EN_ATTENTE', 'CONFIRMEE']
        )
        if date:
            qs = qs.filter(date=date)
        if heure:
            qs = qs.filter(heure=heure)
        return Response(
            {'status': 'success', 'data': ReservationSerializer(qs, many=True).data}
        )


class ToutesReservationsView(APIView):
    def get(self, request):
        user = valider_token(request)
        if not user or user.get('role') != 'ADMIN':
            return Response(
                {'status': 'error', 'message': 'Accès refusé'},
                status=403
            )
        reservations = Reservation.objects.all()
        date_filtre   = request.query_params.get('date')
        statut_filtre = request.query_params.get('statut')
        if date_filtre:
            reservations = reservations.filter(date=date_filtre)
        if statut_filtre:
            reservations = reservations.filter(statut=statut_filtre)
        return Response(
            {'status': 'success', 'data': ReservationSerializer(reservations, many=True).data}
        )