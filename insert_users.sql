-- SQL script to populate the database with 5 users (3 admins)

-- Insert 3 admin users with example hashed passwords
INSERT INTO users (username, email, password, is_admin, is_banned)
VALUES
    ('Atos', 'atos@example.com', '$2b$12$examplehashedpassword1', TRUE, FALSE),
    ('Portos', 'meat@example.com', '$2b$12$examplehashedpassword2', TRUE, FALSE),
    ('Aramis', 'cognac@example.com', '$2b$12$examplehashedpassword3', TRUE, FALSE);

-- Insert 2 regular users with example hashed passwords
INSERT INTO users (username, email, password, is_admin, is_banned)
VALUES
    ('Dartanyan', 'konstanta@example.com', '$2b$12$examplehashedpassword4', FALSE, FALSE),
    ('Vasya', 'vasatron@example.com', '$2b$12$examplehashedpassword5', FALSE, FALSE);