#!/bin/bash

path=$(dirname "$(readlink -f "$0")")
source "${path}/.env.sh"

/usr/local/bin/python -u /usr/app/main.py
