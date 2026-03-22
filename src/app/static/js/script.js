// ─── State ────────────────────────────────────────────────────────────────────
const state = {
    currentStep: 1,
    selectedDegrees: [],
    selectedCampus: '',
    selectedCourses: [],       // [{name, course_number, parent_course_number}]
    allCourses: [],
    lecturerData: {},           // {courseName: {lecture: [], practice: []}}
    lecturerPrefs: {},          // {courseName: {lecture: [], practice: []}}
    attendancePrefs: {},        // {courseName: {lecture: bool, practice: bool}}
    loginTab: 'standard',
    settings: window.APP_DATA.settings,
};

// ─── Utility Functions ───────────────────────────────────────────────────────

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast toast-${type} show`;
    setTimeout(() => toast.classList.remove('show'), 3500);
}

async function apiCall(url, method = 'GET', body = null) {
    const opts = {method, headers: {'Content-Type': 'application/json'}};
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    const data = await res.json();
    if (!res.ok) throw {status: res.status, data};
    return data;
}

// ─── Step Navigation ─────────────────────────────────────────────────────────

function goToStep(step) {
    // Validate before advancing
    if (step > state.currentStep) {
        if (state.currentStep === 1 && (!state.selectedDegrees.length || !state.selectedCampus)) {
            showToast('נא לבחור תואר וקמפוס', 'error');
            return;
        }
        if (state.currentStep === 2 && !state.selectedCourses.length) {
            showToast('נא לבחור קורסים', 'error');
            return;
        }
    }

    // Before going to step 3, load lecturer data
    if (step === 3) {
        loadLecturerData();
    }

    // Before going to step 4, update summary
    if (step === 4) {
        updateSummary();
    }

    state.currentStep = step;

    // Update step indicators
    document.querySelectorAll('.step').forEach(el => {
        const s = parseInt(el.dataset.step);
        el.classList.toggle('active', s === step);
        el.classList.toggle('completed', s < step);
    });

    // Show/hide step content
    document.querySelectorAll('.step-content').forEach(el => {
        el.classList.toggle('active', el.id === `step-${step}`);
    });

    // Scroll to top
    window.scrollTo({top: 0, behavior: 'smooth'});
}

function updateNextButtons() {
    // Step 1 next
    const step1Next = document.querySelector('#step-1 .btn-next');
    if (step1Next) {
        step1Next.disabled = !state.selectedDegrees.length || !state.selectedCampus;
    }

    // Step 2 next
    const step2Next = document.querySelector('#step-2 .btn-next');
    if (step2Next) {
        step2Next.disabled = !state.selectedCourses.length;
    }
}

// ─── Step 1: Degrees & Campus ────────────────────────────────────────────────

function initDegrees() {
    document.querySelectorAll('#degrees-list .chip-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const degree = btn.dataset.degree;
            btn.classList.toggle('active');

            if (btn.classList.contains('active')) {
                if (!state.selectedDegrees.includes(degree)) {
                    state.selectedDegrees.push(degree);
                }
            } else {
                state.selectedDegrees = state.selectedDegrees.filter(d => d !== degree);
            }
            updateNextButtons();
        });
    });
}

function initCampus() {
    const select = document.getElementById('campus-select');
    // Restore from settings
    if (state.settings.campus_name) {
        select.value = state.settings.campus_name;
        state.selectedCampus = state.settings.campus_name;
    }
    select.addEventListener('change', () => {
        state.selectedCampus = select.value;
        updateNextButtons();
    });
}

// ─── Step 2: Course Selection ────────────────────────────────────────────────

async function loadCourses() {
    if (!state.selectedDegrees.length || !state.selectedCampus) {
        state.allCourses = [];
        renderCourses();
        return;
    }

    try {
        const courses = await apiCall('/api/courses', 'POST', {
            degrees: state.selectedDegrees,
            campus: state.selectedCampus,
        });
        state.allCourses = courses;
        renderCourses();
    } catch (e) {
        showToast('שגיאה בטעינת קורסים', 'error');
    }
}

function renderCourses() {
    const container = document.getElementById('courses-list');
    const search = document.getElementById('course-search').value.toLowerCase();

    const filtered = state.allCourses.filter(c =>
        c.name.toLowerCase().includes(search)
    );

    container.innerHTML = filtered.map(course => {
        const isSelected = state.selectedCourses.some(s => s.name === course.name);
        const credits = course.credits ? ` (${course.credits} נ"ז)` : '';
        return `<div class="course-card ${isSelected ? 'selected' : ''}" data-name="${course.name}" data-number="${course.parent_course_number}" data-course-number="${course.course_number}">
            <span class="course-name">${course.name}${credits}</span>
            <span class="course-check">${isSelected ? '✓' : '+'}</span>
        </div>`;
    }).join('');

    // Bind click events
    container.querySelectorAll('.course-card').forEach(card => {
        card.addEventListener('click', () => toggleCourse(card));
    });

    updateSelectedChips();
    updateNextButtons();
}

