import {
  useGetInvitations,
  useAcceptInvitation,
  useDeclineInvitation,
  useGetGroups,
} from '@entities/group'
import { Card, CardContent, Button } from '@shared/ui'
import { Users, Check, X } from 'lucide-react'

export function InvitationsList() {
  const { data: invitations, isLoading } = useGetInvitations()
  const { data: groups } = useGetGroups()
  const acceptInvitation = useAcceptInvitation()
  const declineInvitation = useDeclineInvitation()

  const pendingInvitations = invitations?.filter((inv) => inv.status === 'pending') || []

  if (isLoading || pendingInvitations.length === 0) {
    return null
  }

  const handleAccept = (requestId: number) => {
    acceptInvitation.mutate({ requestId })
  }

  const handleDecline = (requestId: number) => {
    declineInvitation.mutate({ requestId })
  }

  return (
    <div className="space-y-3">
      {pendingInvitations.map((invitation) => {
        const group = groups?.find((g) => g.id === invitation.groupId)
        const groupName = group?.name || `Группа #${invitation.groupId}`

        return (
          <Card key={invitation.id} className="border-blue-200 bg-blue-50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between gap-4">
                <div className="flex flex-1 items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600">
                    <Users className="h-5 w-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">{groupName}</p>
                    <p className="text-xs text-gray-500">От {invitation.inviterName}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDecline(invitation.id)}
                    disabled={declineInvitation.isPending}
                    className="h-9 w-9 border-red-300 p-0 text-red-600 hover:bg-red-50"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleAccept(invitation.id)}
                    disabled={acceptInvitation.isPending}
                    className="h-9 w-9 bg-green-600 p-0 text-white hover:bg-green-700"
                  >
                    <Check className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
