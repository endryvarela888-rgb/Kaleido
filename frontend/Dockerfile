# ---- Etapa 1: build de React con Vite ----
FROM node:22-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- Etapa 2: Nginx sirviendo el build + proxy al backend ----
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.docker.conf /etc/nginx/conf.d/default.conf

EXPOSE 80