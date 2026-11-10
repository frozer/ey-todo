import type { Todo } from "../../api"

export function TodoList({items, onRemove, onEdit, onPositionChange, isPositionPending}: {
  items: Todo[],
  onRemove: (id: string) => void,
  onEdit: (id: string) => void,
  onPositionChange: (id: string, idx: number, direction: 'UP' | 'DOWN') => void
  isPositionPending?: boolean
}) {

  return (
    <ul className="todoList">
      {items?.map((todo, idx) => (        
        <li key={todo.id}>
          <span>{todo.label}</span>
          { idx > 0 ? <button  disabled={isPositionPending} onClick={() => onPositionChange(todo.id, idx, 'UP')}>Up</button> : null }
          { idx < items.length - 1 ? <button disabled={isPositionPending} onClick={() => onPositionChange(todo.id, idx, 'DOWN')}>Down</button> : null }
          <button onClick={() => onEdit(todo.id)}>Edit</button>
          <button onClick={() => onRemove(todo.id)}>Remove</button>
        </li>      
      ))}
    </ul>
  )
}