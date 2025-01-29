const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const errorDiv = document.getElementById('error');
const loadingDiv = document.getElementById('loading');
const resultsDiv = document.getElementById('results');

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
