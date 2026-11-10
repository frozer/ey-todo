import { useLocation, useNavigate } from "react-router-dom";
import { TodoForm } from "./components/TodoForm";
import { useTodo } from "./useTodo";
import { useCallback, useMemo } from "react";
import type { TodoCreate, TodoUpdate } from "../api";
import type { LocationState } from "../core/navigation.types";
import { useTodos } from "./useTodos";

export function TodoPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id = '' }: LocationState = location.state || {}; 

  const mutationOptions = useMemo(() => ({
    onSuccess: () => navigate('/')
  }), [navigate])

  const {
    mutate,
    isLoadPending,
    isCreatePending,
    loadError,
    createError,
    itemToEdit
  } = useTodo(id);
  const {removeTodo, isRemovePending, removeError} = useTodos();

  const mutateAction = useCallback((payload: TodoCreate | TodoUpdate) => mutate(payload, mutationOptions), []);
  const cancelAction = useCallback(() => navigate('/'), []);
  const removeAction = useCallback(() => removeTodo({id}, mutationOptions), []);

  const errorMessage = useMemo(() => [loadError, removeError, createError]
    .map((e) => e?.message).join(' '), [loadError, removeError, createError]);
  
  return (
    <section>
      {errorMessage && <span className="error-message">{errorMessage}</span>}
      {isLoadPending
        ? <span className="info-message">Loading...</span>
        : <TodoForm onSubmit={mutateAction} item={itemToEdit}>
            <div className="form-footer">
              {id && <button disabled={isRemovePending} onClick={() => removeAction()}>Remove</button>}
              <button type="submit" disabled={isCreatePending}>Save</button>
              <button onClick={() => cancelAction()}>Cancel</button>
            </div>
          </TodoForm>
      }
    </section>
  )
}