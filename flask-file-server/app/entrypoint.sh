#!/bin/bash

echo "remove the unused default."
rm -f /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

echo "start uwsgi."
# uwsgi --http :9527 -s ./uwsgi.sock --chmod-socket=777 --manage-script-name --mount /uwsgi=main:APP
#uwsgi --ini uwsgi.ini &

#sleep 1

echo "start nginx."
# nginx -c /etc/nginx/nginx.conf &
# service nginx start
nginx_status=$(service nginx status)

if [[ $nginx_status == *"is running"* ]]; then
  echo "Nginx is already running."
else
  echo "Nginx is not running. Starting it now..."
  service nginx start

  sleep 1
  nginx_status=$(service nginx status)

  while [[ $nginx_status != *"is running"* ]]; do
    echo "Nginx failed to start. Trying again in 1 second..."
    sleep 1
    service nginx start
    sleep 1
    nginx_status=$(service nginx status)
  done

  echo "Nginx is now running."
fi
echo "all done... enter loop."

uwsgi --ini uwsgi.ini

#while true; do sleep 10; done
