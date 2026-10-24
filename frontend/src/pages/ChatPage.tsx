import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { startSession, sendMessage } from '../api/chat'
import type { Message } from '../types'

// ── Types ──────────────────────────────────────────────────────────
interface LikertOption {
  value: number
  label: string
}

interface PendingQuestion {
  instrument: string
  item_number: number
  total_items: number
  question: string
  options: Record<number, string>
  options_str: string
}

const SECTION_LABELS: Record<string, string> = {
  phq9:  'Mood Assessment (PHQ-9)',
  gad7:  'Anxiety Assessment (GAD-7)',
  pss10: 'Stress Assessment (PSS-10)',
}

const SECTION_COLORS: Record<string, string> = {
  phq9:  'from-sky-500 to-indigo-600',
  gad7:  'from-violet-500 to-purple-600',
  pss10: 'from-emerald-500 to-teal-600',
}

// ── Question Modal Component ────────────────────────────────────────
interface QuestionModalProps {
  question: PendingQuestion
  onAnswer: (value: number, label: string) => void
  isSubmitting: boolean
}

function QuestionModal({ question, onAnswer, isSubmitting }: QuestionModalProps) {
  const [selected, setSelected] = useState<number | null>(null)
  const options = Object.entries(question.options).map(([k, v]) => ({
    value: Number(k),
    label: v as string,
  }))

  const headerGradient = SECTION_COLORS[question.instrument] ?? 'from-sky-500 to-blue-600'
  const sectionLabel   = SECTION_LABELS[question.instrument] ?? question.instrument.toUpperCase()
  const progress       = (question.item_number / question.total_items) * 100

  const handleConfirm = () => {
    if (selected === null || isSubmitting) return
    const label = question.options[selected] ?? String(selected)
    onAnswer(selected, label)
    setSelected(null)
  }

  return (
    // Backdrop
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200">

        {/* ── Header ── */}
        <div className={`bg-gradient-to-r ${headerGradient} px-6 py-5 text-white`}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold tracking-wide uppercase opacity-90">
              {sectionLabel}
            </span>
            <span className="text-xs font-bold opacity-90 bg-white/20 px-2.5 py-1 rounded-full">
              {question.item_number} / {question.total_items}
            </span>
          </div>
          {/* Progress bar */}
          <div className="mt-3 bg-white/20 rounded-full h-1.5">
            <div
              className="bg-white rounded-full h-1.5 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* ── Question Text ── */}
        <div className="px-6 pt-6 pb-4">
          <p className="text-slate-800 font-semibold text-base leading-relaxed">
            {question.question}
          </p>
          <p className="text-slate-400 text-xs mt-2">
            Think about how you have been feeling over the relevant period and pick the best match.
          </p>
        </div>

        {/* ── Options ── */}
        <div className="px-6 pb-4 space-y-2.5">
          {options.map((opt) => {
            const isChosen = selected === opt.value
            return (
              <button
                key={opt.value}
                onClick={() => setSelected(opt.value)}
                disabled={isSubmitting}
                className={`w-full text-left flex items-center gap-4 px-4 py-3.5 rounded-2xl border-2 transition-all duration-150 group
                  ${isChosen
                    ? 'border-sky-500 bg-sky-50 shadow-md shadow-sky-100'
                    : 'border-slate-200 bg-white hover:border-sky-300 hover:bg-sky-50/50'
                  }`}
              >
                {/* Option number circle */}
                <span className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors
                  ${isChosen ? 'bg-sky-500 text-white' : 'bg-slate-100 text-slate-500 group-hover:bg-sky-100 group-hover:text-sky-600'}`}>
                  {opt.value}
                </span>
                <span className={`text-sm font-medium transition-colors ${isChosen ? 'text-sky-700' : 'text-slate-700'}`}>
                  {opt.label}
                </span>
                {isChosen && (
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

        {/* ── Confirm Button ── */}
        <div className="px-6 pb-6">
          <button
            onClick={handleConfirm}
            disabled={selected === null || isSubmitting}
            className="w-full bg-sky-600 hover:bg-sky-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-3.5 rounded-xl transition duration-150 shadow-md shadow-sky-200 flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Saving…
              </>
            ) : (
              'Confirm Answer →'
            )}
          </button>
          <p className="text-center text-xs text-slate-400 mt-2">
            🔒 Your answers are private and encrypted
          </p>
        </div>
      </div>
    </div>
  )
}


// ── Main Chat Page ──────────────────────────────────────────────────
export default function ChatPage() {
  const navigate = useNavigate()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputText, setInputText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isCrisis, setIsCrisis] = useState(false)
  const [consentGiven, setConsentGiven] = useState(false)
  const [currentState, setCurrentState] = useState<string>('greeting')
  const [error, setError] = useState<string | null>(null)
  // Modal state — holds the current questionnaire question from the backend
  const [activeQuestion, setActiveQuestion] = useState<PendingQuestion | null>(null)
  const [isModalSubmitting, setIsModalSubmitting] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const isQuestionnaireState = (state: string) =>
    state === 'phq9' || state === 'gad7' || state === 'pss10'

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const addBotMessage = (content: string) => {
    setMessages(prev => [...prev, {
      id: crypto.randomUUID(),
      sender: 'bot',
      content,
      timestamp: new Date(),
    }])
  }

  const initSession = async () => {
    try {
      setError(null)
      const session = await startSession()
      setSessionId(session.session_id)
      setCurrentState('greeting')
      addBotMessage(
        "Hello! I'm MindEase 🌿\n\nI'm here to guide you through a brief, confidential mental health check-in covering mood, anxiety, and stress.\n\nType anything or click 'Start' below to begin."
      )
    } catch (err) {
      setError('Could not connect to the server. Please ensure the backend is running on port 8000.')
      console.error('Session init error:', err)
    }
  }

  // Core send — called both from the text input and from the modal
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
      addBotMessage(botMsg)

      // If the backend returns a pending questionnaire item, open the modal.
      // This covers both mid-section questions AND the transition from
      // background → phq9 (where state may still be "background" but item is present).
      const item = response.questionnaire_item ?? response.questionnaireItem
      if (item && !response.is_crisis) {
        setActiveQuestion(item as PendingQuestion)
      } else {
        setActiveQuestion(null)
      }

      if (state === 'results' || response.screening_complete || response.screeningComplete) {
        setActiveQuestion(null)
        setTimeout(() => navigate(`/results/${sessionId}`), 2500)
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

  // Called when the user clicks "Confirm Answer" in the modal
  const handleModalAnswer = (value: number, label: string) => {
    setIsModalSubmitting(true)
    setActiveQuestion(null)           // close modal immediately for snappy UX
    handleSend(String(value))         // send the numeric answer as a message
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // ── Consent Screen ──────────────────────────────────────────────
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
            <p>🔒 <strong>Confidential & Secure:</strong> Your responses are encrypted and private.</p>
            <p>📋 <strong>Validated Instruments:</strong> Uses standard PHQ-9, GAD-7, and PSS-10 scales.</p>
            <p>⚠️ <strong>Screening Only:</strong> This is a mental wellness check-in, not a medical diagnosis.</p>
            <p>🆘 <strong>24/7 Safety Support:</strong> Emergency helplines (iCall & Vandrevala) are available anytime.</p>
          </div>
          {error && <p className="text-red-500 text-sm mb-4 text-center">{error}</p>}
          <button
            onClick={() => {
              setConsentGiven(true)
              initSession()
            }}
            className="w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-3.5 px-6 rounded-xl transition duration-200 shadow-md shadow-sky-200"
          >
            I Understand and Agree — Begin Check-In
          </button>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="flex flex-col h-screen bg-slate-50">
        {/* ── Top Header ─────────────────────────────────────────────── */}
        <header className="bg-white border-b border-slate-200 px-6 py-3.5 flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-sky-100 flex items-center justify-center text-xl">🌿</div>
            <div>
              <h1 className="font-bold text-slate-800 text-base">MindEase Check-In</h1>
              <p className="text-xs text-slate-500 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse"></span>
                {currentState === 'phq9'    ? 'Section 1/3: Mood (PHQ-9)' :
                 currentState === 'gad7'    ? 'Section 2/3: Anxiety (GAD-7)' :
                 currentState === 'pss10'   ? 'Section 3/3: Stress (PSS-10)' :
                 currentState === 'results' ? 'Screening Complete' : 'Confidential Assessment'}
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/')}
            className="text-xs text-slate-500 hover:text-slate-800 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50"
          >
            Exit Check-In
          </button>
        </header>

        {/* ── Crisis Alert Banner ────────────────────────────────────── */}
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
              <a href="tel:9152987821" className="bg-white text-rose-600 text-xs font-bold px-3 py-1.5 rounded-lg shadow-sm">
                Call iCall: 9152987821
              </a>
              <a href="tel:18602662345" className="bg-rose-700 hover:bg-rose-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg">
                Vandrevala: 1860-2662-345
              </a>
            </div>
          </div>
        )}

        {/* ── Chat Messages ─────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 max-w-3xl mx-auto w-full">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-5 py-3.5 shadow-sm text-sm whitespace-pre-wrap leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-sky-600 text-white rounded-br-none'
                    : 'bg-white text-slate-800 border border-slate-100 rounded-bl-none'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-white text-slate-400 border border-slate-100 rounded-2xl rounded-bl-none px-4 py-3 text-sm flex items-center space-x-1.5 shadow-sm">
                <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce"></div>
                <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:0.2s]"></div>
                <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:0.4s]"></div>
              </div>
            </div>
          )}

          {/* Subtle inline nudge shown when we're in a questionnaire state
              but waiting for the modal — replaces the old quick-select bar */}
          {isQuestionnaireState(currentState) && !activeQuestion && !isTyping && (
            <div className="flex justify-center">
              <div className="text-xs text-slate-400 bg-white border border-slate-100 rounded-full px-4 py-2 shadow-sm animate-pulse">
                ⏳ Loading your next question…
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* ── Input Bar (conversational states only) ─────────────────── */}
        <div className="bg-white border-t border-slate-200 p-4 shadow-sm">
          <div className="max-w-3xl mx-auto flex items-center space-x-3">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                isQuestionnaireState(currentState)
                  ? 'Please use the question popup to answer…'
                  : 'Type your message…'
              }
              className="flex-1 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 bg-slate-50/50 disabled:opacity-50"
              disabled={isTyping || isQuestionnaireState(currentState)}
            />
            <button
              onClick={() => handleSend()}
              disabled={!inputText.trim() || isTyping || isQuestionnaireState(currentState)}
              className="bg-sky-600 hover:bg-sky-700 disabled:opacity-40 text-white font-medium px-5 py-3 rounded-xl text-sm transition duration-150 shadow-sm"
            >
              Send
            </button>
          </div>
        </div>
      </div>

      {/* ── Question Modal (Portal-style, rendered outside scroll div) ── */}
      {activeQuestion && !isCrisis && (
        <QuestionModal
          question={activeQuestion}
          onAnswer={handleModalAnswer}
          isSubmitting={isModalSubmitting}
        />
      )}
    </>
  )
}
