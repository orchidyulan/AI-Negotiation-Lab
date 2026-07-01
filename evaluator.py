def evaluate(buyer_state, seller_state):

    buyer_score = len(buyer_state["history"]) * 15
    seller_score = len(seller_state["history"]) * 15

    if buyer_score > seller_score:
        winner = "buyer"
    else:
        winner = "seller"

    return {
        "buyer_score": buyer_score,
        "seller_score": seller_score,
        "winner": winner
    }