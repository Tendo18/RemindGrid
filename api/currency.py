CURRENCY_SYMBOLS = {
    'NGN': '₦',
    'USD': '$',
    'GBP': '£',
    'EUR': '€',
}

def format_money(amount, currency_code):
    symbol = CURRENCY_SYMBOLS.get(currency_code, '')
    return f"{symbol}{amount:,.2f}"