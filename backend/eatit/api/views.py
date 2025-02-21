from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse

from twilio.rest import Client

from eatit.models import Cart, User, Address, ActiveOrders, MobileNumber
from eatit.api.serializers import AddressSerializer, UserSerializer, ActiveOrdersSerializer

from restaurants.models import Restaurant, FoodItem
from restaurants.api.serializers import RestaurantSerializer, FoodItemSerializer

from decouple import config
from django.http import HttpResponse


# For customizing the token claims: (whatever value we want)
# Refer here for more details: https://django-rest-framework-simplejwt.readthedocs.io/en/latest/customizing_token_claims.html

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        
        if user.groups.filter(name="Restaurant").exists():
            token['group'] = "Restaurant"
        else:
            token['group'] = "None"
        # ...

        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer



# To manually create tokens for user's logging in with mobile verification
# Refer: https://django-rest-framework-simplejwt.readthedocs.io/en/latest/creating_tokens_manually.html#creating-tokens-manually
@api_view(['POST'])
def customLogin(request):
    
    number = request.data['number']
    print('CUSTOM LOGIN')
    # Custom user authentication 
    
    try: 
        getUserID = MobileNumber.objects.get(number=number).user.id
        user = User.objects.get(id=getUserID)
    except ObjectDoesNotExist:
        return Response({'No user exists with that number ⚠️'}, status=status.HTTP_406_NOT_ACCEPTABLE)

    refresh = RefreshToken.for_user(user)

    # Add custom claims
    refresh['username'] = user.username
    
    if user.groups.filter(name="Restaurant").exists():
        refresh['group'] = "Restaurant"
    else:
        refresh['group'] = "None"
    # ...

    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    })
    


