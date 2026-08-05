import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { languageService } from "@/features/profile/services/language-service";
import type { Language, LanguagePayload } from "@/features/profile/types";

export const {
  useList: useLanguageList,
  useCreate: useCreateLanguage,
  useUpdate: useUpdateLanguage,
  useDelete: useDeleteLanguage,
} = createCrudHooks<Language, LanguagePayload>("languages", languageService);
