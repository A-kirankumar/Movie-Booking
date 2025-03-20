import streamlit as st
import mysql.connector
import hashlib
from datetime import datetime
from hashlib import sha256

# Database connection setup
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="chandu@2005",
        database="movie_booking"
    )




conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="chandu@2005",
    database="movie_booking"
)

def hash_password(password):
    return sha256(password.encode()).hexdigest()

# Authentication functions
def login_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    hashed_pw = hash_password(password)
    print(f"Attempting login for username: {username} with hashed password: {hashed_pw}")
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, hashed_pw))
    user = cursor.fetchone()
    conn.close()
    return user


def register_user(username, password, role='customer'):
    conn = create_connection()
    cursor = conn.cursor()
    hashed_pw = hash_password(password)

    try:
        # Check if the username already exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
        if cursor.fetchone()[0] > 0:
            return "Username already exists"
        
        # Insert new user
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, hashed_pw, role))
        conn.commit()
        return "User registered successfully"
    except mysql.connector.Error as e:
        return f"Error: {e}"
    finally:
        conn.close()


# Admin functions
def add_movie(title, genre, release_date):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO movies (title, genre, release_date) VALUES (%s, %s, %s)", (title, genre, release_date))
    conn.commit()
    conn.close()

def delete_movie(movie_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movies WHERE movie_id = %s", (movie_id,))
    conn.commit()
    conn.close()

def add_theater(name, location):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO theaters (name, location) VALUES (%s, %s)", (name, location))
    conn.commit()
    conn.close()

def add_show(movie_id, theater_id, showtime, available_seats):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO shows (movie_id, theater_id, showtime, available_seats) VALUES (%s, %s, %s, %s)", 
                   (movie_id, theater_id, showtime, available_seats))
    conn.commit()
    conn.close()

def delete_show(show_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shows WHERE show_id = %s", (show_id,))
    conn.commit()
    conn.close()

def fetch_movies():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies")
    movies = cursor.fetchall()
    conn.close()
    return movies

def fetch_theaters():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM theaters")
    theaters = cursor.fetchall()
    conn.close()
    return theaters


def fetch_shows():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.show_id, s.movie_id, s.theater_id, s.showtime, s.available_seats, 
               m.title AS movie_name, t.name AS theater_name 
        FROM shows s
        JOIN movies m ON s.movie_id = m.movie_id 
        JOIN theaters t ON s.theater_id = t.theater_id
    """)
    shows = cursor.fetchall()
    conn.close()
    return shows


def movie_page():
    st.title('Movie Booking')

    if 'user_id' not in st.session_state:
        st.warning("Please log in first!")
        return

    st.write('Available Shows: ')
    shows = fetch_shows()

    if shows:
        for show in shows:
            available_seats = show[4] if show[4] is not None else 0
            st.write(f"Movie: {show[5]}, Theater: {show[6]}, Showtime: {show[3]}, Available Seats: {available_seats}")

            if available_seats > 0:
                seats = st.number_input('Seats to Book', min_value=1, max_value=available_seats, key=f"seats_input_{show[0]}")
            else:
                st.warning(f"No seats available for the show: {show[5]}")
                seats = 0

            if st.button(f'Book Now for {show[5]}', key=f"book_button_{show[0]}"):
                if seats > 0 and seats <= available_seats:
                    try:
                        conn = create_connection()
                        cursor = conn.cursor()

                        # Execute stored procedure for booking
                        cursor.callproc('create_booking', (st.session_state.user_id, show[0], seats))

                        # Ensure all results are fetched before closing the cursor
                        for result in cursor.stored_results():
                            result.fetchall()  # Fetch all results returned by the procedure

                        conn.commit()
                        st.success(f'{seats} seat(s) booked for {show[5]}')

                    except mysql.connector.Error as err:
                        st.error(f"Error: {err}")
                    finally:
                        cursor.close()
                        conn.close()
                else:
                    st.error("Invalid number of seats selected.")
    else:
        st.info("No shows available currently.")





def admin_page():
    st.title('Admin Panel')
    
    # Add Movie Section
    st.header('Add New Movie')
    title = st.text_input('Movie Title', key='movie_title')
    genre = st.text_input('Genre', key='genre')
    release_date = st.date_input('Release Date', key='release_date')
    if st.button('Add Movie', key='add_movie_button'):
        if title and genre and release_date:
            add_movie(title, genre, release_date)
            st.success(f"Movie '{title}' added successfully")
        else:
            st.error("Please fill in all fields for the movie.")
    
    # Add Theater Section
    st.header('Add New Theater')
    theater_name = st.text_input('Theater Name', key='theater_name')
    location = st.text_input('Location', key='location')
    if st.button('Add Theater', key='add_theater_button'):
        if theater_name and location:
            add_theater(theater_name, location)
            st.success(f"Theater '{theater_name}' added successfully")
        else:
            st.error("Please fill in all fields for the theater.")
    
    # Add Show Section
    st.header('Add New Show')
    movies = fetch_movies()
    theaters = fetch_theaters()
    if movies and theaters:
        movie_id = st.selectbox('Select Movie', [movie[0] for movie in movies], 
                                format_func=lambda x: next((movie[1] for movie in movies if movie[0] == x), ""))
        theater_id = st.selectbox('Select Theater', [theater[0] for theater in theaters], 
                                  format_func=lambda x: next((theater[1] for theater in theaters if theater[0] == x), ""))
        showtime = st.time_input('Showtime')
        available_seats = st.number_input('Available Seats', min_value=1)
        if st.button('Add Show'):
            showtime_full = datetime.combine(datetime.today().date(), showtime)
            add_show(movie_id, theater_id, showtime_full, available_seats)
            st.success('New Show added successfully')
    else:
        st.warning("No movies or theaters available. Please add them first.")
    
    # View Movies Section
    st.header('View Movies')
    movies = fetch_movies()
    if movies:
        for movie in movies:
            st.write(f"Title: {movie[1]}, Genre: {movie[2]}, Release Date: {movie[3]}")
            if st.button(f"Delete Movie {movie[1]}", key=f"delete_movie_{movie[0]}"):
                delete_movie(movie[0])
                st.success(f"Movie '{movie[1]}' deleted successfully")
    else:
        st.info("No movies available.")
    
    # View Shows Section
    st.header('View Shows')
    shows = fetch_shows()
    if shows:
        for show in shows:
            st.write(f"Movie: {show[5]}, Theater: {show[6]}, Showtime: {show[3]}, Available Seats: {show[4]}")
            if st.button(f"Delete Show {show[0]}"):
                delete_show(show[0])
                st.success("Show deleted successfully")
    else:
        st.info("No shows available.")


def login_page():
    st.title('Login')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    if st.button('Login'):
        user = login_user(username, password)
        if user:
            st.session_state.role = user[3]
            st.session_state.user_id = user[0]
            st.success(f"Welcome {username}!")
            main()
        else:
            st.error('Invalid username or password')
    st.header('Register')
    reg_username = st.text_input('Register Username', key='reg_username')
    reg_password = st.text_input('Register Password', type='password', key='reg_password')
    if st.button('Register', key='register_button'):
        if reg_username and reg_password:
            if register_user(reg_username, reg_password):
                st.success('User registered successfully')
            else:
                st.error('Username already exists')
        else:
            st.error('Please fill in all fields to register.')

def main():
    if 'role' not in st.session_state:
        login_page()
    elif st.session_state.role == 'admin':
        admin_page()
    else:
        movie_page()

if __name__ == "__main__":
    main()