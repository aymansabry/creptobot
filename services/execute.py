def execute_arbitrage(path, amount):
    pair1, pair2 = path
    price1 = float(client.get_symbol_ticker(symbol=pair1)['price'])
    price2 = float(client.get_symbol_ticker(symbol=pair2)['price'])

    qty_base = amount / price1
    final_amount = qty_base * price2

    profit = final_amount - amount

    # سجل الصفقة
    log_arbitrage(user_id=1, symbol=f"{pair1}->{pair2}", amount=amount, profit=profit)

    return {
        'initial': amount,
        'final': round(final_amount, 2),
        'profit': round(profit, 2),
        'path': f"{pair1} → {pair2}"
    }
