from rest_framework import serializers
from .models import Reservation
from datetime import date

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']  # ← statut retiré


class ReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['client_id', 'table_id', 'date', 'heure', 'nb_personnes']

    def validate(self, data):
        if data['date'] < date.today():
            raise serializers.ValidationError("La date ne peut pas être dans le passé.")
        if data['nb_personnes'] < 1:
            raise serializers.ValidationError("Le nombre de personnes doit être au moins 1.")
        return data