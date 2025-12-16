export type TransactionType = 'debit' | 'credit'

export type Transaction = {
  id: string
  accountId: string
  date: string
  description: string
  amount: number
  currency: string
  type: TransactionType
  category?: string
}
