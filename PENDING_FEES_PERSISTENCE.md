# Pending Fees - Permanent Server-Side Storage

## Overview
Imported Excel pending fees are now **permanently stored on the server database** (`rvce_fee.db`) and survive logout/login cycles. All pending fees data is securely isolated by user role.

---

## How It Works

### 1. **Admin Imports Excel** 
- Admin clicks "+ Import Excel" button
- Selects `.xlsx`, `.xls`, or `.csv` file
- Dashboard parses the file and sends rows to server via `POST /api/pending-fees/import`
- Server stores rows in `pending_fees` table with unique IDs

### 2. **Pending Fees Persisted in Database**
```sql
pending_fees TABLE (server-side):
  id (PRIMARY KEY, auto-increment)
  student_name TEXT
  department TEXT
  fee_type TEXT
  amount REAL
  due_date TEXT
  imported_by TEXT (role: admin/owner)
  created_at TEXT (timestamp)
```

### 3. **Admin Logs Out & Back In**
- On next login, `GET /api/pending-fees` is called
- Server returns ALL stored pending fees (only for admin/owner role)
- Dashboard renders fees in the table with server-side IDs
- Students get an empty list (role-based filtering)

### 4. **Bill Generation Removes Matching Pending Fee**
- When a bill is generated for a student:
  - System finds matching pending fee (by student name + due date)
  - Deletes from server database via `DELETE /api/pending-fees/{id}`
  - Removes from dashboard table
  - Pending fee count updates

---

## API Endpoints

### GET /api/pending-fees
**Returns**: List of pending fees (JSON array)
- **Admin/Owner**: Gets all pending fees
- **Student**: Gets empty list []

```json
[
  {
    "id": 1,
    "student_name": "John Doe",
    "department": "CSE",
    "fee_type": "Tuition",
    "amount": 50000,
    "due_date": "2026-03-15"
  }
]
```

### POST /api/pending-fees/import
**Accepts**: Array of pending fee rows (JSON)
**Returns**: Inserted rows with server-assigned IDs

```json
Request:
[
  {
    "student_name": "John Doe",
    "department": "CSE",
    "fee_type": "Tuition",
    "amount": 50000,
    "due_date": "2026-03-15"
  }
]

Response (201):
[
  {
    "id": 25,
    "student_name": "John Doe",
    "department": "CSE",
    "fee_type": "Tuition",
    "amount": 50000,
    "due_date": "2026-03-15"
  }
]
```

### DELETE /api/pending-fees/{id}
**Deletes**: Single pending fee by ID
**Returns**: 204 (No Content)

---

## Verification Steps

### Test 1: Import and Persist
1. Open http://127.0.0.1:5000
2. Click "Login" → "ADMIN" (password: `admin.rvce.in`)
3. Click "+ Import Excel"
4. Upload a CSV/Excel file with pending fees
5. Verify rows appear in the table
6. Check database: `sqlite3 rvce_fee.db` → `SELECT COUNT(*) FROM pending_fees;`

### Test 2: Survive Logout/Login
1. Admin logs out (🚪 Logout button)
2. Login again as Admin
3. **Expected**: Pending fees still shown in table
4. Database should still have the same records

### Test 3: Student Cannot See Pending Fees
1. Login as STUDENT
2. Go to Dashboard
3. **Expected**: No "Pending Payments" table shown; No "+ Import Excel" button
4. IF total_bill is visited: Returns "Access Denied" from server

### Test 4: Delete on Bill Generation
1. Admin logs in and imports fees
2. Go to "Generate Bill" tab
3. Fill form with matching student name and bill date
4. Click "Generate Preview"
5. Check pending fees table: Matching row should be removed
6. Database: `SELECT COUNT(*) FROM pending_fees;` should decrease by 1

---

## Database Storage Verification

```bash
# Check current pending fees count
sqlite3 rvce_fee.db "SELECT COUNT(*) FROM pending_fees;"

# View all pending fees
sqlite3 rvce_fee.db "SELECT student_name, fee_type, amount, due_date FROM pending_fees;"

# View recently added (last 5)
sqlite3 rvce_fee.db "SELECT id, student_name, fee_type, amount FROM pending_fees ORDER BY id DESC LIMIT 5;"
```

---

## Key Features

✅ **Admin-Only Access**: Only admin/owner can import, view, and delete pending fees  
✅ **Permanent Storage**: Data stored in SQLite DB, survives logout/login  
✅ **Role-Based Isolation**: Students cannot see admin-imported pending fees  
✅ **Automatic Cleanup**: Matching pending fees removed when bill is generated  
✅ **Server-Side IDs**: Each pending fee gets unique ID for tracking  
✅ **No Client Leakage**: No localStorage pollution; all data server-managed  

---

## Architecture Shift

### Before
- Pending fees stored in browser `localStorage` (client-side)
- Visible across users sharing browser profile
- Lost if localStorage cleared
- Vulnerable to inspection/manipulation

### After
- Pending fees stored in `rvce_fee.db` (server-side)
- Accessible only through authenticated API endpoints
- Role-based filtering enforced server-side
- Permanent until explicitly deleted
- Secure and audit-able

---

## Troubleshooting

**Issue**: Pending fees not showing after login  
→ Check: Is user role "admin" or "owner"? Run `GET /api/pending-fees` to verify API response.

**Issue**: Import fails  
→ Check: Browser console for errors. Verify CSV has headers: "Student Name", "Department", "Fees Type", "Amount", "Due Date".

**Issue**: Data lost after logout  
→ Check: Database still has data: `SELECT COUNT(*) FROM pending_fees;` should be > 0.

---

## Related Files

- **Backend**: `app.py` (API endpoints `/api/pending-fees/*`)
- **Frontend**: `templates/dashboard.html` (handleFile, loadPendingFeesFromServer, removeMatchingPending)
- **Database**: `rvce_fee.db` (table: `pending_fees`)
