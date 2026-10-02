export const editableProfileFields = [
  'college', 'degree', 'department', 'graduation_year',
  'experience_level', 'target_role', 'target_industry', 'location',
];

export function editableProfile(profile = {}) {
  return Object.fromEntries(editableProfileFields.map((field) => [field, profile[field] ?? '']));
}

export function profilePayload(profile = {}) {
  const values = editableProfile(profile);
  return Object.fromEntries(Object.entries(values).map(([key, value]) => [key, value === '' ? null : value]));
}

export function profileCompletion(profile = {}) {
  const completed = editableProfileFields.filter((field) => {
    const value = profile[field];
    return value !== null && value !== undefined && String(value).trim() !== '';
  }).length;
  return Math.round((completed / editableProfileFields.length) * 100);
}
