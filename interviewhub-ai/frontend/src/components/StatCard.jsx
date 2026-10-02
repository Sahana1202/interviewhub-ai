export default function StatCard({ label, value, detail, icon: Icon }) {
  return <article className="stat-card">{Icon && <span className="stat-icon"><Icon size={18}/></span>}<span className="stat-label">{label}</span><strong>{value}</strong>{detail && <small>{detail}</small>}</article>;
}
