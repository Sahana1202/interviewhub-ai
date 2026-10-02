import { useEffect, useState } from 'react';
import { ArrowLeft, ArrowRight, LoaderCircle, ShieldCheck } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import InterviewerCard from './InterviewerCard';
import InterviewSummary from './InterviewSummary';
import { companyApi, interviewApi, resumeApi } from '../services/api';

const experienceOptions = ['Student', 'Fresher', '0–1 years', '1–3 years', '3+ years'];
const roleOptions = ['Python Developer', 'Full Stack Developer', 'Backend Developer', 'Frontend Developer', 'Software Engineer', 'AI/ML Engineer', 'Data Analyst'];
const difficultyOptions = ['Beginner', 'Intermediate', 'Advanced'];
const advancedTypes = ['HR Interview', 'Technical Interview', 'Technical + HR', 'Project Interview', 'Resume-Based Interview', 'Company Preparation Interview', 'Mixed Interview'];
const durationOptions = [10, 15, 20, 30];

export default function InterviewSetupForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const [interviewers, setInterviewers] = useState([]);
  const [resumes, setResumes] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [resumeLoadError, setResumeLoadError] = useState('');
  const [aiStatus, setAiStatus] = useState({ available: false, provider: null, model: null });
  const [values, setValues] = useState({ company_name: '', company_id: location.state?.companyId || '', job_role: 'Full Stack Developer', experience_level: 'Fresher', interview_type: 'Combined', advanced_interview_type: 'Mixed Interview', difficulty: 'Intermediate', current_difficulty: 'Intermediate', difficulty_mode: 'fixed', duration_minutes: 15, interviewer_id: '', response_mode: 'text', resume_id: location.state?.resumeId || '', ai_enabled: false });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    interviewApi.interviewers().then((items) => {
      if (!active) return;
      setInterviewers(items);
      setValues((current) => ({ ...current, interviewer_id: current.interviewer_id || items[0]?.id || '' }));
    }).catch((requestError) => active && setError(requestError.message)).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  useEffect(() => { interviewApi.aiStatus().then(setAiStatus); }, []);

  useEffect(() => {
    let active = true;
    resumeApi.list().then((items) => {
      if (!active) return;
      setResumes(items.filter((item) => item.status === 'processed'));
      if (location.state?.resumeId && items.some((item) => item.id === location.state.resumeId && item.status === 'processed')) {
        setValues((current) => ({ ...current, resume_id: location.state.resumeId }));
      }
    }).catch((err) => active && setResumeLoadError(err.message));
    return () => { active = false; };
  }, [location.state]);

  useEffect(() => {
    let active = true;
    companyApi.list().then((result) => {
      if (!active) return;
      setCompanies(result.companies);
      if (location.state?.companyId) {
        const company = result.companies.find((item) => item.id === location.state.companyId);
        if (company) setValues((current) => ({ ...current, company_id: company.id, company_name: company.name }));
      }
    }).catch(() => active && setCompanies([]));
    return () => { active = false; };
  }, [location.state]);

  function update(field, value) { setValues((current) => ({ ...current, [field]: value })); }
  function updateAdvancedType(value) {
    const interviewType = value === 'HR Interview' ? 'HR' : value === 'Technical Interview' ? 'Technical' : 'Combined';
    setValues((current) => ({ ...current, advanced_interview_type: value, interview_type: interviewType }));
  }

  async function submit(event) {
    event.preventDefault(); setError('');
    if (values.job_role.trim().length < 2) { setError('Enter a job role with at least two characters.'); return; }
    if (!values.interviewer_id) { setError('Choose a Virtual HR interviewer.'); return; }
    setSubmitting(true);
    try {
      const result = await interviewApi.start({ ...values, company_id: values.company_id ? Number(values.company_id) : null, resume_id: values.resume_id ? Number(values.resume_id) : null, company_name: values.company_name.trim() || null, job_role: values.job_role.trim() });
      navigate(`/interviews/${result.session.id}`);
    } catch (requestError) { setError(requestError.message); }
    finally { setSubmitting(false); }
  }

  const selectedInterviewer = interviewers.find((item) => item.id === values.interviewer_id);
  if (loading) return <div className="interview-loading" role="status"><LoaderCircle className="spin"/> Loading Virtual HR profiles…</div>;

  return <form className="interview-setup-form" onSubmit={submit}>
    {error && <div className="interview-error" role="alert">{error}<button type="button" onClick={()=>{setLoading(true);setError('');interviewApi.interviewers().then((items)=>{setInterviewers(items);update('interviewer_id',items[0]?.id||'');}).catch((e)=>setError(e.message)).finally(()=>setLoading(false));}}>Retry</button></div>}
    <div className="setup-layout"><div className="setup-fields">
      <section className="setup-field-group"><div><span className="eyebrow">INTERVIEW CONTEXT</span><h2>What are you preparing for?</h2><p>Attach available source-backed company context, or keep this as a general interview.</p></div>
        <label className="field-label">Select company <span className="optional-label">OPTIONAL</span><select value={values.company_id} onChange={(event)=>{const id=event.target.value;update('company_id',id);update('company_name',companies.find((item)=>String(item.id)===id)?.name||'');}}><option value="">No company selected</option>{companies.map((company)=><option key={company.id} value={company.id}>{company.name}</option>)}</select></label>
        {values.company_id ? <p className="company-context-confirmation">✓ Company context attached. It will be available to the interview system; current questions remain from the general practice bank.</p> : <label className="field-label">Company name <span className="optional-label">OPTIONAL</span><input value={values.company_name} onChange={(event)=>update('company_name',event.target.value)} maxLength={160} placeholder="Optional context label"/></label>}
        <label className="field-label">Job role <span className="required-mark">REQUIRED</span><input list="interview-role-options" value={values.job_role} onChange={(event)=>update('job_role',event.target.value)} maxLength={120} placeholder="e.g. Backend Developer" required/><datalist id="interview-role-options">{roleOptions.map((role)=><option key={role} value={role}/>)}</datalist></label>
        <label className="field-label">Experience level <span className="required-mark">REQUIRED</span><select value={values.experience_level} onChange={(event)=>update('experience_level',event.target.value)}>{experienceOptions.map((value)=><option key={value}>{value}</option>)}</select></label>
      </section>
      <section className="setup-field-group"><div><span className="eyebrow">INTERVIEW PLAN</span><h2>Choose your practice</h2><p>Choose a structured type and fixed or adaptive difficulty. Adaptive pacing is based on recent AI practice feedback.</p></div>
        <label className="field-label">Interview type<select value={values.advanced_interview_type} onChange={(event)=>updateAdvancedType(event.target.value)}>{advancedTypes.map((value)=><option key={value}>{value}</option>)}</select></label>
        <fieldset><legend>Difficulty</legend><div className="choice-grid">{[...difficultyOptions, 'Adaptive'].map((value)=><button key={value} type="button" className={`choice-chip${(value==='Adaptive'?values.difficulty_mode==='adaptive':values.difficulty_mode==='fixed'&&values.difficulty===value)?' selected':''}`} aria-pressed={value==='Adaptive'?values.difficulty_mode==='adaptive':values.difficulty_mode==='fixed'&&values.difficulty===value} onClick={()=>value==='Adaptive'?update('difficulty_mode','adaptive'):(update('difficulty_mode','fixed'),update('difficulty',value),update('current_difficulty',value))}>{value}</button>)}</div></fieldset>
        <fieldset><legend>Duration</legend><div className="choice-grid duration-choices">{durationOptions.map((value)=><button key={value} type="button" className={`choice-chip${values.duration_minutes===value?' selected':''}`} aria-pressed={values.duration_minutes===value} onClick={()=>update('duration_minutes',value)}>{value} min</button>)}</div></fieldset>
      </section>
      <section className="setup-field-group"><div><span className="eyebrow">YOUR INTERVIEWER</span><h2>Choose a Virtual HR</h2><p>These are AI virtual interviewers, not real human recruiters.</p></div><div className="interviewer-choices">{interviewers.map((interviewer)=><InterviewerCard key={interviewer.id} interviewer={interviewer} selected={values.interviewer_id===interviewer.id} onSelect={()=>update('interviewer_id',interviewer.id)}/>)}</div></section>
      <section className="setup-field-group"><div><span className="eyebrow">RESPONSE</span><h2>How would you like to answer?</h2></div><div className="response-choice-grid"><button type="button" className={`response-option${values.response_mode==='text'?' selected':''}`} aria-pressed={values.response_mode==='text'} onClick={()=>update('response_mode','text')}><strong>Text</strong><small>Type and edit your answer</small></button><button type="button" className={`response-option${values.response_mode==='voice'?' selected':''}`} aria-pressed={values.response_mode==='voice'} onClick={()=>update('response_mode','voice')}><strong>Voice</strong><small>Browser speech recognition, when available</small></button></div><p className="speech-support-note">Voice input depends on your browser. Text answers always remain available.</p></section>
      <section className="setup-field-group"><div><span className="eyebrow">OPTIONAL CONTEXT</span><h2>Resume context</h2><p>Attach extracted resume details to this interview session for future contextual preparation.</p></div><label className="field-label">Select resume<select value={values.resume_id} onChange={(event)=>update('resume_id',event.target.value)}><option value="">No resume</option>{resumes.map((resume)=><option key={resume.id} value={resume.id}>{resume.file_name}</option>)}</select></label>{!resumes.length && <p className="speech-support-note">Upload a resume to enable resume-based interview preparation. You can still start a normal interview.</p>}{resumeLoadError && <p className="speech-support-note">Resume list unavailable: {resumeLoadError}</p>}</section>
      <section className="setup-field-group"><div><span className="eyebrow">AI INTERVIEW MODE</span><h2>{aiStatus.available ? 'AI provider available' : 'AI Interview Mode unavailable'}</h2><p>{aiStatus.available ? `Questions and practice feedback will use ${aiStatus.provider} · ${aiStatus.model}. You can continue with the general practice bank if preferred.` : 'AI interview features unavailable. Please configure an AI provider. General practice questions remain available.'}</p></div><button type="button" className={`choice-chip${values.ai_enabled?' selected':''}`} aria-pressed={values.ai_enabled} disabled={!aiStatus.available} onClick={()=>update('ai_enabled',!values.ai_enabled)}>{values.ai_enabled?'AI Interview Mode enabled':'Enable AI Interview Mode'}</button></section>
    </div><aside className="setup-summary-column"><InterviewSummary company={values.company_name} role={values.job_role} experience={values.experience_level} type={values.advanced_interview_type} difficulty={values.difficulty_mode==='adaptive'?'Adaptive':values.difficulty} duration={values.duration_minutes} interviewer={selectedInterviewer} responseMode={values.response_mode}/><p className="starter-bank-note"><ShieldCheck size={15}/> {values.ai_enabled?'AI questions are generated one at a time and clearly labeled.':'Rule-based questions are general practice prompts, not company facts.'}</p><button className="button button-primary start-interview-button" type="submit" disabled={submitting||!selectedInterviewer}>{submitting ? <><LoaderCircle className="spin" size={17}/> Starting…</> : <>Start Interview <ArrowRight size={17}/></>}</button><Link className="back-link" to="/interviews"><ArrowLeft size={14}/> Back to interviews</Link></aside></div>
  </form>;
}
