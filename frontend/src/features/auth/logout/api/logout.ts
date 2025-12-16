import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, ENDPOINTS } from '@shared/api'

export function useLogout() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => apiClient.post(ENDPOINTS.AUTH.LOGOUT),
    onSuccess: () => {
      // Clear all cached queries on logout
      queryClient.clear()
    },
  })
}
