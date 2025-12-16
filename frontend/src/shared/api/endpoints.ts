import { API_BASE_URL } from '@shared/config/constants'

export const ENDPOINTS = {
  AUTH: {
    SIGN_UP: `${API_BASE_URL}/api/auth/sign-up`,
    SIGN_IN: `${API_BASE_URL}/api/auth/sign-in`,
    VERIFY_EMAIL: `${API_BASE_URL}/api/auth/verify-email`,
    ME: `${API_BASE_URL}/api/auth/me`,
    LOGOUT: `${API_BASE_URL}/api/auth/logout`,
  },
  BANKS: {
    LIST: `${API_BASE_URL}/api/banks`,
  },
  ACCOUNTS: {
    LIST: `${API_BASE_URL}/api/accounts`,
    CREATE: `${API_BASE_URL}/api/accounts`,
    ATTACH: `${API_BASE_URL}/api/accounts/attach`,
    GET: (id: string) => `${API_BASE_URL}/api/accounts/${id}`,
    BALANCES: (id: string) => `${API_BASE_URL}/api/accounts/${id}/balances`,
    TRANSACTIONS: (id: string) => `${API_BASE_URL}/api/accounts/${id}/transactions`,
  },
  GROUPS: {
    LIST: `${API_BASE_URL}/api/groups`,
    CREATE: `${API_BASE_URL}/api/groups`,
    DELETE: `${API_BASE_URL}/api/groups`,
    EXIT: `${API_BASE_URL}/api/groups/exit`,
    SETTINGS: `${API_BASE_URL}/api/groups/settings`,
    ACCOUNTS: (groupId: number) => `${API_BASE_URL}/api/groups/${groupId}/accounts`,
    ACCOUNTS_BY_CLIENT: (groupId: number, clientId: number) =>
      `${API_BASE_URL}/api/groups/${groupId}/accounts/${clientId}`,
    BALANCES: (groupId: number) => `${API_BASE_URL}/api/groups/${groupId}/accounts/balances`,
    TRANSACTIONS: (groupId: number) =>
      `${API_BASE_URL}/api/groups/${groupId}/accounts/transactions`,
    INVITE: `${API_BASE_URL}/api/groups/invite`,
    INVITES: `${API_BASE_URL}/api/groups/invites`,
    INVITE_ACCEPT: `${API_BASE_URL}/api/groups/invite/accept`,
    INVITE_DECLINE: `${API_BASE_URL}/api/groups/invite/decline`,
  },
} as const
