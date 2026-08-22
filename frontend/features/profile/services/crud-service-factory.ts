import { apiClient } from "@/services/api-client";

export function createCrudService<TItem, TPayload>(resourcePath: string) {
  return {
    list: () => apiClient.get<TItem[]>(resourcePath),
    create: (payload: TPayload) => apiClient.post<TItem>(resourcePath, payload),
    update: (id: string, payload: Partial<TPayload>) =>
      apiClient.patch<TItem>(`${resourcePath}/${id}`, payload),
    remove: (id: string) => apiClient.delete<void>(`${resourcePath}/${id}`),
  };
}
