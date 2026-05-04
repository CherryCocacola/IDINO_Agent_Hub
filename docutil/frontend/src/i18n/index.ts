import en from "./en";
import ko from "./ko";

const translations = { ko, en } as const;
type Lang = keyof typeof translations;

export function t(key: string, lang: Lang = "ko"): string {
  const keys = key.split(".");
  let value: unknown = translations[lang];
  for (const k of keys) {
    value = (value as Record<string, unknown>)?.[k];
  }
  return (value as string) || key;
}

export { ko, en };
