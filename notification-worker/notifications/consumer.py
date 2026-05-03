import pika
import json
import django
import os
import time
import sys
print("STARTED")
# Indispensable : initialise Django avant d'utiliser les models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notification_worker.settings')
django.setup()

from notifications.models import Notification
from notifications.email_service import send_email
from decouple import config

def callback(ch, method, properties, body):
    print(f"\n[→] Message reçu : {body}")
    data = json.loads(body)

    email = data.get('email', '')

    try:
        if not email:
            print(f"[!] Email manquant — notification ignorée")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        send_email(
            to=email,
            type=data['type'],
            reservation_id=data.get('reservation_id', 0),
            table_id=data.get('table_id', '?'),
            date=data.get('date', '?'),
            heure=data.get('heure', '?'),
        )
        statut = 'ENVOYEE'
        print(f"[✓] Email envoyé avec succès à {email}")

    except Exception as e:
        statut = 'ECHOUEE'
        print(f"[✗] Échec envoi email : {e}")

    Notification.objects.create(
        reservation_id=data.get('reservation_id', 0),
        client_email=email,
        type=data['type'],
        statut=statut,
    )
    print(f"[✓] Notification sauvegardée en base")
    ch.basic_ack(delivery_tag=method.delivery_tag)

    
    """
    Cette fonction est appelée automatiquement
    chaque fois qu'un message arrive dans la queue
    """
    print(f"\n[→] Message reçu : {body}")
    
    # 1. Convertit le message JSON en dictionnaire Python
    data = json.loads(body)

    # 2. Essaie d'envoyer l'email
    try:
        send_email(
            to=data['email'],
            type=data['type'],
            reservation_id=data.get('reservation_id', 0),
            table_id=data.get('table_id', '?'),
            date=data.get('date', '?'),
            heure=data.get('heure', '?'),
        )
        statut = 'ENVOYEE'
        print(f"[✓] Email envoyé avec succès")

    except Exception as e:
        statut = 'ECHOUEE'
        print(f"[✗] Échec envoi email : {e}")

    # 3. Sauvegarde la notification en base de données
    Notification.objects.create(
        reservation_id=data.get('reservation_id', 0),
        client_email=data['email'],
        type=data['type'],
        statut=statut,
    )
    print(f"[✓] Notification sauvegardée en base")

    # 4. Confirme à RabbitMQ que le message est traité
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consumer():
    """
    Se connecte à RabbitMQ et écoute la queue en permanence.
    Si la connexion est perdue, réessaie toutes les 5 secondes.
    """
    while True:
        try:
            print(f"[*] Connexion à RabbitMQ ({config('RABBITMQ_HOST', default='localhost')})...")
            
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=config('RABBITMQ_HOST', default='localhost')
                )
            )
            channel = connection.channel()

            # Déclare la queue (la crée si elle n'existe pas)
            channel.queue_declare(queue='reservations_queue', durable=True)
            
            # Un message à la fois
            channel.basic_qos(prefetch_count=1)
            
            # Lie la fonction callback à la queue
            channel.basic_consume(
                queue='reservations_queue',
                on_message_callback=callback
            )

            print("[*] En attente de messages... (Ctrl+C pour arrêter)\n")
            channel.start_consuming()

        except KeyboardInterrupt:
            print("\n[!] Arrêt du consumer.")
            sys.exit(0)

        except Exception as e:
            print(f"[!] Erreur : {e}. Reconnexion dans 5 secondes...")
            time.sleep(5)


if __name__ == '__main__':
    start_consumer()