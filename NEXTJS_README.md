# THE DENTAL BOND - Next.js Conversion

This is the Next.js version of THE DENTAL BOND scheduling system.

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Create `.env.local` from `.env.example`:
```bash
cp .env.example .env.local
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

- `app/` - Next.js App Router pages and layouts
- `app/api/` - API routes
- `components/` - React components
- `lib/` - Utility functions and types
- `public/` - Static assets

## Features

- **Scheduling**: Full schedule, by OP, ongoing, and upcoming views
- **Assistants**: Profile management, workload, availability, auto-allocation
- **Doctors**: Profile management, workload overview, per-doctor schedules
- **Admin**: User management, backup, notifications, duties

## Original Streamlit App

The original Streamlit application code is preserved in the `/o` folder for reference.

## Environment Variables

See `.env.example` for required environment variables.

## Build for Production

```bash
npm run build
npm start
```
