import { useQuery } from '@tanstack/react-query'
import { apiClient, ENDPOINTS } from '@shared/api'
import type { UserResponse } from '@shared/api/types'
import type { User } from '../model/types'

function mapUserResponse(response: UserResponse): User {
  return {
    id: response.id,
    name: response.name,
    birthDate: response.birthDate,
    accountType: response.accountType,
  }
}

export function useGetMe() {
  return useQuery({
    queryKey: ['user', 'me'],
    queryFn: async () => {
      const data = await apiClient.get<UserResponse>(ENDPOINTS.AUTH.ME)
      return mapUserResponse(data)
    },
    retry: false,
  })
}
