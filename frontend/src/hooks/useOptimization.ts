import { useMutation } from '@tanstack/react-query'
import { optimizationApi } from '../services/api'
import type { PromoScenario } from '../types'

export const useOptimizeScenarios = () =>
  useMutation({
    mutationFn: (payload: { brief: any; constraints?: Record<string, unknown> }) =>
      optimizationApi.optimize(payload.brief, payload.constraints),
  })

export const useFrontier = () =>
  useMutation({
    mutationFn: (params?: Record<string, unknown>) => optimizationApi.frontier(params),
  })

export const useRankScenarios = () =>
  useMutation({
    mutationFn: (payload: { scenarios: PromoScenario[]; weights?: Record<string, number> }) =>
      optimizationApi.rank(payload.scenarios, payload.weights),
  })

