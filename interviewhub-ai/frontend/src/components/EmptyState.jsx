import { Inbox } from 'lucide-react';

export default function EmptyState({ title, description, action }) {
  return <div className="empty-state"><span><Inbox size={19}/></span><div><strong>{title}</strong><p>{description}</p>{action}</div></div>;
}
