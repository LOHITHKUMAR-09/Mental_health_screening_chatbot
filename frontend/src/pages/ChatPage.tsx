import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { startSession, sendMessage } from '../api/chat'
import type { Message } from '../types'

export default function ChatPage() {
  const navigate = useNavigate()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputText, setInputText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isCrisis, setIsCrisis] = useState(false)
  const [consentGiven, setConsentGiven] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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
      addBotMessage(
        "Hello! I'm MindEase 🧠\n\nI'm here to guide you through a brief, confidential mental health check-in covering mood, anxiety, and stress.\n\nType anything to begin — I'll walk you through each step."
      )
    } catch (err) {
      setError('Could not connect to the server. Please make sure the backend is running on port 8000.')
      console.error('Session init error:', err)
    }
  }

  const handleSend = async () => {
    if (!inputText.trim() || !sessionId || isTyping) return

    const userText = inputText.trim()
    setMessages(prev => [...prev, {
      id: crypto.randomUUID(),
      sender: 'user',
      content: userText,
      timestamp: new Date(),
    }])
    setInputText('')
    setIsTyping(true)
    setError(null)

    try {
      const response = await sendMessage(sessionId, userText)

      if (response.is_crisis) {
        setIsCrisis(true)
      }

      addBotMessage(response.bot_message)

      if (response.current_state === 'results') {
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

  // ── Consent Screen ──────────────────────────────────────────────
  if (!consentGiven) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-sky-50 px-4">
        <div className="bg-white rounded-2xl shadow-md p-8 max-w-lg w-full">
          <div className="text-center mb-4">
            <div className="text-4xl mb-2">🧠</div>
            <h2 className="text-xl font-bold text-slate-700">Before We Begin</h2>
          </div>
          <div className="bg-slate-50 rounded-xl p-4 text-slate-600 text-sm space-y-2 mb-6">
            <p>✅ MindEase is a <strong>screening tool only</strong> — not a diagnostic service.</p>
            <p>✅ Your responses are <strong>private and stored securely</strong>.</p>
            <p>✅ No personal data is shared without your consent.</p>
            <p>✅ Crisis support is provided <strong>immediately</strong> if needed.</p>
            <p>✅ This tool does <strong>not replace</strong> professional mental health care.</p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-300 text-red-700 text-sm rounded-xl px-4 py-3 mb-4">
              {error}
            </div>
          )}

          <button
            onClick={() => { setConsentGiven(true); initSession() }}
            className="w-full bg-sky-600 text-white font-semibold py-3 rounded-xl hover:bg-sky-700 transition-all"
          >
            I Understand — Begin Screening
          </button>
        </div>
      </div>
    )
  }

  // ── Chat Screen ─────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3 shadow-sm">
        <div className="text-2xl">🧠</div>
        <div>
          <h1 className="font-semibold text-slate-700">MindEase</h1>
          <p className="text-xs text-slate-400">Confidential Mental Health Screening</p>
        </div>
        <div className="ml-auto text-xs bg-green-100 text-green-700 px-3 py-1 rounded-full font-medium">
          🔒 Private
        </div>
      </header>

      {/* Disclaimer */}
      <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-xs text-amber-700 text-center">
        ⚠️ Screening tool only — not a clinical diagnosis. Not a substitute for professional care.
      </div>

      {/* Crisis banner */}
      {isCrisis && (
        <div className="bg-red-50 border-b border-red-400 px-4 py-3 text-red-700 text-sm font-medium text-center">
          🆘 Please reach out to <strong>iCall: 9152987821</strong> (Mon–Sat, 8am–10pm) right away.
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="bg-orange-50 border-b border-orange-300 px-4 py-2 text-orange-700 text-xs text-center">
          {error}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 max-w-2xl mx-auto w-full">
        {messages.length === 0 && (
          <div className="text-center text-slate-400 text-sm mt-10">
            Starting your session...
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.sender === 'bot' && (
              <div className="text-xl mr-2 mt-1 flex-shrink-0">🤖</div>
            )}
            <div
              className={`max-w-xs md:max-w-md lg:max-w-lg px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.sender === 'user' ? 'chat-bubble-user' : 'chat-bubble-bot'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="text-xl mr-2 flex-shrink-0">🤖</div>
            <div className="chat-bubble-bot px-4 py-3 text-sm text-slate-400 italic">
              MindEase is typing...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-slate-200 px-4 py-3">
        <div className="max-w-2xl mx-auto flex gap-2">
          <textarea
            value={inputText}
            onChange={e => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={sessionId ? 'Type your reply... (Enter to send)' : 'Connecting...'}
            rows={1}
            disabled={!sessionId || isTyping}
            className="flex-1 border border-slate-300 rounded-xl px-4 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-sky-400 disabled:bg-slate-50 disabled:text-slate-400"
          />
          <button
            onClick={handleSend}
            disabled={!inputText.trim() || isTyping || !sessionId}
            className="bg-sky-600 hover:bg-sky-700 disabled:opacity-40 disabled:cursor-not-allowed text-white px-5 rounded-xl font-semibold text-sm transition-all"
          >
            Send
          </button>
        </div>
        <p className="text-center text-xs text-slate-400 mt-2">
          Press <kbd className="bg-slate-100 px-1 rounded">Enter</kbd> to send · <kbd className="bg-slate-100 px-1 rounded">Shift+Enter</kbd> for new line
        </p>
      </div>
    </div>
  )
}
