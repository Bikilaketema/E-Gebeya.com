from chapa.api import Chapa
from flask import current_app, url_for

def initialize_payment(order_id, amount, email, first_name, last_name):
    """Initialize a payment with Chapa"""
    chapa = Chapa(secret=current_app.config['CHAPA_SECRET_KEY'])
    
    # Use order_id as transaction reference
    tx_ref = str(order_id)
    
    # Initialize payment
    response = chapa.initialize(
        amount=amount,
        currency='ETB',
        email=email,
        first_name=first_name,
        last_name=last_name,
        tx_ref=tx_ref,
        callback_url=url_for('payment_callback', _external=True),
        return_url=url_for('payment_success', _external=True, tx_ref=tx_ref),
        customization={
            "title": "E-Gebeya Payment",
            "description": "Payment for your order"
        }
    )
    
    print("Chapa response:", response)  # Debug print
    return response

def verify_payment(transaction_id):
    """Verify a payment with Chapa"""
    chapa = Chapa(secret=current_app.config['CHAPA_SECRET_KEY'])
    
    response = chapa.verify(transaction_id)
    return response 