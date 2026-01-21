-- Update tenant name from "Default Publisher" to "TF1"
UPDATE tenants 
SET name = 'TF1' 
WHERE tenant_id = 'default';

-- Verify the change
SELECT tenant_id, name FROM tenants WHERE tenant_id = 'default';
