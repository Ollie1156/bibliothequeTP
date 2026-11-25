# syntax=docker/dockerfile:1
# Le front est une simple page HTML : il n'y a rien à compiler, donc pas
# besoin d'étape de build. On utilise directement une image Nginx légère
# (alpine) et "unprivileged", c'est-à-dire qui tourne sans être root.
FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost:8080/health || exit 1
