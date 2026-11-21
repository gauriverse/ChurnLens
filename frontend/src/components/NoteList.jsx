import { orderNotes } from '../profile'

export default function NoteList({ notes }) {
  if (notes.length === 0) return null
  return (
    <ul className="space-y-2">
      {orderNotes(notes).map((note, index) => (
        <li key={index} className="flex gap-2">
          <span
            className={`mt-0.5 h-fit shrink-0 rounded px-1.5 py-0.5 text-[11px] font-medium leading-none ${
              note.level === 'warning' ? 'bg-risk-medium-soft text-risk-medium' : 'bg-canvas text-muted'
            }`}
          >
            {note.level === 'warning' ? 'Warning' : 'Note'}
          </span>
          <span>{note.text}</span>
        </li>
      ))}
    </ul>
  )
}