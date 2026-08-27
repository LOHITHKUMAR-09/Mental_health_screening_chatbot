import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getResults } from '../api/chat'

type RiskLevel = 'low' | 'moderate' | 'high'

const riskConfig: Record<RiskLevel, { label: string; bg: string; text: string; border: string; emoji: string; message: string }> = {
  low: {
    label: 'Low Risk',
    bg: 'bg-emerald-50',
    text: 'text-emerald-800',
    border: 'border-emerald-200',
    emoji: '🟢',
    message: 'Your responses suggest you are generally coping well. Keep practicing healthy self-care habits!',
  },
  moderate: {
    label: 'Moderate Risk',
    bg: 'bg-amber-50',
    text: 'text-amber-800',
    border: 'border-amber-200',
    emoji: '🟡',
    message: 'Your responses suggest some elevated distress. Speaking with a campus counselor or practicing grounding exercises can help.',
  },
  high: {
    label: 'High Risk',
    bg: 'bg-rose-50',
    text: 'text-rose-800',
    border: 'border-rose-200',
    emoji: '🔴',
    message: 'Your responses suggest significant emotional distress. We strongly encourage you to connect with a counseling professional.',
  },
}

export default function ResultsPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [results, setResults] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (sessionId) {
      getResults(sessionId)
        .then((data) => setResults(data))
        .catch((err) => {
          console.error("Results fetch error:", err)
          setError("Failed to load results. Please make sure the screening was completed.")
        })
        .finally(() => setLoading(false))
    }
  }, [sessionId])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="text-5xl animate-bounce">🌿</div>
          <p className="text-slate-600 font-medium text-base">Analyzing clinical scores & ML risk profile...</p>
        </div>
      </div>
    )
  }

  if (error || !results) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full text-center shadow-sm border border-slate-200">
          <div className="text-4xl mb-3">⚠️</div>
          <h2 className="text-lg font-bold text-slate-800 mb-2">Results Unavailable</h2>
          <p className="text-slate-500 text-sm mb-6">{error || "No results found for this session."}</p>
          <button
            onClick={() => navigate('/chat')}
            className="w-full bg-sky-600 hover:bg-sky-700 text-white font-medium py-2.5 px-4 rounded-xl text-sm transition"
          >
            Start New Screening
          </button>
        </div>
      </div>
    )
  }

  const rawRisk = (results.ml_risk_label || results.rule_based_risk || results.mlRiskLabel || results.ruleBasedRisk || 'low').toLowerCase()
  const riskKey: RiskLevel = rawRisk === 'high' ? 'high' : rawRisk === 'moderate' ? 'moderate' : 'low'
  const config = riskConfig[riskKey]

  const phq9Score = results.phq9_score ?? results.phq9Score
  const phq9Sev = results.phq9_severity ?? results.phq9Severity ?? 'minimal'
  const gad7Score = results.gad7_score ?? results.gad7Score
  const gad7Sev = results.gad7_severity ?? results.gad7Severity ?? 'minimal'
  const pss10Score = results.pss10_score ?? results.pss10Score
  const pss10Sev = results.pss10_severity ?? results.pss10Severity ?? 'low'
  const mlConfidence = results.ml_confidence ?? results.mlConfidence
  const shapFeatures = results.shap_top_features ?? results.shapTopFeatures
  const copingList: string[] = results.coping_suggestions ?? results.copingSuggestions ?? []


  return (
    <div className="min-h-screen bg-slate-50 py-10 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="text-center">
          <div className="inline-block p-2 bg-sky-100 rounded-full text-2xl mb-2">🌿</div>
          <h1 className="text-3xl font-bold text-slate-800">Your Screening Summary</h1>
          <p className="text-slate-500 mt-1 text-sm">Completed · Private & Confidential</p>
        </div>

        {/* ── Composite Risk Card ─────────────────────────────────────── */}
        <div className={`${config.bg} ${config.border} border-2 rounded-3xl p-6 text-center shadow-sm`}>
          <div className="text-5xl mb-2">{config.emoji}</div>
          <h2 className={`text-2xl font-bold ${config.text}`}>{config.label}</h2>
          <p className={`mt-2 text-sm max-w-md mx-auto ${config.text}`}>{config.message}</p>
          {mlConfidence && (
            <span className="inline-block mt-3 bg-white/80 border border-slate-200 text-xs font-semibold px-3 py-1 rounded-full text-slate-600">
              ML Model Confidence: {(mlConfidence * 100).toFixed(0)}% (XGBoost Classifier)
            </span>
          )}
        </div>

        {/* ── Standardized Clinical Scales Breakdown ──────────────────── */}
        <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6 space-y-4">
          <h3 className="font-bold text-slate-800 text-base">Standardized Assessment Scales</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* PHQ-9 */}
            <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wide">Depression</div>
              <div className="text-sm font-semibold text-slate-800 mt-0.5">PHQ-9</div>
              <div className="text-2xl font-black text-sky-700 mt-2">{phq9Score ?? '—'}<span className="text-xs font-normal text-slate-400">/27</span></div>
              <div className="text-xs font-medium text-slate-600 capitalize mt-1">Severity: {phq9Sev.replace('_', ' ')}</div>
            </div>

            {/* GAD-7 */}
            <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wide">Anxiety</div>
              <div className="text-sm font-semibold text-slate-800 mt-0.5">GAD-7</div>
              <div className="text-2xl font-black text-sky-700 mt-2">{gad7Score ?? '—'}<span className="text-xs font-normal text-slate-400">/21</span></div>
              <div className="text-xs font-medium text-slate-600 capitalize mt-1">Severity: {gad7Sev.replace('_', ' ')}</div>
            </div>

            {/* PSS-10 */}
            <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wide">Perceived Stress</div>
              <div className="text-sm font-semibold text-slate-800 mt-0.5">PSS-10</div>
              <div className="text-2xl font-black text-sky-700 mt-2">{pss10Score ?? '—'}<span className="text-xs font-normal text-slate-400">/40</span></div>
              <div className="text-xs font-medium text-slate-600 capitalize mt-1">Severity: {pss10Sev.replace('_', ' ')}</div>
            </div>
          </div>
        </div>

        {/* ── Top Explainability Drivers (SHAP) ───────────────────────── */}
        {shapFeatures && Object.keys(shapFeatures).length > 0 && (
          <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6">
            <h3 className="font-bold text-slate-800 text-sm mb-3">🔍 ML Explainability (Top Influencing Factors)</h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(shapFeatures).map(([feat, imp]: [string, any]) => (
                <span key={feat} className="bg-slate-100 text-slate-700 text-xs font-medium px-3 py-1.5 rounded-xl border border-slate-200">
                  {feat.toUpperCase()}: {(imp * 100).toFixed(1)}% influence
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ── Personalized Coping Suggestions ─────────────────────────── */}
        {copingList.length > 0 && (
          <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6">
            <h3 className="font-bold text-slate-800 text-base mb-3">💡 Recommended Self-Care & Coping Strategies</h3>
            <ul className="space-y-2.5">
              {copingList.map((tip, i) => (
                <li key={i} className="text-sm text-slate-700 flex items-start gap-2.5 bg-slate-50/70 p-3 rounded-xl border border-slate-100">
                  <span className="text-sky-600 font-bold">✓</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* ── Support & Helplines Card ─────────────────────────────────── */}
        <div className="bg-gradient-to-br from-sky-500 to-blue-600 text-white rounded-3xl p-6 shadow-md shadow-sky-100 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-base">🏥 Campus Counseling & Emergency Contacts</h3>
            <span className="text-xl">🆘</span>
          </div>
          <p className="text-xs text-sky-100">Confidential support is available free of charge anytime.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 text-xs">
            <a href="tel:9152987821" className="bg-white text-sky-700 font-bold p-2.5 rounded-xl text-center shadow-sm hover:bg-sky-50 transition">
              iCall Helpline: 9152987821
            </a>
            <a href="tel:18602662345" className="bg-sky-700 text-white font-bold p-2.5 rounded-xl text-center hover:bg-sky-800 transition">
              Vandrevala: 1860-2662-345
            </a>
          </div>
        </div>

        {/* ── Disclaimer & Actions ────────────────────────────────────── */}
        <p className="text-center text-xs text-slate-400 px-4">
          Disclaimer: MindEase is an automated clinical screening tool, not a medical diagnosis. If you are experiencing severe distress or crisis, please contact emergency services (112) immediately.
        </p>

        <div className="flex gap-3">
          <button
            onClick={() => navigate('/chat')}
            className="flex-1 bg-sky-600 hover:bg-sky-700 text-white font-semibold py-3 px-4 rounded-xl text-sm transition shadow-sm"
          >
            Start Another Check-In
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex-1 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-semibold py-3 px-4 rounded-xl text-sm transition"
          >
            Home Page
          </button>
        </div>
      </div>
    </div>
  )
}
