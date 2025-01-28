from http.server import HTTPServer, BaseHTTPRequestHandler
import cgi
import json
import pandas as pd
import io
import os

class QuizHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            try:
                # Read and serve the HTML file
                with open('index.html', 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, "File not found")
        else:
            self.send_error(404, "Path not found")

    def do_POST(self):
        if self.path == '/api/quiz/upload':
            try:
                # Parse the multipart form data
                content_type = self.headers.get('Content-Type')
                if not content_type or not content_type.startswith('multipart/form-data'):
                    raise ValueError("Invalid content type")

                # Parse the form data
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )

                # Get the file
                file_item = form['file']
                file_content = file_item.file.read()
                filename = file_item.filename

                # Process the file
                results = self.process_file(file_content, filename)

                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(results).encode())

            except Exception as e:
                self.send_error(400, str(e))

    def process_file(self, file_content, filename):
        # Read the file
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_content))
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                raise ValueError("Invalid file format")

            # Validate required columns
            required_columns = {'student_name', 'question', 'student_answer'}
            if not all(col in df.columns for col in required_columns):
                raise ValueError("Missing required columns")

            # Process the responses using the existing grading logic
            results = grade_responses(df)
            insights = generate_insights(results, df)
            
            return insights

        except Exception as e:
            raise ValueError(f"Error processing file: {str(e)}")

def grade_responses(df):
    # Simplified grading criteria
    grading_criteria = {
        "Q1": {
            "keywords": ["capital", "france", "paris"],
            "ideal_answer": "The capital of France is Paris."
        },
        "Q2": {
            "keywords": ["largest", "whale", "earth", "mammal"],
            "ideal_answer": "The largest mammal on earth is the blue whale."
        }
    }

    results = []
    for _, row in df.iterrows():
        question = row['question']
        response = row['student_answer']
        criteria = grading_criteria.get(question, {})
        
        # Check if answer is correct
        correct = False
        if criteria:
            # Check keywords
            keywords = criteria.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in response.lower():
                    correct = True
                    break
            
            # Check ideal answer
            if not correct and criteria.get("ideal_answer"):
                if criteria["ideal_answer"].lower() in response.lower():
                    correct = True

        results.append({
            'question': question,
            'student': row['student_name'],
            'correct': correct
        })

    return results

def generate_insights(results, df):
    # Calculate question performance
    question_performance = {}
    for result in results:
        question = result['question']
        if question not in question_performance:
            question_performance[question] = {'correct': 0, 'total': 0}
        
        question_performance[question]['total'] += 1
        if result['correct']:
            question_performance[question]['correct'] += 1

    # Calculate percentages
    for stats in question_performance.values():
        stats['percentage'] = (stats['correct'] / stats['total']) * 100

    # Calculate student scores
    student_scores = {}
    for result in results:
        student = result['student']
        if student not in student_scores:
            student_scores[student] = {'correct': 0, 'total': 0}
        
        student_scores[student]['total'] += 1
        if result['correct']:
            student_scores[student]['correct'] += 1

    # Convert to average scores
    average_scores = {
        student: stats['correct'] / stats['total']
        for student, stats in student_scores.items()
    }

    return {
        'question_performance': question_performance,
        'average_scores': average_scores
    }

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8000), QuizHandler)
    print("Server started on http://localhost:8000")
    server.serve_forever()