function toggleCourse(card) {
    const name = card.dataset.name;
    const parentNumber = parseInt(card.dataset.number);
    const courseNumber = parseInt(card.dataset.courseNumber);

    const idx = state.selectedCourses.findIndex(c => c.name === name);
    if (idx >= 0) {
        state.selectedCourses.splice(idx, 1);
    } else {
        state.selectedCourses.push({name, parent_course_number: parentNumber, course_number: courseNumber});
    }

    renderCourses();
}

function updateSelectedChips() {
    const section = document.getElementById('selected-courses-section');
    const container = document.getElementById('selected-courses');
    const countEl = document.getElementById('selected-count');

    if (!state.selectedCourses.length) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    countEl.textContent = state.selectedCourses.length;

    container.innerHTML = state.selectedCourses.map(c =>
        `<span class="selected-chip">
            ${c.name}
            <button class="chip-remove" data-name="${c.name}">&times;</button>
        </span>`
    ).join('');

    container.querySelectorAll('.chip-remove').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const name = btn.dataset.name;
            state.selectedCourses = state.selectedCourses.filter(c => c.name !== name);
            renderCourses();
        });
    });
}

function initCourseSearch() {
    document.getElementById('course-search').addEventListener('input', () => {
        renderCourses();
    });
}

// ─── Step 3: Lecturer Preferences ────────────────────────────────────────────

async function loadLecturerData() {
    if (!state.selectedCourses.length) return;

    try {
        const data = await apiCall('/api/course_lecturers', 'POST', {
            degrees: state.selectedDegrees,
            campus: state.selectedCampus,
            courses: state.selectedCourses.map(c => c.name),
        });
        state.lecturerData = data;
        renderLecturerPrefs();
        renderAttendancePrefs();
    } catch (e) {
        showToast('שגיאה בטעינת מרצים', 'error');
    }
}

function renderLecturerPrefs() {
    const container = document.getElementById('lecturer-prefs-container');

    if (!Object.keys(state.lecturerData).length) {
        container.innerHTML = '<p class="empty-text">אין נתוני מרצים זמינים</p>';
        return;
    }

    container.innerHTML = state.selectedCourses.map(course => {
        const data = state.lecturerData[course.name];
        if (!data) return '';

        const lecturers = data.lecture || [];
        const practices = data.practice || [];

        let html = `<div class="lecturer-course-card">
            <h3 class="lecturer-course-name">${course.name}</h3>`;

        if (lecturers.length > 0) {
            html += `<div class="lecturer-section">
                <h4 class="lecturer-type">מרצים להרצאה</h4>
                <div class="lecturer-chips">
                    ${lecturers.map(l => `<button class="lecturer-chip" data-course="${course.name}" data-type="lecture" data-lecturer="${l}">${l}</button>`).join('')}
                </div>
            </div>`;
        }

        if (practices.length > 0) {
            html += `<div class="lecturer-section">
                <h4 class="lecturer-type">מרצים לתרגול / מעבדה</h4>
                <div class="lecturer-chips">
                    ${practices.map(l => `<button class="lecturer-chip" data-course="${course.name}" data-type="practice" data-lecturer="${l}">${l}</button>`).join('')}
                </div>
            </div>`;
        }

        html += '</div>';
        return html;
    }).join('');

    // Bind lecturer selection
    container.querySelectorAll('.lecturer-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            chip.classList.toggle('active');
            updateLecturerPrefsState();
        });
    });
}

