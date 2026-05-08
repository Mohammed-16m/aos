from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Table
from .serializers import TableSerializer
import requests as http_requests
from decouple import config


import jwt


def valider_token_admin(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ', 1)[1]
    
    # Essai 1 — appel auth_service
    try:
        res = http_requests.get(
            'http://auth_service:8081/auth/validate',
            headers={'Authorization': auth_header},
            timeout=3
        )
        if res.status_code == 200:
            return res.json().get('data', {})
    except Exception:
        pass

    # Essai 2 — décodage local du JWT (fallback)
    try:
        secret = config('JWT_SECRET_KEY', default='secret-auth')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return {
            'user_id': payload.get('user_id'),
            'role':    payload.get('role'),
            'email':   payload.get('email'),
        }
    except Exception:
        pass

    return None


def get_prochain_numero():
    derniere = Table.objects.order_by('-id').first()

    if derniere and derniere.numero:
        dernier_num = int(derniere.numero.replace('T', ''))
        return f"T{dernier_num + 1}"

    return "T1"

# ─── GET toutes les tables / POST ajouter ───
@api_view(['GET', 'POST'])
def liste_tables(request):
    if request.method == 'GET':
        tables = Table.objects.all()
        serializer = TableSerializer(tables, many=True)
        return Response({'status': 'success', 'data': serializer.data})

    # POST — ADMIN uniquement
    

    # Numéro auto-incrémenté — pas besoin de le fournir
    data = request.data.copy()
    data['numero'] = get_prochain_numero()

    serializer = TableSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({'status': 'success', 'data': serializer.data}, status=201)
    print(serializer.errors)
    return Response({'status': 'error', 'errors': serializer.errors}, status=400)


# ─── GET détail / PUT modifier / DELETE supprimer ───
@api_view(['GET', 'PUT', 'DELETE'])
def detail_modifier_supprimer(request, id):
    try:
        table = Table.objects.get(id=id)
    except Table.DoesNotExist:
        return Response({'status': 'error', 'message': 'Table non trouvée'}, status=404)

    if request.method == 'GET':
        return Response({'status': 'success', 'data': TableSerializer(table).data})


    if request.method == 'PUT':
        # Numéro non modifiable — on garde l'ancien
        data = request.data.copy()
        data['numero'] = table.numero

        serializer = TableSerializer(table, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'data': serializer.data})
        return Response({'status': 'error', 'errors': serializer.errors}, status=400)

    if request.method == 'DELETE':
        table.delete()
        return Response({'status': 'success', 'message': 'Table supprimée avec succès'})


# ─── GET tables disponibles ───
@api_view(['GET'])
def tables_disponibles(request):
    date         = request.query_params.get('date')
    heure        = request.query_params.get('heure')
    nb_personnes = request.query_params.get('nb_personnes', 1)

    if not date or not heure:
        return Response({'status': 'error', 'message': 'Paramètres date et heure obligatoires'}, status=400)

    tables = Table.objects.filter(statut='disponible', capacite__gte=int(nb_personnes))
    return Response({'status': 'success', 'data': TableSerializer(tables, many=True).data})


# ─── Pages HTML ───
def page_accueil(request):
    return render(request, 'tables/accueil.html')

def page_admin_tables(request):
    return render(request, 'tables/admin_table.html')

def page_detail_table(request, id):
    return render(request, 'tables/detail_table.html', {'table_id': id})