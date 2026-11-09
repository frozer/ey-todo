import type { Todo } from "../../api"

export function TodoList({items, onRemove, onEdit}: {
  items: Todo[],
  onRemove: (id: string) => void,
  onEdit: (id: string) => void
}) {
  return (
    <ul className="todoList">
      {items?.map(todo => (        
        <li key={todo.id}>
          <span>{todo.label}</span>
          <button onClick={() => onEdit(todo.id)}>Edit</button>
          <button onClick={() => onRemove(todo.id)}>Remove</button>
        </li>      
      ))}
    </ul>
  )
}