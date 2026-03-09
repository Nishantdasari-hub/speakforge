import { useEffect, useState } from "react";
import Swal from "sweetalert2";

export default function AdminQuestions() {

  const token = localStorage.getItem("token");

  const [tests, setTests] = useState([]);
  const [selectedTest, setSelectedTest] = useState("");
  const [questions, setQuestions] = useState([]);

  const [questionText, setQuestionText] = useState("");
  const [timeLimit, setTimeLimit] = useState(30);
  const [questionType, setQuestionType] = useState("audio");

  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState("");
  const [editTimeLimit, setEditTimeLimit] = useState(30);
  const [editType, setEditType] = useState("audio");


  // Load Tests
  useEffect(() => {
    fetch("http://127.0.0.1:8000/tests/", {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
      .then(res => res.json())
      .then(data => setTests(data));
  }, []);


  // Load Questions
  const loadQuestions = async (testId) => {

    const res = await fetch(`http://127.0.0.1:8000/tests/${testId}/questions`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    const data = await res.json();
    setQuestions(data);
  };


  // Select Test
  const handleTestSelect = (e) => {

    const id = e.target.value;
    setSelectedTest(id);
    setQuestions([]);

    if (id) loadQuestions(id);

  };


  // Create Question
  const createQuestion = async () => {

    if (!questionText) {
      Swal.fire("Error", "Question text required", "error");
      return;
    }

    const res = await fetch(`http://127.0.0.1:8000/tests/${selectedTest}/questions`, {

      method: "POST",

      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },

      body: JSON.stringify({
        question_text: questionText,
        time_limit: timeLimit,
        question_type: questionType,
        order_number: questions.length + 1
      })

    });

    setQuestionText("");

    loadQuestions(selectedTest);

    Swal.fire("Success", "Question created", "success");

  };


  // Delete Question
  const deleteQuestion = async (id) => {

    const confirm = await Swal.fire({
      title: "Delete Question?",
      icon: "warning",
      showCancelButton: true
    });

    if (!confirm.isConfirmed) return;

    const res = await fetch(`http://127.0.0.1:8000/tests/${selectedTest}/questions/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    if (res.ok) {

      loadQuestions(selectedTest);
      Swal.fire("Deleted", "Question removed", "success");

    } else {

      Swal.fire("Error", "Delete failed", "error");

    }

  };


  // Start Edit
  const startEditQuestion = (q) => {

    setEditingId(q.id);
    setEditText(q.question_text);
    setEditTimeLimit(q.time_limit);
    setEditType(q.question_type);

  };


  // Save Edit
  const saveEditQuestion = async () => {

    const res = await fetch(`http://127.0.0.1:8000/tests/${selectedTest}/questions/${editingId}`, {

      method: "PUT",

      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },

      body: JSON.stringify({
        question_text: editText,
        time_limit: parseInt(editTimeLimit),
        question_type: editType,
        order_number: questions.find(q => q.id === editingId)?.order_number || 1
      })

    });

    if (res.ok) {

      loadQuestions(selectedTest);
      setEditingId(null);

      Swal.fire("Updated", "Question updated", "success");

    } else {

      Swal.fire("Error", "Update failed", "error");

    }

  };


  const cancelEdit = () => {
    setEditingId(null);
  };


  return (

    <div className="min-h-screen bg-gray-900 text-white p-6">

      <div className="max-w-6xl mx-auto space-y-8">


        {/* ================= HEADER ================= */}

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">

          <h1 className="text-2xl font-bold mb-4">
            📝 Manage Questions
          </h1>

          <label className="text-gray-300 block mb-2">
            Select Test
          </label>

          <select
            value={selectedTest}
            onChange={handleTestSelect}
            className="w-full p-3 bg-gray-700 border border-gray-600 rounded"
          >

            <option value="">Choose Test</option>

            {tests.map(test => (

              <option key={test.id} value={test.id}>
                {test.title}
              </option>

            ))}

          </select>

        </div>


        {/* ================= CREATE QUESTION ================= */}

        {selectedTest && (

          <div className="bg-gray-800 p-6 rounded-lg border border-blue-600">

            <h2 className="text-xl font-semibold mb-4">
              ➕ Create New Question
            </h2>

            <textarea
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              placeholder="Enter question text..."
              className="w-full p-4 bg-gray-700 border border-gray-600 rounded mb-4"
              rows="4"
            />

            <div className="grid grid-cols-2 gap-4 mb-4">

              <input
                type="number"
                value={timeLimit}
                onChange={(e) => setTimeLimit(e.target.value)}
                className="p-3 bg-gray-700 border border-gray-600 rounded"
              />

              <select
                value={questionType}
                onChange={(e) => setQuestionType(e.target.value)}
                className="p-3 bg-gray-700 border border-gray-600 rounded"
              >

                <option value="audio">🎤 Audio Question</option>
                <option value="text">📝 Text Question</option>

              </select>

            </div>

            <button
              onClick={createQuestion}
              className="bg-blue-600 px-6 py-3 rounded hover:bg-blue-700"
            >
              Create Question
            </button>

          </div>

        )}


        {/* ================= QUESTIONS LIST ================= */}

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">

          <h2 className="text-xl font-semibold mb-6">
            📋 Questions List
          </h2>


          {questions.length > 0 ? (

            <div className="space-y-4">

              {questions.map(q => (

                <div
                  key={q.id}
                  className="bg-gray-700 p-4 rounded flex justify-between"
                >

                  {editingId === q.id ? (

                    <div className="w-full">

                      <textarea
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        className="w-full p-3 bg-gray-600 rounded mb-3"
                      />

                      <div className="flex gap-3 mb-3">

                        <input
                          type="number"
                          value={editTimeLimit}
                          onChange={(e) => setEditTimeLimit(e.target.value)}
                          className="p-2 bg-gray-600 rounded"
                        />

                        <select
                          value={editType}
                          onChange={(e) => setEditType(e.target.value)}
                          className="p-2 bg-gray-600 rounded"
                        >

                          <option value="audio">Audio</option>
                          <option value="text">Text</option>

                        </select>

                      </div>

                      <div className="flex gap-2">

                        <button
                          onClick={saveEditQuestion}
                          className="bg-green-600 px-4 py-2 rounded"
                        >
                          Save
                        </button>

                        <button
                          onClick={cancelEdit}
                          className="bg-gray-500 px-4 py-2 rounded"
                        >
                          Cancel
                        </button>

                      </div>

                    </div>

                  ) : (

                    <>
                      <div>

                        <p className="font-medium">
                          {q.question_text}
                        </p>

                        <div className="flex gap-2 mt-2 text-sm">

                          <span className="bg-blue-600 px-2 py-1 rounded">
                            {q.question_type === "audio" ? "🎤 Audio" : "📝 Text"}
                          </span>

                          <span className="bg-gray-600 px-2 py-1 rounded">
                            {q.time_limit}s
                          </span>

                        </div>

                      </div>

                      <div className="flex gap-2">

                        <button
                          onClick={() => startEditQuestion(q)}
                          className="bg-yellow-600 px-3 py-2 rounded"
                        >
                          ✏️
                        </button>

                        <button
                          onClick={() => deleteQuestion(q.id)}
                          className="bg-red-600 px-3 py-2 rounded"
                        >
                          🗑️
                        </button>

                      </div>
                    </>

                  )}

                </div>

              ))}

            </div>

          ) : (

            <div className="text-gray-400 text-center py-10">
              No questions yet
            </div>

          )}

        </div>

      </div>

    </div>

  );

}