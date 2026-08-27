import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { startSession, sendMessage } from '../api/chat'
import type { Message } from '../types'

interface LikertOption {
  value: number
  label: string
}

const PHQ_GAD_OPTIONS: LikertOption[] = [
  { value: 0, label: '0 — Not at all' },
  { value: 1, label: '1 — Several days' },
  { value: 2, label: '2 — More than half the days' },
  { value: 3, label: '3 — Nearly every day' },
]

const PSS_OPTIONS: LikertOption[] = [
  { value: 0, label: '0 — Never' },
  { value: 1, label: '1 — Almost never' },
  { value: 2, label: '2 — Sometimes' },
  { value: 3, label: '3 — Fairly often' },
  { value: 4, label: '4 — Very often' },
]

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
  const bottomRef = useRef<HTMLDivElement>(null)

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
      }

      const botMsg = response.bot_message || response.botMessage || 'Thank you.'
      addBotMessage(botMsg)

      if (state === 'results' || response.screening_complete || response.screeningComplete) {
        setTimeout(() => navigate(`/results/${sessionId}`), 2500)
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Something went wrong.'
      addBotMessage(`⚠️ Sorry, I encountered an error: ${msg}\n\nPlease try again.`)
      console.error('Send message error:', err)
    } finally {
      setIsTyping(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Active Likert options based on current instrument state
  const currentOptions = 
    currentState === 'phq9' || currentState === 'gad7' 
      ? PHQ_GAD_OPTIONS 
      : currentState === 'pss10' 
        ? PSS_OPTIONS 
        : null

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
    <div className="flex flex-col h-screen bg-slate-50">
      {/* ── Top Header ─────────────────────────────────────────────── */}
      <header className="bg-white border-b border-slate-200 px-6 py-3.5 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-sky-100 flex items-center justify-center text-xl">🌿</div>
          <div>
            <h1 className="font-bold text-slate-800 text-base">MindEase Check-In</h1>
            <p className="text-xs text-slate-500 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse"></span>
              {currentState === 'phq9' ? 'Section 1/3: Mood (PHQ-9)' :
               currentState === 'gad7' ? 'Section 2/3: Anxiety (GAD-7)' :
               currentState === 'pss10' ? 'Section 3/3: Stress (PSS-10)' :
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

      {/* ── Crisis Alert Overlay ───────────────────────────────────── */}
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

      {/* ── Chat Messages Container ─────────────────────────────────── */}
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
        <div ref={bottomRef} />
      </div>

      {/* ── Likert Scale Clickable Quick-Option Buttons ──────────────── */}
      {currentOptions && !isTyping && (
        <div className="bg-slate-100/90 border-t border-slate-200 px-4 py-2.5 max-w-3xl mx-auto w-full">
          <p className="text-xs text-slate-500 font-medium mb-1.5">Quick Select Options:</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {currentOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => handleSend(String(opt.value))}
                className="bg-white hover:bg-sky-50 hover:border-sky-300 border border-slate-200 text-slate-700 text-xs font-medium py-2 px-3 rounded-xl transition duration-150 shadow-sm text-left truncate"
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Input Bar ──────────────────────────────────────────────── */}
      <div className="bg-white border-t border-slate-200 p-4 shadow-sm">
        <div className="max-w-3xl mx-auto flex items-center space-x-3">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              currentOptions 
                ? "Type your answer or click an option above..." 
                : "Type your message..."
            }
            className="flex-1 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 bg-slate-50/50"
            disabled={isTyping}
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputText.trim() || isTyping}
            className="bg-sky-600 hover:bg-sky-700 disabled:opacity-40 text-white font-medium px-5 py-3 rounded-xl text-sm transition duration-150 shadow-sm"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
