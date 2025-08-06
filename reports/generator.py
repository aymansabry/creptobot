import pandas as pd
from db.models import Transaction

def generate_user_report(user_id: str):
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    df = pd.DataFrame([t.__dict__ for t in transactions])
    return df.to_markdown(tablefmt="grid")
