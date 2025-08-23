#!/usr/bin/env sh
set -eu
envsubst '$CB_DOMAIN $UPSTREAM_HOST $UPSTREAM_PORT' < /etc/nginx/templates/cb.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g 'daemon off;'
