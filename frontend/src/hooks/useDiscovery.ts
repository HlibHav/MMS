import { useQuery } from '@tanstack/react-query'
import { discoveryApi } from '../services/api'
import type { AnalyzeRequest } from '../types'

export const useDiscoveryAnalyze = (params: AnalyzeRequest, enabled = true) =>
  useQuery({
    queryKey: ['discovery', 'analyze', params.month, params.geo],
    queryFn: () => discoveryApi.analyze(params),
    enabled,
  })

export const useDiscoveryContext = (geo: string, startDate: string, endDate: string, enabled = true) =>
  useQuery({
    queryKey: ['discovery', 'context', geo, startDate, endDate],
    queryFn: () => discoveryApi.context(geo, startDate, endDate),
    enabled,
  })

export const useDiscoveryGaps = (month: string, geo: string, enabled = true) =>
  useQuery({
    queryKey: ['discovery', 'gaps', month, geo],
    queryFn: () => discoveryApi.gaps(month, geo),
    enabled,
  })

export const useDiscoveryOpportunities = (month: string, geo: string, enabled = true) =>
  useQuery({
    queryKey: ['discovery', 'opportunities', month, geo],
    queryFn: () => discoveryApi.opportunities(month, geo),
    enabled,
  })

