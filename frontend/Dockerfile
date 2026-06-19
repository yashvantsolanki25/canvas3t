FROM rustlang/rust:nightly AS wasm
WORKDIR /src
RUN cargo install wasm-pack --version 0.12.1
COPY wasm ./wasm
RUN cd wasm && wasm-pack build --release --target web --out-dir /tmp/pkg

FROM node:18-alpine AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

FROM node:18-alpine AS builder
WORKDIR /app
ARG VITE_API_URL=http://localhost:5000
ENV VITE_API_URL=$VITE_API_URL
COPY --from=deps /app/node_modules ./node_modules
COPY frontend .
COPY --from=wasm /tmp/pkg ./src/wasm/pkg
RUN npm run build

FROM nginx:alpine AS runner
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 4173
CMD ["nginx", "-g", "daemon off;"]

