import os
import json
import requests
from flask import Flask, render_template, jsonify, request
from functools import lru_cache
import numpy as np

app = Flask(__name__)

# Configuration from environment variables
OPENAI_API_URL = os.getenv('OPENAI_API_URL', 'https://api.openai.com/v1')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.75'))

# Sample hotel data with parameters
HOTEL_DATA = {
    "hotel_1": {
        "name": "Гранд Отель Москва",
        "description": "Роскошный пятизвездочный отель в центре Москвы с видом на Кремль. Предлагает просторные номера с премиальной мебелью, ресторан высокой кухни, спа-центр и бассейн.",
        "features": ["5 звезд", "Бассейн", "Спа", "Ресторан", "Вид на Кремль", "Центр города"]
    },
    "hotel_2": {
        "name": "Эконом Хостел Петербург",
        "description": "Бюджетный хостел с общими номерами, расположенный недалеко от метро. Базовые удобства, общая кухня, Wi-Fi.",
        "features": ["Бюджетный", "Общие номера", "Рядом с метро", "Wi-Fi", "Общая кухня"]
    },
    "hotel_3": {
        "name": "Бизнес Отель Сити",
        "description": "Комфортабельный трехзвездочный отель для деловых путешественников. Конференц-залы, быстрый Wi-Fi, завтрак включен.",
        "features": ["3 звезды", "Для бизнеса", "Конференц-залы", "Завтрак включен", "Быстрый Wi-Fi"]
    }
}

# Sample reviews dataset
REVIEWS_DATASET = {
    "hotel_1": [
        "Потрясающий отель! Шикарные номера, великолепный вид на Кремль. Персонал очень внимательный. Ресторан на высшем уровне, спа-процедуры превосходные.",
        "Люксовый отель с отличным расположением. Бассейн чистый, спа замечательное. Номера просторные и роскошные. Полностью оправдывает свои 5 звезд.",
        "Прекрасное место для отдыха! Все на высшем уровне - от номеров до обслуживания. Вид из окна потрясающий, завтраки отличные."
    ],
    "hotel_2": [
        "Недорогой хостел с базовыми удобствами. Чисто, но очень шумно в общих номерах. Метро рядом, что удобно. За свои деньги нормально.",
        "Бюджетный вариант для ночлега. Кровати удобные, есть кухня. Интернет работает хорошо. Не ждите роскоши, но для экономных туристов подойдет.",
        "Простой хостел, все минимально. Чисто, есть Wi-Fi и общая кухня. Хорошее расположение возле метро. Цена соответствует качеству."
    ],
    "hotel_3": [
        "Отличный отель для командировки. Хороший интернет, есть где провести встречу. Завтраки включены, номера чистые и комфортные.",
        "Удобно для деловых поездок. Конференц-залы оборудованы всем необходимым. Персонал профессиональный, Wi-Fi быстрый. Рекомендую для бизнеса.",
        "Комфортный отель для работы. Номера спокойные, есть рабочее место. Завтраки хорошие, интернет стабильный. Для деловых целей идеально."
    ]
}

# Anomalous reviews for testing (reviews that don't match hotel parameters)
ANOMALOUS_REVIEWS = {
    "hotel_1": [
        "Очень дешево, но шумно. Общие номера не очень чистые. Для бюджетного варианта сойдет.",  # Budget review for luxury hotel
    ],
    "hotel_2": [
        "Роскошные апартаменты, бассейн чистейший, персонал безупречен. Великолепный спа-центр!",  # Luxury review for budget hostel
    ],
    "hotel_3": [
        "Пляжный отдых удался! Море рядом, песочек чистый, коктейли у бассейна весь день.",  # Beach resort review for business hotel
    ]
}


def get_embedding(text):
    """
    Get embedding vector for text using OpenAI API
    """
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'input': text,
        'model': EMBEDDING_MODEL,
        'encoding_format': 'float'
    }
    
    try:
        response = requests.post(
            f'{OPENAI_API_URL}/embeddings',
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result['data'][0]['embedding']
    except Exception as e:
        app.logger.error(f"Error getting embedding: {e}")
        raise


@lru_cache(maxsize=100)
def get_cached_embedding(text):
    """Cached version of get_embedding to avoid redundant API calls"""
    return get_embedding(text)


def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def analyze_hotel_reviews(hotel_id):
    """
    Analyze hotel reviews against hotel parameters using embeddings
    Returns similarity scores and anomaly detection results
    """
    if hotel_id not in HOTEL_DATA:
        return None
    
    hotel = HOTEL_DATA[hotel_id]
    
    # Create hotel description from parameters
    hotel_text = f"{hotel['name']}. {hotel['description']} Особенности: {', '.join(hotel['features'])}"
    
    # Get hotel embedding
    hotel_embedding = get_cached_embedding(hotel_text)
    
    # Analyze normal reviews
    normal_reviews = REVIEWS_DATASET.get(hotel_id, [])
    normal_results = []
    
    for review in normal_reviews:
        review_embedding = get_cached_embedding(review)
        similarity = cosine_similarity(hotel_embedding, review_embedding)
        
        normal_results.append({
            'review': review,
            'similarity': float(similarity),
            'needs_check': similarity < SIMILARITY_THRESHOLD
        })
    
    # Analyze anomalous reviews
    anomalous_reviews = ANOMALOUS_REVIEWS.get(hotel_id, [])
    anomalous_results = []
    
    for review in anomalous_reviews:
        review_embedding = get_cached_embedding(review)
        similarity = cosine_similarity(hotel_embedding, review_embedding)
        
        anomalous_results.append({
            'review': review,
            'similarity': float(similarity),
            'needs_check': similarity < SIMILARITY_THRESHOLD
        })
    
    return {
        'hotel': hotel,
        'hotel_text': hotel_text,
        'normal_reviews': normal_results,
        'anomalous_reviews': anomalous_results,
        'threshold': SIMILARITY_THRESHOLD
    }


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', hotels=HOTEL_DATA)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"}), 200


@app.route('/api/analyze/<hotel_id>')
def analyze(hotel_id):
    """API endpoint to analyze hotel reviews"""
    try:
        result = analyze_hotel_reviews(hotel_id)
        if result is None:
            return jsonify({"error": "Hotel not found"}), 404
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error analyzing hotel {hotel_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/custom_review', methods=['POST'])
def custom_review():
    """Analyze a custom review against a hotel"""
    try:
        data = request.get_json()
        hotel_id = data.get('hotel_id')
        review_text = data.get('review_text')
        
        if not hotel_id or not review_text:
            return jsonify({"error": "hotel_id and review_text are required"}), 400
        
        if hotel_id not in HOTEL_DATA:
            return jsonify({"error": "Hotel not found"}), 404
        
        hotel = HOTEL_DATA[hotel_id]
        hotel_text = f"{hotel['name']}. {hotel['description']} Особенности: {', '.join(hotel['features'])}"
        
        # Get embeddings
        hotel_embedding = get_cached_embedding(hotel_text)
        review_embedding = get_cached_embedding(review_text)
        
        # Calculate similarity
        similarity = cosine_similarity(hotel_embedding, review_embedding)
        
        return jsonify({
            'hotel': hotel,
            'review': review_text,
            'similarity': float(similarity),
            'needs_check': similarity < SIMILARITY_THRESHOLD,
            'threshold': SIMILARITY_THRESHOLD
        })
    except Exception as e:
        app.logger.error(f"Error analyzing custom review: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('APP_PORT', 8080))
    host = os.getenv('APP_HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=False)
