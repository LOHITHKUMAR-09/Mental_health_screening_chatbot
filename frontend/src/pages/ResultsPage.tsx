import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getResults } from '../api/chat'
import type { SessionResults, RiskLevel } from '../types'

const riskConfig: Record<RiskLevel, { label: string; color: string; emoji: string; message: string }> = {
  low: {
    label: 'Low Risk',
    color: 'risk-low',
    emoji: '🟢',
    message: 'Your responses suggest you are generally coping well. Keep maintaining healthy habits!',
  },
  moderate: {
    label: 'Moderate Risk',
    color: 'risk-moderate',
    emoji: '🟡',
    message: 'Your responses suggest some areas of concern. Consider speaking with a counselor for support.',
  },
  high: {
    label: 'High Risk',
    color: 'risk-high',
    emoji: '🔴',
    message: 'Your responses suggest significant distress. We strongly encourage you to reach out to a counselor soon.',
  },
}

export default function ResultsPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [results, setResults] = useState<SessionResults | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (sessionId) {
      getResults(sessionId)
        .then(setResults)
        .finally(() => setLoading(false))
    }
  }, [sessionId])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-slate-400 text-lg">Analyzing your responses... 🧠</p>
      </div>
    )
  }

  const risk = (results?.mlRiskLabel || results?.ruleBasedRisk || 'low') as RiskLevel
  const config = riskConfig[risk]

  return (
    <div className="min-h-screen bg-slate-50 py-10 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-slate-700">Your Results</h1>
          <p className="text-slate-400 mt-1 text-sm">Screening completed · Results are private</p>
        </div>

        {/* Risk Level Card */}
        <div className={`${config.color} rounded-2xl p-6 text-center`}>
          <div className="text-5xl mb-3">{config.emoji}</div>
          <h2 className="text-2xl font-bold">{config.label}</h2>
          <p className="mt-2 text-sm">{config.message}</p>
        </div>

        {/* Score Breakdown */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
          <h3 className="font-semibold text-slate-700 mb-4">Score Breakdown</h3>
          <div className="space-y-3">
            {results?.phq9Score !== undefined && (
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Depression (PHQ-9)</span>
                <span className="font-semibold">{results.phq9Score}/27 — {results.phq9Severity}</span>
              </div>
            )}
            {results?.gad7Score !== undefined && (
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Anxiety (GAD-7)</span>
                <span className="font-semibold">{results.gad7Score}/21 — {results.gad7Severity}</span>
              </div>
            )}
            {results?.pss10Score !== undefined && (
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">Stress (PSS-10)</span>
                <span className="font-semibold">{results.pss10Score}/40 — {results.pss10Severity}</span>
              </div>
            )}
            {results?.mlConfidence && (
              <div className="flex justify-between text-sm border-t border-slate-100 pt-3">
                <span className="text-slate-500">ML Model Confidence</span>
                <span className="font-semibold">{(results.mlConfidence * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>
        </div>

        {/* Coping Suggestions */}
        {results?.copingSuggestions?.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h3 className="font-semibold text-slate-700 mb-4">💡 Coping Suggestions</h3>
            <ul className="space-y-2">
              {results.copingSuggestions.map((tip, i) => (
                <li key={i} className="text-sm text-slate-600 flex gap-2">
                  <span className="text-primary-500">→</span> {tip}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Counseling Resources */}
        <div className="bg-sky-50 border border-sky-200 rounded-2xl p-6">
          <h3 className="font-semibold text-sky-700 mb-2">🏥 University Counseling Center</h3>
          <p className="text-sm text-sky-600">{results?.counselingResources?.name}</p>
          <p className="text-sm text-sky-600">{results?.counselingResources?.phone}</p>
          <a
            href={results?.counselingResources?.bookingUrl || '#'}
            className="mt-3 inline-block bg-sky-600 text-white text-sm font-semibold px-6 py-2 rounded-full hover:bg-sky-700 transition-all"
          >
            Book Appointment →
          </a>
        </div>

        <p className="text-center text-xs text-slate-400">
          Results are for informational purposes only and do not constitute a clinical diagnosis.
        </p>

        <button
          onClick={() => navigate('/')}
          className="w-full text-sky-600 underline text-sm"
        >
          Return to Home
        </button>
      </div>
    </div>
  )
}

