import { create } from 'zustand'

interface UIState {
  loading: boolean
  setLoading: (v: boolean) => void
  toast?: string
  setToast: (msg?: string) => void
}

export const useUIStore = create<UIState>((set) => ({
  loading: false,
  setLoading: (loading) => set({ loading }),
  toast: undefined,
  setToast: (toast) => set({ toast }),
}))

