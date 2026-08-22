import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

interface CrudService<TItem, TPayload> {
  list: () => Promise<TItem[]>;
  create: (payload: TPayload) => Promise<TItem>;
  update: (id: string, payload: Partial<TPayload>) => Promise<TItem>;
  remove: (id: string) => Promise<void>;
}

export const PROFILE_QUERY_KEY = ["profile", "me"];

export function createCrudHooks<TItem, TPayload>(
  queryKey: string,
  service: CrudService<TItem, TPayload>,
) {
  const key = [queryKey];

  function useList() {
    return useQuery({ queryKey: key, queryFn: service.list });
  }

  function useCreate() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: service.create,
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: key });
        queryClient.invalidateQueries({ queryKey: PROFILE_QUERY_KEY });
      },
    });
  }

  function useUpdate() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ id, payload }: { id: string; payload: Partial<TPayload> }) =>
        service.update(id, payload),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: key });
        queryClient.invalidateQueries({ queryKey: PROFILE_QUERY_KEY });
      },
    });
  }

  function useDelete() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: service.remove,
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: key });
        queryClient.invalidateQueries({ queryKey: PROFILE_QUERY_KEY });
      },
    });
  }

  return { useList, useCreate, useUpdate, useDelete };
}
