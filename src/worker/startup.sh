#!/bin/bash

path=$(dirname "$(readlink -f "$0")")

printenv | grep ^APP_ | sed "s/^\(.*\)$/export \1/g" > ${path}/.env.sh
chmod +x ${path}/.env.sh

runInterval=$(expr 60 / $APP_FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR)
cronSchedule="*/$runInterval * * * *"

cat << EOF > /etc/cron.d/crontab
$cronSchedule root /usr/app/run.sh > /proc/1/fd/1 2>/proc/1/fd/2
EOF

cron -f
