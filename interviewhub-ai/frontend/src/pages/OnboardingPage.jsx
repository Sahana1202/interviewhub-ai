import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Check, LoaderCircle, LogOut, Sparkles } from 'lucide-react';
import ProfileFields from '../components/ProfileFields';
import { useAuth } from '../context/AuthContext';
import { profileApi } from '../services/api';
import { editableProfile, profilePayload } from '../utils/profile';

const emptyProfile = { college: '', degree: '', department: '', graduation_year: '', experience_level: '', target_role: '', target_industry: '', location: '' };
const stepNames = ['About you', 'Career goal', 'Review'];

export default function OnboardingPage() {
  const { user, logout, setUserProfile } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [values, setValues] = useState(()=>({...emptyProfile, ...editableProfile(user?.profile)}));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  const fields = useMemo(()=>[
    ['College', values.college], ['Degree', values.degree], ['Department', values.department],
    ['Graduation Year', values.graduation_year], ['Experience', values.experience_level],
    ['Target Role', values.target_role], ['Industry', values.target_industry], ['Location', values.location],
  ], [values]);

  function update(event) {
    const {name, value} = event.target;
    setValues((current)=>({...current, [name]: name==='graduation_year' && value ? Number(value) : value}));
  }

  async function saveDraft() {
    setBusy(true); setError('');
    try {
      const profile = await profileApi.update(profilePayload(values));
      setUserProfile(profile);
      setValues({...emptyProfile, ...editableProfile(profile)});
      return true;
    } catch (cause) { setError(cause.message); return false; }
    finally { setBusy(false); }
  }

  async function next() {
    if (step === 0 && !(await saveDraft())) return;
    if (step === 1) {
      if (!values.experience_level || !values.target_role?.trim()) { setError('Choose an experience level and enter a target role to continue.'); return; }
      if (!(await saveDraft())) return;
    }
    setError(''); setStep((current)=>Math.min(2, current+1));
  }

  async function complete() {
    setBusy(true); setError(''); setSaved(false);
    try {
      if (!values.experience_level || !values.target_role?.trim()) { setError('Choose an experience level and enter a target role to complete onboarding.'); return; }
      const profile = await profileApi.completeOnboarding(profilePayload(values));
      setUserProfile(profile); setSaved(true);
      navigate('/dashboard', {replace:true});
    } catch (cause) { setError(cause.message); }
    finally { setBusy(false); }
  }

  function signOut() { logout(); navigate('/login', {replace:true}); }

  return <main className="onboarding-page">
    <header className="onboarding-topbar"><a className="brand-lockup" href="/"><span className="brand-icon"><Sparkles size={19}/></span><span>InterviewHub <b>AI</b></span></a><button className="quiet-button" onClick={signOut}><LogOut size={16}/> Sign out</button></header>
    <section className="onboarding-content"><div className="onboarding-heading"><span className="eyebrow">LET’S MAKE THIS YOURS</span><h1>Build your preparation profile</h1><p>Share a few details so your career preparation can fit your goals. You can leave optional fields blank and change everything later.</p></div>
      <div className="onboarding-card"><div className="step-progress" aria-label={`Step ${step+1} of 3`}>{stepNames.map((name,index)=><div className={`step-item ${index===step?'current':''} ${index<step?'done':''}`} key={name}><span>{index<step?<Check size={15}/>:index+1}</span><label>{name}</label></div>)}</div>
        {step===0 && <section><span className="step-kicker">STEP 1 OF 3</span><h2>About you</h2><p className="step-description">Your education details are optional. Add what you’d like to include.</p><ProfileFields values={values} onChange={update} section="about"/></section>}
        {step===1 && <section><span className="step-kicker">STEP 2 OF 3</span><h2>Where do you want to go?</h2><p className="step-description">Your experience level and target role help us shape your preparation.</p><ProfileFields values={values} onChange={update} section="career"/></section>}
        {step===2 && <section><span className="step-kicker">STEP 3 OF 3</span><h2>Review your profile</h2><p className="step-description">Check your details before completing your profile.</p><div className="profile-summary">{fields.map(([label,value])=><div key={label}><span>{label}</span><strong>{value || 'Not provided'}</strong></div>)}</div></section>}
        {error && <p className="form-error" role="alert">{error}</p>}{saved && <p className="success-message" role="status">Your profile is complete.</p>}
        <div className="onboarding-actions">{step>0?<button className="button button-secondary" onClick={()=>{setError('');setStep((current)=>current-1)}} disabled={busy}><ArrowLeft size={16}/> Back</button>:<span/>}{step<2?<button className="button button-primary" onClick={next} disabled={busy}>{busy?<><LoaderCircle className="spin" size={17}/> Saving…</>:<>Continue <ArrowRight size={16}/></>}</button>:<button className="button button-primary" onClick={complete} disabled={busy}>{busy?<><LoaderCircle className="spin" size={17}/> Completing…</>:<>Complete profile <Check size={16}/></>}</button>}</div>
      </div><p className="onboarding-footnote">Signed in as {user?.email}. Your details are only used to personalize your InterviewHub workspace.</p>
    </section>
  </main>;
}
