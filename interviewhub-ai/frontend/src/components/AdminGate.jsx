import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
export default function AdminGate(){
  const {user,loading}=useAuth();
  if(loading)return <main className="page-center">Loading your workspace…</main>;
  if(!user)return <Navigate to="/login" replace/>;
  if(user.role!=='admin')return <Navigate to="/dashboard" replace/>;
  return <Outlet/>;
}
