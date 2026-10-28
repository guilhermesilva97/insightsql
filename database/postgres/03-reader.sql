CREATE ROLE insightql_reader LOGIN PASSWORD 'reader';
GRANT CONNECT ON DATABASE insightql TO insightql_reader;
GRANT USAGE ON SCHEMA public TO insightql_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO insightql_reader;
ALTER ROLE insightql_reader SET statement_timeout = '5s';
ALTER ROLE insightql_reader SET default_transaction_read_only = on;
