import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { createApiTodosPost, getApiTodosItemIdGet, updateApiTodosItemIdPatch, type Todo, type TodoCreate, type TodoUpdate } from "../api";
import { STORE_KEY } from "./types";
import { convertApiError } from "../core/error.utils";

const isUpdatePayload = (value: any): value is TodoUpdate => {
  return true
}

export function useTodo(id?: string) {
  const queryClient = useQueryClient();

  const {data: itemToEdit = null, isPending : isLoadPending = false, error: loadError} = id ? useQuery({
    queryKey: [...STORE_KEY, id],
    queryFn: async (): Promise<Todo> => {
      const {data, error} = await getApiTodosItemIdGet({path: {item_id: id}});
      if (error) {
        throw convertApiError(error);
      }
      return data;
    }
  }) : {};

  const { mutate, error: createError, isPending: isCreatePending, isSuccess } = useMutation({
    mutationFn: async (payload: TodoCreate | TodoUpdate): Promise<void> => {
      let error = null;

      if (itemToEdit && isUpdatePayload(payload)) {
        const changedRecord: Partial<TodoUpdate> = {};
        
        if (itemToEdit.label !== payload.label)
          changedRecord.label = payload.label;

        if (itemToEdit.status !== payload.status)
          changedRecord.status = payload.status;
      
        if (itemToEdit.text !== payload.text)
          changedRecord.text = payload.text;
        
        if (payload.lft || payload.rgt) {
          changedRecord.lft = payload.lft ?? null;
          changedRecord.rgt = payload.rgt ?? null;
        }

        const {error: updateError} = await updateApiTodosItemIdPatch({
          path: {item_id: itemToEdit.id},
          body: changedRecord
        });
        error = updateError;
      } else {
        const {error: createError} = await createApiTodosPost({body: payload as TodoCreate});
        error = createError;
      }

      if (error) {
        throw convertApiError(error)
      }
    },
    onSuccess: async () => {      
      await queryClient.invalidateQueries({ queryKey: STORE_KEY });
    }      
  })

  return {
    mutate,
    createError,
    isCreatePending,
    isLoadPending,
    itemToEdit,
    loadError,
    isSuccess
  }
}