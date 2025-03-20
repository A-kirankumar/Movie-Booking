-- Create Database
CREATE DATABASE movie_booking;

-- Use the database
USE movie_booking;

-- Create Users table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user'
);

-- Create Movies table
CREATE TABLE movies (
    movie_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    genre VARCHAR(50),
    release_date DATE
);

-- Create Theaters table
CREATE TABLE theaters (
    theater_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100)
);

-- Create Shows table (Movies + Theaters + Showtimes)
CREATE TABLE shows (
    show_id INT AUTO_INCREMENT PRIMARY KEY,
    movie_id INT,
    theater_id INT,
    showtime DATETIME,
    available_seats INT,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
    FOREIGN KEY (theater_id) REFERENCES theaters(theater_id)
);

-- Create Bookings table
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    show_id INT,
    seats_booked INT,
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (show_id) REFERENCES shows(show_id)
);

DELIMITER $$

CREATE TRIGGER after_booking_update
AFTER UPDATE ON shows
FOR EACH ROW
BEGIN
    -- Only perform logic if available_seats is being updated
    IF OLD.available_seats <> NEW.available_seats THEN
        -- Log the seat update for debugging purposes (optional)
        INSERT INTO seat_updates_log (show_id, old_seats, new_seats, update_time)
        VALUES (OLD.show_id, OLD.available_seats, NEW.available_seats, NOW());
    END IF;
END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE create_booking(IN userId INT, IN showId INT, IN seats INT)
BEGIN
    DECLARE available INT;

    -- Get available seats for the show
    SELECT available_seats INTO available FROM shows WHERE show_id = showId;

    -- Check if enough seats are available
    IF available >= seats THEN
        -- Insert booking into bookings table
        INSERT INTO bookings (user_id, show_id, seats_booked) 
        VALUES (userId, showId, seats);

        -- Update available seats after booking (only subtract the seats booked)
        UPDATE shows 
        SET available_seats = available_seats - seats 
        WHERE show_id = showId;

    ELSE
        -- Raise an error if not enough seats are available
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Not enough seats available';
    END IF;
END$$

DELIMITER ;



ALTER TABLE shows MODIFY available_seats INT;

ALTER TABLE bookings
ADD COLUMN booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

UPDATE shows
SET available_seats = 0
WHERE available_seats IS NULL;

ALTER TABLE shows
ADD COLUMN show_time DATETIME;

ALTER TABLE shows
    DROP FOREIGN KEY shows_ibfk_1;
ALTER TABLE shows
    ADD CONSTRAINT shows_ibfk_1
    FOREIGN KEY (movie_id)
    REFERENCES movies(movie_id)
    ON DELETE CASCADE;

CREATE TABLE seat_updates_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    show_id INT NOT NULL,
    old_seats INT NOT NULL,
    new_seats INT NOT NULL,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (show_id) REFERENCES shows(show_id)
);

CREATE USER 'admin_user'@'localhost' IDENTIFIED BY 'chandu@2005';
GRANT ALL PRIVILEGES ON movie_booking.* TO 'admin_user'@'localhost';

CREATE USER 'admin_user'@'localhost' IDENTIFIED BY 'chandu@2005';
GRANT SELECT ON movie_booking.movies TO 'customer_user'@'localhost';   -- To view movies
GRANT SELECT ON movie_booking.shows TO 'customer_user'@'localhost';    -- To view available shows
GRANT INSERT ON movie_booking.bookings TO 'customer_user'@'localhost'; -- To insert booking records




