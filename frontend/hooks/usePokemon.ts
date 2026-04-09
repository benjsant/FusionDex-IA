import { useQuery } from "@tanstack/react-query";
import {
  getPokemon,
  getPokemonList,
  getPokemonMoves,
  getPokemonEvolutions,
  getPokemonWeaknesses,
  searchPokemon,
} from "@/lib/api";

export function usePokemonList(params?: {
  type?: string;
  gen?: number;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: ["pokemon-list", params],
    queryFn: () => getPokemonList(params),
  });
}

export function usePokemonSearch(q: string) {
  return useQuery({
    queryKey: ["pokemon-search", q],
    queryFn: () => searchPokemon(q),
    enabled: q.trim().length >= 2,
  });
}

export function usePokemon(id: number) {
  return useQuery({
    queryKey: ["pokemon", id],
    queryFn: () => getPokemon(id),
    enabled: id > 0,
  });
}

export function usePokemonMoves(id: number) {
  return useQuery({
    queryKey: ["pokemon-moves", id],
    queryFn: () => getPokemonMoves(id),
    enabled: id > 0,
  });
}

export function usePokemonEvolutions(id: number) {
  return useQuery({
    queryKey: ["pokemon-evolutions", id],
    queryFn: () => getPokemonEvolutions(id),
    enabled: id > 0,
  });
}

export function usePokemonWeaknesses(id: number) {
  return useQuery({
    queryKey: ["pokemon-weaknesses", id],
    queryFn: () => getPokemonWeaknesses(id),
    enabled: id > 0,
  });
}
