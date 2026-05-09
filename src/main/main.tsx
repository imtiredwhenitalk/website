import React from 'react';
import { createRoot } from 'react-dom/client';
import Navbar from '../navbar/navbar';
import Chat from '../chat/chat';
import '../../static.css';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Missing #root element');
}

createRoot(rootElement).render(
  <React.StrictMode>
    <Navbar />
    <Chat />
  </React.StrictMode>,
);
