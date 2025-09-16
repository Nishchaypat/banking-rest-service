from fastapi import APIRouter, HTTPException, Security
from pydantic import BaseModel
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/cards", tags=["cards"])

class CardUpdateStatus(BaseModel):
    status: str  # e.g. 'active', 'blocked'

class CardPINUpdate(BaseModel):
    pin: str  # New PIN - store hashed in real apps

@router.delete("/{card_id}")
def delete_card(card_id: str, username: str = Security(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id FROM cards c
        JOIN accounts a ON c.account_id = a.id
        JOIN users u ON a.user_id = u.id
        WHERE c.id = ? AND u.username = ?
    """, (card_id, username))
    card = cursor.fetchone()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found or unauthorized")
    cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.commit()
    conn.close()
    return {"message": "Card deleted successfully"}

@router.put("/{card_id}/status")
def update_card_status(card_id: str, status_update: CardUpdateStatus, username: str = Security(get_current_user)):
    if status_update.status not in ["active", "blocked"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id FROM cards c
        JOIN accounts a ON c.account_id = a.id
        JOIN users u ON a.user_id = u.id
        WHERE c.id = ? AND u.username = ?
    """, (card_id, username))
    card = cursor.fetchone()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found or unauthorized")
    cursor.execute("UPDATE cards SET status = ? WHERE id = ?", (status_update.status, card_id))
    conn.commit()
    conn.close()
    return {"message": f"Card status updated to {status_update.status}"}

@router.put("/{card_id}/pin")
def update_card_pin(card_id: str, pin_update: CardPINUpdate, username: str = Security(get_current_user)):
    # For demo, store plain pin; hash it in production
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id FROM cards c
        JOIN accounts a ON c.account_id = a.id
        JOIN users u ON a.user_id = u.id
        WHERE c.id = ? AND u.username = ?
    """, (card_id, username))
    card = cursor.fetchone()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found or unauthorized")
    cursor.execute("UPDATE cards SET pin = ? WHERE id = ?", (pin_update.pin, card_id))
    conn.commit()
    conn.close()
    return {"message": "PIN updated successfully"}
