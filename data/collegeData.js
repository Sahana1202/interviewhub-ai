const collegeData = {
  collegeName: "Bright Future College",
  fees: {
    btech: "B.Tech annual tuition fee is Rs. 95,000.",
    bba: "BBA annual tuition fee is Rs. 60,000.",
    bca: "BCA annual tuition fee is Rs. 55,000.",
    hostel: "Hostel fee is Rs. 45,000 per year including basic facilities."
  },
  timetable: {
    weekdays: "Classes run from Monday to Friday, 9:00 AM to 4:00 PM.",
    firstYear: "First-year timetable usually includes core classes from 9:30 AM to 3:30 PM.",
    lab: "Lab sessions are generally scheduled between 1:00 PM and 4:00 PM."
  },
  departments: [
    "Computer Science",
    "Mechanical Engineering",
    "Civil Engineering",
    "Electronics and Communication",
    "Business Administration",
    "Computer Applications"
  ],
  contact: {
    phone: "+91 98765 43210",
    email: "admissions@brightfuturecollege.edu",
    website: "www.brightfuturecollege.edu"
  },
  quickReplies: [
    "What are the course fees?",
    "Show the class timetable",
    "List all departments",
    "How can I contact the college?"
  ]
};

function formatDepartments() {
  return `Available departments are: ${collegeData.departments.join(", ")}.`;
}

function formatFees() {
  return [
    "Here is the current fee information:",
    `- ${collegeData.fees.btech}`,
    `- ${collegeData.fees.bba}`,
    `- ${collegeData.fees.bca}`,
    `- ${collegeData.fees.hostel}`
  ].join("\n");
}

function formatTimetable() {
  return [
    "Here is the timetable overview:",
    `- ${collegeData.timetable.weekdays}`,
    `- ${collegeData.timetable.firstYear}`,
    `- ${collegeData.timetable.lab}`
  ].join("\n");
}

function formatContact() {
  return `You can contact ${collegeData.collegeName} at ${collegeData.contact.phone}, email ${collegeData.contact.email}, or visit ${collegeData.contact.website}.`;
}

function answerCollegeQuery(message) {
  const normalizedMessage = message.toLowerCase();

  if (normalizedMessage.includes("fee") || normalizedMessage.includes("tuition") || normalizedMessage.includes("hostel")) {
    return formatFees();
  }

  if (normalizedMessage.includes("timetable") || normalizedMessage.includes("class time") || normalizedMessage.includes("schedule")) {
    return formatTimetable();
  }

  if (normalizedMessage.includes("department") || normalizedMessage.includes("courses") || normalizedMessage.includes("branch")) {
    return formatDepartments();
  }

  if (normalizedMessage.includes("contact") || normalizedMessage.includes("phone") || normalizedMessage.includes("email") || normalizedMessage.includes("website")) {
    return formatContact();
  }

  if (normalizedMessage.includes("college") || normalizedMessage.includes("admission")) {
    return `${collegeData.collegeName} offers career-focused programs with supportive faculty, modern labs, and student services. Ask me about fees, timetable, departments, or contact details.`;
  }

  return "I can help with fees, timetable, departments, and contact information. Please ask a college-related question such as 'What are the B.Tech fees?' or 'List the departments.'";
}

module.exports = {
  answerCollegeQuery,
  collegeData
};
