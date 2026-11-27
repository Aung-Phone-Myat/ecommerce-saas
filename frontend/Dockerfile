FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies from the committed lockfile before copying the source.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite embeds the API origin at build time; the browser reaches the host port.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

FROM nginx:alpine

ENV PORT=80

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
