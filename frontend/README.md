# Promo Scenario Co-Pilot Frontend

React + TypeScript frontend for the Promo Scenario Co-Pilot application.

## Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm preview
```

## Environment Variables

Create a `.env` file in the frontend directory:

```
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable React components
│   ├── screens/         # Main application screens
│   ├── services/        # API client services
│   ├── hooks/           # Custom React hooks
│   └── App.tsx          # Main app component
├── public/              # Static assets
└── package.json         # Dependencies and scripts
```

## Features

- **Discovery Screen**: View opportunities and gap analysis
- **Scenario Lab**: Create and compare promotional scenarios
- **Optimization**: Generate optimized scenarios and view efficient frontier
- **Creative**: Generate creative briefs and asset specifications

## Tech Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- TanStack Query (React Query)
- Axios
