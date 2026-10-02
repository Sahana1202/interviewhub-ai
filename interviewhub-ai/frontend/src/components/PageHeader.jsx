export default function PageHeader({ eyebrow, title, description, action }) {
  return <div className="page-heading"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h1>{title}</h1>{description && <p className="muted">{description}</p>}</div>{action}</div>;
}
