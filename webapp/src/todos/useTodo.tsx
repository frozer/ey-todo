import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { createApiTodosPost, getApiTodosItemIdGet, updateApiTodosItemIdPatch, type Todo, type TodoCreate, type TodoUpdate } from "../api";
import { STORE_KEY } from "./types";
import { convertApiError } from "../core/error.utils";

function diffTodo(original: Todo, payload: TodoUpdate): TodoUpdate {
  const changed: TodoUpdate = {};

  if (original.label !== payload.label) changed.label = payload.label;
  if (original.status !== payload.status) changed.status = payload.status;
  if (original.text !== payload.text) changed.text = payload.text;

  if (payload.lft || payload.rgt) {
    changed.lft = payload.lft ?? null;
    changed.rgt = payload.rgt ?? null;
  }

  return changed;
}

export function useTodo(id?: string) {
  const queryClient = useQueryClient();

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

  const { mutate, error: createError, isPending: isCreatePending, isSuccess } = useMutation({
    mutationFn: async (payload: TodoCreate | TodoUpdate): Promise<void> => {
      const { error } = itemToEdit
        ? await updateApiTodosItemIdPatch({
            path: { item_id: itemToEdit.id },
            body: diffTodo(itemToEdit, payload),
          })
        : await createApiTodosPost({ body: payload as TodoCreate });

      if (error) {
        throw convertApiError(error);
      }
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: STORE_KEY });
    },
  });

  return {
    mutate,
    createError,
    isCreatePending,
    isLoadPending,
    itemToEdit,
    loadError,
    isSuccess,
  };
}
