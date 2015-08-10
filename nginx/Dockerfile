FROM nginx
RUN mkdir /app/ /app/static/ /app/media/
VOLUME ["./static:/app/static/", "./media:/app/media/"]
ADD nginx.conf /etc/nginx/nginx.conf
