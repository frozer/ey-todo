import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { createApiTodosPost, getApiTodosItemIdGet, updateApiTodosItemIdPatch, type Todo, type TodoCreate, type TodoUpdate } from "../api";
import { STORE_KEY } from "./types";

const ALLOWED_KEYS = ['label', 'text', 'status', 'position'];

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
        throw error;
      }
      return data;
    }
  }) : {};

  const { mutate, error: createError, isPending: isCreatePending, isSuccess } = useMutation({
    mutationFn: async (payload: TodoCreate | TodoUpdate): Promise<void> => {
      let error = null;

      if (itemToEdit && isUpdatePayload(payload)) {
        const changedRecord: Partial<TodoUpdate> = {};
        (Object.keys(payload) as Array<keyof TodoUpdate>).forEach((key) => {
          if ((ALLOWED_KEYS as Array<keyof TodoUpdate>).includes(key) && payload[key] !== itemToEdit[key]) {
            changedRecord[key] = payload[key] as any;
          }
        });

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
        throw error;
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