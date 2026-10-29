FROM node:24-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
# Sin scripts de instalación: el build no los necesita (comprobado) y así no depende
# de la versión de npm de la imagen ni de herramientas de compilación nativas.
RUN npm ci --ignore-scripts --no-audit --no-fund

COPY . .
RUN npx ng build --configuration production

FROM nginx:stable-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/valdelumbre/browser /usr/share/nginx/html
EXPOSE 80
