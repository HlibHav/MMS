import { useMutation } from '@tanstack/react-query'
import { postmortemApi } from '../services/api'
import { PostMortemReport } from '../types'

export const usePostmortemAnalyze = () =>
  useMutation<PostMortemReport, unknown, { scenario_id: string; actual_data: Record<string, number>; period: { start: string; end: string } }>({
    mutationFn: ({ scenario_id, actual_data, period }) => postmortemApi.analyze(scenario_id, actual_data, period),
  })

