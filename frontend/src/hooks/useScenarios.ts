import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { scenariosApi } from '../services/api'
import type { PromoScenario, ScenarioKPI, ValidationReport } from '../types'

export const useScenario = (scenarioId?: string, enabled = false) =>
  useQuery({
    queryKey: ['scenarios', scenarioId],
    queryFn: () => scenariosApi.get(scenarioId as string),
    enabled: Boolean(scenarioId) && enabled,
  })

export const useCreateScenario = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: { brief: any; parameters?: Record<string, unknown> }) =>
      scenariosApi.create(payload.brief, payload.parameters),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['scenarios'] })
    },
  })
}

export const useUpdateScenario = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, scenario }: { id: string; scenario: PromoScenario }) => scenariosApi.update(id, scenario),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['scenarios', id] })
    },
  })
}

export const useDeleteScenario = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => scenariosApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scenarios'] }),
  })
}

export const useEvaluateScenario = () =>
  useMutation({
    mutationFn: (scenario: PromoScenario) => scenariosApi.evaluate(scenario),
  })

export const useCompareScenarios = () =>
  useMutation({
    mutationFn: (scenarios: PromoScenario[]) => scenariosApi.compare(scenarios),
  })

export const useValidateScenario = () =>
  useMutation<ValidationReport, unknown, { scenario: PromoScenario; kpi?: ScenarioKPI }>({
    mutationFn: ({ scenario, kpi }) => scenariosApi.validate(scenario, kpi),
  })

