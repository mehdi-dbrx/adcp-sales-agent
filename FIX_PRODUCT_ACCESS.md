# Fix Product Access Issue

## Problem
The agent returns: "L'accès aux produits et tarifs TF1 nécessite une authentification commerciale spécifique."

This happens because:
1. Products either don't exist in the database, OR
2. Products exist but have `allowed_principal_ids` restrictions that exclude your test principal

## Solution

### Option 1: Create/Update Products via Script (Recommended)

Run the script to create accessible products:

```bash
cd salesagent
source venv/bin/activate  # or use buyagent venv
python create_test_products.py
```

This will:
- Create TF1-specific products if none exist
- Update existing products to remove access restrictions
- Make products accessible to all principals (including test-token)

### Option 2: Use Admin UI

1. **Access Admin UI:**
   ```
   http://localhost:8000/admin
   ```
   Login with: `test123`

2. **Navigate to Products:**
   - Click "Products" in the sidebar
   - You should see existing products

3. **Create/Edit Products:**
   - Click "Add Product" to create new ones
   - OR click "Edit" on existing products
   - **Important:** Make sure "Allowed Principals" field is **empty** (not restricted)
   - Products with empty `allowed_principal_ids` are visible to all principals

### Option 3: Check Database Directly

```bash
cd salesagent
source venv/bin/activate
python -c "
from src.core.database.database_session import get_db_session
from src.core.database.models import Product
from sqlalchemy import select

with get_db_session() as session:
    products = session.scalars(select(Product).filter_by(tenant_id='default')).all()
    print(f'Found {len(products)} products')
    for p in products:
        restricted = 'YES' if p.allowed_principal_ids else 'NO'
        print(f'  {p.product_id}: {p.name} - Restricted: {restricted}')
"
```

## Understanding Access Control

Products have an `allowed_principal_ids` field:
- **`None` or `[]`**: Product is visible to ALL principals (public)
- **`['principal_id_1', 'principal_id_2']`**: Only those specific principals can see it

Your `test-token` corresponds to principal_id `test_principal` (or `default_principal`).

## Verify It Works

After creating/updating products, test:

```bash
curl -H "x-adcp-auth: test-token" \
  http://localhost:8000/mcp/ \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"method":"tools/call","params":{"name":"get_products","arguments":{"brief":"TF1"}}}'
```

You should see products in the response!
