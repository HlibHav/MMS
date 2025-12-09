export const LoadingState = ({ message = 'Loading...' }: { message?: string }) => (
  <div className="text-sm text-gray-600">{message}</div>
)

export const ErrorState = ({ message }: { message: string }) => (
  <div className="text-sm text-red-600">{message}</div>
)

export const EmptyState = ({ message }: { message: string }) => (
  <div className="text-sm text-gray-500">{message}</div>
)

