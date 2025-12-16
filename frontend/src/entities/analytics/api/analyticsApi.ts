import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@shared/api'
import type { AnalyticsOverview, CategoryBreakdown } from '../model/types'

export function useGetAnalyticsOverview() {
  return useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: async () => {
      const data = await apiClient.get<AnalyticsOverview>('/api/analytics/overview')
      return data
    },
    retry: 2,
    staleTime: 1000 * 60 * 5, // 5 минут
    gcTime: 1000 * 60 * 10, // 10 минут в кеше
    refetchOnWindowFocus: false, // Не обновлять при фокусе
  })
}

export function useGetCategoriesBreakdown() {
  return useQuery({
    queryKey: ['analytics', 'categories'],
    queryFn: async () => {
      const data = await apiClient.get<CategoryBreakdown[]>('/api/analytics/categories')
      return data
    },
    retry: 2,
    staleTime: 1000 * 60 * 5, // 5 минут
    gcTime: 1000 * 60 * 10, // 10 минут в кеше
    refetchOnWindowFocus: false,
  })
}

export function useGetAdvancedInsights() {
  return useQuery({
    queryKey: ['analytics', 'insights'],
    queryFn: async () => {
      const data = await apiClient.get<any>('/api/analytics/insights')
      return data
    },
    retry: 2,
    staleTime: 1000 * 60 * 5, // 5 минут
    gcTime: 1000 * 60 * 10, // 10 минут в кеше
    refetchOnWindowFocus: false,
  })
}

