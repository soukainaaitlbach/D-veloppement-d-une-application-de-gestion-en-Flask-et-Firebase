

from flask import Flask, request, jsonify
from flask_cors import CORS
from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime

# Configuration Firebase
cred = credentials.Certificate("/content/miniprojet-4bd26-firebase-adminsdk-fbsvc-c376d81eee.json")
initialize_app(cred)
db = firestore.client()

app = Flask(__name__)
CORS(app)

# Modèles de données
class Sport:
    def __init__(self, name, description, max_participants):
        self.name = name
        self.description = description
        self.max_participants = max_participants

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "max_participants": self.max_participants,
            "created_at": datetime.now().isoformat()
        }

class Participant:
    def __init__(self, name, email, phone):
        self.name = name
        self.email = email
        self.phone = phone

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "created_at": datetime.now().isoformat()
        }

# Routes pour Sports
@app.route('/api/sports', methods=['POST'])
def create_sport():
    try:
        data = request.json
        sport = Sport(
            name=data['name'],
            description=data['description'],
            max_participants=data['max_participants']
        )
        db.collection('sports').add(sport.to_dict())
        return jsonify({"message": "Sport créé avec succès"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/sports', methods=['GET'])
def get_sports():
    try:
        sports_ref = db.collection('sports').stream()
        sports = [{doc.id: doc.to_dict()} for doc in sports_ref]
        return jsonify(sports), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sports/<sport_id>', methods=['GET'])
def get_sport(sport_id):
    try:
        sport_doc = db.collection('sports').document(sport_id).get()
        if sport_doc.exists:
            return jsonify({sport_id: sport_doc.to_dict()}), 200
        return jsonify({"error": "Sport non trouvé"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route pour les inscriptions avec validation
@app.route('/api/inscriptions', methods=['POST'])
def create_inscription():
    try:
        data = request.json

        # Vérification de l'existence de l'événement et du participant
        event_ref = db.collection('events').document(data['event_id']).get()
        participant_ref = db.collection('participants').document(data['participant_id']).get()

        if not event_ref.exists:
            return jsonify({"error": "Événement non trouvé"}), 404
        if not participant_ref.exists:
            return jsonify({"error": "Participant non trouvé"}), 404

        # Vérification du nombre maximum de participants
        inscriptions_count = len(list(db.collection('inscriptions')
            .where('event_id', '==', data['event_id'])
            .stream()))

        event_data = event_ref.to_dict()
        if inscriptions_count >= event_data.get('max_participants', 0):
            return jsonify({"error": "Événement complet"}), 400

        # Création de l'inscription
        inscription_data = {
            "event_id": data['event_id'],
            "participant_id": data['participant_id'],
            "created_at": datetime.now().isoformat(),
            "status": "confirmed"
        }

        db.collection('inscriptions').add(inscription_data)
        return jsonify({"message": "Inscription créée avec succès"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001)
