const roleOptions = ['Python Developer', 'Full Stack Developer', 'Backend Developer', 'Frontend Developer', 'Software Engineer', 'AI/ML Engineer', 'Data Analyst', 'Data Scientist', 'QA Engineer', 'DevOps Engineer'];
const industryOptions = ['Information Technology', 'Software', 'AI & Machine Learning', 'FinTech', 'Healthcare', 'EdTech', 'E-commerce', 'Consulting'];
const degreeOptions = ['B.E.', 'B.Tech', 'M.E.', 'M.Tech', 'MCA', 'MBA', 'Other'];

function TextField({ label, name, value, onChange, placeholder, maxLength, list, type = 'text', required = false, min, max, hint }) {
  return <label className="field-label">{label}{required && <span className="required-mark">Required</span>}
    <input name={name} type={type} value={value ?? ''} onChange={onChange} placeholder={placeholder} maxLength={maxLength} list={list} required={required} min={min} max={max}/>
    {hint && <small>{hint}</small>}
  </label>;
}

export default function ProfileFields({ values, onChange, section = 'all' }) {
  const currentYear = new Date().getFullYear();
  return <div className="profile-fields">
    {(section === 'all' || section === 'about') && <>
      <TextField label="College or university" name="college" value={values.college} onChange={onChange} placeholder="Your college name" maxLength={200}/>
      <TextField label="Degree" name="degree" value={values.degree} onChange={onChange} placeholder="e.g. B.E." maxLength={120} list="degree-options"/>
      <datalist id="degree-options">{degreeOptions.map((item)=><option key={item} value={item}/>)}</datalist>
      <TextField label="Department" name="department" value={values.department} onChange={onChange} placeholder="e.g. Computer Science" maxLength={120}/>
      <TextField label="Graduation year" name="graduation_year" value={values.graduation_year} onChange={onChange} placeholder={`${currentYear}`} type="number" min="1950" max={currentYear + 10} hint="Enter a year between 1950 and 10 years from now."/>
    </>}
    {(section === 'all' || section === 'career') && <>
      <label className="field-label">Experience level{section==='career' && <span className="required-mark">Required</span>}
        <select name="experience_level" value={values.experience_level ?? ''} onChange={onChange} required={section==='career'}>
          <option value="">Choose your experience</option><option>Student</option><option>Fresher</option><option>0–1 years</option><option>1–3 years</option><option>3+ years</option>
        </select>
      </label>
      <TextField label="Target role" name="target_role" value={values.target_role} onChange={onChange} placeholder="e.g. Full Stack Developer" maxLength={120} list="role-options" required={section==='career'}/>
      <datalist id="role-options">{roleOptions.map((item)=><option key={item} value={item}/>)}</datalist>
      <TextField label="Target industry" name="target_industry" value={values.target_industry} onChange={onChange} placeholder="e.g. Software" maxLength={120} list="industry-options"/>
      <datalist id="industry-options">{industryOptions.map((item)=><option key={item} value={item}/>)}</datalist>
      <TextField label="Preferred location" name="location" value={values.location} onChange={onChange} placeholder="City, state, or region" maxLength={160}/>
    </>}
  </div>;
}
