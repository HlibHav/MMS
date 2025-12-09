import toast from 'react-hot-toast'

export const notifySuccess = (msg: string) => toast.success(msg)
export const notifyError = (msg: string) => toast.error(msg)
export const notifyInfo = (msg: string) => toast(msg, { icon: 'ℹ️' })

