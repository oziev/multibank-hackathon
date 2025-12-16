import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, ENDPOINTS } from '@shared/api'
import type { SignInRequest } from '@shared/api/types'

export function useSignIn() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: SignInRequest) => apiClient.post(ENDPOINTS.AUTH.SIGN_IN, data),
    onSuccess: () => {
      // Invalidate user query to fetch fresh data
      queryClient.invalidateQueries({ queryKey: ['user', 'me'] })
    },
  })
}
