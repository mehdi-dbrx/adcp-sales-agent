#!/bin/bash
# Update tenant name from "Default Publisher" to "TF1"

cd "$(dirname "$0")"

echo "🔄 Updating tenant name to TF1..."

docker compose exec -T postgres psql -U adcp_user -d adcp << 'EOF'
UPDATE tenants 
SET name = 'TF1' 
WHERE tenant_id = 'default' AND name = 'Default Publisher';

SELECT tenant_id, name FROM tenants WHERE tenant_id = 'default';
EOF

echo ""
echo "✅ Tenant name updated to TF1!"
echo "   Refresh your browser to see the change."
