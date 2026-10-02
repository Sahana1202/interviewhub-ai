import { useLocation } from 'react-router-dom';
import ComingSoon from '../components/ComingSoon';
import PageHeader from '../components/PageHeader';

const modules = {
  '/interviews': ['Interview Practice', 'Structured interview practice sessions will be available here.'],
  '/resume': ['Resume Analyzer', 'Resume review tools and guidance will be available here.'],
  '/job-match': ['Job Match', 'Role matching and job fit guidance will be available here.'],
  '/companies': ['Company Preparation', 'Company research and interview preparation resources will be available here.'],
  '/learning': ['Learning Hub', 'Curated learning paths and resources will be available here.'],
  '/aptitude': ['Aptitude Practice', 'Practice questions and explanations will be available here.'],
  '/english': ['English Coach', 'English communication practice will be available here.'],
  '/roadmap': ['Learning Roadmap', 'A learning plan based on your career goal will be available here.'],
  '/performance': ['Performance', 'Your practice performance summary will be available here.'],
  '/history': ['Interview History', 'Completed interview sessions will be listed here.'],
};

export default function ComingSoonPage() {
  const [title, description] = modules[useLocation().pathname] || ['Preparation tools', 'This section is being prepared.'];
  return <div className="dashboard-content placeholder-page"><PageHeader eyebrow="PREPARATION WORKSPACE" title={title} description={description}/><ComingSoon title={`${title} is in development`} description="This section is a planned part of InterviewHub AI. It does not have active tools yet."/></div>;
}
