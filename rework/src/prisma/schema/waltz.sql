CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(400) NOT NULL,
    email TEXT NOT NULL UNIQUE,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


CREATE TABLE IF NOT EXISTS security (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL UNIQUE REFERENCES clients(id),
    client_secret TEXT NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contracts (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id),
    contract JSONB NOT NULL
);