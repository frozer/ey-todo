import { useCallback, useMemo } from "react";
import { TodoList } from "./components/TodoList";
import { useTodos } from "./useTodos";
import { useNavigate } from "react-router-dom";

export function TodosPage() {
  const navigate = useNavigate();

  const {todos,
    isPending,
    error,
    setQuery,
    removeTodo,
    updateTodo,
    updateError,
    isUpdatePending
  } = useTodos();

  const onQuery = useCallback((q: string) => setQuery(q), []);

  const removeAction = useCallback((id: string) => removeTodo({id}), []);
  const createAction = useCallback(() => navigate('todo'), []);
  const editAction = useCallback((id: string) => navigate('todo', {state: {id}}), []);
  const changePosition = useCallback((id: string, idx: number, direction: 'UP' | 'DOWN') => {
    let lft, rgt;

    if (direction === 'UP') {
      lft = (idx - 2 < 0) ? null : todos[idx - 2].id
      rgt = todos[idx - 1].id
    }

    if (direction === 'DOWN') {
      rgt = idx + 2 > todos.length - 1 ? null : todos[idx + 2].id;
      lft = todos[idx + 1].id
    }

    updateTodo({id, data: {lft,rgt}});
  }, [todos])

  const errorMessage = useMemo(() => [error, updateError]
    .map((e) => e?.message).join(' '), []);

  return (
    <section>
      {errorMessage && <span className="error-message">{errorMessage}</span>}
      <header>
        <input type="text" onChange={(e) => onQuery(e.target.value)} placeholder="Search..."></input>
        <button type="button" onClick={() => createAction()}>New Todo</button>
      </header>
      {isPending ? <span className="info-message">Loading...</span> : null }
  
      <TodoList 
        items={todos} 
        onRemove={removeAction}
        onEdit={editAction}
        isPositionPending={isUpdatePending}
        onPositionChange={changePosition}></TodoList>
    </section>
  )
}