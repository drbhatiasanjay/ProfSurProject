import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { TerminalErrorBoundary } from './components/shared/TerminalErrorBoundary';
import './index.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <TerminalErrorBoundary>
      <App />
    </TerminalErrorBoundary>
  </React.StrictMode>
);
