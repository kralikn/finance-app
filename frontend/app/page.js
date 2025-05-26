'use client';
import { useEffect, useState } from 'react';

export default function Home() {
  const [apiStatus, setApiStatus] = useState('loading...');

  useEffect(() => {
    fetch('http://localhost:8000/api/health')
      .then(res => res.json())
      .then(data => setApiStatus(data.status))
      .catch(() => setApiStatus('error - API nem elérhető'));
  }, []);

  return (
    <div className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Finance App
        </h1>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-lg text-gray-800">
            API Státusz: <span className="font-semibold">{apiStatus}</span>
          </p>
        </div>
      </div>
    </div>
  );
}