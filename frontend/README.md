# QoE Tool Frontend

React frontend for the QoE Tool application.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The frontend will run on http://localhost:3000

## Build

To build for production:
```bash
npm run build
```

The built files will be in the `dist` directory.

## API Configuration

The frontend is configured to proxy API requests to `http://localhost:8000` (the FastAPI backend). Make sure the backend is running before starting the frontend.


