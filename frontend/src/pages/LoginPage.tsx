import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Connect to /auth/login API
    navigate('/chat')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-primary-50 px-4">
      <div className="bg-white rounded-2xl shadow-md p-8 w-full max-w-md">
        <div className="text-center mb-6">
          <div className="text-4xl mb-2">🧠</div>
          <h2 className="text-2xl font-bold text-slate-700">Sign In to MindEase</h2>
          <p className="text-slate-400 text-sm mt-1">Track your wellbeing over time</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <input
            type="email"
            placeholder="University Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full border border-slate-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary-400"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full border border-slate-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary-400"
          />
          <button
            type="submit"
            className="w-full bg-primary-600 text-white font-semibold py-3 rounded-xl hover:bg-primary-700 transition-all"
          >
            Sign In
          </button>
        </form>

        <p className="text-center text-slate-400 text-sm mt-4">
          Or{' '}
          <button onClick={() => navigate('/')} className="text-primary-600 underline">
            continue anonymously
          </button>
        </p>
      </div>
    </div>
  )
}
