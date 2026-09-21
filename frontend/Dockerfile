FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Where the FastAPI backend lives. docker-compose reaches it by service name;
# override this in deployments where frontend and backend are separate hosts
# (e.g. Render, where each service gets its own onrender.com URL).
ENV BACKEND_ORIGIN=http://backend:8000

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
