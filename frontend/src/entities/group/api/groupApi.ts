import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, ENDPOINTS } from '@shared/api'
import type {
  GroupResponse,
  GroupCreateRequest,
  InviteRequest,
  InviteResponse,
  InviteActionRequest,
  GroupSettingsResponse,
  GroupAccountResponse,
} from '@shared/api/types'
import type { Group, Invitation, GroupSettings } from '../model/types'
import type { GroupAccount } from '@entities/account'
import { useGetMe } from '@entities/user'

function mapGroup(response: GroupResponse): Group {
  return {
    id: response.id,
    name: response.name,
    ownerId: response.ownerId,
    createdAt: response.createdAt,
  }
}

function mapInvitation(response: InviteResponse): Invitation {
  return {
    id: response.id,
    groupId: response.groupId,
    inviterEmail: response.inviterEmail,
    inviterName: response.inviterName,
    status: response.status,
    createdAt: response.createdAt,
  }
}

function mapGroupAccount(response: GroupAccountResponse): GroupAccount {
  return {
    accountId: response.accountId,
    clientId: response.clientId,
    clientName: response.clientName,
    accountName: response.accountName,
    owner: response.owner,
  }
}

function mapGroupSettings(
  response: GroupSettingsResponse,
  accountType: 'free' | 'premium'
): GroupSettings {
  const settings = response[accountType]
  return {
    accountType,
    maxGroups: settings.maxGroups,
    maxMembers: settings.maxMembers,
  }
}

export function useGetGroups() {
  return useQuery({
    queryKey: ['groups'],
    queryFn: async () => {
      const data = await apiClient.get<GroupResponse[]>(ENDPOINTS.GROUPS.LIST)
      return data.map(mapGroup)
    },
  })
}

export function useGetGroupSettings() {
  const { data: user } = useGetMe()

  return useQuery({
    queryKey: ['group-settings', user?.accountType],
    queryFn: async () => {
      const data = await apiClient.get<GroupSettingsResponse>(ENDPOINTS.GROUPS.SETTINGS)
      return mapGroupSettings(data, user?.accountType || 'free')
    },
    enabled: !!user,
  })
}

export function useGetInvitations() {
  return useQuery({
    queryKey: ['invitations'],
    queryFn: async () => {
      const data = await apiClient.get<InviteResponse[]>(ENDPOINTS.GROUPS.INVITES)
      return data.map(mapInvitation)
    },
  })
}

export function useCreateGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: GroupCreateRequest) =>
      apiClient.post<GroupResponse>(ENDPOINTS.GROUPS.CREATE, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    },
  })
}

export function useInviteToGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: InviteRequest) =>
      apiClient.post<InviteResponse>(ENDPOINTS.GROUPS.INVITE, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    },
  })
}

export function useAcceptInvitation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: InviteActionRequest) => apiClient.post(ENDPOINTS.GROUPS.INVITE_ACCEPT, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] })
      queryClient.invalidateQueries({ queryKey: ['invitations'] })
    },
  })
}

export function useDeclineInvitation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: InviteActionRequest) =>
      apiClient.post(ENDPOINTS.GROUPS.INVITE_DECLINE, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations'] })
    },
  })
}

export function useDeleteGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (groupId: number) => apiClient.delete(ENDPOINTS.GROUPS.DELETE, { groupId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    },
  })
}

export function useExitGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (groupId: number) => apiClient.post(ENDPOINTS.GROUPS.EXIT, { groupId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] })
    },
  })
}

export function useGetGroupAccounts(groupId: number) {
  return useQuery({
    queryKey: ['group-accounts', groupId],
    queryFn: async () => {
      const data = await apiClient.get<GroupAccountResponse[]>(ENDPOINTS.GROUPS.ACCOUNTS(groupId))
      return data.map(mapGroupAccount)
    },
    enabled: !!groupId,
  })
}

type GroupBalanceResponse = {
  clientId: string
  name: string
  accountName: string
  owner: {
    name: string
  }
  balance: {
    amount: number
    currency: string
  }
}

export function useGetGroupBalance(groupId: number) {
  return useQuery({
    queryKey: ['group-balance', groupId],
    queryFn: async () => {
      const data = await apiClient.get<GroupBalanceResponse[]>(ENDPOINTS.GROUPS.BALANCES(groupId))

      // Sum all balances (assuming all are in RUB)
      const totalAmount = data.reduce((sum, item) => sum + item.balance.amount, 0)
      const currency = data[0]?.balance.currency || 'RUB'

      return {
        amount: totalAmount,
        currency,
      }
    },
    enabled: !!groupId,
  })
}
