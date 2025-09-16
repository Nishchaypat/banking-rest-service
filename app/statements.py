from fastapi.responses import StreamingResponse
from io import StringIO
from fastapi import HTTPException, Security
from app.database import get_db
from app.auth import get_current_user
from fastapi import APIRouter

router = APIRouter(prefix="/statements", tags=["statements"])

@router.get("/{account_id}/monthly")
def monthly_statement(account_id: int, year: int, month: int, username: str = Security(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id FROM accounts a
        JOIN users u ON a.user_id = u.id
        WHERE a.id = ? AND u.username = ?
    """, (account_id, username))
    account = cursor.fetchone()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found or unauthorized")

    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    cursor.execute("""
        SELECT type, amount, timestamp FROM transactions
        WHERE account_id = ? AND timestamp >= ? AND timestamp < ?
        ORDER BY timestamp
    """, (account_id, start_date, end_date))
    transactions = cursor.fetchall()
    conn.close()

    output = StringIO()
    output.write("type,amount,timestamp\n")
    for t in transactions:
        output.write(f"{t['type']},{t['amount']},{t['timestamp']}\n")
    output.seek(0)

    return StreamingResponse(output, media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename=statement_{account_id}_{year}_{month}.csv"})
