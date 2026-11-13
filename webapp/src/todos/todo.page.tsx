import { useLocation, useNavigate } from "react-router-dom";
import { TodoForm } from "./components/TodoForm";
import { useTodo } from "./useTodo";
import { useCallback, useMemo } from "react";
import type { TodoCreate, TodoUpdate } from "../api";
import type { LocationState } from "../core/navigation.types";
import { useTodoOperations } from "./useTodoOperations";

export function TodoPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id = '' }: LocationState = location.state || {}; 

  const mutationOptions = useMemo(() => ({
    onSuccess: () => navigate('/')
  }), [navigate])

  const {
    isLoadPending,
    loadError,
    itemToEdit
  } = useTodo(id);
  const {createTodo, createError, isCreatePending, removeTodo, isRemovePending, removeError, updateTodo, updateError} = useTodoOperations();

  const mutateAction = useCallback(
    (payload: TodoCreate | TodoUpdate) => id 
      ? updateTodo({id, data: payload, prev: itemToEdit!}, mutationOptions) 
      : createTodo(payload as TodoCreate, mutationOptions),
    [updateTodo, createTodo, mutationOptions, itemToEdit]);
  const cancelAction = useCallback(() => navigate('/'), [navigate]);
  const removeAction = useCallback(
    () => removeTodo({id}, mutationOptions),
    [removeTodo, id, mutationOptions]);

  const errorMessage = useMemo(() => [loadError, removeError, createError, updateError]
    .map((e) => e?.message).filter(Boolean).join(' '), [loadError, removeError, createError]);

  return (
    <section className="w-full max-w-2xl space-y-4">
      {errorMessage && <span className="error-message">{errorMessage}</span>}
      {isLoadPending
        ? <span className="info-message">Loading...</span>
        : <TodoForm onSubmit={mutateAction} item={itemToEdit}>
            <div className="form-footer">
              {id && <button type="button" className="btn btn-danger mr-auto" disabled={isRemovePending} onClick={() => removeAction()}>Remove</button>}
              <button type="button" className="btn" onClick={() => cancelAction()}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={isCreatePending}>Save</button>
            </div>
          </TodoForm>
      }
    </section>
  )
}