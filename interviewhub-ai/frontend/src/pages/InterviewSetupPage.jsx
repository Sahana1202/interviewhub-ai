import PageHeader from '../components/PageHeader';
import InterviewSetupForm from '../components/InterviewSetupForm';

export default function InterviewSetupPage() {
  return <div className="interview-content"><PageHeader eyebrow="SET UP PRACTICE" title="Configure your interview" description="Choose a role, format, time limit, and Virtual HR interviewer."/><InterviewSetupForm/></div>;
}
