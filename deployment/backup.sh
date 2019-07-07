#!/bin/sh
# This is a script to backup the necessary components for a deployment with
# nginx and uwsgi with borgbackup.

# stop the services
service ticketfrei-web stop
service ticketfrei-backend stop

# export repository passphrase
export BORG_PASSPHRASE='password'

# create backup
borg create --stats --progress backup:repositories-borg/ticketfrei::'backup{now:%Y%m%d}' /etc/aliases /var/ticketfrei/db.sqlite /srv/ticketfrei/config.toml

# restart the service
service ticketfrei-backend start
service ticketfrei-web start

# prune outdated backups to save storage
borg prune --keep-daily=7 --keep-weekly=4 backup:repositories-borg/ticketfrei

