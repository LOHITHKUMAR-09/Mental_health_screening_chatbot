import { apiClient } from './client'
import type { ChatMessageResponse, SessionResults } from '../types'

export const startSession = async () => {
  const { data } = await apiClient.post('/sessions/start')
  return data
}

export const sendMessage = async (sessionId: string, message: string): Promise<ChatMessageResponse> => {
  const { data } = await apiClient.post('/chat/message', {
    session_id: sessionId,
    message,
  })
  return data
}

export const getResults = async (sessionId: string): Promise<SessionResults> => {
  const { data } = await apiClient.get(/results/)
  return data
}

export const loginAnonymous = async () => {
  const { data } = await apiClient.post('/auth/anonymous')
  localStorage.setItem('mindease_token', data.access_token)
  return data
}
