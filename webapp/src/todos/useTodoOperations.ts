import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createApiTodosPost, deleteApiTodosItemIdDelete, updateApiTodosItemIdPatch, type Todo, type TodoCreate, type TodoUpdate } from "../api";
import { convertApiError } from "../core/error.utils";
import { STORE_KEY } from "./types";

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

export function useTodoOperations() {
  const queryClient = useQueryClient();

  const { mutate: createTodo, isPending: isCreatePending, error: createError  } = useMutation({
      mutationFn: async (payload: TodoCreate): Promise<void> => {
        const { error } = await createApiTodosPost({ body: payload as TodoCreate });
  
        if (error) {
          throw convertApiError(error);
        }
      },
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: STORE_KEY });
      },
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
    mutationFn: async (payload: {id: string, data: Partial<TodoUpdate>, prev?: Todo}): Promise<void> => {
      const {error} = await updateApiTodosItemIdPatch({
        path: {item_id: payload.id},
        body: payload.prev ? diffTodo(payload.prev, payload.data) : payload.data
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
    createTodo,
    isCreatePending,
    createError,
    removeTodo,
    isRemovePending,
    removeError,
    updateTodo,
    isUpdatePending,
    updateError
  }
}