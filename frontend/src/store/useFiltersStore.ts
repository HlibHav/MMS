import { create } from 'zustand'

interface FiltersState {
  month: string
  geo: string
  setMonth: (month: string) => void
  setGeo: (geo: string) => void
}

export const useFiltersStore = create<FiltersState>((set) => ({
  month: '2024-10',
  geo: 'DE',
  setMonth: (month) => set({ month }),
  setGeo: (geo) => set({ geo }),
}))

