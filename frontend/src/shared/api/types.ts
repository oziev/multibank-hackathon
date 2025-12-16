// Response wrapper types
export type ApiSuccessResponse<T> = {
  success: true
  data: T
}

export type ApiErrorResponse = {
  success: false
  error: {
    message: string
    details?: unknown
  }
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse

// Auth types
export type SignUpRequest = {
  email: string
  password: string
  name: string
  birthDate: string
  phone: string
  referral_code?: string
}

export type VerifyEmailRequest = {
  email: string
  otpCode: string
}

export type SignInRequest = {
  email: string
  password: string
}

export type UserResponse = {
  id: number
  name: string
  birthDate: string
  accountType: 'free' | 'premium'
}

// Bank types
export type BankResponse = {
  id: number
  name: string
  displayName: string
  isAvailable: boolean
}

// Account types
export type AccountCreateRequest = {
  clientId: number
}

export type AccountAttachRequest = {
  id: string
}

export type AccountResponse = {
  accountId: string
  clientId: number
  clientName: string
  accountName: string
  isActive: boolean
}

export type GroupAccountResponse = {
  accountId: string
  clientId: string
  clientName: string
  accountName: string
  owner: {
    name: string
  }
}

export type BalanceResponse = {
  amount: number
  currency: string
}

export type TransactionType = 'debit' | 'credit'

export type TransactionResponse = {
  id: string
  date: string
  description: string
  amount: number
  currency: string
  type: TransactionType
}

// Group types
export type GroupCreateRequest = {
  name: string
}

export type GroupResponse = {
  id: number
  name: string
  ownerId: number
  createdAt: string
}

export type InviteRequest = {
  groupId: number
  email: string
}

export type InviteResponse = {
  id: number
  groupId: number
  inviterEmail: string
  inviterName: string
  status: 'pending' | 'accepted' | 'declined'
  createdAt: string
}

export type InviteActionRequest = {
  requestId: number
}

export type GroupSettingsResponse = {
  free: {
    maxGroups: number
    maxMembers: number
  }
  premium: {
    maxGroups: number
    maxMembers: number
  }
}
