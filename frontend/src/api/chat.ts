import { apiClient } from './client'

export const startSession = async () => {
  const { data } = await apiClient.post('/sessions/start')
  return data  // { session_id, current_state, message }
}

export const sendMessage = async (sessionId: string, message: string) => {
  const { data } = await apiClient.post('/chat/message', {
    session_id: sessionId,
    message,
    conversation_history: [],
  })
  return data  // { session_id, bot_message, current_state, is_crisis, ... }
}

export const getResults = async (sessionId: string) => {
  const { data } = await apiClient.get(`/results/${sessionId}`)
  return data
}

export const loginAnonymous = async () => {
  const { data } = await apiClient.post('/auth/anonymous')
  localStorage.setItem('mindease_token', data.access_token)
  return data
}

export const loginWithEmail = async (email: string, password: string) => {
  const { data } = await apiClient.post('/auth/login', { email, password })
  localStorage.setItem('mindease_token', data.access_token)
  return data
}

export const register = async (email: string, password: string, fullName?: string) => {
  const { data } = await apiClient.post('/auth/register', {
    email,
    password,
    full_name: fullName,
  })
  localStorage.setItem('mindease_token', data.access_token)
  return data
}
