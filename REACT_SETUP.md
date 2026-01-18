# React Frontend Setup Guide

This guide explains how to set up and run the React frontend for the QoE Tool.

## Prerequisites

- Node.js (v18 or higher)
- npm (comes with Node.js)
- Python backend running on port 8000

## Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

### Development Mode

Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Production Build

To create a production build:
```bash
npm run build
```

The built files will be in the `dist` directory.

### Preview Production Build

To preview the production build locally:
```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable React components
│   │   └── PrivateRoute.jsx
│   ├── contexts/         # React context providers
│   │   └── AuthContext.jsx
│   ├── pages/           # Page components
│   │   ├── Landing.jsx
│   │   ├── SignUp.jsx
│   │   ├── Login.jsx
│   │   ├── Dashboard.jsx
│   │   └── GLProcessing.jsx
│   ├── services/        # API service layer
│   │   └── api.js
│   ├── App.jsx          # Main app component with routing
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles
├── index.html
├── package.json
└── vite.config.js
```

## API Configuration

The frontend is configured to proxy API requests to the FastAPI backend running on `http://localhost:8000`. This is configured in `vite.config.js`.

If your backend runs on a different port, update the proxy configuration in `vite.config.js`:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:YOUR_PORT',
    changeOrigin: true,
  }
}
```

## Features

- **Landing Page**: Marketing/landing page with feature highlights
- **Authentication**: Sign up and login functionality
- **Dashboard**: Project management interface
- **GL Processing**: Upload and process General Ledger files
- **Validation**: View validation results and metrics
- **Excel Download**: Download generated databooks

## Development Workflow

1. Start the Python backend (port 8000)
2. Start the React frontend (port 3000)
3. Open `http://localhost:3000` in your browser
4. The frontend will automatically reload when you make changes

## Troubleshooting

### Port Already in Use

If port 3000 is already in use, Vite will automatically try the next available port. Check the terminal output for the actual port.

### API Connection Issues

- Ensure the backend is running on port 8000
- Check browser console for CORS errors
- Verify the proxy configuration in `vite.config.js`

### Build Errors

- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be v18+)

