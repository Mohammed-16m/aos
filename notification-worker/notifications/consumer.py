import pika
import json
import django
import os
import time
import sys

print("STARTED")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notification_worker.settings')
django.setup()

from notifications.models import Notification
from notifications.email_service import send_email
from decouple import config


def callback(ch, method, properties, body):
    print(f"\n[→] Message reçu : {body}")

    data = json.loads(body)
    email = data.get('email', '')

    # Si pas d'email → on ack quand même pour vider la queue
    if not email:
        print(f"[!] Email manquant — notification ignorée (message supprimé de la queue)")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    statut = 'ECHOUEE'
    try:
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
        print(f"[✗] Échec envoi email : {e}")

    # Sauvegarde en base
    try:
        Notification.objects.create(
            reservation_id=data.get('reservation_id', 0),
            client_email=email,
            type=data['type'],
            statut=statut,
        )
        print(f"[✓] Notification sauvegardée en base")
    except Exception as e:
        print(f"[✗] Erreur sauvegarde BDD : {e}")

    # Confirme à RabbitMQ que le message est traité
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consumer():
    while True:
        try:
            rabbitmq_host = config('RABBITMQ_HOST', default='localhost')
            print(f"[*] Connexion à RabbitMQ ({rabbitmq_host})...")

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbitmq_host)
            )
            channel = connection.channel()
            channel.queue_declare(queue='reservations_queue', durable=True)
            channel.basic_qos(prefetch_count=1)
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