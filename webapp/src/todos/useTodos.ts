import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { deleteApiTodosItemIdDelete, listApiTodosGet, updateApiTodosItemIdPatch, type Todo, type TodoUpdate } from "../api";
import { STORE_KEY } from "./types";
import { convertApiError } from "../core/error.utils";

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
        throw convertApiError(error);
      }
      return data.items
    }
  });

  const { mutate: removeTodo, isPending: isRemovePending, error: removeError } = useMutation({
    mutationFn: async (payload: {id: string}): Promise<void> => {
      const {error} = await deleteApiTodosItemIdDelete({path: {item_id: payload.id}});
      if (error) {
        throw convertApiError(error);
      }      
    },
    onSuccess: async () => {      
      await queryClient.invalidateQueries({ queryKey: STORE_KEY })
    }      
  });

  const { mutate: updateTodo, isPending: isUpdatePending, error: updateError } = useMutation({
    mutationFn: async (payload: {id: string, data: Partial<TodoUpdate>}): Promise<void> => {
      const {error} = await updateApiTodosItemIdPatch({
        path: {item_id: payload.id},
        body: payload.data
      });
      if (error) {
        throw convertApiError(error);
      }      
    },
    onSuccess: async () => {      
      await queryClient.invalidateQueries({ queryKey: STORE_KEY })
    }      
  });

  return {
    todos: todos || [],
    isPending,
    query,
    error,
    setQuery,
    removeTodo,
    isRemovePending,
    removeError,
    updateTodo,
    isUpdatePending,
    updateError
  }
}