from http.server import HTTPServer, BaseHTTPRequestHandler
import cgi
import json
import pandas as pd
import io
import os
import httpx
import asyncio
from typing import List, Dict, Any

# Constants
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Store API key in environment variable
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

class QuizHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            try:
                with open('index.html', 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, "File not found")
        elif self.path == '/styles.css':
            try:
                with open('styles.css', 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/css')
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, "File not found")
        elif self.path == '/script.js':
            try:
                with open('script.js', 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/javascript')
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, "File not found")
        else:
            self.send_error(404, "Path not found")

    def do_POST(self):
        if self.path == '/api/quiz/upload':
            try:
                content_type = self.headers.get('Content-Type')
                if not content_type or not content_type.startswith('multipart/form-data'):
                    raise ValueError("Invalid content type")

                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )

                file_item = form['file']
                file_content = file_item.file.read()
                filename = file_item.filename

                # Use asyncio to run the async process_file function
                results = asyncio.run(self.process_file(file_content, filename))

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(results).encode())

            except Exception as e:
                self.send_error(400, str(e))

    async def process_file(self, file_content, filename):
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_content))
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                raise ValueError("Invalid file format")

            required_columns = {'student_name', 'question', 'student_answer'}
            if not all(col in df.columns for col in required_columns):
                raise ValueError("Missing required columns")

            # Await the async grade_responses function
            results = await grade_responses(df)
            insights = generate_insights(results, df)
            
            return insights

        except Exception as e:
            raise ValueError(f"Error processing file: {str(e)}")

async def grade_single_response(question: str, student_answer: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Grade a single response using the Groq API."""
    prompt = f"""You are grading a student's answer to the following question:

Question: {question}
Student's Answer: {student_answer}

Please evaluate the answer based on:
1. Factual correctness
2. Completeness of response
3. Understanding of core concepts

Respond with a JSON object containing:
{{
    "correct": true/false,
    "feedback": "brief explanation of grade"
}}"""

    try:
        response = await client.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "mixtral-8x7b-32768",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 150
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            grading = json.loads(result['choices'][0]['message']['content'])
            return grading
        else:
            print(f"Error from Groq API: {response.status_code}")
            return {"correct": False, "feedback": "Error in grading"}
            
    except Exception as e:
        print(f"Error grading response: {str(e)}")
        return {"correct": False, "feedback": "Error in grading"}

async def grade_responses(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Grade all responses using the Groq API."""
    results = []
    
    async with httpx.AsyncClient() as client:
        # Create a list of tasks for all responses
        tasks = [
            grade_single_response(
                row['question'],
                row['student_answer'],
                client
            )
            for _, row in df.iterrows()
        ]
        
        # Wait for all grading tasks to complete
        gradings = await asyncio.gather(*tasks)
        
        # Combine results with student information
        for (_, row), grading in zip(df.iterrows(), gradings):
            results.append({
                'question': row['question'],
                'student': row['student_name'],
                'correct': grading['correct'],
                'feedback': grading['feedback']
            })
    
    return results

def generate_insights(results: List[Dict[str, Any]], df: pd.DataFrame) -> Dict[str, Any]:
    """Generate insights from grading results."""
    # Initialize performance dictionaries
    question_performance = {}
    student_scores = {}
    
    # Calculate performance metrics
    for result in results:
        # Update question performance
        question = result['question']
        if question not in question_performance:
            question_performance[question] = {'correct': 0, 'total': 0}
        
        question_performance[question]['total'] += 1
        if result['correct']:
            question_performance[question]['correct'] += 1
        
        # Update student scores
        student = result['student']
        if student not in student_scores:
            student_scores[student] = {'correct': 0, 'total': 0}
        
        student_scores[student]['total'] += 1
        if result['correct']:
            student_scores[student]['correct'] += 1
    
    # Calculate percentages for questions
    for stats in question_performance.values():
        stats['percentage'] = (stats['correct'] / stats['total']) * 100
    
    # Convert student scores to averages
    average_scores = {
        student: stats['correct'] / stats['total']
        for student, stats in student_scores.items()
    }
    
    return {
        'question_performance': question_performance,
        'average_scores': average_scores
    }

if __name__ == '__main__':
    if not GROQ_API_KEY:
        print("Warning: GROQ_API_KEY environment variable not set")
    
    server = HTTPServer(('localhost', 8000), QuizHandler)
    print("Server started on http://localhost:8000")
    server.serve_forever()
