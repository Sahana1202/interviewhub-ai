import PageHeader from '../components/PageHeader';
import InterviewHistory from '../components/InterviewHistory';

export default function InterviewHistoryPage() {
  return <div className="interview-content"><PageHeader eyebrow="YOUR PREPARATION RECORD" title="Interview History" description="Review saved interviews and revisit your answers."/><InterviewHistory/></div>;
}
