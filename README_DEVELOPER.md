# mobile-flashcards README for developers

# Table of contents
1. [Docker cheat sheet & tutorials](#Docker-cheat-sheet-&-tutorials)
1. [MongoDB cheat sheet & tutorials](#MongoDB-cheat-sheet-&-tutorials)

# Docker cheat sheet & tutorials
### Cheat sheet
- Build the images with BuildKit:
    - `DOCKER_BUILDKIT=1 docker-compose build`
- Start the containers: 
    - `docker-compose up -d`
- Stops the containers: 
    - `docker-compose down`
- Pause running containers: 
    - `docker-compose pause`
- Unpause the containers: 
    - `docker-compose unpause`
- Obtain containers resource usage statistics: 
    - `docker stats flashcard-worker flashcard-database`
- List containers
    - `docker ps -s -f "name=flashcard"`
- Get the Bash prompt of the containers
    - `docker-compose exec worker bash`
    - `docker-compose exec database bash`
- Fetch the logs of a container
    - `docker logs flashcard-worker`
    - `docker logs flashcard-database`
- References
    - Doc: [Reference documentation](https://docs.docker.com/reference/)
    - Guide: [Build images with BuildKit](https://docs.docker.com/develop/develop-images/build_enhancements/)

# MongoDB cheat sheet & tutorials
### Cheat sheet
- Login
    - `mongo -u <username> -p <password>`
    - Parameters:
        - *username*: *DB_ROOT_USERNAME* defined in `.env`
        - *password*: *DB_ROOT_PASSWORD* defined in `.env`
- Access database
    - `use <db_name>`
    - Parameters:
        - *db_name*: *DB_NAME* defined in `.env`
- List collections in current database
    - `show collections`
- Find all documents in a collection
    - `db.<collection_name>.find()`
    - Parameters:
        - *collection_name*: *DB_FLASHCARD_COLLECTION_NAME* defined in `.env`
- References
    - Doc: [MongoDB Documentation](https://docs.mongodb.com/)
