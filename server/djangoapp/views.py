from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import logout, login, authenticate
from django.views.decorators.csrf import csrf_exempt
import logging
import json

from .models import CarMake, CarModel
from .restapis import get_request, analyze_review_sentiments, post_review
from .populate import initiate

logger = logging.getLogger(__name__)


@csrf_exempt
def login_user(request):
    """Handle user login"""
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    user = authenticate(username=username, password=password)
    response_data = {"userName": username}

    if user is not None:
        login(request, user)
        response_data["status"] = "Authenticated"

    return JsonResponse(response_data)


def logout_request(request):
    """Handle user logout"""
    logout(request)
    return JsonResponse({"userName": ""})


@csrf_exempt
def registration(request):
    """Handle user registration"""
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']

    try:
        User.objects.get(username=username)
        return JsonResponse({"userName": username, "error": "Already Registered"})
    except User.DoesNotExist:
        logger.debug("%s is a new user", username)
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email
        )
        login(request, user)
        return JsonResponse({"userName": username, "status": "Authenticated"})


def get_cars(request):
    """Return list of car models and their makes"""
    if CarMake.objects.count() == 0:
        initiate()

    car_models = CarModel.objects.select_related('car_make')
    cars = [
        {"CarModel": car.name, "CarMake": car.car_make.name}
        for car in car_models
    ]

    return JsonResponse({"CarModels": cars})


def get_dealerships(request, state="All"):
    """Return list of dealerships (optionally filtered by state)"""
    endpoint = f"/fetchDealers/{state}" if state != "All" else "/fetchDealers"
    dealerships = get_request(endpoint)
    return JsonResponse({"status": 200, "dealers": dealerships})


def get_dealer_reviews(request, dealer_id):
    """Return reviews of a specific dealer with sentiment analysis"""
    if not dealer_id:
        return JsonResponse({"status": 400, "message": "Bad Request"})

    endpoint = f"/fetchReviews/dealer/{dealer_id}"
    reviews = get_request(endpoint)

    for review in reviews:
        sentiment_response = analyze_review_sentiments(review['review'])
        review['sentiment'] = sentiment_response.get('sentiment', 'neutral')

    return JsonResponse({"status": 200, "reviews": reviews})


def get_dealer_details(request, dealer_id):
    """Return details of a specific dealer"""
    if not dealer_id:
        return JsonResponse({"status": 400, "message": "Bad Request"})

    endpoint = f"/fetchDealer/{dealer_id}"
    dealership = get_request(endpoint)

    if dealership is None:
        dealership = {}
    elif isinstance(dealership, list) and len(dealership) > 0:
        dealership = dealership[0]
    else:
        dealership = {}

    return JsonResponse({"status": 200, "dealer": dealership})


def add_review(request):
    """Allow authenticated users to add a review"""
    if request.user.is_anonymous:
        return JsonResponse({"status": 403, "message": "Unauthorized"})

    data = json.loads(request.body)
    try:
        post_review(data)
        return JsonResponse({"status": 200})
    except Exception:
        return JsonResponse({"status": 401, "message": "Error in posting review"})