function updateLecturerPrefsState() {
    state.lecturerPrefs = {};
    document.querySelectorAll('.lecturer-chip.active').forEach(chip => {
        const course = chip.dataset.course;
        const type = chip.dataset.type;
        const lecturer = chip.dataset.lecturer;

        if (!state.lecturerPrefs[course]) {
            state.lecturerPrefs[course] = {lecture: [], practice: []};
        }
        state.lecturerPrefs[course][type].push(lecturer);
    });
}

function renderAttendancePrefs() {
    const container = document.getElementById('attendance-prefs-container');

    if (state.settings.attendance_required_all_courses) {
        container.innerHTML = '<p class="empty-text">חובת נוכחות מופעלת לכל הקורסים (ניתן לשנות בהגדרות)</p>';
        return;
    }

    container.innerHTML = state.selectedCourses.map(course => {
        const data = state.lecturerData[course.name];
        if (!data) return '';

        const hasLecture = data.lecture && data.lecture.length > 0;
        const hasPractice = data.practice && data.practice.length > 0;

        return `<div class="attendance-course-card">
            <h3 class="attendance-course-name">${course.name}</h3>
            <div class="attendance-toggles">
                ${hasLecture ? `<label class="setting-toggle compact">
                    <span>נוכחות בהרצאה</span>
                    <input type="checkbox" class="att-check" data-course="${course.name}" data-type="lecture" checked>
                    <span class="toggle-slider"></span>
                </label>` : ''}
                ${hasPractice ? `<label class="setting-toggle compact">
                    <span>נוכחות בתרגול</span>
                    <input type="checkbox" class="att-check" data-course="${course.name}" data-type="practice" checked>
                    <span class="toggle-slider"></span>
                </label>` : ''}
            </div>
        </div>`;
    }).join('');

    container.querySelectorAll('.att-check').forEach(check => {
        check.addEventListener('change', () => {
            updateAttendancePrefsState();
        });
    });
}

function updateAttendancePrefsState() {
    state.attendancePrefs = {};
    document.querySelectorAll('.att-check').forEach(check => {
        const course = check.dataset.course;
        const type = check.dataset.type;
        if (!state.attendancePrefs[course]) {
            state.attendancePrefs[course] = {lecture: true, practice: true};
        }
        state.attendancePrefs[course][type] = check.checked;
    });
}

// ─── Step 4: Summary & Generate ──────────────────────────────────────────────

function updateSummary() {
    const degreeBtns = document.querySelectorAll('#degrees-list .chip-btn.active');
    const degreeNames = Array.from(degreeBtns).map(b => b.dataset.display);
    document.getElementById('summary-degrees').textContent = degreeNames.join(', ') || '-';
    document.getElementById('summary-campus').textContent = state.selectedCampus || '-';
    document.getElementById('summary-courses').textContent = state.selectedCourses.map(c => c.name).join(', ') || '-';

    const formats = [];
    document.querySelectorAll('.format-checkbox input:checked').forEach(cb => formats.push(cb.value));
    document.getElementById('summary-formats').textContent = formats.join(', ') || 'IMAGE';
}

async function generateSchedules() {
    const resultContainer = document.getElementById('generate-result');
    const loading = document.getElementById('result-loading');
    const success = document.getElementById('result-success');
    const error = document.getElementById('result-error');

    resultContainer.style.display = 'block';
    loading.style.display = 'flex';
    success.style.display = 'none';
    error.style.display = 'none';

    document.getElementById('generate-btn').disabled = true;

    try {
        const result = await apiCall('/api/generate', 'POST', {
            degrees: state.selectedDegrees,
            campus: state.selectedCampus,
            courses: state.selectedCourses.map(c => c.name),
            lecturer_preferences: state.lecturerPrefs,
            attendance_preferences: state.attendancePrefs,
        });

        loading.style.display = 'none';
        success.style.display = 'flex';
        document.getElementById('result-message').textContent = result.message;
        document.getElementById('result-status-message').textContent = result.status_message || '';

    } catch (e) {
        loading.style.display = 'none';
        error.style.display = 'flex';
        document.getElementById('error-message').textContent = e.data?.message || 'שגיאה ביצירת מערכת שעות';
    } finally {
        document.getElementById('generate-btn').disabled = false;
    }
}

