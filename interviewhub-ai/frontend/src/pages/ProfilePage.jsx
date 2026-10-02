import { useEffect, useState } from 'react';
import { Check, LoaderCircle, Save } from 'lucide-react';
import ProfileFields from '../components/ProfileFields';
import { useAuth } from '../context/AuthContext';
import { profileApi } from '../services/api';
import { editableProfile, profilePayload } from '../utils/profile';

export default function ProfilePage() {
  const { user, setUserProfile } = useAuth();
  const [values, setValues] = useState(()=>editableProfile(user?.profile));
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(()=>{
    let active=true;
    profileApi.get().then((profile)=>{if(active){setValues(editableProfile(profile));setUserProfile(profile)}})
      .catch((cause)=>{if(active)setError(cause.message)})
      .finally(()=>{if(active)setLoading(false)});
    return ()=>{active=false};
  },[setUserProfile]);

  function update(event) {
    const {name,value}=event.target;
    setValues((current)=>({...current,[name]:name==='graduation_year'&&value?Number(value):value}));
    setSuccess('');
  }

  async function save(event) {
    event.preventDefault(); setBusy(true); setError(''); setSuccess('');
    if (!values.experience_level || !values.target_role?.trim()) { setBusy(false); setError('Experience level and target role are required.'); return; }
    try {
      const profile=await profileApi.update(profilePayload(values));
      setValues(editableProfile(profile)); setUserProfile(profile); setSuccess('Your profile changes have been saved.');
    } catch(cause) { setError(cause.message); }
    finally { setBusy(false); }
  }

  if(loading) return <div className="dashboard-content"><p className="muted">Loading your profile…</p></div>;
  return <div className="dashboard-content profile-page"><span className="eyebrow">ACCOUNT</span><h1>My profile</h1><p className="muted">Keep your education and career goals up to date.</p>
    <form className="profile-edit-card" onSubmit={save}><ProfileFields values={values} onChange={update}/>
      <p className="profile-policy">Experience level and target role are required to keep onboarding complete. Clearing either returns you to onboarding.</p>
      {error&&<p className="form-error" role="alert">{error}</p>}{success&&<p className="success-message" role="status"><Check size={16}/>{success}</p>}
      <div className="profile-save-row"><span>Editing {user?.name}’s profile</span><button className="button button-primary" disabled={busy}>{busy?<><LoaderCircle className="spin" size={16}/> Saving…</>:<><Save size={16}/> Save changes</>}</button></div>
    </form>
  </div>;
}
