import json
import logging
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt

from .models import CarMake, CarModel
from .restapis import (
    get_request,
    analyze_review_sentiments,
    post_review,
)
from .populate import initiate

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------
@csrf_exempt
def login_user(request):
    """Authenticate and log in a user."""
    data = json.loads(request.body)
    username = data["userName"]
    password = data["password"]

    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse(
            {"userName": username, "status": "Authenticated"}
        )

    return JsonResponse({"userName": username})


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------
def logout_request(request):
    logout(request)
    return JsonResponse({"userName": ""})


# ---------------------------------------------------------
# REGISTRATION
# ---------------------------------------------------------
@csrf_exempt
def registration(request):
    data = json.loads(request.body)

    username = data["userName"]
    password = data["password"]
    first_name = data["firstName"]
    last_name = data["lastName"]
    email = data["email"]

    try:
        User.objects.get(username=username)
        return JsonResponse(
            {"userName": username, "error": "Already Registered"}
        )
    except User.DoesNotExist:
        logger.debug("%s is a new user", username)

    user = User.objects.create_user(
        username=username,
        first_name=first_name,
        last_name=last_name,
        password=password,
        email=email,
    )

    login(request, user)

    return JsonResponse(
        {"userName": username, "status": "Authenticated"}
    )


# ---------------------------------------------------------
# GET CARS
# ---------------------------------------------------------
def get_cars(request):
    count = CarMake.objects.count()

    # Auto-populate if empty
    if count == 0:
        initiate()

    car_models = CarModel.objects.select_related("car_make")
    cars = [
        {"CarModel": c.name, "CarMake": c.car_make.name}
        for c in car_models
    ]

    return JsonResponse({"CarModels": cars})


# ---------------------------------------------------------
# DEALERSHIPS
# ---------------------------------------------------------
def get_dealerships(request, state="All"):
    if state == "All":
        endpoint = "/fetchDealers"
    else:
        endpoint = f"/fetchDealers/{state}"

    dealerships = get_request(endpoint)

    return JsonResponse({"status": 200, "dealers": dealerships})


# ---------------------------------------------------------
# DEALER REVIEWS
# ---------------------------------------------------------
def get_dealer_reviews(request, dealer_id):
    if not dealer_id:
        return JsonResponse(
            {"status": 400, "message": "Bad Request"}
        )

    endpoint = f"/fetchReviews/dealer/{dealer_id}"
    reviews = get_request(endpoint)

    for review_detail in reviews:
        sentiment = analyze_review_sentiments(
            review_detail["review"]
        )
        review_detail["sentiment"] = sentiment["sentiment"]

    return JsonResponse({"status": 200, "reviews": reviews})


# ---------------------------------------------------------
# DEALER DETAILS
# ---------------------------------------------------------
def get_dealer_details(request, dealer_id):
    if not dealer_id:
        return JsonResponse(
            {"status": 400, "message": "Bad Request"}
        )

    endpoint = f"/fetchDealer/{dealer_id}"
    dealership = get_request(endpoint)

    if dealership is None:
        return JsonResponse({"status": 404, "dealer": {}})

    if isinstance(dealership, list):
        dealership = dealership[0] if dealership else {}

    return JsonResponse({"status": 200, "dealer": dealership})


# ---------------------------------------------------------
# ADD REVIEW
# ---------------------------------------------------------
def add_review(request):
    if request.user.is_anonymous:
        return JsonResponse(
            {"status": 403, "message": "Unauthorized"}
        )

    data = json.loads(request.body)
    try:
        post_review(data)
        return JsonResponse({"status": 200})
    except Exception:
        return JsonResponse(
            {"status": 401, "message": "Error in posting review"}
        )
