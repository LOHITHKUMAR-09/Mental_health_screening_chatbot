import { useState, useRef, useEffect, useCallback } from 'react'
import { startSession, sendMessage, getResults } from '../api/chat'
import type { Message } from '../types'

// ── Types ──────────────────────────────────────────────────────────────────────
interface PendingQuestion {
  instrument: string
  item_number: number
  total_items: number
  question: string
  options: Record<number, string>
}

interface ScreeningResults {
  session_id: string
  phq9_score?: number
  phq9_severity?: string
  gad7_score?: number
  gad7_severity?: string
  pss10_score?: number
  pss10_severity?: string
  rule_based_risk?: string
  ml_risk_label?: string
  ml_confidence?: number
  shap_top_features?: Record<string, number>
  coping_suggestions?: string[]
  completed_at?: string  // for previous-session results
}

interface ResultsCardMessage extends Message {
  resultsSessionId: string
}

// ── Helpers ────────────────────────────────────────────────────────────────────
const SECTION_LABELS: Record<string, string> = {
  phq9: 'Mood Assessment (PHQ-9)',
  gad7: 'Anxiety Assessment (GAD-7)',
  pss10: 'Stress Assessment (PSS-10)',
}
const SECTION_COLORS: Record<string, string> = {
  phq9: 'from-sky-500 to-indigo-600',
  gad7: 'from-violet-500 to-purple-600',
  pss10: 'from-emerald-500 to-teal-600',
}
const RISK_CONFIG: Record<string, { label: string; bg: string; text: string; border: string; emoji: string; bar: string }> = {
  low:      { label: 'Low Risk',      bg: 'bg-emerald-50', text: 'text-emerald-800', border: 'border-emerald-300', emoji: '🟢', bar: 'bg-emerald-500' },
  moderate: { label: 'Moderate Risk', bg: 'bg-amber-50',   text: 'text-amber-800',   border: 'border-amber-300',   emoji: '🟡', bar: 'bg-amber-500'   },
  high:     { label: 'High Risk',     bg: 'bg-rose-50',    text: 'text-rose-800',    border: 'border-rose-300',    emoji: '🔴', bar: 'bg-rose-500'    },
}

