DO
$$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_database WHERE datname = 'db'
   ) THEN
      CREATE DATABASE db;
   END IF;
END
$$;
