import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { PromoScenario, ScenarioKPI } from '../types'

export interface ScenarioEntry {
  scenario: PromoScenario
  kpi?: ScenarioKPI
}

interface ScenarioState {
  items: ScenarioEntry[]
  upsert: (entry: ScenarioEntry) => void
  setKpi: (scenarioId: string, kpi: ScenarioKPI) => void
  byId: (scenarioId: string) => ScenarioEntry | undefined
}

export const useScenarioStore = create<ScenarioState>()(
  persist(
    (set, get) => ({
      items: [],
      upsert: (entry) =>
        set((state) => {
          const exists = state.items.find((i) => i.scenario.id === entry.scenario.id)
          if (exists) {
            return {
              items: state.items.map((i) =>
                i.scenario.id === entry.scenario.id ? { ...i, ...entry } : i
              ),
            }
          }
          return { items: [...state.items, entry] }
        }),
      setKpi: (scenarioId, kpi) =>
        set((state) => ({
          items: state.items.map((i) => (i.scenario.id === scenarioId ? { ...i, kpi } : i)),
        })),
      byId: (scenarioId) => get().items.find((i) => i.scenario.id === scenarioId),
    }),
    {
      name: 'scenario-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ items: state.items }),
    }
  )
)

