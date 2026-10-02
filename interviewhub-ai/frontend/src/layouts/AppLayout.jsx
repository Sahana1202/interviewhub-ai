import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopNavbar from '../components/TopNavbar';

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  return <div className="signed-shell">
    <Sidebar open={sidebarOpen} onClose={()=>setSidebarOpen(false)}/>
    <main className="signed-main">
      <TopNavbar sidebarOpen={sidebarOpen} onOpenNavigation={()=>setSidebarOpen(true)}/>
      <Outlet/>
    </main>
  </div>;
}
