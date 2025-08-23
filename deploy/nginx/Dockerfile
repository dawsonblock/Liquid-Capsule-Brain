FROM nginx:alpine
RUN apk add --no-cache bash openssl
COPY entrypoint.sh /entrypoint.sh
RUN mkdir -p /etc/nginx/templates
COPY cb.conf.template /etc/nginx/templates/cb.conf.template
EXPOSE 80 443
ENTRYPOINT ["/entrypoint.sh"]
