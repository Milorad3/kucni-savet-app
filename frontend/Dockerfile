FROM node:20-slim AS builder
WORKDIR /app

# VAZNO: ovo "prevlaci" env varijablu iz Render dashboard-a UNUTAR docker build procesa.
# Bez ovoga, Next.js "peguje" fallback vrednost iz next.config.js (localhost) u kod,
# jer se NEXT_PUBLIC_* vrednosti ugradjuju u JS bundle tokom "npm run build" koraka,
# a Render env varijable su bez ovoga dostupne tek kada se kontejner POKRENE, ne dok se GRADI.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app ./
EXPOSE 3000
CMD ["npm", "start"]
