grant usage on schema radar to anon, authenticated, service_role;

grant all privileges on all tables in schema radar to service_role;
grant all privileges on all sequences in schema radar to service_role;

grant select on all tables in schema radar to anon, authenticated;

alter default privileges in schema radar
grant all privileges on tables to service_role;

alter default privileges in schema radar
grant all privileges on sequences to service_role;