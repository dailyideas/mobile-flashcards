# mobile-flashcards README for developers

# Table of contents
1. [Git commit message best practices](#Git-commit-message-best-practices)
1. [Docker cheat sheet & tutorials](#Docker-cheat-sheet-&-tutorials)
1. [MongoDB cheat sheet & tutorials](#MongoDB-cheat-sheet-&-tutorials)

# Git commit message best practices
Mainly following the conventions suggested by [kazupon/git-commit-message-convention](https://github.com/kazupon/git-commit-message-convention). Therefore, this section is copied and modified from [kazupon/git-commit-message-convention](https://github.com/kazupon/git-commit-message-convention), which is licensed under the [MIT License](https://github.com/kazupon/git-commit-message-convention/blob/master/LICENSE).

### Commit message format
```
<Type>[(<Scope>)]: <Subject>
<BLANK-LINE-IF-ADDING-MESSAGE-BODY>
[<Message Body>]
<BLANK-LINE-IF-ADDING-MESSAGE-FOOTER>
[<Message Footer>]


NOTE:
<...>: Replace it will relevant/required content
[...]: Optional fields
```

### Commit message types
| Type          | Description                                                  |
| ------------- | ------------------------------------------------------------ |
| `new`         | This commit contains new feature(s)                          |
| `bug`         | This commit fixes bug(s) (including missing semi-colon)      |
| `docs`        | This commit modifies documentations (readme, notes, etc.)    |
| `example`     | This commit adds/modifies example codes                      |
| `test`        | This commit adds/modifies test codes                         |
| `security`    | This commit fixes security issue(s)                          |
| `performance` | This commit improves system performance                      |
| `refactor`    | This commit refactors the codes, without change any feature (change code structures, change variables naming, etc.) |
| `wip`         | This commit is ADDING something, but has yet to be done. Changes to existing codes must be completed before committing. |
| `deprecated`  | This commit alters deprecated feature(s)                     |
| `revert`      | This commit reverts a previous commit. Message body should says: This reverts commit `hash-of-commit-being-reverted`. |
| `chore`       | This commit changes very minor things that does not fall into any type above |

### Scope
Specifying place or category of the commit change.

### Subject
- Use the imperative, present tense: "change" not "changed" nor "changes".
- Don't capitalize first letter.
- No dot (.) at the end.

### Message Body
- Same requirements as in Subject.
- Include the motivation for the change and contrast this with previous behaviour.

### Message Footer
- Refer to GitHub issue ID, such as `Issue #27`, `Fixes #1`, `Closes #2`, `Resolves #3`.

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

### Tutorials
- Guide: [Best practices for writing Dockerfiles](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

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
