export function optionalStringSort(
  a: string | null | undefined,
  b: string | null | undefined
): number {
  return a?.localeCompare(b || "") || -1;
}

export function optionalNumberSort(
  a: number | null | undefined,
  b: number | null | undefined
): number {
  return (a || 0) - (b || 0);
}

export function getUniqueValues<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}