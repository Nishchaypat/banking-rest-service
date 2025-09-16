from fastapi import APIRouter, HTTPException, Security
from pydantic import BaseModel
from app.database import get_db
from app.auth import get_current_user

router = APIRouter()

EXTERNAL_TRANSFER_LIMIT = 5000.0

class ExternalTransfer(BaseModel):
    from_account_id: int
    external_account: str
    amount: float

@router.post("/external-transfer")
def external_transfer(transfer: ExternalTransfer, username: str = Security(get_current_user)):
    if transfer.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if transfer.amount > EXTERNAL_TRANSFER_LIMIT:
        raise HTTPException(status_code=400, detail=f"Transfer amount exceeds limit of {EXTERNAL_TRANSFER_LIMIT}")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT balance FROM accounts a
        JOIN users u ON a.user_id = u.id
        WHERE a.id = ? AND u.username = ?
        """,
        (transfer.from_account_id, username)
    )
    from_acc = cursor.fetchone()
    if not from_acc:
        conn.close()
        raise HTTPException(status_code=404, detail="Source account not found or unauthorized")

    if from_acc["balance"] < transfer.amount:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient funds in source account")

    try:
        cursor.execute("BEGIN")
        new_balance = from_acc["balance"] - transfer.amount
        cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, transfer.from_account_id))
        cursor.execute(
            "INSERT INTO transactions (account_id, type, amount) VALUES (?, ?, ?)",
            (transfer.from_account_id, "external_transfer", -transfer.amount)
        )
        # Simulate external API call here - assumed successful
        conn.commit()
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="External transfer failed")
    finally:
        conn.close()

    return {"message": "External transfer successful"}
