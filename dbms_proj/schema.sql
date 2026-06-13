DROP DATABASE IF EXISTS media_app;
CREATE DATABASE media_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE media_app;

CREATE TABLE User (
  user_id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  join_date DATE NOT NULL DEFAULT (CURRENT_DATE)
);

CREATE TABLE Media (
  media_id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255) NOT NULL,
  media_type ENUM('Movie','Series') NOT NULL,
  release_year YEAR,
  runtime_min INT,
  imdb_rating DECIMAL(3,1),
  production_budget BIGINT,
  worldwide_collection BIGINT,
  theatrical_verdict ENUM('Blockbuster','Hit','Average','Flop'),
  image_url VARCHAR(512),
  description TEXT
);

CREATE TABLE Genre (
  genre_id INT PRIMARY KEY AUTO_INCREMENT,
  genre_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE MediaGenre (
  media_id INT NOT NULL,
  genre_id INT NOT NULL,
  PRIMARY KEY (media_id, genre_id),
  FOREIGN KEY (media_id) REFERENCES Media(media_id) ON DELETE CASCADE,
  FOREIGN KEY (genre_id) REFERENCES Genre(genre_id) ON DELETE CASCADE
);

CREATE TABLE StreamingPlatform (
  platform_id INT PRIMARY KEY AUTO_INCREMENT,
  platform_name VARCHAR(100) NOT NULL UNIQUE,
  website VARCHAR(255)
);

CREATE TABLE MediaPlatform (
  media_id INT NOT NULL,
  platform_id INT NOT NULL,
  availability_status ENUM('Available','Removed','Coming Soon'),
  PRIMARY KEY (media_id, platform_id),
  FOREIGN KEY (media_id) REFERENCES Media(media_id) ON DELETE CASCADE,
  FOREIGN KEY (platform_id) REFERENCES StreamingPlatform(platform_id) ON DELETE CASCADE
);

CREATE TABLE Media_Cast_Crew (
  id INT PRIMARY KEY AUTO_INCREMENT,
  media_id INT NOT NULL,
  person_name VARCHAR(100) NOT NULL,
  role VARCHAR(50),           
  character_name VARCHAR(100), 
  FOREIGN KEY (media_id) REFERENCES Media(media_id) ON DELETE CASCADE
);

CREATE TABLE WatchlistItem (
  list_item_id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  media_id INT NOT NULL,
  status ENUM('Planned','Watching','Completed','Dropped') NOT NULL DEFAULT 'Planned',
  date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
  personal_rating INT DEFAULT NULL,
  UNIQUE (user_id, media_id),
  FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
  FOREIGN KEY (media_id) REFERENCES Media(media_id) ON DELETE CASCADE
);

CREATE TABLE UserReviews (
  review_id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  media_id INT NOT NULL,
  review_text TEXT,
  rating INT,
  review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
  FOREIGN KEY (media_id) REFERENCES Media(media_id) ON DELETE CASCADE
);

INSERT INTO Genre (genre_name) VALUES ('Action'),('Drama'),('Comedy'),('Sci-Fi'),('Thriller');

INSERT INTO StreamingPlatform (platform_name, website) VALUES
('Netflix','https://www.netflix.com'),
('Amazon Prime','https://www.primevideo.com'),
('Disney+','https://www.disneyplus.com');

INSERT INTO Media (title, media_type, release_year, runtime_min, imdb_rating, production_budget, worldwide_collection, theatrical_verdict, image_url, description)
VALUES
('Interstellar','Movie',2014,169,8.6,165000000,677000000,'Hit',
 'https://m.media-amazon.com/images/M/MV5BMjIxMjgxNjY3MV5BMl5BanBnXkFtZTgwMzUxNzE3MTE@._V1_.jpg',
 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity''s survival.'),
('The Matrix','Movie',1999,136,8.7,63000000,463517383,'Blockbuster',
 'https://m.media-amazon.com/images/I/51EG732BV3L.jpg',
 'A computer hacker learns about the true nature of his reality and his role in the war against its controllers.'),
('Stranger Things','Series',2016,50,8.7,NULL,NULL,'Hit',
 'https://m.media-amazon.com/images/M/MV5BMjExNzE0MDA1Nl5BMl5BanBnXkFtZTgwNzk4ODQ2MTI@.V1.jpg',
 'When a young boy vanishes, a small town uncovers a mystery involving secret experiments and supernatural forces.');

INSERT INTO MediaGenre (media_id, genre_id) VALUES (1,4),(1,2),(2,4),(2,1),(3,4),(3,5);

INSERT INTO Media_Cast_Crew (media_id, person_name, role, character_name) VALUES
(1,'Christopher Nolan','Director',NULL),
(1,'Matthew McConaughey','Actor','Cooper'),
(2,'Lana Wachowski','Director',NULL),
(2,'Keanu Reeves','Actor','Neo'),
(3,'The Duffer Brothers','Creator',NULL);

INSERT INTO MediaPlatform (media_id, platform_id, availability_status) VALUES
(1,2,'Available'), 
(2,1,'Available'); 


INSERT INTO User (username, email, password_hash) VALUES ('a','1234','<password-hash-placeholder>');