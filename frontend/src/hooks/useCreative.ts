import { useMutation } from '@tanstack/react-query'
import { creativeApi } from '../services/api'
import type { PromoScenario, CreativeBrief } from '../types'

export const useFinalizeCampaign = () =>
  useMutation({
    mutationFn: (scenarios: PromoScenario[]) => creativeApi.finalize(scenarios),
  })

export const useGenerateBrief = () =>
  useMutation({
    mutationFn: (payload: { scenario: PromoScenario; segments?: string[] }) =>
      creativeApi.brief(payload.scenario, payload.segments),
  })

export const useGenerateAssets = () =>
  useMutation({
    mutationFn: (brief: CreativeBrief) => creativeApi.assets(brief),
  })

