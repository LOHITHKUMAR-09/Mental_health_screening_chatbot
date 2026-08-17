import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { startSession, sendMessage } from '../api/chat'
import type { Message, ChatMessageResponse } from '../types'

export default function ChatPage() {
  const navigate = useNavigate()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputText, setInputText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isCrisis, setIsCrisis] = useState(false)
  const [consentGiven, setConsentGiven] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const initSession = async () => {
    const session = await startSession()
    setSessionId(session.session_id)
    addBotMessage("Hello! I'm MindEase 🧠 — your mental health companion. I'll guide you through a brief, confidential screening. Everything shared here is private. Are you ready to begin?")
  }

  const addBotMessage = (content: string) => {
    setMessages(prev => [...prev, {
      id: crypto.randomUUID(),
      sender: 'bot',
      content,
      timestamp: new Date(),
    }])
  }

  const handleSend = async () => {
    if (!inputText.trim() || !sessionId) return

    const userMsg: Message = {
      id: crypto.randomUUID(),
      sender: 'user',
      content: inputText,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setInputText('')
    setIsTyping(true)

    try {
      const response: ChatMessageResponse = await sendMessage(sessionId, inputText)
      
      if (response.isCrisis) {
        setIsCrisis(true)
      }

      addBotMessage(response.botMessage)

      if (response.currentState === 'results') {
        setTimeout(() => navigate(/results/), 2000)
      }
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

  if (!consentGiven) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-primary-50 px-4">
        <div className="bg-white rounded-2xl shadow-md p-8 max-w-lg w-full">
          <h2 className="text-xl font-bold text-slate-700 mb-4">🔒 Before We Begin</h2>
          <div className="text-slate-600 text-sm space-y-3 mb-6">
            <p>✅ MindEase is a <strong>screening tool only</strong> — not a diagnostic service.</p>
            <p>✅ Your responses are <strong>encrypted and anonymized</strong>.</p>
            <p>✅ No personal data is shared without your explicit consent.</p>
            <p>✅ If you experience a mental health crisis, you will be given <strong>emergency resources immediately</strong>.</p>
            <p>✅ This tool does <strong>not replace</strong> professional mental health care.</p>
          </div>
          <button
            onClick={() => { setConsentGiven(true); initSession() }}
            className="w-full bg-primary-600 text-white font-semibold py-3 rounded-xl hover:bg-primary-700 transition-all"
          >
            I Understand — Begin Screening
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3 shadow-sm">
        <div className="text-2xl">🧠</div>
        <div>
          <h1 className="font-semibold text-slate-700">MindEase</h1>
          <p className="text-xs text-slate-400">Confidential Mental Health Screening</p>
        </div>
        <div className="ml-auto text-xs bg-calm-100 text-calm-600 px-3 py-1 rounded-full font-medium">
          🔒 Private Session
        </div>
      </header>

      {/* Disclaimer Banner */}
      <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-xs text-amber-700 text-center">
        ⚠️ This is a screening tool, not a diagnosis. Not a substitute for professional care.
      </div>

      {/* Crisis Alert */}
      {isCrisis && (
        <div className="bg-crisis-100 border border-crisis-500 px-4 py-3 text-crisis-700 text-sm font-medium text-center">
          🆘 Crisis resources have been shared below. Please reach out to <strong>iCall: 9152987821</strong> right away.
        </div>
      )}

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 max-w-2xl mx-auto w-full">
        {messages.map(msg => (
          <div key={msg.id} className={lex }>
            {msg.sender === 'bot' && <div className="text-xl mr-2 mt-1">🤖</div>}
            <div
              className={max-w-xs md:max-w-md px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap }
            >
              {msg.content}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="text-xl mr-2">🤖</div>
            <div className="chat-bubble-bot px-4 py-3 text-sm text-slate-400 italic">
              MindEase is typing...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-slate-200 px-4 py-3 max-w-2xl mx-auto w-full">
        <div className="flex gap-2">
          <textarea
            value={inputText}
            onChange={e => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Enter to send)"
            rows={1}
            className="flex-1 border border-slate-300 rounded-xl px-4 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary-400"
          />
          <button
            onClick={handleSend}
            disabled={!inputText.trim() || isTyping}
            className="bg-primary-600 hover:bg-primary-700 disabled:opacity-40 text-white px-5 rounded-xl font-semibold text-sm transition-all"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
