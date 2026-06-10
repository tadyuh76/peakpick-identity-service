CREATE TABLE IF NOT EXISTS stores (
    store_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS identity_users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'store_manager', 'customer')),
    store_id TEXT NOT NULL REFERENCES stores(store_id),
    display_name TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO stores (store_id, name)
VALUES
    ('store-ueh', 'UEH Campus Store'),
    ('store-d1', 'District 1 Store')
ON CONFLICT (store_id) DO UPDATE
    SET name = EXCLUDED.name,
        active = true;

INSERT INTO identity_users (username, password_hash, role, store_id, display_name)
VALUES
    ('admin@peakpick.local', '11cf072926003cc1ff6dc60064170469c01f39fba8a2319d58e99a842d08b292', 'admin', 'store-ueh', 'PeakPick Admin'),
    ('manager.ueh@peakpick.local', '7bd7e62467b6d51191887630a664ea3ba3f46364068ddfc1b80392e73878054a', 'store_manager', 'store-ueh', 'UEH Store Manager'),
    ('manager.d1@peakpick.local', '7bd7e62467b6d51191887630a664ea3ba3f46364068ddfc1b80392e73878054a', 'store_manager', 'store-d1', 'District 1 Store Manager')
ON CONFLICT (username) DO UPDATE
    SET password_hash = EXCLUDED.password_hash,
        role = EXCLUDED.role,
        store_id = EXCLUDED.store_id,
        display_name = EXCLUDED.display_name,
        active = true;
