import { useMutation, useQuery } from '@tanstack/react-query'
import { dataApi } from '../services/api'

export const useProcessXlsb = () =>
  useMutation({
    mutationFn: (files: File[]) => dataApi.processXlsb(files),
  })

export const useQualityReport = (datasetId: string, enabled = true) =>
  useQuery({
    queryKey: ['data', 'quality', datasetId],
    queryFn: () => dataApi.getQuality(datasetId),
    enabled,
  })

