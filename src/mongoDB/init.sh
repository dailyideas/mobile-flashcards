echo "Initialize MongoDB"

mongo --username "$MONGO_INITDB_ROOT_USERNAME" \
--password "$MONGO_INITDB_ROOT_PASSWORD" \
--authenticationDatabase admin << EOF
use $MONGO_INITDB_DATABASE

const webScrapingCollections = [
    'cache.HtmlDataContainer'
]
for (var c of webScrapingCollections) {
    db.createCollection(c)
}

var workerPrivileges = webScrapingCollections.map(function(c) {
    return {
        resource: {
            db: '$MONGO_INITDB_DATABASE',
            collection: c
        },
        actions: ['createIndex', 'find', 'insert', 'remove', 'update']
    }
} )
db.createRole( {
    role: 'worker',
    roles: [],
    privileges: workerPrivileges
} )
db.createUser( {
    user: '$MONGO_INITDB_WORKER_USERNAME',
    pwd: '$MONGO_INITDB_WORKER_PASSWORD',
    roles: ['worker']
} )
EOF
