export type Group = {
  id: number
  name: string
  ownerId: number
  createdAt: string
}

export type Invitation = {
  id: number
  groupId: number
  inviterEmail: string
  inviterName: string
  status: 'pending' | 'accepted' | 'declined'
  createdAt: string
}

export type GroupSettings = {
  accountType: 'free' | 'premium'
  maxGroups: number
  maxMembers: number
}
