import { create } from 'zustand'

interface ScenarioSelectionState {
  selectedScenarioIds: string[]
  setSelectedScenarioIds: (ids: string[]) => void
  addScenarioId: (id: string) => void
  removeScenarioId: (id: string) => void
}

export const useScenarioSelectionStore = create<ScenarioSelectionState>((set, get) => ({
  selectedScenarioIds: [],
  setSelectedScenarioIds: (ids) => set({ selectedScenarioIds: ids }),
  addScenarioId: (id) => {
    const current = get().selectedScenarioIds
    if (!current.includes(id)) {
      set({ selectedScenarioIds: [...current, id] })
    }
  },
  removeScenarioId: (id) => {
    const current = get().selectedScenarioIds
    set({ selectedScenarioIds: current.filter((x) => x !== id) })
  },
}))

