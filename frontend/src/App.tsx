import { useState, useEffect } from 'react'
import { checkHealth } from './api/health'

function App() {
  const [status, setStatus] = useState<'loading' | 'connected' | 'disconnected'>('loading')

  useEffect(() => {
    checkHealth()
      .then(() => setStatus('connected'))
      .catch(() => setStatus('disconnected'))
  }, [])

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900">Qdra</h1>
        <p className="mt-2 text-gray-600">Hello World</p>
        <div className="mt-4">
          <p className="text-gray-700">Backend Status:</p>
          {status === 'loading' && <p className="text-gray-500">Loading...</p>}
          {status === 'connected' && <p className="text-green-600 font-semibold">Connected</p>}
          {status === 'disconnected' && <p className="text-red-600 font-semibold">Disconnected</p>}
        </div>
      </div>
    </div>
  )
}

export default App
