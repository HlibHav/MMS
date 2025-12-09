import { useMutation } from '@tanstack/react-query'
import { chatApi } from '../services/api'
import { ChatMessageRequest, ChatMessageResponse } from '../types'

export const useChat = () =>
  useMutation<ChatMessageResponse, unknown, ChatMessageRequest>({
    mutationFn: (payload) => chatApi.message(payload),
  })

