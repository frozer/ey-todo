import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { deleteApiTodosItemIdDelete, listApiTodosGet, type Todo, type TodoUpdate } from "../api";
import { STORE_KEY } from "./types";

export function useTodos() {
  const [query, setQuery] = useState<string>('');
  
  const queryClient = useQueryClient();

  const { isPending, error, data: todos } = useQuery({
    queryKey: [...STORE_KEY, query],
    queryFn: async (): Promise<Todo[]> => {
      const {data, error} = query 
        ? await listApiTodosGet({query: {q: query}})
        : await listApiTodosGet();
      if (error) {
        throw error;
      }
      return data.items
    }
  });

  const { mutate: removeTodo, isPending: isRemovePending, error: removeError } = useMutation({
    mutationFn: async (id: string): Promise<void> => {
      if (id) {
        const {error} = await deleteApiTodosItemIdDelete({path: {item_id: id}});
        if (error) {
          throw error;
        }
      }
    },
    onSuccess: async () => {      
      await queryClient.invalidateQueries({ queryKey: STORE_KEY })
    }      
  });

  return {
    todos: todos as unknown as Todo[],
    isPending,
    query,
    error,
    setQuery,
    removeTodo,
    isRemovePending,
    removeError
  }
}