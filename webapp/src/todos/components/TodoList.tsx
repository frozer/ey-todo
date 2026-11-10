import type { Todo } from "../../api"

export function TodoList({items, onRemove, onEdit, onPositionChange, isPositionPending}: {
  items: Todo[],
  onRemove: (id: string) => void,
  onEdit: (id: string) => void,
  onPositionChange: (id: string, idx: number, direction: 'UP' | 'DOWN') => void
  isPositionPending?: boolean
}) {
  if (!items?.length) return null;

  return (
    <ul className="divide-y divide-line rounded-lg border border-line bg-surface">
      {items.map((todo, idx) => (
        <li key={todo.id} className="flex flex-wrap items-center gap-2 px-4 py-3">
          <span className="min-w-0 flex-1 basis-full truncate sm:basis-auto">{todo.label}</span>
          <div className="flex gap-1.5">
            { idx > 0 && <button type="button" className="btn" disabled={isPositionPending} onClick={() => onPositionChange(todo.id, idx, 'UP')}>Up</button>}
            { idx < items.length - 1 && <button type="button" className="btn" disabled={isPositionPending} onClick={() => onPositionChange(todo.id, idx, 'DOWN')}>Down</button>}
            <button type="button" className="btn" onClick={() => onEdit(todo.id)}>Edit</button>
            <button type="button" className="btn btn-danger" onClick={() => onRemove(todo.id)}>Remove</button>
          </div>
        </li>
      ))}
    </ul>
  )
}
