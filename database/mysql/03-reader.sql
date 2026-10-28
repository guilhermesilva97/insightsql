CREATE USER 'insightql_reader'@'%' IDENTIFIED BY 'reader';
GRANT SELECT ON insightql.* TO 'insightql_reader'@'%';
FLUSH PRIVILEGES;