async function downloadSchedules() {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/api/download';
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
}

// ─── Settings Sidebar ────────────────────────────────────────────────────────

function openSettings() {
    document.getElementById('settings-sidebar').classList.add('open');
    document.getElementById('settings-overlay').classList.add('show');
}

function closeSettings() {
    document.getElementById('settings-sidebar').classList.remove('open');
    document.getElementById('settings-overlay').classList.remove('show');
}

async function saveSettings() {
    const days = [];
    document.querySelectorAll('.days-grid input:checked').forEach(cb => days.push(cb.value));

    const formats = [];
    document.querySelectorAll('.format-grid input:checked').forEach(cb => formats.push(cb.value));

    const settings = {
        semester: document.getElementById('setting-semester').value,
        show_only_classes_in_days: days,
        output_formats: formats.length ? formats : ['IMAGE'],
        attendance_required_all_courses: document.getElementById('setting-attendance').checked,
        show_hertzog_and_yeshiva: document.getElementById('setting-hertzog').checked,
        show_only_courses_with_free_places: document.getElementById('setting-free-places').checked,
        show_only_courses_active_classes: document.getElementById('setting-active-classes').checked,
        show_only_courses_with_the_same_actual_number: document.getElementById('setting-same-number').checked,
        dont_show_courses_already_done: document.getElementById('setting-hide-done').checked,
        show_only_classes_can_enroll: document.getElementById('setting-can-enroll').checked,
        show_only_courses_with_prerequisite_done: document.getElementById('setting-prereq').checked,
        show_english_speaker_courses: document.getElementById('setting-english').checked,
    };

    try {
        const result = await apiCall('/api/settings', 'POST', settings);
        state.settings = result;
        showToast('ההגדרות נשמרו בהצלחה', 'success');
        closeSettings();
    } catch (e) {
        showToast('שגיאה בשמירת הגדרות', 'error');
    }
}

// ─── Login Modal ─────────────────────────────────────────────────────────────

function openLogin() {
    document.getElementById('login-modal').classList.add('open');
    document.getElementById('login-overlay').classList.add('show');
    checkLoginStatus();
}

function closeLogin() {
    document.getElementById('login-modal').classList.remove('open');
    document.getElementById('login-overlay').classList.remove('show');
}

async function checkLoginStatus() {
    try {
        const result = await apiCall('/api/login/status');
        if (result.logged_in) {
            document.getElementById('login-btn-text').textContent = result.username;
            document.getElementById('login-username').value = result.username;
        }
    } catch (e) { /* ignore */ }
}

async function doLogin() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const errorEl = document.getElementById('login-error');
    const successEl = document.getElementById('login-success');

    errorEl.style.display = 'none';
    successEl.style.display = 'none';

    if (!username || !password) {
        errorEl.textContent = 'נא למלא שם משתמש וסיסמה';
        errorEl.style.display = 'block';
        return;
    }

    document.getElementById('login-submit').disabled = true;
    document.getElementById('login-submit').textContent = 'מתחבר...';

    const endpoint = state.loginTab === 'microsoft' ? '/api/login/microsoft' : '/api/login';

    try {
        const result = await apiCall(endpoint, 'POST', {username, password});
        successEl.textContent = result.message;
        successEl.style.display = 'block';
        document.getElementById('login-btn-text').textContent = username;
        setTimeout(closeLogin, 1500);
    } catch (e) {
        const message = e.data?.message || 'שגיאה בהתחברות';
        errorEl.textContent = message;
        errorEl.style.display = 'block';

        // If standard login fails, suggest Microsoft login
        if (state.loginTab === 'standard') {
            errorEl.textContent = message + '\nנסה להתחבר דרך Microsoft';
        }
    } finally {
        document.getElementById('login-submit').disabled = false;
        document.getElementById('login-submit').textContent = 'התחבר';
    }
}