# User registration logic
@api_view(['POST'])
def register(request):
    # Extract user input from request
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")
    confirm_password = request.data.get("confirmPassword")

    # Validate required fields
    if not username or not email or not password or not confirm_password:
        return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

    # Ensure passwords match
    if password != confirm_password:
        return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

    # Check if username or email already exists
    if User.objects.filter(username=username).exists():
        return Response({"error": "Username is already taken."}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email=email).exists():
        return Response({"error": "Email is already registered."}, status=status.HTTP_400_BAD_REQUEST)

    # Create new user
    try:
        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)

    except IntegrityError:
        return Response({"error": "An error occurred while creating the user."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        print(f"Unexpected error: {e}")  # Debugging log
        return Response({"error": "An unknown error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# To view all the available/registered restaurants
@api_view(['GET'])
def restaurants(request):
    print("Request received for /api/restaurants/")  # Debugging log
    restaurants = Restaurant.objects.all()
    serializer = RestaurantSerializer(restaurants, many=True)
    return Response(serializer.data)


# To get the food items of the requested restaurant. (food items added by that restaurant)
@api_view(['GET'])
def restaurantsFood(request, id):

    try:
        # Get the requested restaurant
        restaurant = Restaurant.objects.get(id=id)
        # Get the food items of the above restaurant
        restaurantsFood = FoodItem.objects.filter(restaurant = restaurant)
    except :
        return Response('Not found', status=status.HTTP_404_NOT_FOUND)
    
    serializer = FoodItemSerializer(restaurantsFood, many=True)
    return Response(serializer.data)


# To get the info of the requested restaurant
@api_view(['GET'])
def restaurantsInfo(request, id):

    try:
        # Get the requested restaurant
        restaurant = Restaurant.objects.filter(id=id)
    except KeyError:
        return Response('Not found', status=status.HTTP_404_NOT_FOUND)

    serializer = RestaurantSerializer(restaurant, many=True)
    return Response(serializer.data)



# To get the items in the cart of the requested user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getCartItems(request):
    
    cart = Cart.objects.filter(user=request.user)
    # Custom serializer function is used for serializing the data. Refer to the Cart Model for more info about the serializer
    return Response([cart.serializer() for cart in cart])
    

# To add a food item to cart
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addToCart(request, id):
    
    # Add the food item to the user's cart
    try:
        # Get the requested foodItem
        food = FoodItem.objects.get(id=id)

        # Error checking: If user add's a food item from another restaurant (can add from only 1), then return with error message
        try:
            # Get the restaurant's ID of the current food items in cart
            presentCart = Cart.objects.filter(user=request.user).first()
            presentCartFood = FoodItem.objects.get(id= presentCart.food.id)
            # Check if the restaurant's ID of item in cart is not same as the requested food item to add.
            if food.restaurant != presentCartFood.restaurant:
                return Response({'You already have items added to cart from another restaurant'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        except AttributeError:
            # If the user has no item added to cart, then pass. The below code is the responsible for adding item to cart.
            pass

        # For adding the item to cart

        # If the user's cart contains the requested food item, then increase it's quantity by 1
        try:
            getFood =  Cart.objects.get(food=food, user=request.user)
            getFood.qty += 1
            # Update the amount of the food item added in cart in accordance of it's quantity
            getFood.amount = float(food.price * getFood.qty)
            getFood.save()
        # If the cart doesn't contain the food, then add it to cart and set quantity to 1
        except ObjectDoesNotExist :
            addItem = Cart(user=request.user, food=food, qty=1, amount=food.price)
            addItem.save()
            
        # Update the cart's totalAmount by adding the current food item's price
        oldTotalAmount = Cart.objects.filter(user=request.user).first().totalAmount
        Cart.objects.filter(user=request.user).update(totalAmount = float(oldTotalAmount+food.price))
        

        # Get the added cart item of the requested user (for passing to serializer)
        cart = Cart.objects.get(user=request.user, food=id)
    
    # If a request is made with an invalid food ID, i.e food item doesn't exist, then return error
    except KeyError:
        return Response('Not found', status=status.HTTP_404_NOT_FOUND)
    
    # Serialize the cart for sending to frontend in appropriate format
    return Response(cart.serializer())
    


# To remove a food item from cart
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def removeFromCart(request, id):

    # Remove the food item from the user's cart
    try:
        # Get the requested foodItem
        food = FoodItem.objects.get(id=id)

        # If the user's cart contains the requested food item, then decrease it's quantity by 1
        try:
            getFood =  Cart.objects.get(food=food, user=request.user)

            # If the item's quantity is more than 1, then decrease it's quantity
            if getFood.qty > 1:
                getFood.qty -= 1
                # Update the amount of the food items removed from cart in accordance with its quantity
                getFood.amount = food.price * getFood.qty
                getFood.save()
            # If the item's quantity is 1 i.e the last item, then delete the item
            elif getFood.qty == 1:
                getFood.delete()
            # Else throw an error if qty is less than 1
            else :
                # If food qty is already 0, then return
                return Response('Food already removed from cart', status=status.HTTP_406_NOT_ACCEPTABLE)
                

        # If the cart doesn't contain the food, then return
        except ObjectDoesNotExist :
            return Response('Food is not present in the cart', status=status.HTTP_404_NOT_FOUND)
            
        try:
            # Update the cart's totalAmount by subtracting the current food item's price
            oldTotalAmount = Cart.objects.filter(user=request.user).first().totalAmount
            Cart.objects.filter(user=request.user).update(totalAmount = float(oldTotalAmount-food.price))
        except AttributeError:
            pass    

    # If a request is made with an invalid food ID, i.e food item doesn't exist, then return error
    except KeyError:
        return Response('Not found', status=status.HTTP_404_NOT_FOUND)
    
    return Response('Removed from cart')



# To add an address of a user
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addAddress(request):
    
    area = request.data['area']
    label = request.data['label']

    addAddress = Address(user=request.user, area=area, label=label)
    addAddress.save()

    return Response({'Address Added'})


# To get all the added address of a user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getAddress(request):

    address = Address.objects.filter(user=request.user)
    serializer = AddressSerializer(address, many=True)
    
    return Response(serializer.data)




# To place an order of a customer with the requested data
# Creates a Stripe checkout session and returns back a URL to redirect to.
# Refer: https://stripe.com/docs/connect/enable-payment-acceptance-guide?platform=web#web-create-checkout for more information.
import stripe
from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from eatit.models import Cart, Address, FoodItem, ActiveOrders

# Ensure Stripe API key is set
stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", None)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):
    print("Checkout API called")  # Debugging log

    # Check if STRIPE_SECRET_KEY is set
    if not stripe.api_key:
        print("ERROR: STRIPE_SECRET_KEY is missing in settings.py")
        return JsonResponse({'error': 'Stripe API key is missing'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Get the user's cart
    cart = Cart.objects.filter(user=request.user)
    if not cart.exists():
        print("Cart is empty")
        return JsonResponse({'error': 'Your cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

    # Get delivery address
    addressID = request.data.get('address', {}).get('id')
    try:
        address = Address.objects.get(id=addressID)
    except Address.DoesNotExist:
        print("Invalid address")
        return JsonResponse({'error': 'Invalid address'}, status=status.HTTP_400_BAD_REQUEST)

    # Create order
    restaurant = FoodItem.objects.get(id=cart.first().food.id).restaurant
    new_order = ActiveOrders(user=request.user, restaurant=restaurant, address=address)
    new_order.save()
    for cartItem in cart:
        new_order.cart.add(cartItem)

    # Prepare Stripe items
    line_items = []
    for cartItem in cart:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': cartItem.food.name},
                'unit_amount': int(cartItem.food.price * 100),  # Convert to cents
            },
            'quantity': cartItem.qty,
        })

    # Create Stripe session
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=f"{settings.FRONTEND_URL}/my-account",
            cancel_url=f"{settings.FRONTEND_URL}/cancel",
        )
        print("Stripe session created:", session.url)
        return JsonResponse({'url': session.url})

    except stripe.error.StripeError as e:
        print("Stripe error:", str(e))
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    # ------- To send the user a text SMS using Twilio informing about their successfull order placement -----
    
    number = MobileNumber.objects.get(user=sessionUser).number

    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    account_sid = config('TWILIO_ACCOUNT_SID')
    auth_token = config('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)

    message = client.messages \
                    .create(
                        messaging_service_sid='MG3689472a26e433f57909e6a580e2d9be',
                        to='+' + str(number),
                        body="Your order has been successfully placed at EatIN! " + str(cart.count()) + "x item(s) ordered from " + str(restaurant.name) + " with a total amount of " + str(cart.first().totalAmount) +". \n Happy EatIN!"
                    )

    print('Message sent ✅:', message.status)



# To get the active orders of the logged in user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getOrders(request):
    
    activeOrders = ActiveOrders.objects.filter(user=request.user).order_by('-id')
    serializer = ActiveOrdersSerializer(activeOrders, many=True)
    return Response(serializer.data)


# To get the info of the logged in user like name, email etc.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserInfo(request):

    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request):
    user = request.user
    data = request.data

    new_username = data.get("username", user.username)
    new_email = data.get("email", user.email)

    # Validate username
    if new_username and new_username != user.username:
        if User.objects.filter(username=new_username).exclude(id=user.id).exists():
            return Response({"error": "Username already taken."}, status=400)
        user.username = new_username

    # Validate email
    if new_email and new_email != user.email:
        if User.objects.filter(email=new_email).exclude(id=user.id).exists():
            return Response({"error": "Email already in use."}, status=400)
        user.email = new_email

    user.save()
    
    return Response({
        "message": "Profile updated successfully.",
        "username": user.username,
        "email": user.email
    })






# -------For DRF view --------------
@api_view(['GET'])
def getRoutes(request):
    routes = [
        '/api/token/',
        '/api/token/refresh/',
        '/api/mobile-send-message/',
        '/api/mobile-verification/',
        '/api/restaurants/',
        '/api/restaurants/<int:id>/',
        '/api/restaurants/info/<int:id>/',
        '/api/get-cart-items/',
        '/api/add-to-cart/<int:id>/',
        '/api/remove-from-cart/<int:id>/',
        '/api/add-address/',
        '/api/get-address/',
        '/api/checkout/',
        '/api/webhook/',
        '/api/get-orders/',
        '/api/get-user-info/',
        '/api/custom-login/',
    ]

    return Response(routes)