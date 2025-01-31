const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const errorDiv = document.getElementById('error');
const loadingDiv = document.getElementById('loading');
const resultsDiv = document.getElementById('results');
const criteriaForm = document.getElementById('criteriaForm');
const addCriteriaBtn = document.getElementById('addCriteriaBtn');

let gradingCriteria = {};

// Load grading criteria from localStorage on page load
window.addEventListener('DOMContentLoaded', () => {
    const savedCriteria = localStorage.getItem('gradingCriteria');
    if (savedCriteria) {
        gradingCriteria = JSON.parse(savedCriteria);
        displaySavedCriteria();
    }
});

uploadZone.addEventListener('click', () => fileInput.click());
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.style.background = '#f5f5f5';
});
uploadZone.addEventListener('dragleave', () => {
    uploadZone.style.background = '';
});
uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.style.background = '';
    handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', (e) => {
    handleFile(e.target.files[0]);
});

// Remove the form's submit event, just listen for the button click
addCriteriaBtn.addEventListener('click', () => {
    const formData = new FormData(criteriaForm);
    const questionId = formData.get('questionId');
    const keywords = formData.get('keywords').split(',').map(k => k.trim());
    const points = parseInt(formData.get('points'), 10);

    gradingCriteria[questionId] = { keywords, points };
    localStorage.setItem('gradingCriteria', JSON.stringify(gradingCriteria));
    criteriaForm.reset();
    displaySavedCriteria();
});

function handleFile(file) {
    if (!file) return;
    
    const validTypes = [
        'text/csv',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel'
    ];
    
    if (!validTypes.includes(file.type)) {
        errorDiv.textContent = 'Please upload a CSV or Excel file';
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('criteria', JSON.stringify(gradingCriteria));

    errorDiv.textContent = '';
    loadingDiv.style.display = 'block';
    resultsDiv.innerHTML = '';

    fetch('/api/quiz/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error('Upload failed');
        return response.json();
    })
    .then(data => {
        displayResults(data);
    })
    .catch(err => {
        errorDiv.textContent = err.message;
    })
    .finally(() => {
        loadingDiv.style.display = 'none';
    });
}

function displayResults(data) {
    const questionPerformance = data.question_performance;
    const studentScores = data.average_scores;

    let html = `
        <h2>Question Performance</h2>
        <table>
            <tr>
                <th>Question</th>
                <th>Correct Answers</th>
                <th>Total Responses</th>
                <th>Percentage</th>
            </tr>
    `;

    for (const [question, stats] of Object.entries(questionPerformance)) {
        html += `
            <tr>
                <td>${question}</td>
                <td>${stats.correct}</td>
                <td>${stats.total}</td>
                <td>${stats.percentage.toFixed(1)}%</td>
            </tr>
        `;
    }

    html += `
        </table>
        <h2>Student Scores</h2>
        <table>
            <tr>
                <th>Student</th>
                <th>Score</th>
            </tr>
    `;

    for (const [student, score] of Object.entries(studentScores)) {
        html += `
            <tr>
                <td>${student}</td>
                <td>${(score * 100).toFixed(1)}%</td>
            </tr>
        `;
    }

    html += '</table>';
    resultsDiv.innerHTML = html;
}

// Function to display saved grading criteria
function displaySavedCriteria() {
    const criteriaList = document.getElementById('criteriaList') || createCriteriaList();
    criteriaList.innerHTML = '';

    for (const [question, details] of Object.entries(gradingCriteria)) {
        const listItem = document.createElement('li');
        listItem.textContent = `Question ${question}: Keywords - [${details.keywords.join(', ')}], Points - ${details.points}`;
        criteriaList.appendChild(listItem);
    }
}

function createCriteriaList() {
    const criteriaSection = document.createElement('div');
    criteriaSection.id = 'savedCriteria';
    criteriaSection.innerHTML = '<h3>Saved Grading Criteria:</h3><ul id="criteriaList"></ul>';
    document.body.insertBefore(criteriaSection, resultsDiv);
    return document.getElementById('criteriaList');
}