// ── QuestionModal ──────────────────────────────────────────────────────────────
function QuestionModal({
  question,
  onAnswer,
  isSubmitting,
}: {
  question: PendingQuestion
  onAnswer: (value: number) => void
  isSubmitting: boolean
}) {
  const [selected, setSelected] = useState<number | null>(null)
  const options = Object.entries(question.options).map(([k, v]) => ({ value: Number(k), label: v as string }))
  const gradient = SECTION_COLORS[question.instrument] ?? 'from-sky-500 to-blue-600'
  const sectionLabel = SECTION_LABELS[question.instrument] ?? question.instrument.toUpperCase()
  const progress = (question.item_number / question.total_items) * 100

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden">
        {/* Header */}
        <div className={`bg-gradient-to-r ${gradient} px-6 py-5 text-white`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold tracking-wide uppercase opacity-90">{sectionLabel}</span>
            <span className="text-xs font-bold bg-white/20 px-2.5 py-1 rounded-full">
              {question.item_number} / {question.total_items}
            </span>
          </div>
          <div className="mt-3 bg-white/20 rounded-full h-1.5">
            <div className="bg-white rounded-full h-1.5 transition-all duration-500" style={{ width: `${progress}%` }} />
          </div>
        </div>

        {/* Question */}
        <div className="px-6 pt-6 pb-3">
          <p className="text-slate-800 font-semibold text-base leading-relaxed">{question.question}</p>
          <p className="text-slate-400 text-xs mt-1.5">Think about the relevant period and pick the closest match.</p>
        </div>

        {/* Options */}
        <div className="px-6 pb-4 space-y-2">
          {options.map((opt) => {
            const chosen = selected === opt.value
            return (
              <button
                key={opt.value}
                onClick={() => setSelected(opt.value)}
                disabled={isSubmitting}
                className={`w-full text-left flex items-center gap-3 px-4 py-3 rounded-2xl border-2 transition-all group
                  ${chosen ? 'border-sky-500 bg-sky-50 shadow-md shadow-sky-100' : 'border-slate-200 bg-white hover:border-sky-300 hover:bg-sky-50/50'}`}
              >
                <span className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors
                  ${chosen ? 'bg-sky-500 text-white' : 'bg-slate-100 text-slate-500 group-hover:bg-sky-100 group-hover:text-sky-600'}`}>
                  {opt.value}
                </span>
                <span className={`text-sm font-medium ${chosen ? 'text-sky-700' : 'text-slate-700'}`}>{opt.label}</span>
                {chosen && (
                  <span className="ml-auto text-sky-500">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </span>
                )}
              </button>
            )
          })}
        </div>

        {/* Confirm */}
        <div className="px-6 pb-6">
          <button
            onClick={() => { if (selected !== null) { onAnswer(selected); setSelected(null) } }}
            disabled={selected === null || isSubmitting}
            className="w-full bg-sky-600 hover:bg-sky-700 disabled:opacity-40 text-white font-semibold py-3.5 rounded-xl transition shadow-md shadow-sky-200 flex items-center justify-center gap-2"
          >
            {isSubmitting
              ? <><svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" /></svg>Saving…</>
              : 'Confirm Answer →'
            }
          </button>
          <p className="text-center text-xs text-slate-400 mt-2">🔒 Your answers are private and encrypted</p>
        </div>
      </div>
    </div>
  )
}

// ── ResultsModal ───────────────────────────────────────────────────────────────
function ResultsModal({
  results,
  onClose,
  onStartNew,
}: {
  results: ScreeningResults
  onClose: () => void
  onStartNew?: () => void
}) {
  const rawRisk = (results.ml_risk_label || results.rule_based_risk || 'low').toLowerCase()
  const riskKey = rawRisk === 'high' ? 'high' : rawRisk === 'moderate' ? 'moderate' : 'low'
  const cfg = RISK_CONFIG[riskKey]
  const coping: string[] = results.coping_suggestions ?? []
  const shap = results.shap_top_features

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-sky-500 to-blue-600 px-6 py-5 text-white flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide opacity-80">MindEase Screening Summary</p>
            <h2 className="text-lg font-bold mt-0.5">Your Mental Health Check-In</h2>
          </div>
          <button onClick={onClose} className="bg-white/20 hover:bg-white/30 rounded-full p-2 transition">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Risk badge */}
          <div className={`${cfg.bg} ${cfg.border} border-2 rounded-2xl p-5 text-center`}>
            <div className="text-4xl mb-1">{cfg.emoji}</div>
            <h3 className={`text-xl font-bold ${cfg.text}`}>{cfg.label}</h3>
            {results.ml_confidence && (
              <span className="inline-block mt-2 bg-white/80 border border-slate-200 text-xs font-semibold px-3 py-1 rounded-full text-slate-600">
                ML Confidence: {(results.ml_confidence * 100).toFixed(0)}%
              </span>
            )}
            {results.completed_at && (
              <p className="text-xs text-slate-500 mt-2">
                From screening on {new Date(results.completed_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
              </p>
            )}
          </div>

          {/* Scale scores */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'PHQ-9', sub: 'Depression', score: results.phq9_score, max: 27, sev: results.phq9_severity, color: 'text-sky-700' },
              { label: 'GAD-7', sub: 'Anxiety',    score: results.gad7_score,  max: 21, sev: results.gad7_severity,  color: 'text-violet-700' },
              { label: 'PSS-10', sub: 'Stress',    score: results.pss10_score, max: 40, sev: results.pss10_severity, color: 'text-emerald-700' },
            ].map((s) => (
              <div key={s.label} className="bg-slate-50 rounded-2xl p-3 border border-slate-100 text-center">
                <p className="text-xs text-slate-500 font-semibold uppercase">{s.sub}</p>
                <p className="text-xs text-slate-400 mt-0.5">{s.label}</p>
                <p className={`text-2xl font-black mt-1.5 ${s.color}`}>
                  {s.score ?? '—'}<span className="text-xs font-normal text-slate-400">/{s.max}</span>
                </p>
                <p className="text-xs text-slate-500 capitalize mt-0.5">{s.sev?.replace('_', ' ') ?? '—'}</p>
              </div>
            ))}
          </div>

          {/* SHAP features */}
          {shap && Object.keys(shap).length > 0 && (
            <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100">
              <p className="text-xs font-bold text-slate-600 mb-2">🔍 Top Influencing Factors</p>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(shap).map(([feat, imp]) => (
                  <span key={feat} className="bg-white text-slate-600 text-xs px-2.5 py-1 rounded-lg border border-slate-200">
                    {feat.toUpperCase()}: {((imp as number) * 100).toFixed(0)}%
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Coping suggestions */}
          {coping.length > 0 && (
            <div>
              <p className="text-sm font-bold text-slate-700 mb-2">💡 Recommended Actions</p>
              <ul className="space-y-2">
                {coping.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-700 bg-sky-50/60 p-3 rounded-xl border border-sky-100">
                    <span className="text-sky-500 font-bold mt-0.5">✓</span>
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Helplines */}
          <div className="bg-gradient-to-r from-sky-500 to-blue-600 text-white rounded-2xl p-4 space-y-2">
            <p className="text-xs font-bold">🏥 Campus Counseling & Emergency Contacts</p>
            <div className="grid grid-cols-2 gap-2">
              <a href="tel:9152987821" className="bg-white text-sky-700 font-bold text-xs p-2 rounded-xl text-center">iCall: 9152987821</a>
              <a href="tel:18602662345" className="bg-sky-700 text-white font-bold text-xs p-2 rounded-xl text-center">Vandrevala: 1860-2662-345</a>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button
              onClick={onClose}
              className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-3 rounded-xl text-sm transition"
            >
              Back to Chat
            </button>
            {onStartNew && (
              <button
                onClick={onStartNew}
                className="flex-1 bg-sky-600 hover:bg-sky-700 text-white font-semibold py-3 rounded-xl text-sm transition"
              >
                New Check-In
              </button>
            )}
          </div>

          <p className="text-center text-xs text-slate-400">
            Disclaimer: MindEase is a screening tool, not a medical diagnosis. Contact 112 for emergencies.
          </p>
        </div>
      </div>
    </div>
  )
}

// ── Results Card (inline chat bubble) ─────────────────────────────────────────
function ResultsCard({ results, onView }: { results: ScreeningResults; onView: () => void }) {
  const rawRisk = (results.ml_risk_label || results.rule_based_risk || 'low').toLowerCase()
  const riskKey = rawRisk === 'high' ? 'high' : rawRisk === 'moderate' ? 'moderate' : 'low'
  const cfg = RISK_CONFIG[riskKey]

  return (
    <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-none shadow-sm overflow-hidden max-w-[85%]">
      <div className="bg-gradient-to-r from-sky-500 to-blue-600 px-4 py-2.5 flex items-center gap-2">
        <span className="text-white text-xs font-semibold">📋 Screening Results</span>
        <span className="ml-auto text-xs text-sky-100">Completed</span>
      </div>
      <div className="px-4 py-3 space-y-2">
        <div className={`${cfg.bg} ${cfg.border} border rounded-xl px-3 py-2 flex items-center gap-2`}>
          <span className="text-lg">{cfg.emoji}</span>
          <div>
            <p className={`text-xs font-bold ${cfg.text}`}>{cfg.label}</p>
            <p className="text-xs text-slate-500">
              PHQ-9: {results.phq9_score ?? '—'} · GAD-7: {results.gad7_score ?? '—'} · PSS-10: {results.pss10_score ?? '—'}
            </p>
          </div>
        </div>
        <button
          onClick={onView}
          className="w-full text-xs font-semibold text-sky-600 hover:text-sky-700 hover:bg-sky-50 py-1.5 rounded-lg transition text-center border border-sky-200"
        >
          View Full Results →
        </button>
      </div>
    </div>
  )
}

// ── Cooldown Suggestion Card (chat bubble for blocked sessions) ─────────────────
function CooldownCard({
  results,
  hoursLeft,
  onViewPrevious,
}: {
  results: ScreeningResults | null
  hoursLeft: number | null
  onViewPrevious: () => void
}) {
  const rawRisk = (results?.ml_risk_label || results?.rule_based_risk || 'low').toLowerCase()
  const riskKey = rawRisk === 'high' ? 'high' : rawRisk === 'moderate' ? 'moderate' : 'low'
  const cfg = RISK_CONFIG[riskKey]

  return (
    <div className="bg-white border border-amber-200 rounded-2xl rounded-bl-none shadow-sm overflow-hidden max-w-[85%]">
      <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 flex items-center gap-2">
        <span className="text-amber-700 text-xs font-semibold">⏱ Screening Cooldown Active</span>
        {hoursLeft !== null && (
          <span className="ml-auto text-xs text-amber-500">{hoursLeft}h remaining</span>
        )}
      </div>
      <div className="px-4 py-3 space-y-2 text-xs text-slate-600">
        <p>You completed a screening recently. To protect your wellbeing, the full questionnaire will be available again after the cooldown period.</p>
        {results && (
          <div className={`${cfg.bg} ${cfg.border} border rounded-xl px-3 py-2 flex items-center gap-2`}>
            <span className="text-lg">{cfg.emoji}</span>
            <div>
              <p className={`text-xs font-bold ${cfg.text}`}>Last result: {cfg.label}</p>
              <p className="text-xs text-slate-500">PHQ-9: {results.phq9_score ?? '—'} · GAD-7: {results.gad7_score ?? '—'} · PSS-10: {results.pss10_score ?? '—'}</p>
            </div>
          </div>
        )}
        <button
          onClick={onViewPrevious}
          className="w-full text-xs font-semibold text-sky-600 hover:text-sky-700 hover:bg-sky-50 py-1.5 rounded-lg transition text-center border border-sky-200"
        >
          View Previous Results →
        </button>
      </div>
    </div>
  )
}

// ── Main ChatPage ──────────────────────────────────────────────────────────────
export default function ChatPage() {
  const [sessionId, setSessionId]             = useState<string | null>(null)
  const [messages, setMessages]               = useState<Message[]>([])
  const [inputText, setInputText]             = useState('')
  const [isTyping, setIsTyping]               = useState(false)
  const [isCrisis, setIsCrisis]               = useState(false)
  const [consentGiven, setConsentGiven]       = useState(false)
  const [currentState, setCurrentState]       = useState<string>('greeting')
  const [error, setError]                     = useState<string | null>(null)

  // Question popup
  const [activeQuestion, setActiveQuestion]   = useState<PendingQuestion | null>(null)
  const [isModalSubmitting, setIsModalSubmitting] = useState(false)

  // Results modal
  const [showResultsModal, setShowResultsModal] = useState(false)
  const [resultsData, setResultsData]           = useState<ScreeningResults | null>(null)

  // Cooldown state (previous session results when blocked)
  const [prevResults, setPrevResults]           = useState<ScreeningResults | null>(null)
  const [cooldownHours, setCooldownHours]       = useState<number | null>(null)

  // Track which messages have inline results cards keyed by messageId → results
  const [resultsCards, setResultsCards] = useState<Record<string, ScreeningResults>>({})

  const bottomRef = useRef<HTMLDivElement>(null)

  const isQuestionnaireState = (s: string) => s === 'phq9' || s === 'gad7' || s === 'pss10'

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const addBotMessage = (content: string): string => {
    const id = crypto.randomUUID()
    setMessages(prev => [...prev, { id, sender: 'bot', content, timestamp: new Date() }])
    return id
  }

  // ── Fetch & show results in modal, add card to chat ──────────────
  const loadAndShowResults = useCallback(async (sid: string, attachToMsgId?: string) => {
    try {
      const data = await getResults(sid)
      setResultsData(data)
      setShowResultsModal(true)
      if (attachToMsgId) {
        setResultsCards(prev => ({ ...prev, [attachToMsgId]: data }))
      }
    } catch (e) {
      console.error('Failed to load results', e)
    }
  }, [])

  // ── Session init ──────────────────────────────────────────────────
  const initSession = async () => {
    try {
      setError(null)
      const session = await startSession()
      setSessionId(session.session_id)
      const state = session.current_state || 'greeting'
      setCurrentState(state)

      if (session.questionnaire_blocked) {
        // Cooldown mode
        setPrevResults(session.previous_results ?? null)
        setCooldownHours(session.cooldown_remaining_hours ?? null)

        const cardMsgId = addBotMessage(
          `Hello again! 💙 I'm glad you're checking in.\n\nYou recently completed a full mental health screening, so the full questionnaire won't run again yet — this protects the validity of your results.\n\nI can still chat with you, share coping suggestions based on your last results, or answer any questions you have.`
        )
        // Add cooldown card after a small delay so it appears below the bot message
        setTimeout(() => {
          const cooldownId = crypto.randomUUID()
          setMessages(prev => [...prev, {
            id: cooldownId,
            sender: 'bot',
            content: '__COOLDOWN_CARD__',
            timestamp: new Date(),
          }])
        }, 300)
      } else {
        addBotMessage(
          "Hello! I'm MindEase 🌿\n\nI'm here to guide you through a brief, confidential mental health check-in covering mood, anxiety, and stress.\n\nType anything or click 'Start' below to begin."
        )
      }
    } catch (err) {
      setError('Could not connect to the server. Please ensure the backend is running on port 8000.')
      console.error('Session init error:', err)
    }
  }

  // ── Core send (used by text input + question modal) ───────────────
  const handleSend = async (customText?: string) => {
    const textToSend = (customText ?? inputText).trim()
    if (!textToSend || !sessionId || isTyping) return

    setMessages(prev => [...prev, {
      id: crypto.randomUUID(),
      sender: 'user',
      content: textToSend,
      timestamp: new Date(),
    }])
    if (!customText) setInputText('')
    setIsTyping(true)
    setError(null)

    try {
      const response = await sendMessage(sessionId, textToSend)
      const state = response.current_state || response.currentState || 'greeting'
      setCurrentState(state)

      if (response.is_crisis || response.isCrisis) {
        setIsCrisis(true)
        setActiveQuestion(null)
      }

      const botMsg = response.bot_message || response.botMessage || 'Thank you.'
      const newMsgId = addBotMessage(botMsg)

      // Open questionnaire modal for next question
      const item = response.questionnaire_item ?? response.questionnaireItem
      if (item && !response.is_crisis) {
        setActiveQuestion(item as PendingQuestion)
      } else {
        setActiveQuestion(null)
      }

      // Screening complete → fetch results, embed card in chat, show modal, stay on chat
      if (state === 'results' || response.screening_complete || response.screeningComplete) {
        setActiveQuestion(null)
        if (sessionId) {
          await loadAndShowResults(sessionId, newMsgId)
          // Mark session complete on backend
          try {
            await fetch(`http://localhost:8000/api/v1/sessions/${sessionId}/complete`, { method: 'POST' })
          } catch {}
        }
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Something went wrong.'
      addBotMessage(`⚠️ Sorry, I encountered an error: ${msg}\n\nPlease try again.`)
      console.error('Send message error:', err)
    } finally {
      setIsTyping(false)
      setIsModalSubmitting(false)
    }
  }

  const handleModalAnswer = (value: number) => {
    setIsModalSubmitting(true)
    setActiveQuestion(null)
    handleSend(String(value))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // ── Consent screen ────────────────────────────────────────────────
  if (!consentGiven) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="bg-white rounded-3xl shadow-xl border border-slate-100 p-8 max-w-lg w-full">
          <div className="text-center mb-6">
            <div className="text-5xl mb-3">🌿</div>
            <h2 className="text-2xl font-bold text-slate-800">Informed Consent</h2>
            <p className="text-slate-500 text-sm mt-1">Please review before starting your screening</p>
          </div>
          <div className="bg-sky-50/70 border border-sky-100 rounded-2xl p-5 text-slate-700 text-sm space-y-3 mb-6">
            <p>🔒 <strong>Confidential &amp; Secure:</strong> Your responses are encrypted and private.</p>
            <p>📋 <strong>Validated Instruments:</strong> Uses standard PHQ-9, GAD-7, and PSS-10 scales.</p>
            <p>⚠️ <strong>Screening Only:</strong> This is a mental wellness check-in, not a medical diagnosis.</p>
            <p>🆘 <strong>24/7 Safety Support:</strong> Emergency helplines (iCall &amp; Vandrevala) are always available.</p>
          </div>
          {error && <p className="text-red-500 text-sm mb-4 text-center">{error}</p>}
          <button
            onClick={() => { setConsentGiven(true); initSession() }}
            className="w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-3.5 px-6 rounded-xl transition duration-200 shadow-md shadow-sky-200"
          >
            I Understand and Agree — Begin Check-In
          </button>
        </div>
      </div>
    )
  }

  // ── Main chat view ────────────────────────────────────────────────
  return (
    <>
      <div className="flex flex-col h-screen bg-slate-50">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-6 py-3.5 flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-sky-100 flex items-center justify-center text-xl">🌿</div>
            <div>
              <h1 className="font-bold text-slate-800 text-base">MindEase Check-In</h1>
              <p className="text-xs text-slate-500 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse" />
                {currentState === 'phq9'     ? 'Section 1/3: Mood (PHQ-9)' :
                 currentState === 'gad7'     ? 'Section 2/3: Anxiety (GAD-7)' :
                 currentState === 'pss10'    ? 'Section 3/3: Stress (PSS-10)' :
                 currentState === 'results'  ? 'Screening Complete' :
                 currentState === 'cooldown' ? 'Cooldown — Chat Mode' :
                 'Confidential Assessment'}
              </p>
            </div>
          </div>
          {resultsData && (
            <button
              onClick={() => setShowResultsModal(true)}
              className="text-xs text-sky-600 font-semibold hover:text-sky-700 px-3 py-1.5 rounded-lg border border-sky-200 hover:bg-sky-50 transition"
            >
              📋 View Results
            </button>
          )}
        </header>

        {/* Crisis banner */}
        {isCrisis && (
          <div className="bg-rose-500 text-white px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-3 shadow-lg">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🆘</span>
              <div>
                <p className="font-bold text-sm">Crisis Support Available Immediately</p>
                <p className="text-xs text-rose-100">You are not alone. Please reach out to counselors right now.</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <a href="tel:9152987821" className="bg-white text-rose-600 text-xs font-bold px-3 py-1.5 rounded-lg shadow-sm">iCall: 9152987821</a>
              <a href="tel:18602662345" className="bg-rose-700 hover:bg-rose-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg">Vandrevala: 1860-2662-345</a>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 max-w-3xl mx-auto w-full">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              {/* Cooldown card (special sentinel message) */}
              {msg.content === '__COOLDOWN_CARD__' ? (
                <CooldownCard
                  results={prevResults}
                  hoursLeft={cooldownHours}
                  onViewPrevious={() => {
                    if (prevResults) {
                      setResultsData(prevResults)
                      setShowResultsModal(true)
                    }
                  }}
                />
              ) : resultsCards[msg.id] ? (
                /* Results card attached to bot message */
                <div className="flex flex-col gap-2 max-w-[85%]">
                  <div className="bg-white text-slate-800 border border-slate-100 rounded-2xl rounded-bl-none px-5 py-3.5 shadow-sm text-sm whitespace-pre-wrap leading-relaxed">
                    {msg.content}
                  </div>
                  <ResultsCard
                    results={resultsCards[msg.id]}
                    onView={() => {
                      setResultsData(resultsCards[msg.id])
                      setShowResultsModal(true)
                    }}
                  />
                </div>
              ) : (
                /* Normal chat bubble */
                <div className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-5 py-3.5 shadow-sm text-sm whitespace-pre-wrap leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-sky-600 text-white rounded-br-none'
                    : 'bg-white text-slate-800 border border-slate-100 rounded-bl-none'
                }`}>
                  {msg.content}
                </div>
              )}
            </div>
          ))}

          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-100 rounded-2xl rounded-bl-none px-4 py-3 flex items-center space-x-1.5 shadow-sm">
                <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:0.2s]" />
                <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="bg-white border-t border-slate-200 p-4 shadow-sm">
          <div className="max-w-3xl mx-auto flex items-center space-x-3">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                isQuestionnaireState(currentState)
                  ? 'Use the question popup to answer…'
                  : 'Type your message…'
              }
              className="flex-1 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 bg-slate-50/50 disabled:opacity-50"
              disabled={isTyping || isQuestionnaireState(currentState)}
            />
            <button
              onClick={() => handleSend()}
              disabled={!inputText.trim() || isTyping || isQuestionnaireState(currentState)}
              className="bg-sky-600 hover:bg-sky-700 disabled:opacity-40 text-white font-medium px-5 py-3 rounded-xl text-sm transition shadow-sm"
            >
              Send
            </button>
          </div>
        </div>
      </div>

      {/* Question popup modal */}
      {activeQuestion && !isCrisis && (
        <QuestionModal
          question={activeQuestion}
          onAnswer={handleModalAnswer}
          isSubmitting={isModalSubmitting}
        />
      )}

      {/* Results modal */}
      {showResultsModal && resultsData && (
        <ResultsModal
          results={resultsData}
          onClose={() => setShowResultsModal(false)}
          onStartNew={currentState === 'results' ? () => {
            setShowResultsModal(false)
            setConsentGiven(false)
            setMessages([])
            setSessionId(null)
            setCurrentState('greeting')
            setResultsData(null)
            setResultsCards({})
          } : undefined}
        />
      )}
    </>
  )
}
