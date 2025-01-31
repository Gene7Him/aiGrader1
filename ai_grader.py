import pandas as pd

# Function to read uploaded CSV/Excel files
def read_file(file_path):
    try:
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            return pd.read_excel(file_path)
        else:
            raise ValueError("Invalid file format. Only CSV and Excel are supported.")
    except Exception as e:
        return {"error": str(e)}

# Function to evaluate student responses based on grading criteria
def evaluate_response(question, response, criteria):
    keywords = criteria.get("keywords", [])
    ideal_answer = criteria.get("ideal_answer", "")

    # Check if any keyword is present in the student's response
    for keyword in keywords:
        if keyword.lower() in response.lower():
            return True

    # Check if the response matches the ideal answer
    if ideal_answer and ideal_answer.lower() in response.lower():
        return True

    return False

# Function to grade the responses and store the results
def grade_responses(df, grading_criteria):
    results = []

    for _, row in df.iterrows():
        question = row['question']
        response = row['student_answer']

        # Fetch grading criteria for the current question
        criteria = grading_criteria.get(question, {})

        if evaluate_response(question, response, criteria):
            results.append({'question': question, 'student': row['student_name'], 'correct': True})
        else:
            results.append({'question': question, 'student': row['student_name'], 'correct': False})

    return results

# Function to generate aggregated insights (e.g., percentage correct per question and average scores)
def aggregated_insights(results, df):
    question_performance = {}

    # Calculate performance for each question
    for result in results:
        question = result['question']
        correct = result['correct']

        if question not in question_performance:
            question_performance[question] = {'correct': 0, 'total': 0}

        question_performance[question]['total'] += 1
        if correct:
            question_performance[question]['correct'] += 1

    # Calculate percentage correct for each question
    for question, data in question_performance.items():
        question_performance[question]['percentage'] = (data['correct'] / data['total']) * 100

    # Calculate average score across all students (considering correct answers per student)
    student_scores = df.groupby('student_name')['score'].mean()

    aggregated = {
        'question_performance': question_performance,
        'average_scores': student_scores.to_dict()
    }

    return aggregated

# Main function to handle file processing and grading
def process_grading(file_path, grading_criteria):
    # Step 1: Read the uploaded file
    df = read_file(file_path)
    if isinstance(df, dict) and "error" in df:
        return df  # Return error message if the file is invalid

    # Step 2: Grade Responses
    results = grade_responses(df, grading_criteria)

    # Step 3: Generate Insights
    insights = aggregated_insights(results, df)

    return insights
