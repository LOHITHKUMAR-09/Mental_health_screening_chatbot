// Core type definitions for MindEase frontend

export type RiskLevel = 'low' | 'moderate' | 'high'

export type ConversationState =
  | 'greeting'
  | 'consent'
  | 'background'
  | 'phq9'
  | 'gad7'
  | 'pss10'
  | 'results'

export interface Message {
  id: string
  sender: 'user' | 'bot'
  content: string
  timestamp: Date
  isTyping?: boolean
}

export interface QuestionnaireItem {
  instrument: 'phq9' | 'gad7' | 'pss10'
  itemNumber: number
  questionText: string
  options: { value: number; label: string }[]
}

export interface ChatMessageResponse {
  sessionId: string
  botMessage: string
  currentState: ConversationState
  isCrisis: boolean
  crisisResources?: {
    icall: { name: string; phone: string; hours: string }
    vandrevala: { name: string; phone: string; hours: string }
    emergency: string
  }
  questionnaireItem?: QuestionnaireItem
}

export interface SessionResults {
  sessionId: string
  phq9Score?: number
  phq9Severity?: string
  gad7Score?: number
  gad7Severity?: string
  pss10Score?: number
  pss10Severity?: string
  ruleBasedRisk?: RiskLevel
  mlRiskLabel?: RiskLevel
  mlConfidence?: number
  copingSuggestions: string[]
  counselingResources: {
    name: string
    phone: string
    bookingUrl: string
  }
}

export interface AuthState {
  token: string | null
  userId: string | null
  role: string | null
  isAnonymous: boolean
}