// ─── Courses Already Done ────────────────────────────────────────────────────

async function loadCoursesAlreadyDone() {
    try {
        const courses = await apiCall('/api/courses_already_done');
        renderCoursesAlreadyDone(courses);
    } catch (e) { /* ignore */ }
}

function renderCoursesAlreadyDone(doneList) {
    const container = document.getElementById('courses-done-list');
    if (!state.allCourses.length) {
        container.innerHTML = '<p class="empty-text">טען קורסים תחילה</p>';
        return;
    }

    const doneNumbers = new Set(doneList.map(c => c.parent_course_number));

    container.innerHTML = state.allCourses.map(course => {
        const checked = doneNumbers.has(course.parent_course_number) ? 'checked' : '';
        return `<label class="done-course-item">
            <input type="checkbox" class="done-course-check" data-number="${course.parent_course_number}" ${checked}>
            <span>${course.name}</span>
        </label>`;
    }).join('');
}

async function extractCoursesFromLevnet() {
    document.getElementById('extract-done-btn').disabled = true;
    document.getElementById('extract-done-btn').textContent = 'מחלץ נתונים...';

    try {
        const result = await apiCall('/api/courses_already_done/extract', 'POST');
        showToast('הקורסים חולצו בהצלחה', 'success');
        renderCoursesAlreadyDone(result.courses);
    } catch (e) {
        const message = e.data?.message || 'שגיאה בחילוץ נתונים';
        showToast(message, 'error');
    } finally {
        document.getElementById('extract-done-btn').disabled = false;
        document.getElementById('extract-done-btn').textContent = 'חלץ מלבנט אוטומטית';
    }
}

// ─── Personal Activities ─────────────────────────────────────────────────────

async function loadPersonalActivities() {
    try {
        const activities = await apiCall('/api/personal_activities');
        renderPersonalActivities(activities);
    } catch (e) { /* ignore */ }
}

function renderPersonalActivities(activities) {
    const container = document.getElementById('personal-activities-list');
    if (!activities.length) {
        container.innerHTML = '<p class="empty-text">אין פעילויות אישיות</p>';
        return;
    }

    container.innerHTML = activities.map(a => {
        const meetings = a.meetings.map(m => `${m.day} ${m.start_time}-${m.end_time}`).join(', ');
        return `<div class="personal-activity-item">
            <div class="activity-info">
                <strong>${a.name}</strong>
                <span class="activity-time">${meetings}</span>
            </div>
            <button class="btn-icon delete-activity" data-id="${a.id}" title="מחק">&times;</button>
        </div>`;
    }).join('');

    container.querySelectorAll('.delete-activity').forEach(btn => {
        btn.addEventListener('click', async () => {
            try {
                await apiCall(`/api/personal_activities/${btn.dataset.id}`, 'DELETE');
                loadPersonalActivities();
                showToast('הפעילות נמחקה', 'success');
            } catch (e) {
                showToast('שגיאה במחיקה', 'error');
            }
        });
    });
}

async function savePersonalActivity() {
    const name = document.getElementById('activity-name').value.trim();
    if (!name) {
        showToast('נא להזין שם פעילות', 'error');
        return;
    }

    const meetings = [];
    document.querySelectorAll('#activity-meetings .meeting-row').forEach(row => {
        meetings.push({
            day: row.querySelector('.meeting-day').value,
            start_time: row.querySelector('.meeting-start').value,
            end_time: row.querySelector('.meeting-end').value,
        });
    });

    try {
        await apiCall('/api/personal_activities', 'POST', {name, meetings});
        document.getElementById('activity-name').value = '';
        loadPersonalActivities();
        showToast('הפעילות נשמרה', 'success');
    } catch (e) {
        showToast(e.data?.message || 'שגיאה בשמירה', 'error');
    }
}

