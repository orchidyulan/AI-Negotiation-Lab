def generate_report(case_name, result, buyer_state, seller_state):

    report = {
        "case": case_name,
        "winner": result["winner"],
        "buyer_score": result["buyer_score"],
        "seller_score": result["seller_score"],
        "buyer_dialogue": buyer_state["history"],
        "seller_dialogue": seller_state["history"]
    }

    return report