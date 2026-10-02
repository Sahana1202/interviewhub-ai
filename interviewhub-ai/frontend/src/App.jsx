import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import AuthLayout from './layouts/AuthLayout';
import AppLayout from './layouts/AppLayout';
import ProtectedRoute from './components/ProtectedRoute';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import OnboardingPage from './pages/OnboardingPage';
import ProfilePage from './pages/ProfilePage';
import SettingsPage from './pages/SettingsPage';
import ComingSoonPage from './pages/ComingSoonPage';
import InterviewsPage from './pages/InterviewsPage';
import InterviewSetupPage from './pages/InterviewSetupPage';
import InterviewRoomPage from './pages/InterviewRoomPage';
import InterviewCompletePage from './pages/InterviewCompletePage';
import InterviewReportPage from './pages/InterviewReportPage';
import InterviewHistoryPage from './pages/InterviewHistoryPage';
import ResumePage from './pages/ResumePage';
import ResumeDetailPage from './pages/ResumeDetailPage';
import CompanyPage from './pages/CompanyPage';
import CompanyKnowledgePage from './pages/CompanyKnowledgePage';
import LearningHubPage from './pages/LearningHubPage';
import LearningCategoryPage from './pages/LearningCategoryPage';
import LearningTopicPage from './pages/LearningTopicPage';
import LearningPracticePage from './pages/LearningPracticePage';
import LearningHistoryPage from './pages/LearningHistoryPage';
import PlacementResourcesPage, { LearningResourceDetailPage } from './pages/PlacementResourcesPage';
import './interviews.css';
import './resume.css';
import './company.css';
import './learning.css';
import AdminLayout from './layouts/AdminLayout';
import AdminPage from './pages/AdminPage';
import AdminGate from './components/AdminGate';

export default function App() {
  return <AuthProvider><Routes>
    <Route path="/" element={<LandingPage/>}/>
    <Route element={<AuthLayout/>}>
      <Route path="/login" element={<LoginPage/>}/>
      <Route path="/register" element={<RegisterPage/>}/>
    </Route>
    <Route path="/onboarding" element={<ProtectedRoute profileStatus="incomplete"><OnboardingPage/></ProtectedRoute>}/>
    <Route element={<AdminGate/>}>
      <Route element={<AdminLayout/>}>
        {['/admin','/admin/users','/admin/companies','/admin/learning','/admin/resources','/admin/interviews','/admin/activity-logs'].map(path=><Route key={path} path={path} element={<AdminPage/>}/>)}
      </Route>
    </Route>
    <Route element={<ProtectedRoute profileStatus="complete"><AppLayout/></ProtectedRoute>}>
      <Route path="/dashboard" element={<DashboardPage/>}/>
      <Route path="/profile" element={<ProfilePage/>}/>
      <Route path="/settings" element={<SettingsPage/>}/>
      <Route path="/resume" element={<ResumePage/>}/>
      <Route path="/resume/:resumeId" element={<ResumeDetailPage/>}/>
      <Route path="/company" element={<CompanyPage/>}/>
      <Route path="/company/:companyId" element={<CompanyPage/>}/>
      <Route path="/company/:companyId/knowledge" element={<CompanyKnowledgePage/>}/>
      <Route path="/learning" element={<LearningHubPage/>}/>
      <Route path="/learning/category/:categoryId" element={<LearningCategoryPage/>}/>
      <Route path="/learning/english" element={<LearningCategoryPage slugOverride="professional-english"/>}/>
      <Route path="/learning/aptitude" element={<LearningCategoryPage slugOverride="aptitude"/>}/>
      <Route path="/learning/topic/:topicId" element={<LearningTopicPage/>}/>
      <Route path="/learning/practice" element={<LearningPracticePage/>}/>
      <Route path="/learning/practice/:attemptId" element={<LearningPracticePage/>}/>
      <Route path="/learning/history" element={<LearningHistoryPage/>}/>
      <Route path="/learning/resources" element={<PlacementResourcesPage/>}/>
      <Route path="/resources" element={<PlacementResourcesPage/>}/>
      <Route path="/resources/:resourceId" element={<LearningResourceDetailPage/>}/>
      <Route path="/interviews" element={<InterviewsPage/>}/>
      <Route path="/interviews/setup" element={<InterviewSetupPage/>}/>
      <Route path="/interviews/history" element={<InterviewHistoryPage/>}/>
      <Route path="/interviews/:sessionId/complete" element={<InterviewCompletePage/>}/>
      <Route path="/interviews/:sessionId/report" element={<InterviewReportPage/>}/>
      <Route path="/interview/:sessionId/report" element={<InterviewReportPage/>}/>
      <Route path="/interviews/:sessionId" element={<InterviewRoomPage/>}/>
      <Route path="/history" element={<InterviewHistoryPage/>}/>
      <Route path="/companies" element={<Navigate to="/company" replace/>}/>
      <Route path="/aptitude" element={<Navigate to="/learning/aptitude" replace/>}/>
      <Route path="/english" element={<Navigate to="/learning/english" replace/>}/>
      {['job-match','roadmap','performance'].map((path)=><Route key={path} path={`/${path}`} element={<ComingSoonPage/>}/>)}
    </Route>
    <Route path="*" element={<Navigate to="/" replace/>}/>
  </Routes></AuthProvider>;
}
