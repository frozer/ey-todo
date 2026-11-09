import { useCallback } from "react";
import { TodoList } from "./components/TodoList";
import { useTodos } from "./useTodos";
import { useNavigate } from "react-router-dom";

export function TodosPage() {
  const navigate = useNavigate();

  const {todos, isPending, error, setQuery, removeTodo} = useTodos();

  const onQuery = useCallback((q: string) => setQuery(q), []);

  const removeAction = useCallback((id: string) => removeTodo(id), []);
  const createAction = useCallback(() => navigate('todo'), []);
  const editAction = useCallback((id: string) => navigate('todo', {state: {id}}), []);

  return (
    <section>
      <header>
        <input type="text" onChange={(e) => onQuery(e.target.value)}></input>
        <button type="button" onClick={() => createAction()}>New</button>
      </header>
      {isPending ? <span>Loading...</span> : null }

      <TodoList items={todos} onRemove={removeAction} onEdit={editAction}></TodoList>
      
    </section>
  )
}