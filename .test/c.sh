#!/bin/bash

let b=12
a=$(expr 60 / $b)
cronSchedule="*/$a * * * *"
echo "$cronSchedule root /usr/app/run.sh"
