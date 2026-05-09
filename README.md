# website

Basic website skeleton (React + Vite) with a simple Navbar and a tiny API helper.

## Quick start

### 1) Install

In PowerShell from the project folder:

- If `npm` works normally:
	- `npm install`
- If PowerShell blocks `npm` (ExecutionPolicy error), run npm via `npm.cmd`:
	- `& 'C:\Program Files\nodejs\npm.cmd' install`

### 2) Run dev server

- `npm run dev`
- (or) `& 'C:\Program Files\nodejs\npm.cmd' run dev`

Open the URL Vite prints (usually `http://localhost:5173/`).

### 3) Build for production

- `npm run build`
- Then preview:
	- `npm run preview`

## What is where

- [index.html](index.html) — Vite entry HTML used by `npm run dev` / `build`.
- [static.html](static.html) — simple standalone HTML file (useful for quick checks), but TSX modules still need a server to run.
- [static.css](static.css) — base styles (also imported from TSX so it is bundled correctly).

### Source

- [src/main/main.tsx](src/main/main.tsx) — app entry point; mounts React into `#root`.
- [src/navbar/navbar.tsx](src/navbar/navbar.tsx) — `Navbar` component.
- [src/api/api.tsx](src/api/api.tsx) — minimal `api.get()` wrapper built on `fetch`.

## API notes

`Navbar` tries to request `GET /info` on page load. If you don’t have a backend running on the same origin that serves `/info`, you’ll see a “Failed to fetch /info” message — that’s expected.