function addMeetingRow() {
    const container = document.getElementById('activity-meetings');
    const daysHTML = Array.from(document.querySelectorAll('#activity-meetings .meeting-row:first-child .meeting-day option'))
        .map(opt => `<option value="${opt.value}">${opt.textContent}</option>`).join('');

    const row = document.createElement('div');
    row.className = 'meeting-row';
    row.innerHTML = `
        <select class="form-select meeting-day">${daysHTML}</select>
        <input type="time" class="form-input meeting-start" value="08:00">
        <span>-</span>
        <input type="time" class="form-input meeting-end" value="10:00">
        <button class="btn-icon remove-meeting-btn" title="הסר">&times;</button>
    `;
    container.appendChild(row);

    row.querySelector('.remove-meeting-btn').addEventListener('click', () => row.remove());
}

// ─── Collapsible Cards ───────────────────────────────────────────────────────

function initCollapsibles() {
    document.querySelectorAll('.collapsible .card-header').forEach(header => {
        header.addEventListener('click', () => {
            const body = header.nextElementSibling;
            body.classList.toggle('collapsed');
            header.querySelector('.collapse-icon').classList.toggle('rotated');
        });
    });
}

// ─── Extract Activities Can Enroll ────────────────────────────────────────────

async function extractActivitiesCanEnroll() {
    const btn = document.getElementById('extract-enroll-btn');
    btn.disabled = true;
    btn.textContent = 'מעדכן...';

    try {
        const result = await apiCall('/api/activities_can_enroll', 'POST');
        showToast(result.message, 'success');
    } catch (e) {
        showToast(e.data?.message || 'שגיאה בעדכון', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'עדכן רשימת הרשמה';
    }
}

// ─── Initialization ──────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    // Init step 1
    initDegrees();
    initCampus();

    // Init step 2
    initCourseSearch();
    initCollapsibles();

    // Navigation buttons
    document.querySelectorAll('.btn-next').forEach(btn => {
        btn.addEventListener('click', () => {
            const next = parseInt(btn.dataset.next);
            // Load courses when moving to step 2
            if (next === 2) loadCourses();
            goToStep(next);
        });
    });

    document.querySelectorAll('.btn-prev').forEach(btn => {
        btn.addEventListener('click', () => goToStep(parseInt(btn.dataset.prev)));
    });

    // Step indicators clickable
    document.querySelectorAll('.step').forEach(el => {
        el.addEventListener('click', () => {
            const step = parseInt(el.dataset.step);
            if (step <= state.currentStep || el.classList.contains('completed')) {
                if (step === 2) loadCourses();
                goToStep(step);
            }
        });
    });

    // Settings
    document.getElementById('settings-toggle').addEventListener('click', openSettings);
    document.getElementById('settings-close').addEventListener('click', closeSettings);
    document.getElementById('settings-overlay').addEventListener('click', closeSettings);
    document.getElementById('save-settings-btn').addEventListener('click', saveSettings);
    document.getElementById('extract-enroll-btn').addEventListener('click', extractActivitiesCanEnroll);

    // Login
    document.getElementById('login-toggle').addEventListener('click', openLogin);
    document.getElementById('login-close').addEventListener('click', closeLogin);
    document.getElementById('login-overlay').addEventListener('click', closeLogin);
    document.getElementById('login-submit').addEventListener('click', doLogin);
    document.getElementById('login-password').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') doLogin();
    });

    // Login tabs
    document.querySelectorAll('.login-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.login-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            state.loginTab = tab.dataset.tab;
        });
    });

    // Generate
    document.getElementById('generate-btn').addEventListener('click', generateSchedules);
    document.getElementById('download-btn').addEventListener('click', downloadSchedules);

    // Courses already done
    document.getElementById('extract-done-btn').addEventListener('click', extractCoursesFromLevnet);

    // Personal activities
    document.getElementById('save-activity-btn').addEventListener('click', savePersonalActivity);
    document.querySelector('.add-meeting-btn').addEventListener('click', addMeetingRow);
    loadPersonalActivities();

    // Check login status
    checkLoginStatus();

    // Update initial button state
    updateNextButtons();

    // Restore degree selection from settings
    if (state.settings.degrees) {
        state.settings.degrees.forEach(d => {
            const btn = document.querySelector(`[data-degree="${d}"]`);
            if (btn) {
                btn.classList.add('active');
                if (!state.selectedDegrees.includes(d)) {
                    state.selectedDegrees.push(d);
                }
            }
        });
        updateNextButtons();
    }
});
