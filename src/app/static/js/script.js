function getSelectedDegrees() {
    let selectedDegrees = [];
    document.querySelectorAll('.degree-item.selected').forEach(item => {
        selectedDegrees.push(item.dataset.degree);
    });
    selectedDegrees = Array.from(selectedDegrees)
    return selectedDegrees;
}

// Update campuses based on selected degrees
async function loadCampuses() {
        if (getSelectedDegrees().length === 0) {
            // Reset the dropdown when no degrees are selected
            updateCampusesOptions([]);
            // Clear courses if no degrees are selected
            loadCourses();
            return;
        }

        const response = await fetch('/get_campuses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ degrees: getSelectedDegrees() })
        });

        const campuses = await response.json();
        updateCampusesOptions(campuses);
        loadCourses();
        
}


// Toggle course selection (add/remove chip)
function toggleCourseSelection(course) {
    const selectedCourses = document.getElementById('selected-courses');

    // Check if already exists
    const existingChip = Array.from(selectedCourses.children)
        .find(chip => chip.textContent.includes(course));

    if (existingChip) {
        existingChip.remove();
    } else {
        const chip = document.createElement('div');
        chip.className = 'chip';
        chip.innerHTML = `
            <span class="close">×</span>
            <span class="mr-2">${course}</span>
        `;
        chip.querySelector('.close').addEventListener('click', () => {
            chip.remove();
            // Deselect the corresponding course in the list
            const courseItem = Array.from(document.querySelectorAll('#courses-list .course-item'))
                .find(item => item.textContent === course);
            if (courseItem) {
                courseItem.classList.remove('selected');
            }
        });
        selectedCourses.appendChild(chip);
    }
}

function updateCampusesOptions(items) {
    const dropdown = document.getElementById("campuses");
    const previousValue = dropdown.value;

    if (items.length === 0) {
        dropdown.innerHTML = '<option value="">-- בחר תואר ולאחר מכן קמפוס --</option>';
        renderCourses([]);
        removeInvalidSelectedCourses([]);
        return;
    }

    dropdown.innerHTML = '<option value="">-- בחר קמפוס --</option>';

    items.forEach(item => {
        const option = document.createElement('option');
        option.value = item;
        option.textContent = item;
        dropdown.appendChild(option);
    });

    // Restore previous selection if it still exists
    if (items.includes(previousValue)) {
        dropdown.value = previousValue;
    }
}




// Load courses for the selected campus and degrees
async function loadCourses() {
    const campus = document.getElementById('campuses').value;
    if (!campus || getSelectedDegrees().length === 0) {
        renderCourses([]);
        removeInvalidSelectedCourses([]);
        return;
    }
    const response = await fetch('/get_courses', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            degrees: getSelectedDegrees(),
            campus: campus
        })
    });
    
    const courses = await response.json();
    renderCourses(courses);
    removeInvalidSelectedCourses(courses);
}

// Remove selected courses if they are no longer available
function removeInvalidSelectedCourses(availableCourses) {
    const selectedCoursesContainer = document.getElementById('selected-courses');
    const selectedChips = Array.from(selectedCoursesContainer.children);

    selectedChips.forEach(chip => {
        const courseName = chip.querySelector('span:not(.close)').textContent.trim();
        if (!availableCourses.includes(courseName)) {
            chip.remove(); // Remove from selected list if no longer available
        }
    });
}

// Render courses in the courses list
function renderCourses(courses) {
    const coursesList = document.getElementById('courses-list');
    coursesList.innerHTML = ''; // Clear previous

    courses.forEach(course => {
        const courseItem = document.createElement('div');
        courseItem.className = 'course-item';
        courseItem.textContent = course;

        // Check if already selected
        if (Array.from(document.querySelectorAll('#selected-courses .chip'))
            .some(chip => chip.textContent.includes(course))) {
            courseItem.classList.add('selected');
        }

        courseItem.addEventListener('click', () => {
            courseItem.classList.toggle('selected');
            toggleCourseSelection(course);
        });

        coursesList.appendChild(courseItem);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // Degree selection
    document.querySelectorAll('.degree-item').forEach(item => {
        item.addEventListener('click', () => {
            item.classList.toggle('selected');
            loadCampuses();
        });
    });

    // Campus selection
    document.getElementById('campuses').addEventListener('change', loadCourses);

    // Search functionality
    document.getElementById('search-box').addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase();
        const courses = document.querySelectorAll('#courses-list .course-item');

        courses.forEach(course => {
            const courseName = course.textContent.toLowerCase();
            if (courseName.includes(searchTerm)) {
                course.style.display = 'block';
            } else {
                course.style.display = 'none';
            }
        });
    });

    document.getElementById('generate-btn').addEventListener('click', async () => {
        const selectedDegrees = getSelectedDegrees();
        const selectedCampus = document.getElementById('campuses').value;
        const selectedCourses = Array.from(document.querySelectorAll('#selected-courses .chip span:not(.close)'))
                                     .map(chip => chip.textContent.trim());
    
        if (!selectedDegrees.length || !selectedCampus || !selectedCourses.length) {
            alert("נא לבחור תואר, קמפוס וקורסים");
            return;
        }
    
        // Remove any existing loading animation
        let existingLoader = document.getElementById('loading-container');
        if (existingLoader) {
            existingLoader.remove();
        }
    
        // Create a new loading spinner container at the bottom of #container
        const loadingContainer = document.createElement('div');
        loadingContainer.id = "loading-container";
        loadingContainer.innerHTML = `
            <div class="spinner"></div>
            <span id="loading-text">יוצר מערכת שעות נא להמתין...</span>
        `;
    
        // Append loading container **inside #container at the bottom**
        document.getElementById("container").appendChild(loadingContainer);
    
        // Auto-scroll to loading spinner
        loadingContainer.scrollIntoView({ behavior: "smooth", block: "center" });
    
        const requestData = {
            degrees: selectedDegrees,
            campus: selectedCampus,
            courses: selectedCourses
        };
    
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });
    
            const result = await response.json();
    
            if (result.zip) {
                document.getElementById('loading-text').textContent = "נוצר בהצלחה ✅";

                // Use POST method to download the zip file
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = '/download_zip';
                document.body.appendChild(form);
                form.submit();
                document.body.removeChild(form);
    
                // Remove the loading spinner after success
                setTimeout(() => {
                    loadingContainer.remove();
                }, 2000);
            }
        } catch (error) {
            console.error('Error generating files:', error);
            document.getElementById('loading-text').textContent = "שגיאה ביצירת הקבצים ❌";
        }
    });
});
