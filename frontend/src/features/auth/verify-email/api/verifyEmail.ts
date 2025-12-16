import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, ENDPOINTS } from '@shared/api'
import type { VerifyEmailRequest } from '@shared/api/types'

export function useVerifyEmail() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: VerifyEmailRequest) => apiClient.post(ENDPOINTS.AUTH.VERIFY_EMAIL, data),
    onSuccess: () => {
      // Invalidate user query to fetch fresh data after verification
      queryClient.invalidateQueries({ queryKey: ['user', 'me'] })
    },
  })
}
