import { useNavigate } from 'react-router-dom'
import { loginAnonymous } from '../api/chat'

export default function HomePage() {
  const navigate = useNavigate()

  const handleStart = async () => {
    await loginAnonymous()
    navigate('/chat')
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-sky-50 to-white px-4">
      {/* Logo / Title */}
      <div className="text-center mb-10">
        <div className="text-5xl mb-4">🧠</div>
        <h1 className="text-4xl font-bold text-sky-700">MindEase</h1>
        <p className="text-slate-500 mt-2 text-lg">Mental Health Screening Chatbot for University Students</p>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl w-full mb-10">
        {[
          { icon: '🔒', title: 'Private & Secure', desc: 'Your responses are anonymized and encrypted.' },
          { icon: '⏱️', title: '10 Minutes', desc: 'A brief check-in covering stress, anxiety, and mood.' },
          { icon: '💬', title: 'Supportive', desc: 'Personalized coping suggestions and counseling links.' },
        ].map(({ icon, title, desc }) => (
          <div key={title} className="bg-white rounded-2xl shadow-sm border border-slate-100 p-5 text-center">
            <div className="text-3xl mb-2">{icon}</div>
            <h3 className="font-semibold text-slate-700">{title}</h3>
            <p className="text-slate-400 text-sm mt-1">{desc}</p>
          </div>
        ))}
      </div>

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 max-w-2xl w-full mb-6 text-sm text-amber-800">
        ⚠️ <strong>Disclaimer:</strong> MindEase is a screening tool, not a diagnostic service. It does not replace professional mental health care. If you are in crisis, please call <strong>9152987821</strong> (iCall) immediately.
      </div>

      {/* CTA Buttons */}
      <div className="flex gap-4">
        <button
          onClick={handleStart}
          className="bg-sky-600 hover:bg-sky-700 text-white font-semibold px-8 py-3 rounded-full shadow-md transition-all"
        >
          Start Screening (Anonymous)
        </button>
        <button
          onClick={() => navigate('/login')}
          className="border border-sky-600 text-sky-600 hover:bg-sky-50 font-semibold px-8 py-3 rounded-full transition-all"
        >
          Sign In
        </button>
      </div>
    </div>
  )
}

