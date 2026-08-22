import { useMutation, useQueryClient } from "@tanstack/react-query";

interface AttachmentService<TItem> {
  upload: (id: string, file: File) => Promise<TItem>;
  remove: (id: string) => Promise<void>;
}

export function createAttachmentHooks<TItem>(
  queryKey: string,
  service: AttachmentService<TItem>,
) {
  const key = [queryKey];

  function useUploadAttachment() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: ({ id, file }: { id: string; file: File }) => service.upload(id, file),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: key }),
    });
  }

  function useRemoveAttachment() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: (id: string) => service.remove(id),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: key }),
    });
  }

  return { useUploadAttachment, useRemoveAttachment };
}
