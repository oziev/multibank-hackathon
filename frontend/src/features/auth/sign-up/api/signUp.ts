import { useMutation } from '@tanstack/react-query'
import { apiClient, ENDPOINTS } from '@shared/api'
import type { SignUpRequest } from '@shared/api/types'

export function useSignUp() {
  return useMutation({
    mutationFn: (data: SignUpRequest) => apiClient.post(ENDPOINTS.AUTH.SIGN_UP, data),
  })
}
