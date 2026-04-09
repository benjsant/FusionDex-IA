import { useQuery } from "@tanstack/react-query";
import { getMoves, getMove, searchMoves, getMovesByType } from "@/lib/api";

export function useMoves() {
  return useQuery({
    queryKey: ["moves"],
    queryFn: getMoves,
    staleTime: 10 * 60 * 1000,
  });
}

export function useMove(id: number) {
  return useQuery({
    queryKey: ["move", id],
    queryFn: () => getMove(id),
    enabled: id > 0,
  });
}

export function useMoveSearch(q: string) {
  return useQuery({
    queryKey: ["move-search", q],
    queryFn: () => searchMoves(q),
    enabled: q.trim().length >= 2,
  });
}

export function useMovesByType(typeName: string) {
  return useQuery({
    queryKey: ["moves-by-type", typeName],
    queryFn: () => getMovesByType(typeName),
    enabled: typeName.length > 0,
  });
}
