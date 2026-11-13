import { useQuery } from "@tanstack/react-query";
import { getApiTodosItemIdGet, type Todo } from "../api";
import { STORE_KEY } from "./types";
import { convertApiError } from "../core/error.utils";

export function useTodo(id?: string) {

  const { data: itemToEdit = null, isLoading: isLoadPending, error: loadError } = useQuery({
    queryKey: [...STORE_KEY, id],
    queryFn: async (): Promise<Todo> => {
      const { data, error } = await getApiTodosItemIdGet({ path: { item_id: id! } });
      if (error) {
        throw convertApiError(error);
      }
      return data;
    },
    enabled: !!id,
  });

  return {
    isLoadPending,
    itemToEdit,
    loadError
  };
}
